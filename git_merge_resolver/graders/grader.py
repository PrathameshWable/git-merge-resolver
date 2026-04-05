"""
Deterministic grading system for the Git Merge Conflict Resolver.

Each task has a TaskGrader that compares agent resolutions against ground
truth and returns a reproducible score in [0.0, 1.0].

The grader is fully deterministic: same inputs always produce same outputs.
"""

from __future__ import annotations

from typing import Dict, Optional

from git_merge_resolver.rewards.reward import compute_conflict_reward
from git_merge_resolver.tasks.task_registry import get_task


class TaskGrader:
    """
    Deterministic grader for a specific task.

    Compares agent resolutions against ground truth resolutions using
    the multi-component reward function. Score range: 0.0–1.0.
    """

    def __init__(self, task_id: str, ground_truths: Dict[str, str]) -> None:
        """
        Initialize the grader for a specific task.

        Args:
            task_id: The task this grader applies to.
            ground_truths: Dict mapping conflict_id to the expected resolution.
        """
        self.task_id = task_id
        self.ground_truths = ground_truths
        self._file_paths: Dict[str, str] = {}

    def set_file_paths(self, conflict_file_map: Dict[str, str]) -> None:
        """
        Provide a mapping of conflict_id to file_path for syntax checking.

        Args:
            conflict_file_map: Dict mapping conflict_id to file_path.
        """
        self._file_paths = conflict_file_map

    def grade(
        self,
        agent_resolutions: Dict[str, str],
        penalties: float = 0.0,
    ) -> float:
        """
        Grade the agent's resolutions against ground truth.

        Args:
            agent_resolutions: Dict mapping conflict_id to agent's resolution.
            penalties: Total accumulated penalties from the episode.

        Returns:
            Final score in [0.0, 1.0].
        """
        if not self.ground_truths:
            return 1.0

        scores = []
        for conflict_id, ground_truth in self.ground_truths.items():
            if conflict_id in agent_resolutions:
                agent_res = agent_resolutions[conflict_id]
                file_path = self._file_paths.get(conflict_id, "unknown.py")
                reward = compute_conflict_reward(
                    agent_resolution=agent_res,
                    ground_truth=ground_truth,
                    file_path=file_path,
                )
                scores.append(reward.total_reward)
            else:
                # Unresolved conflict — 0 score for this conflict
                scores.append(0.0)

        if not scores:
            return 0.0

        avg = sum(scores) / len(scores)
        final = max(0.0, avg - penalties)
        return min(final, 1.0)

    def grade_single_conflict(
        self,
        conflict_id: str,
        agent_resolution: str,
    ) -> float:
        """
        Grade a single conflict resolution.

        Args:
            conflict_id: The conflict being graded.
            agent_resolution: The agent's proposed resolution.

        Returns:
            Score for this conflict in [0.0, 1.0].
        """
        if conflict_id not in self.ground_truths:
            return 0.0

        ground_truth = self.ground_truths[conflict_id]
        file_path = self._file_paths.get(conflict_id, "unknown.py")
        reward = compute_conflict_reward(
            agent_resolution=agent_resolution,
            ground_truth=ground_truth,
            file_path=file_path,
        )
        return reward.total_reward


def build_grader_for_task(task_id: str) -> TaskGrader:
    """
    Build a TaskGrader for the given task_id using the task registry.

    Args:
        task_id: The task to build a grader for.

    Returns:
        A configured TaskGrader instance.
    """
    task = get_task(task_id)
    ground_truths = task["ground_truths"]

    grader = TaskGrader(task_id=task_id, ground_truths=ground_truths)

    # Build conflict_id → file_path mapping from conflict blocks
    file_path_map = {
        block.conflict_id: block.file_path
        for block in task["conflict_blocks"]
    }
    grader.set_file_paths(file_path_map)

    return grader


def grade_episode(
    task_id: str,
    agent_resolutions: Dict[str, str],
    penalties: float = 0.0,
) -> float:
    """
    Convenience function to grade a complete episode.

    Args:
        task_id: The task that was being solved.
        agent_resolutions: All of the agent's submitted resolutions.
        penalties: Total accumulated penalties.

    Returns:
        Final episode score in [0.0, 1.0].
    """
    grader = build_grader_for_task(task_id)
    return grader.grade(agent_resolutions, penalties)
