"""
Pydantic models for the Git Merge Conflict Resolver OpenEnv environment.

Defines all data structures exchanged between the environment and the agent:
- MergeObservation: what the agent sees
- MergeAction: what the agent submits
- MergeReward: the reward signal after each action
- MergeState: the full serializable environment state
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConflictBlock(BaseModel):
    """A single conflict block within a file (one <<<<<<< ... >>>>>>> section)."""

    conflict_id: str = Field(
        ...,
        description="Unique identifier for this conflict block, e.g. 'conflict_001'",
        examples=["conflict_001"],
    )
    file_path: str = Field(
        ...,
        description="Relative path of the file containing this conflict",
        examples=["src/utils/calculator.py"],
    )
    ours_content: str = Field(
        ...,
        description="Content from HEAD (the 'ours' branch, i.e. the branch being merged into)",
    )
    theirs_content: str = Field(
        ...,
        description="Content from the incoming branch (the 'theirs' branch, i.e. the branch being merged from)",
    )
    surrounding_context_before: str = Field(
        default="",
        description="10–15 lines of code immediately before the conflict marker",
    )
    surrounding_context_after: str = Field(
        default="",
        description="10–15 lines of code immediately after the conflict closing marker",
    )
    ours_branch_name: str = Field(
        default="main",
        description="Name of the 'ours' branch",
        examples=["main"],
    )
    theirs_branch_name: str = Field(
        default="feature-branch",
        description="Name of the 'theirs' (incoming) branch",
        examples=["feature/add-tax-calculation"],
    )


class MergeObservation(BaseModel):
    """
    Full observation the agent receives at each step.

    Contains all unresolved conflict blocks, contextual information about
    the two branches, and step/progress metadata.
    """

    task_id: str = Field(..., description="Unique identifier for the current task")
    task_description: str = Field(
        ..., description="Human-readable description of what this task involves"
    )
    difficulty: str = Field(
        ...,
        description="Difficulty level: 'easy', 'medium', or 'hard'",
        examples=["easy"],
    )
    conflict_blocks: List[ConflictBlock] = Field(
        default_factory=list,
        description="All conflict blocks that remain unresolved",
    )
    ours_commit_message: str = Field(
        ...,
        description="The commit message from the 'ours' branch that introduced these changes",
    )
    theirs_commit_message: str = Field(
        ...,
        description="The commit message from the 'theirs' branch that introduced these changes",
    )
    file_contents: Dict[str, str] = Field(
        default_factory=dict,
        description="Full contents of each conflicted file (with conflict markers still present)",
    )
    num_conflicts_remaining: int = Field(
        ..., description="Number of conflict blocks still pending resolution"
    )
    num_conflicts_total: int = Field(
        ..., description="Total number of conflict blocks in this task"
    )
    step_number: int = Field(..., description="Current step number (1-indexed)")
    max_steps: int = Field(
        ..., description="Maximum number of steps allowed for this task"
    )
    previous_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from the previous action, if any (e.g. syntax error message)",
    )
    done: bool = Field(
        default=False,
        description="Whether the episode is complete (all conflicts resolved or max steps reached)",
    )


class MergeAction(BaseModel):
    """
    Action the agent takes to resolve a single conflict block.

    The agent must specify which conflict to resolve and provide the merged content.
    """

    conflict_id: str = Field(
        ...,
        description="The conflict_id of the block to resolve (must match an existing unresolved block)",
        examples=["conflict_001"],
    )
    resolved_content: str = Field(
        ...,
        description=(
            "The agent's proposed resolution for the conflict. "
            "Must NOT contain conflict markers (<<<<<<, ======, >>>>>>). "
            "Must be syntactically valid code."
        ),
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Optional explanation of why this resolution is correct (used for explanation bonus)",
    )


class MergeReward(BaseModel):
    """
    Decomposed reward signal returned after each step.

    Scores are in [0.0, 1.0]. The total_reward is the weighted sum of components.
    """

    total_reward: float = Field(
        ...,
        description="Overall reward for this step, in [0.0, 1.0]",
        ge=0.0,
        le=1.0,
    )
    conflict_resolution_score: float = Field(
        ...,
        description="How closely the resolution matches ground truth (weight: 0.40)",
        ge=0.0,
        le=0.4,
    )
    syntax_validity_score: float = Field(
        ...,
        description="Whether the resolved code is syntactically valid Python (weight: 0.30)",
        ge=0.0,
        le=0.3,
    )
    consistency_score: float = Field(
        ...,
        description="Cross-file consistency score for hard tasks (weight: 0.20)",
        ge=0.0,
        le=0.2,
    )
    explanation_bonus: float = Field(
        ...,
        description="Small bonus for providing a meaningful explanation (weight: 0.10)",
        ge=0.0,
        le=0.1,
    )


class MergeState(BaseModel):
    """
    Full serializable environment state.

    Returned by the GET /state endpoint. Contains everything needed to
    reconstruct the current episode's progress.
    """

    episode_id: str = Field(..., description="Unique episode identifier (UUID4)")
    task_id: str = Field(..., description="Current task identifier")
    step_count: int = Field(
        ..., description="Number of steps taken so far in this episode"
    )
    resolved_conflicts: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of conflict_id to the agent's submitted resolution",
    )
    pending_conflicts: List[str] = Field(
        default_factory=list,
        description="List of conflict_ids that have not yet been resolved",
    )
    cumulative_reward: float = Field(
        ...,
        description="Sum of all per-step rewards so far",
        ge=0.0,
    )
    done: bool = Field(default=False, description="Whether the episode is complete")


class ResetRequest(BaseModel):
    """Request body for POST /reset."""

    task_id: Optional[str] = Field(
        default=None,
        description="Task to load. If None, a random task is selected.",
    )


class StepRequest(BaseModel):
    """Request body for POST /step."""

    action: MergeAction


class StepResponse(BaseModel):
    """Response body for POST /step."""

    observation: MergeObservation
    reward: MergeReward
    done: bool
    info: Dict[str, object] = Field(default_factory=dict)
