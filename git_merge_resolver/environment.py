"""
Core environment logic for the Git Merge Conflict Resolver.

Implements the OpenEnv state machine:
    reset(task_id) → initial MergeObservation
    step(action)   → (observation, reward, done, info)
    state()        → current MergeState

Sessions are identified by episode_id and held in-memory.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Tuple

from git_merge_resolver.graders.grader import build_grader_for_task
from git_merge_resolver.models import (
    ConflictBlock,
    MergeAction,
    MergeObservation,
    MergeReward,
    MergeState,
)
from git_merge_resolver.rewards.reward import (
    PENALTY_ALREADY_RESOLVED,
    PENALTY_EMPTY_RESOLUTION,
    PENALTY_INVALID_CONFLICT_ID,
    PENALTY_UNRESOLVED_AT_END,
    compute_conflict_reward,
    compute_episode_reward,
)
from git_merge_resolver.tasks.task_registry import get_random_task, get_task
from git_merge_resolver.utils.diff_utils import contains_conflict_markers


class _EpisodeSession:
    """
    Internal state for a single episode.

    Tracks which conflicts have been resolved, accumulated penalties,
    per-conflict reward scores, and the current step count.
    """

    def __init__(self, task: dict) -> None:
        self.episode_id: str = str(uuid.uuid4())
        self.task: dict = task
        self.task_id: str = task["task_id"]
        self.max_steps: int = task["max_steps"]
        self.step_count: int = 0
        self.done: bool = False

        # Maps conflict_id → resolved content (filled as agent resolves)
        self.resolved_conflicts: Dict[str, str] = {}

        # Maps conflict_id → per-conflict reward score
        self.conflict_scores: Dict[str, float] = {}

        # Accumulated penalty points
        self.penalties: float = 0.0

        # Feedback string to include in the next observation
        self.last_feedback: Optional[str] = None

        self.all_conflict_ids: List[str] = [
            b.conflict_id for b in task["conflict_blocks"]
        ]
        self.conflict_map: Dict[str, ConflictBlock] = {
            b.conflict_id: b for b in task["conflict_blocks"]
        }
        self.file_path_map: Dict[str, str] = {
            b.conflict_id: b.file_path for b in task["conflict_blocks"]
        }
        self.grader = build_grader_for_task(self.task_id)

    @property
    def pending_conflicts(self) -> List[str]:
        """Return list of conflict_ids that have not yet been resolved."""
        return [cid for cid in self.all_conflict_ids if cid not in self.resolved_conflicts]

    @property
    def cumulative_reward(self) -> float:
        """Sum of all per-conflict reward scores so far."""
        return sum(self.conflict_scores.values())

    def get_pending_conflict_blocks(self) -> List[ConflictBlock]:
        """Return ConflictBlock objects for all pending (unresolved) conflicts."""
        return [self.conflict_map[cid] for cid in self.pending_conflicts]

    def build_observation(self) -> MergeObservation:
        """Build the current MergeObservation for the agent."""
        return MergeObservation(
            task_id=self.task_id,
            task_description=self.task["task_description"],
            difficulty=self.task["difficulty"],
            conflict_blocks=self.get_pending_conflict_blocks(),
            ours_commit_message=self.task["ours_commit_message"],
            theirs_commit_message=self.task["theirs_commit_message"],
            file_contents=self.task["file_contents"],
            num_conflicts_remaining=len(self.pending_conflicts),
            num_conflicts_total=len(self.all_conflict_ids),
            step_number=self.step_count,
            max_steps=self.max_steps,
            previous_feedback=self.last_feedback,
            done=self.done,
        )


class GitMergeResolverEnvironment:
    """
    OpenEnv-compatible environment for Git merge conflict resolution.

    Manages multiple concurrent episodes via episode_id. Exposes the
    standard OpenEnv interface: reset(), step(), state().
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, _EpisodeSession] = {}
        self._current_episode_id: Optional[str] = None
        # TODO: add session cleanup — old episodes just pile up in memory right now

    # ------------------------------------------------------------------
    # Public OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self, task_id: Optional[str] = None) -> MergeObservation:
        """
        Start a new episode.

        Loads the specified task (or a random task if task_id is None),
        initialises the session state, and returns the initial observation
        with all conflict blocks unresolved.

        Args:
            task_id: The task to load. If None, a random task is selected.

        Returns:
            Initial MergeObservation with all conflicts pending.
        """
        if task_id is not None:
            task = get_task(task_id)
        else:
            task = get_random_task()

        session = _EpisodeSession(task)
        self._sessions[session.episode_id] = session
        self._current_episode_id = session.episode_id

        return session.build_observation()

    def step(
        self,
        action: MergeAction,
        episode_id: Optional[str] = None,
    ) -> Tuple[MergeObservation, MergeReward, bool, Dict]:
        """
        Take one step: resolve a single conflict block.

        Validates the action, computes the reward, updates session state,
        and determines whether the episode is complete.

        Args:
            action: The agent's proposed resolution for a conflict block.
            episode_id: Which session to use. Defaults to the current session.

        Returns:
            Tuple of (observation, reward, done, info).
        """
        session = self._get_session(episode_id)

        if session.done:
            # Episode already ended — return terminal observation with zero reward
            obs = session.build_observation()
            zero_reward = MergeReward(
                total_reward=0.0,
                conflict_resolution_score=0.0,
                syntax_validity_score=0.0,
                consistency_score=0.0,
                explanation_bonus=0.0,
            )
            return obs, zero_reward, True, {"error": "Episode already ended"}

        session.step_count += 1

        # --- Validate action ---
        conflict_id = action.conflict_id
        resolved_content = action.resolved_content.strip() if action.resolved_content else ""

        # Case 1: Empty resolution
        if not resolved_content:
            session.penalties += PENALTY_EMPTY_RESOLUTION
            session.last_feedback = (
                f"Empty resolution submitted for '{conflict_id}'. "
                f"Penalty -{PENALTY_EMPTY_RESOLUTION:.2f} applied. "
                f"Please provide a non-empty resolution."
            )
            reward = MergeReward(
                total_reward=0.0,
                conflict_resolution_score=0.0,
                syntax_validity_score=0.0,
                consistency_score=0.0,
                explanation_bonus=0.0,
            )
            done = self._check_done(session)
            obs = session.build_observation()
            return obs, reward, done, {"feedback": session.last_feedback}

        # Case 2: Invalid conflict_id
        if conflict_id not in session.conflict_map:
            session.penalties += PENALTY_INVALID_CONFLICT_ID
            valid_ids = list(session.conflict_map.keys())
            session.last_feedback = (
                f"Invalid conflict_id '{conflict_id}'. "
                f"Valid IDs are: {valid_ids}. "
                f"Penalty -{PENALTY_INVALID_CONFLICT_ID:.2f} applied."
            )
            reward = MergeReward(
                total_reward=0.0,
                conflict_resolution_score=0.0,
                syntax_validity_score=0.0,
                consistency_score=0.0,
                explanation_bonus=0.0,
            )
            done = self._check_done(session)
            obs = session.build_observation()
            return obs, reward, done, {"feedback": session.last_feedback}

        # Case 3: Already-resolved conflict_id
        if conflict_id in session.resolved_conflicts:
            session.penalties += PENALTY_ALREADY_RESOLVED
            session.last_feedback = (
                f"Conflict '{conflict_id}' has already been resolved. "
                f"Penalty -{PENALTY_ALREADY_RESOLVED:.2f} applied. "
                f"Remaining conflicts: {session.pending_conflicts}"
            )
            reward = MergeReward(
                total_reward=0.0,
                conflict_resolution_score=0.0,
                syntax_validity_score=0.0,
                consistency_score=0.0,
                explanation_bonus=0.0,
            )
            done = self._check_done(session)
            obs = session.build_observation()
            return obs, reward, done, {"feedback": session.last_feedback}

        # --- Valid action: compute reward ---
        ground_truth = session.task["ground_truths"].get(conflict_id, "")
        file_path = session.file_path_map.get(conflict_id, "unknown.py")

        reward = compute_conflict_reward(
            agent_resolution=resolved_content,
            ground_truth=ground_truth,
            file_path=file_path,
            explanation=action.explanation,
        )

        # Store resolution and score
        session.resolved_conflicts[conflict_id] = resolved_content
        session.conflict_scores[conflict_id] = reward.total_reward

        # Build feedback message
        feedback_parts = [f"Resolved '{conflict_id}' — score: {reward.total_reward:.3f}."]
        if contains_conflict_markers(resolved_content):
            feedback_parts.append("WARNING: Resolution still contains conflict markers.")
        if reward.syntax_validity_score < 0.15:
            feedback_parts.append("WARNING: Resolution may have syntax issues.")
        if reward.conflict_resolution_score < 0.2:
            feedback_parts.append(
                "NOTE: Resolution differs significantly from expected — "
                "check that you're using the correct naming conventions."
            )
        if session.pending_conflicts:
            feedback_parts.append(
                f"Remaining conflicts: {session.pending_conflicts}"
            )

        session.last_feedback = " ".join(feedback_parts)

        # --- Check done conditions ---
        done = self._check_done(session)

        obs = session.build_observation()
        return (
            obs,
            reward,
            done,
            {
                "feedback": session.last_feedback,
                "episode_id": session.episode_id,
                "conflict_score": reward.total_reward,
                "cumulative_reward": session.cumulative_reward,
            },
        )

    def state(self, episode_id: Optional[str] = None) -> MergeState:
        """
        Return the current environment state.

        Args:
            episode_id: Which session to return state for.

        Returns:
            MergeState with all resolved/pending conflicts and cumulative reward.
        """
        session = self._get_session(episode_id)
        return MergeState(
            episode_id=session.episode_id,
            task_id=session.task_id,
            step_count=session.step_count,
            resolved_conflicts=dict(session.resolved_conflicts),
            pending_conflicts=session.pending_conflicts,
            cumulative_reward=session.cumulative_reward,
            done=session.done,
        )

    def final_score(self, episode_id: Optional[str] = None) -> float:
        """
        Compute the final episode score.

        Args:
            episode_id: Which session to score.

        Returns:
            Final score in [0.0, 1.0].
        """
        session = self._get_session(episode_id)
        conflict_rewards = list(session.conflict_scores.values())

        # Add penalty for unresolved conflicts at episode end
        unresolved_count = len(session.pending_conflicts)
        end_penalties = session.penalties + (
            unresolved_count * PENALTY_UNRESOLVED_AT_END
        )

        return compute_episode_reward(conflict_rewards, end_penalties)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_session(self, episode_id: Optional[str] = None) -> _EpisodeSession:
        """Retrieve the session for the given episode_id."""
        eid = episode_id or self._current_episode_id
        if eid is None or eid not in self._sessions:
            raise RuntimeError(
                "No active episode. Call reset() before step() or state()."
            )
        return self._sessions[eid]

    def _check_done(self, session: _EpisodeSession) -> bool:
        """
        Determine whether the episode should end.

        Ends when:
        - All conflicts are resolved, OR
        - max_steps has been reached
        """
        all_resolved = len(session.pending_conflicts) == 0
        steps_exhausted = session.step_count >= session.max_steps

        if all_resolved or steps_exhausted:
            session.done = True
            if steps_exhausted and not all_resolved:
                # Add end-of-episode penalty for unresolved conflicts
                unresolved = len(session.pending_conflicts)
                session.penalties += unresolved * PENALTY_UNRESOLVED_AT_END
                session.last_feedback = (
                    f"Episode ended: max steps ({session.max_steps}) reached with "
                    f"{unresolved} conflict(s) unresolved. "
                    f"Penalty: -{unresolved * PENALTY_UNRESOLVED_AT_END:.2f}"
                )
            elif all_resolved:
                final = self.final_score(session.episode_id)
                session.last_feedback = (
                    f"All conflicts resolved! Final score: {final:.3f}"
                )

        return session.done
