#!/usr/bin/env python3
"""
Baseline inference script for the Git Merge Conflict Resolver OpenEnv environment.

Runs an LLM agent against all tasks and logs results in the required format.

Required environment variables:
    API_BASE_URL  — The base URL for the LLM API endpoint
    MODEL_NAME    — The model identifier to use
    HF_TOKEN      — HuggingFace / API authentication token

Usage:
    API_BASE_URL=http://localhost:8000/v1 MODEL_NAME=gpt-4o HF_TOKEN=hf_... python inference.py

Log format (stdout):
    [START] task=<task_name> env=git_merge_resolver model=<model_name>
    [STEP] step=<N> action=<conflict_id> reward=<reward> done=<true/false> error=<null/msg>
    [END] success=<true/false> steps=<N> score=<score> rewards=[<r1>,<r2>,...]
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Environment variable configuration (MUST be set before running)
# ---------------------------------------------------------------------------
API_BASE_URL: str = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "your-active-model")
HF_TOKEN: str = os.environ.get("HF_TOKEN")

# Server base URL for the environment (separate from LLM API)
ENV_BASE_URL: str = os.environ.get("ENV_BASE_URL", API_BASE_URL)

# LLM API base URL (may differ from env URL if LLM is a separate service)
LLM_API_BASE_URL: str = os.environ.get("LLM_API_BASE_URL", "")

# All tasks to evaluate
TASKS: List[str] = [
    "simple_variable_rename",
    "import_and_usage_update",
    "function_signature_change",
    "class_refactor_vs_feature_addition",
    "multi_file_api_overhaul",
]

ENV_NAME = "git_merge_resolver"

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy imports — only loaded when actually used
# ---------------------------------------------------------------------------
def _get_openai_client():
    """Create an OpenAI client configured for the LLM API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package not installed. Run: pip install openai"
        )

    # Determine LLM base URL
    llm_url = LLM_API_BASE_URL or API_BASE_URL
    if not llm_url.endswith("/v1"):
        llm_url = llm_url.rstrip("/") + "/v1"

    api_key = HF_TOKEN or "no-key"
    return OpenAI(base_url=llm_url, api_key=api_key)


def _get_env_client():
    """Create an environment HTTP client."""
    try:
        import httpx
    except ImportError:
        raise ImportError("httpx package not installed. Run: pip install httpx")

    # Determine env URL: check if ENV_BASE_URL points to the FastAPI server
    env_url = ENV_BASE_URL
    # If API_BASE_URL ends in /v1 it's an LLM endpoint, not our env server
    if env_url.endswith("/v1"):
        env_url = "http://localhost:7860"

    return httpx.Client(base_url=env_url, timeout=30.0)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an expert software engineer specializing in resolving Git merge conflicts. "
    "You understand both the syntactic and semantic requirements of code merging. "
    "Your goal is to produce the most correct merged resolution that preserves the intent "
    "of both branches."
)

_RESOLUTION_PROMPT_TEMPLATE = """\
You are resolving a Git merge conflict in a real codebase.

## Task Context
- **File**: {file_path}
- **Branch "ours" ({ours_branch})**: {ours_commit_message}
- **Branch "theirs" ({theirs_branch})**: {theirs_commit_message}
- **Conflict ID**: {conflict_id}

## Code Before Conflict:
```python
{context_before}
```

## Conflict — OURS (current branch `{ours_branch}`):
```python
{ours_content}
```

## Conflict — THEIRS (incoming branch `{theirs_branch}`):
```python
{theirs_content}
```

## Code After Conflict:
```python
{context_after}
```
{feedback_section}
## Instructions:
Resolve this merge conflict by producing the correct merged code that:
1. Preserves the intent of BOTH branches where possible
2. Uses the naming conventions and patterns from the "ours" (main) branch as the baseline
3. Integrates any NEW code from "theirs" branch, updated to follow the "ours" branch's conventions
4. Does NOT include any conflict markers (<<<<<<, ======, >>>>>>>)
5. Is syntactically valid Python

Output ONLY the resolved code. Do not include any explanation, markdown fences, or extra text.
"""


def build_prompt(
    conflict_block: dict,
    ours_commit_message: str,
    theirs_commit_message: str,
    previous_feedback: Optional[str] = None,
) -> str:
    """Build the resolution prompt for a single conflict block."""
    feedback_section = ""
    if previous_feedback and "WARNING" in previous_feedback:
        feedback_section = f"\n## Previous Attempt Feedback:\n{previous_feedback}\n"

    return _RESOLUTION_PROMPT_TEMPLATE.format(
        file_path=conflict_block.get("file_path", "unknown"),
        ours_branch=conflict_block.get("ours_branch_name", "main"),
        theirs_branch=conflict_block.get("theirs_branch_name", "feature-branch"),
        ours_commit_message=ours_commit_message,
        theirs_commit_message=theirs_commit_message,
        conflict_id=conflict_block.get("conflict_id", "unknown"),
        context_before=conflict_block.get("surrounding_context_before", ""),
        ours_content=conflict_block.get("ours_content", ""),
        theirs_content=conflict_block.get("theirs_content", ""),
        context_after=conflict_block.get("surrounding_context_after", ""),
        feedback_section=feedback_section,
    )


# ---------------------------------------------------------------------------
# LLM resolution
# ---------------------------------------------------------------------------

def strip_markdown_fences(text: str) -> str:
    """Remove ```python ... ``` or ``` ... ``` fences from LLM output."""
    # Remove opening fence (with optional language specifier)
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    # Remove closing fence
    text = re.sub(r"\n?```$", "", text.strip())
    return text


def call_llm(
    client,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.1,
) -> str:
    """
    Call the LLM via the OpenAI client and return the response text.

    Uses low temperature (0.1) for more deterministic, accurate resolutions.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    raw = response.choices[0].message.content or ""
    return strip_markdown_fences(raw)


# ---------------------------------------------------------------------------
# Logging helpers (EXACT format required)
# ---------------------------------------------------------------------------

def log_start(task_id: str) -> None:
    """Emit the [START] log line."""
    print(
        f"[START] task={task_id} env={ENV_NAME} model={MODEL_NAME}",
        flush=True,
    )


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str] = None,
) -> None:
    """Emit a [STEP] log line."""
    error_str = "null" if error is None else error.replace("\n", " ")
    done_str = "true" if done else "false"
    print(
        f"[STEP] step={step} action={action} reward={reward:.4f} "
        f"done={done_str} error={error_str}",
        flush=True,
    )


def log_end(
    success: bool,
    steps: int,
    score: float,
    rewards: List[float],
) -> None:
    """Emit the [END] log line."""
    success_str = "true" if success else "false"
    rewards_str = "[" + ",".join(f"{r:.4f}" for r in rewards) + "]"
    print(
        f"[END] success={success_str} steps={steps} score={score:.4f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------

def run_task(env_client, llm_client, task_id: str) -> Tuple[float, bool, int, List[float]]:
    """
    Run the agent on a single task.

    Returns:
        Tuple of (final_score, success, total_steps, per_step_rewards).
    """
    log_start(task_id)

    # Reset environment
    reset_response = env_client.post("/reset", json={"task_id": task_id})
    reset_response.raise_for_status()
    obs_data = reset_response.json()

    step_num = 0
    all_rewards: List[float] = []
    done = obs_data.get("done", False)
    previous_feedback = obs_data.get("previous_feedback")

    while not done:
        conflict_blocks = obs_data.get("conflict_blocks", [])
        if not conflict_blocks:
            break

        ours_msg = obs_data.get("ours_commit_message", "")
        theirs_msg = obs_data.get("theirs_commit_message", "")

        # Pick the first unresolved conflict
        conflict_block = conflict_blocks[0]
        conflict_id = conflict_block.get("conflict_id", "")

        # Build LLM prompt
        prompt = build_prompt(
            conflict_block=conflict_block,
            ours_commit_message=ours_msg,
            theirs_commit_message=theirs_msg,
            previous_feedback=previous_feedback,
        )

        # Call LLM
        try:
            resolved_content = call_llm(llm_client, prompt)
            error_msg = None
        except Exception as exc:
            resolved_content = conflict_block.get("ours_content", "")
            error_msg = f"LLM call failed: {type(exc).__name__}: {exc}"
            logger.warning("LLM error for %s/%s: %s", task_id, conflict_id, exc)

        # Submit action
        action_payload = {
            "action": {
                "conflict_id": conflict_id,
                "resolved_content": resolved_content,
                "explanation": f"Resolved by synthesizing both branch intents for {conflict_id}",
            }
        }

        try:
            step_response = env_client.post("/step", json=action_payload)
            step_response.raise_for_status()
            step_data = step_response.json()
        except Exception as exc:
            error_msg = f"Step request failed: {exc}"
            log_step(step_num + 1, conflict_id, 0.0, False, error_msg)
            break

        reward_data = step_data.get("reward", {})
        step_reward = reward_data.get("total_reward", 0.0)
        done = step_data.get("done", False)
        info = step_data.get("info", {})
        obs_data = step_data.get("observation", obs_data)
        previous_feedback = obs_data.get("previous_feedback")

        step_num += 1
        all_rewards.append(step_reward)

        log_step(
            step=step_num,
            action=conflict_id,
            reward=step_reward,
            done=done,
            error=error_msg,
        )

        if done:
            break

    # Get final score from state
    try:
        state_response = env_client.get("/state")
        state_response.raise_for_status()
        state_data = state_response.json()
        pending = state_data.get("pending_conflicts", [])
        cumulative = state_data.get("cumulative_reward", 0.0)
        final_score = cumulative / max(len(all_rewards), 1)
        success = len(pending) == 0 and final_score >= 0.8
    except Exception:
        final_score = sum(all_rewards) / max(len(all_rewards), 1)
        success = final_score >= 0.8

    log_end(
        success=success,
        steps=step_num,
        score=final_score,
        rewards=all_rewards,
    )

    return final_score, success, step_num, all_rewards


def main() -> None:
    """Run the inference agent on all tasks."""
    # Validate environment variables
    if not HF_TOKEN and not os.environ.get("LLM_API_BASE_URL"):
        print(
            "WARNING: HF_TOKEN not set. LLM calls may fail if authentication is required.",
            file=sys.stderr,
        )

    env_client = _get_env_client()
    llm_client = _get_openai_client()

    # Verify environment server is reachable
    try:
        health = env_client.get("/health")
        health.raise_for_status()
        print(f"# Environment server: {health.json()}", file=sys.stderr)
    except Exception as exc:
        print(f"WARNING: Could not reach environment server: {exc}", file=sys.stderr)
        print("# Proceeding anyway...", file=sys.stderr)

    all_scores: List[float] = []
    all_success: List[bool] = []

    for task_id in TASKS:
        try:
            score, success, steps, rewards = run_task(env_client, llm_client, task_id)
            all_scores.append(score)
            all_success.append(success)
        except Exception as exc:
            print(f"ERROR: Task {task_id} failed: {exc}", file=sys.stderr)
            log_start(task_id)
            log_end(success=False, steps=0, score=0.0, rewards=[])
            all_scores.append(0.0)
            all_success.append(False)

        # Brief pause between tasks to avoid rate limiting
        time.sleep(1)

    # Summary
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    num_success = sum(all_success)
    print(
        f"\n# SUMMARY: {num_success}/{len(TASKS)} tasks succeeded, "
        f"average score: {avg_score:.4f}",
        file=sys.stderr,
    )

    env_client.close()


if __name__ == "__main__":
    main()
