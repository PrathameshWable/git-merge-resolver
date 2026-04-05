# Milestone Document: Git Merge Conflict Resolver — OpenEnv Environment

## Timeline Overview
**Total Estimated Duration**: 28 hours  
**Submission Deadline**: April 8, 2026, 11:59 PM IST  
**Start Date**: April 5, 2026

---

## Milestone 1 — Scaffold & Models (Hour 0–2)

### Description
Initialize the complete project structure, define all Pydantic data models, and set up the `openenv.yaml` specification file and `pyproject.toml` package configuration.

### Deliverables
- [ ] Project directory tree created (`git-merge-resolver/` with all subdirectories)
- [ ] `openenv.yaml` — Complete environment specification
- [ ] `pyproject.toml` — Package metadata and dependencies
- [ ] `git_merge_resolver/models.py` — All Pydantic models: `ConflictBlock`, `MergeObservation`, `MergeAction`, `MergeReward`, `MergeState`
- [ ] All `__init__.py` files created
- [ ] `planning.md` and `milestone.md` complete
- [ ] `.gitignore` created

### Success Criteria
- `python -c "from git_merge_resolver.models import MergeObservation, MergeAction"` succeeds
- `openenv validate` passes on yaml structure (syntax check)
- All model instantiations work with example data

### Estimated Time
2 hours

---

## Milestone 2 — Core Environment Logic (Hour 2–6)

### Description
Implement the core `GitMergeResolverEnvironment` class with full `step()`, `reset()`, and `state()` methods. Implement the state machine: IDLE → ACTIVE → STEPPING → DONE. Implement session management for concurrent episodes.

### Deliverables
- [ ] `git_merge_resolver/environment.py` — Full environment class
  - `reset(task_id: str) -> MergeObservation`
  - `step(action: MergeAction) -> Tuple[MergeObservation, MergeReward, bool, Dict]`
  - `state() -> MergeState`
  - Session management (episode_id → state)
  - Error handling: invalid conflict_id, already-resolved, empty resolution
- [ ] `git_merge_resolver/utils/conflict_parser.py` — Parse conflict markers from file contents
- [ ] `git_merge_resolver/utils/diff_utils.py` — SequenceMatcher similarity, key element extraction

### Success Criteria
- `reset("simple_variable_rename")` returns a valid `MergeObservation` with `done=False`
- `step()` with a valid action returns updated observation, reward, done=False
- `step()` after all conflicts resolved returns `done=True`
- `state()` returns consistent `MergeState` at any point
- Invalid conflict_id returns error feedback with -0.05 penalty

### Estimated Time
4 hours

---

## Milestone 3 — Tasks & Graders (Hour 6–10)

### Description
Implement all 5 task definitions with realistic code scenarios, ground truth resolutions, and deterministic graders. Tasks must look like real production code.

### Deliverables
- [ ] `git_merge_resolver/tasks/easy_tasks.py` — Tasks 1–2 (simple_variable_rename, import_and_usage_update)
- [ ] `git_merge_resolver/tasks/medium_tasks.py` — Tasks 3–4 (function_signature_change, class_refactor_vs_feature_addition)
- [ ] `git_merge_resolver/tasks/hard_tasks.py` — Task 5 (multi_file_api_overhaul)
- [ ] `git_merge_resolver/tasks/task_registry.py` — Registry that loads tasks by task_id
- [ ] `git_merge_resolver/graders/grader.py` — `TaskGrader` class with `grade()` method
- [ ] `git_merge_resolver/rewards/reward.py` — `compute_conflict_reward()`, `compute_episode_reward()`

### Success Criteria
- All 5 tasks loadable via `task_registry.get_task(task_id)`
- Grader returns 1.0 when given ground truth as agent resolution
- Grader returns 0.0 when given empty string as agent resolution
- Grader returns deterministic scores (same input → same output)
- Reward components sum to ≤ 1.0

### Estimated Time
4 hours

---

## Milestone 4 — Test Cases (Hour 10–14)

### Description
Write comprehensive unit and integration tests for all components. Verify that the full reset→step→done cycle works end-to-end for each task.

### Deliverables
- [ ] `tests/test_models.py` — Model instantiation, validation, serialization
- [ ] `tests/test_graders.py` — Grader correctness: perfect score, zero score, partial score
- [ ] `tests/test_rewards.py` — Reward computation: each component, edge cases
- [ ] `tests/test_environment.py` — Full episode simulation for each task, error cases
- [ ] Verify all 5 tasks pass grading tests

### Success Criteria
- `pytest tests/` passes with no errors
- Grader tests verify: perfect=1.0, empty=0.0, partial ∈ (0.0, 1.0)
- Full episode test: reset → N steps → done=True, final reward ∈ [0.0, 1.0]
- Error cases test: invalid conflict_id, already-resolved, empty resolution

### Estimated Time
4 hours

---

## Milestone 5 — Inference Script (Hour 14–18)

### Description
Implement the baseline inference script `inference.py` in the project root. The script must use the OpenAI client with environment variables `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`. Must emit exact `[START]`, `[STEP]`, `[END]` log format.

### Deliverables
- [ ] `inference.py` in project root
  - OpenAI client using `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
  - Loops through all 5 tasks
  - Structured prompt for each conflict block
  - Exact logging format: `[START]`, `[STEP]`, `[END]`
  - Retry logic for syntax errors / remaining markers
  - Completes in under 20 minutes on vcpu=2, memory=8gb
- [ ] `git_merge_resolver/client.py` — `GitMergeResolverEnv` client class (HTTP + WebSocket)

### Success Criteria
- `API_BASE_URL=http://localhost:8000 MODEL_NAME=gpt-4o HF_TOKEN=test python inference.py` runs without import errors
- Log format matches exactly: `[START]`, `[STEP]`, `[END]` lines
- All required fields present in each log line
- Script connects to running server and completes all tasks

### Estimated Time
4 hours

---

## Milestone 6 — Containerization (Hour 18–22)

### Description
Write the Dockerfile and verify the complete container lifecycle: build, run, and validate all endpoints respond correctly inside the container.

### Deliverables
- [ ] `server/Dockerfile` — Multi-stage build with Python 3.11-slim
- [ ] `server/requirements.txt` — Pinned dependency versions
- [ ] `server/app.py` — Complete FastAPI application with HTTP + WebSocket endpoints
- [ ] `docker build -t git-merge-resolver:latest .` succeeds
- [ ] `docker run -p 7860:7860 git-merge-resolver:latest` starts cleanly
- [ ] `curl http://localhost:7860/reset` returns 200

### Success Criteria
- Docker image builds in < 5 minutes
- Container starts in < 30 seconds
- `/reset` endpoint responds in < 2 seconds
- `/step` endpoint responds in < 1 second
- WebSocket `/ws` connects and handles messages
- Container uses < 4GB RAM at runtime

### Estimated Time
4 hours

---

## Milestone 7 — Deployment & Polish (Hour 22–26)

### Description
Deploy to Hugging Face Spaces, write the comprehensive README, and validate the deployment is fully functional.

### Deliverables
- [ ] `README.md` — Complete documentation (all 10 required sections)
- [ ] HF Space created with Docker SDK
- [ ] Code pushed to HF Space repository
- [ ] Space URL responds to `/reset` within 60 seconds of deployment
- [ ] Space tagged with `openenv`
- [ ] `openenv validate` passes against deployed Space

### Success Criteria
- HF Space URL is accessible
- `curl https://<space-url>/reset` returns `{"task_id": ..., "conflict_blocks": ...}` (200 OK)
- README covers all 10 required sections
- `openenv validate` reports no errors

### Estimated Time
4 hours

---

## Milestone 8 — Final Validation (Hour 26–28)

### Description
Run the pre-submission validation checklist, fix any remaining issues, and prepare the final submission.

### Deliverables
- [ ] Pre-submission checklist fully passing:
  - [ ] HF Space deploys and responds
  - [ ] `openenv validate` passes
  - [ ] `docker build` succeeds
  - [ ] `inference.py` completes without error
  - [ ] 5 tasks with deterministic graders
  - [ ] Scores in [0.0, 1.0] range
- [ ] Final `git commit` with clean state
- [ ] Submission URL registered on hackathon platform

### Success Criteria
- All 5 checklist items pass
- Inference script produces score output for all 5 tasks
- No unhandled exceptions in any endpoint
- Clean git history

### Estimated Time
2 hours

---

## Risk Buffer
1 hour reserved for unexpected blockers (HF Space cold start issues, OpenEnv spec changes, dependency conflicts).

---

## Dependencies Map

```
Milestone 1 (Models)
    └── Milestone 2 (Environment) ─────────────────────┐
            └── Milestone 3 (Tasks & Graders) ─────────┤
                    └── Milestone 4 (Tests)             │
                    └── Milestone 5 (Inference) ────────┤
                            └── Milestone 6 (Docker) ───┤
                                    └── Milestone 7 (Deploy)
                                            └── Milestone 8 (Validate)
```

All milestones are sequential. No parallel work streams (single developer).
