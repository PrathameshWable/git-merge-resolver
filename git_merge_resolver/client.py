"""
OpenEnv client for the Git Merge Conflict Resolver environment.

Provides both HTTP and WebSocket based access to the environment.
The GitMergeResolverEnv class follows the OpenEnv client interface convention.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from git_merge_resolver.models import (
    MergeAction,
    MergeObservation,
    MergeReward,
    MergeState,
    StepResponse,
)

logger = logging.getLogger(__name__)


class GitMergeResolverEnv:
    """
    HTTP client for the Git Merge Conflict Resolver environment server.

    Implements the OpenEnv client interface:
        reset() → MergeObservation
        step(action) → (MergeObservation, MergeReward, bool, dict)
        state() → MergeState
    """

    def __init__(
        self,
        base_url: str = "http://localhost:7860",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the environment client.

        Args:
            base_url: Base URL of the environment server.
            timeout: HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        self._current_episode_id: Optional[str] = None

    def reset(self, task_id: Optional[str] = None) -> MergeObservation:
        """
        Reset the environment and start a new episode.

        Args:
            task_id: Task to load. If None, a random task is selected.

        Returns:
            Initial MergeObservation.
        """
        payload: Dict[str, Any] = {}
        if task_id is not None:
            payload["task_id"] = task_id

        response = self._client.post("/reset", json=payload)
        response.raise_for_status()
        data = response.json()

        # Track episode_id if returned in headers or body
        if "episode_id" in data:
            self._current_episode_id = data["episode_id"]

        return MergeObservation(**data)

    def step(
        self,
        action: MergeAction,
    ) -> Tuple[MergeObservation, MergeReward, bool, Dict]:
        """
        Take a step in the environment.

        Args:
            action: The merge action to submit.

        Returns:
            Tuple of (observation, reward, done, info).
        """
        payload = {"action": action.model_dump()}
        response = self._client.post("/step", json=payload)
        response.raise_for_status()

        data = response.json()
        step_resp = StepResponse(**data)
        return (
            step_resp.observation,
            step_resp.reward,
            step_resp.done,
            step_resp.info,
        )

    def state(self) -> MergeState:
        """
        Get the current environment state.

        Returns:
            MergeState with all resolved/pending conflicts and cumulative reward.
        """
        response = self._client.get("/state")
        response.raise_for_status()
        return MergeState(**response.json())

    def list_tasks(self) -> List[Dict]:
        """Return a list of all available tasks."""
        response = self._client.get("/tasks")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "GitMergeResolverEnv":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
