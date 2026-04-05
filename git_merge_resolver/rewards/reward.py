"""
Reward computation for the Git Merge Conflict Resolver environment.

Implements a multi-component reward function that provides meaningful
partial credit signal throughout the episode, not just at the end.

Score components (total: 1.0):
  - Exact/near-exact match vs ground truth: 0.40
  - Syntactic validity (Python AST parse): 0.30
  - Semantic element preservation: 0.20
  - Absence of conflict markers: 0.10
"""

from __future__ import annotations

from typing import List, Optional

from git_merge_resolver.models import MergeReward
from git_merge_resolver.utils.diff_utils import (
    contains_conflict_markers,
    extract_key_elements,
    is_partially_syntactically_valid,
    is_python_file,
    is_syntax_valid,
    normalize_whitespace,
    sequence_similarity,
)

# Reward component weights
WEIGHT_MATCH = 0.40
WEIGHT_SYNTAX = 0.30
WEIGHT_SEMANTIC = 0.20
WEIGHT_NO_MARKERS = 0.10

# Penalty amounts
PENALTY_INVALID_CONFLICT_ID = 0.05
PENALTY_ALREADY_RESOLVED = 0.02
PENALTY_EMPTY_RESOLUTION = 0.10
PENALTY_UNRESOLVED_AT_END = 0.10

# Explanation bonus cap
EXPLANATION_BONUS_MAX = 0.05


def compute_match_score(agent_resolution: str, ground_truth: str) -> float:
    """
    Compute the match component score (weight: 0.40).

    Returns 1.0 for exact match (whitespace-normalized), otherwise
    SequenceMatcher similarity.
    """
    if not ground_truth.strip():
        return 1.0 if not agent_resolution.strip() else 0.5

    norm_agent = normalize_whitespace(agent_resolution)
    norm_truth = normalize_whitespace(ground_truth)

    if norm_agent == norm_truth:
        return 1.0

    return sequence_similarity(agent_resolution, ground_truth)


def compute_syntax_score(
    agent_resolution: str,
    file_path: str,
    full_file_context: Optional[str] = None,
) -> float:
    """
    Compute the syntax validity component score (weight: 0.30).

    For Python files:
      - 1.0 if the full file (with resolution applied) is valid Python
      - 0.5 if the resolution snippet itself is partially valid
      - 0.0 if clearly invalid

    For non-Python files: always returns 1.0.
    """
    if not is_python_file(file_path):
        return 1.0

    # Try parsing the full file context if provided
    if full_file_context and is_syntax_valid(full_file_context):
        return 1.0

    # Fall back to checking the snippet itself
    if is_syntax_valid(agent_resolution):
        return 1.0

    if is_partially_syntactically_valid(agent_resolution):
        return 0.5

    return 0.0


def compute_semantic_score(agent_resolution: str, ground_truth: str) -> float:
    """
    Compute the semantic element preservation score (weight: 0.20).

    Measures what fraction of key identifiers (function names, variable names,
    class names) from the ground truth appear in the agent's resolution.
    """
    key_elements = extract_key_elements(ground_truth)
    if not key_elements:
        return 1.0  # No key elements to check → full score

    present = sum(1 for elem in key_elements if elem in agent_resolution)
    return present / len(key_elements)


def compute_no_markers_score(agent_resolution: str) -> float:
    """
    Compute the no-conflict-markers component score (weight: 0.10).

    Returns 1.0 if no markers are present, 0.0 otherwise.
    """
    return 0.0 if contains_conflict_markers(agent_resolution) else 1.0


def compute_explanation_bonus(explanation: Optional[str], ground_truth: str) -> float:
    """
    Compute a small bonus for providing a meaningful explanation (up to 0.05).

    The explanation gets bonus points if it:
    - Is non-empty and non-trivial (> 20 characters)
    - Mentions at least one key element from the ground truth
    """
    if not explanation or len(explanation.strip()) < 20:
        return 0.0

    key_elements = extract_key_elements(ground_truth)
    if not key_elements:
        return EXPLANATION_BONUS_MAX * 0.5  # Generic bonus for any explanation

    mentions = sum(1 for elem in key_elements if elem in explanation)
    fraction = min(mentions / len(key_elements), 1.0)
    return EXPLANATION_BONUS_MAX * fraction


def compute_conflict_reward(
    agent_resolution: str,
    ground_truth: str,
    file_path: str,
    explanation: Optional[str] = None,
    full_file_context: Optional[str] = None,
) -> MergeReward:
    """
    Compute the full reward for a single conflict resolution.

    Args:
        agent_resolution: The agent's proposed resolution text.
        ground_truth: The correct expected resolution.
        file_path: Path of the file (used for syntax checking language).
        explanation: Optional explanation provided by the agent.
        full_file_context: Full file content with resolution applied (for syntax check).

    Returns:
        MergeReward with all component scores and total.
    """
    if not agent_resolution.strip():
        # Empty resolution: hard penalty on all components
        return MergeReward(
            total_reward=0.0,
            conflict_resolution_score=0.0,
            syntax_validity_score=0.0,
            consistency_score=0.0,
            explanation_bonus=0.0,
        )

    match_raw = compute_match_score(agent_resolution, ground_truth)
    syntax_raw = compute_syntax_score(agent_resolution, file_path, full_file_context)
    semantic_raw = compute_semantic_score(agent_resolution, ground_truth)
    no_markers_raw = compute_no_markers_score(agent_resolution)
    explanation_bonus = compute_explanation_bonus(explanation, ground_truth)

    conflict_resolution_score = WEIGHT_MATCH * match_raw
    syntax_validity_score = WEIGHT_SYNTAX * syntax_raw
    consistency_score = WEIGHT_SEMANTIC * semantic_raw
    no_markers_contribution = WEIGHT_NO_MARKERS * no_markers_raw

    total = (
        conflict_resolution_score
        + syntax_validity_score
        + consistency_score
        + no_markers_contribution
        + explanation_bonus
    )
    total = min(max(total, 0.0), 1.0)

    return MergeReward(
        total_reward=total,
        conflict_resolution_score=conflict_resolution_score,
        syntax_validity_score=syntax_validity_score,
        consistency_score=consistency_score,
        explanation_bonus=explanation_bonus,
    )


def compute_episode_reward(
    conflict_rewards: List[float],
    penalties: float = 0.0,
) -> float:
    """
    Compute the final episode reward.

    Args:
        conflict_rewards: List of per-conflict total reward values.
        penalties: Total accumulated penalties for the episode.

    Returns:
        Final episode score in [0.0, 1.0].
    """
    if not conflict_rewards:
        return 0.0
    avg = sum(conflict_rewards) / len(conflict_rewards)
    final = avg - penalties
    return min(max(final, 0.0), 1.0)
