"""
FastAPI server for the Git Merge Conflict Resolver OpenEnv environment.

Exposes:
    POST /reset   — Start a new episode
    POST /step    — Submit a conflict resolution action
    GET  /state   — Get current environment state
    GET  /tasks   — List all available tasks
    GET  /health  — Health check
    WS   /ws      — WebSocket endpoint for persistent sessions
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from git_merge_resolver.environment import GitMergeResolverEnvironment
from git_merge_resolver.models import (
    MergeAction,
    MergeObservation,
    MergeReward,
    MergeState,
    ResetRequest,
    StepRequest,
    StepResponse,
)
from git_merge_resolver.tasks.task_registry import list_tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Git Merge Conflict Resolver",
    description=(
        "OpenEnv environment for evaluating AI agent ability to resolve "
        "Git merge conflicts across varying difficulty levels."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global environment instance (stateful, single-session mode)
_env = GitMergeResolverEnvironment()


# ---------------------------------------------------------------------------
# HTTP Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/reset",
    response_model=MergeObservation,
    summary="Reset the environment and start a new episode",
)
async def reset(request: ResetRequest = ResetRequest()) -> MergeObservation:
    """
    Start a new episode by loading the specified task (or a random task).

    Returns the initial observation with all conflict blocks unresolved.
    """
    try:
        observation = _env.reset(task_id=request.task_id)
        logger.info(
            "Episode started: task=%s episode=%s",
            observation.task_id,
            _env._current_episode_id,
        )
        return observation
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post(
    "/step",
    response_model=StepResponse,
    summary="Submit a conflict resolution action",
)
async def step(request: StepRequest) -> StepResponse:
    """
    Submit a resolution for a single conflict block.

    The agent specifies which conflict_id to resolve and the resolved content.
    Returns the updated observation, reward breakdown, done flag, and info dict.
    """
    try:
        obs, reward, done, info = _env.step(action=request.action)
        return StepResponse(
            observation=obs,
            reward=reward,
            done=done,
            info=info,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.get(
    "/state",
    response_model=MergeState,
    summary="Get the current environment state",
)
async def get_state() -> MergeState:
    """
    Return the full current episode state including all resolved/pending
    conflict IDs and cumulative reward.
    """
    try:
        return _env.state()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.get(
    "/tasks",
    summary="List all available tasks",
)
async def get_tasks() -> list:
    """Return metadata for all available tasks."""
    return list_tasks()


@app.get(
    "/health",
    summary="Health check",
)
async def health() -> Dict[str, str]:
    """Return server health status."""
    return {"status": "healthy", "environment": "git_merge_resolver", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for persistent session management.

    Messages are JSON objects with a "type" field:
        {"type": "reset", "task_id": "..."}
        {"type": "step", "action": {...}}
        {"type": "state"}

    Responses are JSON objects with a "type" field:
        {"type": "observation", "data": {...}}
        {"type": "step_result", "data": {...}}
        {"type": "state", "data": {...}}
        {"type": "error", "message": "..."}
    """
    await websocket.accept()
    ws_env = GitMergeResolverEnvironment()
    logger.info("WebSocket connection opened")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON"}
                )
                continue

            msg_type = message.get("type", "")

            if msg_type == "reset":
                task_id = message.get("task_id")
                try:
                    obs = ws_env.reset(task_id=task_id)
                    await websocket.send_json(
                        {"type": "observation", "data": obs.model_dump()}
                    )
                except KeyError as exc:
                    await websocket.send_json(
                        {"type": "error", "message": str(exc)}
                    )

            elif msg_type == "step":
                action_data = message.get("action", {})
                try:
                    action = MergeAction(**action_data)
                    obs, reward, done, info = ws_env.step(action=action)
                    await websocket.send_json(
                        {
                            "type": "step_result",
                            "data": {
                                "observation": obs.model_dump(),
                                "reward": reward.model_dump(),
                                "done": done,
                                "info": info,
                            },
                        }
                    )
                except (ValueError, RuntimeError) as exc:
                    await websocket.send_json(
                        {"type": "error", "message": str(exc)}
                    )

            elif msg_type == "state":
                try:
                    state = ws_env.state()
                    await websocket.send_json(
                        {"type": "state", "data": state.model_dump()}
                    )
                except RuntimeError as exc:
                    await websocket.send_json(
                        {"type": "error", "message": str(exc)}
                    )

            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unknown message type '{msg_type}'. "
                        f"Valid types: reset, step, state",
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")


def main() -> None:
    """Entry point for the server — callable via project.scripts."""
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, workers=1)


if __name__ == "__main__":
    main()
