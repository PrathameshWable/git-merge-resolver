"""
Task registry for the Git Merge Conflict Resolver environment.

Provides a central registry for loading tasks by ID, listing available tasks,
and randomly sampling tasks by difficulty.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from git_merge_resolver.tasks.easy_tasks import get_task1, get_task2
from git_merge_resolver.tasks.medium_tasks import get_task3, get_task4
from git_merge_resolver.tasks.hard_tasks import get_task5


def _build_registry() -> Dict[str, dict]:
    """Build the task registry by loading all task definitions."""
    tasks = [get_task1(), get_task2(), get_task3(), get_task4(), get_task5()]
    return {task["task_id"]: task for task in tasks}


# Module-level registry — built once at import time
_REGISTRY: Dict[str, dict] = _build_registry()


def get_task(task_id: str) -> dict:
    """
    Load a task definition by its task_id.

    Args:
        task_id: The unique identifier of the task.

    Returns:
        The task definition dict.

    Raises:
        KeyError: If the task_id is not found in the registry.
    """
    if task_id not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(
            f"Task '{task_id}' not found. Available tasks: {available}"
        )
    return _REGISTRY[task_id]


def list_tasks() -> List[Dict[str, str]]:
    """
    Return a list of all available tasks with their metadata.

    Returns:
        List of dicts with task_id, difficulty, and description fields.
    """
    return [
        {
            "task_id": task["task_id"],
            "difficulty": task["difficulty"],
            "description": task["task_description"],
            "num_conflicts": len(task["conflict_blocks"]),
            "max_steps": task["max_steps"],
        }
        for task in _REGISTRY.values()
    ]


def get_random_task(difficulty: Optional[str] = None) -> dict:
    """
    Return a random task, optionally filtered by difficulty.

    Args:
        difficulty: If provided, only sample from tasks with this difficulty.
                    Valid values: 'easy', 'medium', 'hard'.

    Returns:
        A task definition dict.

    Raises:
        ValueError: If no tasks match the requested difficulty.
    """
    tasks = list(_REGISTRY.values())
    if difficulty is not None:
        tasks = [t for t in tasks if t["difficulty"] == difficulty]
        if not tasks:
            raise ValueError(
                f"No tasks found with difficulty '{difficulty}'. "
                f"Valid values: 'easy', 'medium', 'hard'."
            )
    return random.choice(tasks)


def get_all_task_ids() -> List[str]:
    """Return a list of all registered task IDs."""
    return list(_REGISTRY.keys())
