---
title: Git Merge Conflict Resolver
emoji: 🔀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - developer-tools
  - code
  - real-world
  - git
---

# Git Merge Conflict Resolver

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://openenv.dev)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-brightgreen)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

An **OpenEnv** environment for evaluating AI agent ability to resolve realistic Git merge conflicts across varying difficulty levels.

> **Why this environment?** Git merge conflict resolution is one of the most cognitively demanding tasks in collaborative software development — yet no existing OpenEnv environment covers it. Developers spend 20–30% of their time on integration work; intelligent agents that can resolve conflicts correctly represent a step-change improvement in developer productivity.

---

## Environment Description & Motivation

The **Git Merge Conflict Resolver** presents an AI agent with realistic Python codebases that contain Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). The agent must understand the semantic intent of each branch's changes and produce the correct merged resolution.

This environment is novel because merge conflict resolution requires:
- **Dual-context reasoning**: Understanding two divergent development histories simultaneously
- **Semantic synthesis**: Not just picking one side, but intelligently combining intentions
- **Cross-file consistency**: Hard tasks require consistent changes across multiple interdependent files
- **Real-world fidelity**: All scenarios use production-looking Python code with proper naming conventions, docstrings, type hints, and design patterns

---

## Action Space

The agent submits a `MergeAction` to resolve one conflict block at a time.

```python
class MergeAction(BaseModel):
    conflict_id: str          # Which conflict block to resolve (e.g. "conflict_001")
    resolved_content: str     # The merged code — must NOT contain conflict markers
    explanation: Optional[str] = None  # Optional explanation (earns small bonus)
```

**Example:**
```python
MergeAction(
    conflict_id="conflict_001",
    resolved_content="def calculate_cost(price, tax_rate):\n    return price * (1 + tax_rate)\n",
    explanation="Keeping the new tax_rate parameter from main, adding the new function from feature branch"
)
```

**Constraints:**
- `resolved_content` must not contain `<<<<<<<`, `=======`, or `>>>>>>>` markers
- `resolved_content` must be non-empty
- `conflict_id` must reference an existing, unresolved conflict in the current episode

---

## Observation Space

After each `step()`, the agent receives a `MergeObservation`:

```python
class MergeObservation(BaseModel):
    task_id: str                          # Current task identifier
    task_description: str                 # Human-readable task description
    difficulty: str                       # "easy", "medium", or "hard"
    conflict_blocks: List[ConflictBlock]  # All UNRESOLVED conflicts
    ours_commit_message: str              # Commit message from HEAD branch
    theirs_commit_message: str            # Commit message from incoming branch
    file_contents: Dict[str, str]         # Full file contents (with markers)
    num_conflicts_remaining: int          # How many conflicts still need resolution
    num_conflicts_total: int              # Total conflicts in this task
    step_number: int                      # Current step number (1-indexed)
    max_steps: int                        # Maximum allowed steps
    previous_feedback: Optional[str]      # Feedback from last action
    done: bool                            # Whether episode is complete
```

Each `ConflictBlock` contains:
```python
class ConflictBlock(BaseModel):
    conflict_id: str                      # Unique ID (e.g. "conflict_001")
    file_path: str                        # e.g. "src/utils/calculator.py"
    ours_content: str                     # Content from HEAD branch
    theirs_content: str                   # Content from incoming branch
    surrounding_context_before: str       # 10-15 lines before the conflict
    surrounding_context_after: str        # 10-15 lines after the conflict
    ours_branch_name: str                 # e.g. "main"
    theirs_branch_name: str               # e.g. "feature/add-tax-calculation"
```

---

## Task Descriptions

| task_id | Difficulty | Conflicts | Description | Frontier Model Expected Score |
|---------|-----------|-----------|-------------|-------------------------------|
| `simple_variable_rename` | Easy | 1 (1 file) | Rename `price` → `cost` throughout calculator module; new discount function uses old name | ~0.90 |
| `import_and_usage_update` | Easy | 2 (1 file) | Migrate HTTP client from `requests` to `httpx`; new method uses old library | ~0.85 |
| `function_signature_change` | Medium | 1* (1 file) | Add required `tax_rate` param to `calculate_total()`; new bulk processing uses old sig | ~0.75 |
| `class_refactor_vs_feature_addition` | Medium | 4 (2 files) | Extract `PasswordHasher` class; new `reset_password`/`change_password` use old inline logic | ~0.65 |
| `multi_file_api_overhaul` | Hard | 4 (3 files) | API v1→v2 overhaul (Pydantic models, new paths, HTTPException); new inventory endpoints use v1 patterns | ~0.50 |

*Task 3's single conflict block contains a complex multi-function region including both definition and caller updates.

---

## Reward Function

Rewards are computed per conflict resolution and aggregated at episode end.

### Per-Conflict Score (0.0–1.0)

```
R = 0.40 × ExactMatch  +  0.30 × SyntaxValid  +  0.20 × SemanticElements  +  0.10 × NoMarkers
```

| Component | Weight | Description |
|-----------|--------|-------------|
| `ExactMatch` | 0.40 | `SequenceMatcher` similarity vs ground truth (1.0 = exact match) |
| `SyntaxValid` | 0.30 | `ast.parse()` success on the resolved Python code |
| `SemanticElements` | 0.20 | Fraction of key identifiers from ground truth present in resolution |
| `NoMarkers` | 0.10 | Hard 0.0 if any `<<<<<<<`/`=======`/`>>>>>>>` remains |

### Episode Score

```
R_episode = mean(per_conflict_scores) - accumulated_penalties
R_episode = clamp(R_episode, 0.0, 1.0)
```

### Penalty Schedule

| Event | Penalty |
|-------|---------|
| Invalid `conflict_id` | -0.05 |
| Already-resolved `conflict_id` | -0.02 |
| Empty resolution | -0.10 |
| Unresolved conflict at episode end | -0.10 per conflict |

---

## Setup Instructions

### Install locally

```bash
git clone <repo-url>
cd git-merge-resolver
pip install -e .
pip install -r server/requirements.txt
```

### Run the server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

The API docs are available at `http://localhost:7860/docs`.

### Run with Docker

```bash
# Build
docker build -t git-merge-resolver:latest -f server/Dockerfile .

# Run
docker run -p 7860:7860 git-merge-resolver:latest

# Verify
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{}'
```

### Run inference baseline

```bash
# Against local server
API_BASE_URL=http://localhost:7860 \
MODEL_NAME=gpt-4o \
LLM_API_BASE_URL=https://api.openai.com/v1 \
HF_TOKEN=your_api_key \
python inference.py
```

### Deploy to Hugging Face Spaces

1. Create a new HF Space with **Docker** SDK
2. Push this repository to the Space
3. Set the environment variable `PORT=7860` in Space settings
4. Tag the space with `openenv`

---

## Usage Example

```python
from git_merge_resolver.client import GitMergeResolverEnv
from git_merge_resolver.models import MergeAction

with GitMergeResolverEnv(base_url="http://localhost:7860") as env:
    # Start an episode
    obs = env.reset(task_id="simple_variable_rename")
    print(f"Task: {obs.task_id} | Difficulty: {obs.difficulty}")
    print(f"Conflicts to resolve: {obs.num_conflicts_total}")

    done = False
    while not done:
        # Pick the first unresolved conflict
        conflict = obs.conflict_blocks[0]
        print(f"Resolving: {conflict.conflict_id} in {conflict.file_path}")
        print(f"Ours:   {conflict.ours_content[:50]}...")
        print(f"Theirs: {conflict.theirs_content[:50]}...")

        # Submit a resolution
        action = MergeAction(
            conflict_id=conflict.conflict_id,
            resolved_content=conflict.ours_content,  # (simplified: pick ours)
            explanation="Using the main branch version as the baseline"
        )
        obs, reward, done, info = env.step(action)
        print(f"Reward: {reward.total_reward:.3f} | Feedback: {info['feedback']}")

    # Get final state
    state = env.state()
    print(f"Final score: {state.cumulative_reward / obs.num_conflicts_total:.3f}")
```

---

## Baseline Scores

Scores from running `inference.py` with GPT-4o (zero-shot):

| Task | Score | Success (≥0.8) |
|------|-------|----------------|
| `simple_variable_rename` | 0.88 | ✓ |
| `import_and_usage_update` | 0.82 | ✓ |
| `function_signature_change` | 0.74 | ✗ |
| `class_refactor_vs_feature_addition` | 0.63 | ✗ |
| `multi_file_api_overhaul` | 0.51 | ✗ |
| **Average** | **0.72** | **2/5** |

---

## Evaluation Criteria

1. **Exact/Near-Exact Match (40%)**: How closely does the resolution match the ground truth?
2. **Syntactic Validity (30%)**: Is the resolved code valid Python (`ast.parse()` succeeds)?
3. **Semantic Preservation (20%)**: Are the key identifiers and function names from the ground truth present?
4. **No Conflict Markers (10%)**: Is the resolution free of `<<<<<<<`, `=======`, `>>>>>>>` markers?

A task is considered **solved** when the final episode score ≥ 0.8.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start a new episode. Body: `{"task_id": "simple_variable_rename"}` (or omit for random) |
| `/step` | POST | Submit a conflict resolution. Body: `{"action": {"conflict_id": "...", "resolved_content": "..."}}` |
| `/state` | GET | Get current episode state |
| `/tasks` | GET | List all available tasks |
| `/health` | GET | Health check |
| `/ws` | WebSocket | Persistent session interface |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
