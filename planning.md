# Planning Document: Git Merge Conflict Resolver — OpenEnv Environment

## Project Overview

### What This Environment Does
The **Git Merge Conflict Resolver** is an OpenEnv environment that simulates one of the most common yet cognitively demanding tasks in software development: resolving Git merge conflicts. An AI agent is presented with conflicted source files containing `<<<<<<<`, `=======`, and `>>>>>>>` markers, alongside context about what each branch intended, and must produce the correct merged resolution.

The agent must:
- Understand the semantic intent of both branches' changes
- Synthesize a correct resolution that preserves both intents where possible
- Produce syntactically valid code
- Handle multi-file, cross-dependency scenarios in harder tasks

### Why It Matters
Git merge conflicts are an unavoidable part of collaborative software development. Studies show developers spend 20–30% of their time on integration work, with merge conflict resolution being one of the most mentally taxing sub-tasks. Current AI coding assistants (GitHub Copilot, Cursor) handle simple conflicts but fail on complex, multi-file scenarios. A rigorous benchmark environment enables systematic evaluation and improvement.

### Why It's Novel
No Git merge conflict resolver exists in the OpenEnv catalog. The closest environments involve single-file code completion or bug fixing — but merge resolution requires:
- **Dual-context reasoning**: Understanding two divergent development histories simultaneously
- **Semantic synthesis**: Not just picking one side, but combining intentions intelligently
- **Cross-file consistency**: In hard tasks, changes must be consistent across multiple interdependent files
- **Realistic code understanding**: Production-level Python code with classes, imports, decorators, type hints

---

## Architecture Design

### System Overview
```
┌─────────────────────────────────────────────┐
│              Inference Script                │
│  (inference.py — runs LLM agent)            │
└───────────────────┬─────────────────────────┘
                    │ HTTP + WebSocket
┌───────────────────▼─────────────────────────┐
│           FastAPI Server (server/app.py)     │
│  POST /reset   POST /step   GET /state      │
│  WebSocket /ws                              │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│        GitMergeResolverEnvironment           │
│         (git_merge_resolver/environment.py) │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Tasks   │  │ Graders  │  │ Rewards  │ │
│  │ Registry │  │  System  │  │  Engine  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

### Session Management
- Sessions are identified by `episode_id` (UUID4 generated at `reset()`)
- Session state is held in-memory in a dictionary keyed by `episode_id`
- WebSocket connections maintain their session for the lifetime of the connection
- HTTP endpoints use a single global session (simple mode, suitable for evaluation)
- Concurrent sessions are supported via the session dictionary

### Environment State Machine
```
        ┌─────────────────────────────────────────┐
        │             IDLE (pre-reset)             │
        └──────────────────┬──────────────────────┘
                           │ POST /reset?task_id=X
        ┌──────────────────▼──────────────────────┐
        │           ACTIVE (step loop)             │
        │  - All conflicts pending                 │
        │  - step_count = 0                       │
        └──┬───────────────────────────────────────┘
           │ POST /step (MergeAction)
           │ (repeat for each conflict)
        ┌──▼────────────────────────────────────────┐
        │  STEPPING                                  │
        │  - One conflict resolved per step          │
        │  - Reward computed incrementally           │
        │  - Feedback generated for next step        │
        └──┬──────────────────────────────────────┬─┘
           │ all conflicts resolved                │ max_steps reached
        ┌──▼──────────────────────┐  ┌────────────▼────────────┐
        │  DONE (success)         │  │  DONE (timeout)          │
        │  done=True              │  │  done=True               │
        │  penalties=0            │  │  penalties applied       │
        └─────────────────────────┘  └──────────────────────────┘
```

---

## Data Model Design

### ConflictBlock
Represents a single `<<<<<<< ... ======= ... >>>>>>>` section within a file.

| Field | Type | Example |
|-------|------|---------|
| conflict_id | str | `"conflict_001"` |
| file_path | str | `"src/utils/calculator.py"` |
| ours_content | str | `"    cost = base_price * 1.1\n"` |
| theirs_content | str | `"    price = base_price * 1.1\n"` |
| surrounding_context_before | str | 10–15 lines before the conflict marker |
| surrounding_context_after | str | 10–15 lines after the conflict marker |
| ours_branch_name | str | `"main"` |
| theirs_branch_name | str | `"feature/add-tax-calculation"` |

### MergeObservation
The full observation returned to the agent at each step.

| Field | Type | Example |
|-------|------|---------|
| task_id | str | `"simple_variable_rename"` |
| task_description | str | `"Resolve variable rename conflict..."` |
| difficulty | str | `"easy"` |
| conflict_blocks | List[ConflictBlock] | List of all unresolved conflicts |
| ours_commit_message | str | `"refactor: rename price to cost for clarity"` |
| theirs_commit_message | str | `"feat: add discount calculation feature"` |
| file_contents | Dict[str, str] | `{"src/calc.py": "<full file with markers>"}` |
| num_conflicts_remaining | int | `2` |
| num_conflicts_total | int | `3` |
| step_number | int | `1` |
| max_steps | int | `5` |
| previous_feedback | Optional[str] | `"Syntax valid, missing key identifier 'cost'"` |
| done | bool | `False` |

### MergeAction
The action the agent submits to resolve a single conflict.

| Field | Type | Example |
|-------|------|---------|
| conflict_id | str | `"conflict_001"` |
| resolved_content | str | `"    cost = base_price * 1.1\n"` |
| explanation | Optional[str] | `"Using 'cost' as it's the new canonical name"` |

### MergeReward
Decomposed reward signal returned after each step.

| Field | Type | Range |
|-------|------|-------|
| total_reward | float | 0.0–1.0 |
| conflict_resolution_score | float | 0.0–0.4 |
| syntax_validity_score | float | 0.0–0.3 |
| consistency_score | float | 0.0–0.2 |
| explanation_bonus | float | 0.0–0.1 |

### MergeState
Full serializable environment state.

| Field | Type | Description |
|-------|------|-------------|
| episode_id | str | UUID4 |
| task_id | str | Current task identifier |
| step_count | int | Number of steps taken |
| resolved_conflicts | Dict[str, str] | conflict_id → agent's resolution |
| pending_conflicts | List[str] | conflict_ids not yet resolved |
| cumulative_reward | float | Sum of all per-step rewards |
| done | bool | Episode completion flag |

---

## Task Design

### Task 1: `simple_variable_rename` (EASY)
**Scenario**: A utility module for a financial calculator. Developer A renamed the variable `price` to `cost` throughout the file for semantic clarity (a common refactoring). Developer B, working on a feature branch, added a `calculate_discount` function that uses the old variable name `price`.

**Conflicts**: 1 conflict block in `src/utils/calculator.py`
**Ground Truth**: Use `cost` everywhere — it's the canonical new name
**Difficulty Factors**:
- Single conflict, single file
- Intent is unambiguous from commit messages
- Resolution is straightforwardly using the new name

---

### Task 2: `import_and_usage_update` (EASY)
**Scenario**: A data processing module. Developer A upgraded from `requests` to `httpx` for async support, updating both the import and the HTTP call pattern. Developer B added a new API call using the old `requests` pattern.

**Conflicts**: 2 conflict blocks in `src/api/client.py` (import + usage)
**Ground Truth**: Keep `httpx` import AND update the new code to use `httpx.get()` pattern
**Difficulty Factors**:
- Two conflicts but clearly linked (both about the same library migration)
- Agent must infer the new pattern from the first resolved conflict

---

### Task 3: `function_signature_change` (MEDIUM)
**Scenario**: A tax calculation service. Developer A added a required `tax_rate: float` parameter to `calculate_total()` and updated all existing call sites. Developer B added new invoice processing functions that call `calculate_total()` with the old signature.

**Conflicts**: 3 conflict blocks in `src/services/billing.py`
**Ground Truth**: Keep new signature AND update new call sites to pass `tax_rate=0.0` as default
**Difficulty Factors**:
- Multiple conflicts with semantic dependency (definition + callers)
- Agent must infer a reasonable default value for the new parameter

---

### Task 4: `class_refactor_vs_feature_addition` (MEDIUM)
**Scenario**: A user authentication module. Developer A extracted password hashing into a dedicated `PasswordHasher` class (Strategy pattern). Developer B added new `reset_password()` and `change_password()` methods to `UserManager` that use the old inline hashing logic.

**Conflicts**: 4 conflict blocks across 2 files (`src/auth/manager.py`, `src/auth/models.py`)
**Ground Truth**: Use `PasswordHasher` in the new methods, update models to reference new structure
**Difficulty Factors**:
- Cross-file dependency: models.py must be consistent with manager.py
- Agent must understand the design pattern being introduced
- New methods must be adapted to the refactored architecture

---

### Task 5: `multi_file_api_overhaul` (HARD)
**Scenario**: A REST API service. Developer A overhauled the API layer: changed endpoint paths from `/api/v1/` to `/api/v2/`, migrated from `dict` responses to Pydantic response models, and standardized error handling with `HTTPException`. Developer B added new `/products/` endpoints and integration tests using the old v1 patterns.

**Conflicts**: 6 conflict blocks across 3 files (`api/routes.py`, `api/models.py`, `tests/test_api.py`)
**Ground Truth**: New endpoints must follow v2 patterns (Pydantic models, v2 paths, HTTPException errors), tests must use v2 paths
**Difficulty Factors**:
- Three interdependent files
- Agent must recognize and apply an architectural pattern to new code
- Tests must be updated to match new patterns
- Consistency across all three files is required for full score

---

## Reward Function Design

### Mathematical Formulation

For a single conflict resolution, the reward `R(a, g)` where `a` is the agent's resolution and `g` is the ground truth:

```
R(a, g) = w1 * ExactMatch(a, g) + w2 * Syntax(a, ctx) + w3 * Semantic(a, g) + w4 * NoMarkers(a)

where:
  w1 = 0.40  (exact/near-exact match)
  w2 = 0.30  (syntactic validity)
  w3 = 0.20  (semantic element preservation)
  w4 = 0.10  (absence of conflict markers)
  w1 + w2 + w3 + w4 = 1.00
```

**ExactMatch(a, g)**:
```
ExactMatch(a, g) = {
  1.0,  if normalize(a) == normalize(g)
  SequenceMatcher(a, g).ratio(),  otherwise
}
```

Where `normalize()` strips leading/trailing whitespace and normalizes internal whitespace.

**Syntax(a, ctx)**:
```
Syntax(a, ctx) = {
  1.0,  if ast.parse(ctx_with_a) succeeds
  0.5,  if ast.parse(a) succeeds (partial context)
  0.0,  if ast.parse fails
}
```
For non-Python files: `Syntax = 1.0` (no penalty)

**Semantic(a, g)**:
```
Semantic(a, g) = |{e ∈ KeyElements(g) : e ∈ a}| / |KeyElements(g)|
```
Where `KeyElements(g)` = set of identifiers, function names, class names extracted from ground truth.

**NoMarkers(a)**:
```
NoMarkers(a) = {
  1.0,  if a contains no "<<<<<", "=====", or ">>>>>" substrings
  0.0,  otherwise
}
```

### Episode-Level Reward
```
R_episode = mean({R(a_i, g_i) for i in conflicts}) - Σ penalties
R_episode = clamp(R_episode, 0.0, 1.0)
```

### Penalty Schedule
| Action | Penalty |
|--------|---------|
| Invalid conflict_id | -0.05 |
| Already-resolved conflict_id | -0.02 |
| Empty resolution | -0.10 |
| Unresolved conflict at episode end | -0.10 per conflict |

### Score Range Analysis
- **Perfect agent**: 1.0 (all conflicts exactly matched, no penalties)
- **Good agent**: 0.7–0.9 (correct intent, minor whitespace differences)
- **Partial agent**: 0.4–0.6 (correct identifiers but structural differences)
- **Poor agent**: 0.1–0.3 (picks one side verbatim, misses synthesis)
- **Failing agent**: 0.0–0.1 (leaves markers, empty resolutions)

---

## Grading System Design

Each task's grader is deterministic and reproducible:

1. **Input**: `Dict[conflict_id → agent_resolution]`
2. **Process**: For each conflict in the task's ground truth set, compute `R(a, g)`. If a conflict is missing from agent's resolutions, score = 0.0.
3. **Output**: Average score across all conflicts ∈ [0.0, 1.0]

The grader is deterministic because:
- `difflib.SequenceMatcher` is deterministic for fixed inputs
- `ast.parse()` is deterministic
- String operations are deterministic
- No randomness or LLM calls in the grader

Success criterion: score ≥ 0.8 is considered a "pass" for a task (agent understood and correctly resolved the conflicts).

---

## Test Case Generation Strategy

Conflicts are generated by simulating realistic development scenarios:

1. **Base file**: Production-looking Python code with proper conventions
2. **Branch A changes**: Semantic refactoring (rename, restructure, new parameter)
3. **Branch B changes**: Feature addition using the old structure
4. **Conflict insertion**: Merge both branches to create actual conflict markers
5. **Ground truth derivation**: Manually craft the correct merged resolution

Each scenario follows these realism principles:
- Code uses real Python idioms (dataclasses, type hints, context managers)
- Variable/function names follow PEP 8
- There are realistic import statements, docstrings, and error handling
- Commit messages are realistic (`feat:`, `refactor:`, `fix:` prefixes)

---

## Inference Strategy

The baseline agent uses a zero-shot LLM approach:

1. **Observation parsing**: Extract all `ConflictBlock` objects from the observation
2. **Prioritization**: Process conflicts in order (conflict_001, conflict_002, ...)
3. **Prompt construction**: For each conflict, build a structured prompt with:
   - File path and branch names
   - Commit messages (critical context)
   - 10-15 lines of context before/after
   - The exact conflict content (ours vs theirs)
4. **LLM call**: Single-turn, zero-shot resolution request
5. **Response parsing**: Extract only the code (strip markdown fences if present)
6. **Action submission**: Submit `MergeAction(conflict_id, resolved_content)`
7. **Feedback integration**: If previous_feedback indicates an error, retry with hint

Retry logic: If feedback indicates "conflict markers remain" or "syntax invalid", regenerate with explicit instruction to fix the specific issue.

---

## Deployment Plan

### Phase 1: Local Development
```bash
cd git-merge-resolver
pip install -e .
cd server && pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

### Phase 2: Docker Build & Test
```bash
docker build -t git-merge-resolver:latest .
docker run -p 7860:7860 git-merge-resolver:latest
curl http://localhost:7860/reset
```

### Phase 3: HF Spaces Deployment
1. Create new HF Space with Docker SDK
2. Push code to Space repository
3. Space auto-builds and deploys
4. Tag space with `openenv`
5. Verify `/reset` endpoint responds within 30s of deployment

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker build fails | Low | High | Test locally first, pin dependency versions |
| HF Space timeout | Medium | High | Keep environment lightweight, no heavy imports |
| Grader non-determinism | Low | High | Avoid random operations in grader, use fixed seeds |
| Inference > 20 min | Medium | High | Limit conflicts per task, use efficient prompts |
| OpenEnv spec drift | Low | Medium | Validate against spec early, keep spec pinned |
| Memory leak in sessions | Low | Medium | Implement session cleanup after episode completion |
