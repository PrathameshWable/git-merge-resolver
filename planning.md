# Planning Notes

rough notes before I start building — will clean up later (or not)

---

## What is this

An OpenEnv environment for resolving git merge conflicts. Agent gets a file with
`<<<<<<<` markers, has to figure out the right merge and submit it.

No environment like this exists in the catalog which is the main reason I'm doing this.
Merge conflicts are genuinely annoying and something LLMs *should* be good at but
nobody has actually benchmarked it properly.

---

## How it works (rough sketch)

```
reset(task_id) → give agent the conflicted file + context
step(action)   → agent submits resolution for one conflict block
               → score it, give feedback, repeat
done           → all conflicts resolved or ran out of steps
```

Session state lives in memory. Simple dict keyed by episode_id.
Good enough for a hackathon, would need a proper store for production.

---

## Data models (what I need)

**ConflictBlock** — one `<<<<<<< ... >>>>>>>` section
- conflict_id, file_path
- ours_content, theirs_content
- some context lines before/after so the agent isn't flying blind
- branch names

**MergeObservation** — what the agent sees each step
- all unresolved conflict blocks
- commit messages from both branches (this is actually really useful context)
- file contents with markers still in them
- step count, max steps, feedback from last action

**MergeAction** — what the agent submits
- which conflict_id to resolve
- the resolved content (no markers allowed)
- optional explanation

**MergeReward** — score breakdown
- total, match score, syntax score, semantic score, no-markers check

---

## Tasks (5 total, easy → hard)

1. variable rename — someone renamed `price` to `cost`, other person added code using old name. 1 conflict. obvious answer.

2. import swap — migration from `requests` to `httpx`. new code uses old library. 2 conflicts (import + usage).

3. function signature — added required param `tax_rate`. callers in feature branch use old signature. need to update callers with sensible default.

4. class refactor — extracted password hashing into its own class. new methods use old inline approach. spans 2 files.

5. API overhaul — v1 to v2 migration. new endpoints added in v1 style. need to port them to v2 (pydantic models, new paths, proper error handling). 3 files.

difficulty comes from: number of conflicts, number of files, whether you need to infer something (like a default value), whether the pattern needs to be recognized and applied

---

## Reward function

want partial credit — binary 0/1 is bad for training signal

breakdown:
- 40% exact/near-exact match vs ground truth (sequence matcher ratio)
- 30% syntax valid (ast.parse on resolved python)
- 20% semantic — are the key identifiers from ground truth present?
- 10% no conflict markers left (hard zero if markers remain)
- small bonus for explanation quality

penalties:
- wrong conflict_id: -0.05
- already resolved: -0.02
- empty submission: -0.10
- unresolved at end: -0.10 per conflict

episode score = mean of conflict scores - penalties, clamped to [0, 1]

---

## Server

FastAPI. endpoints:
- POST /reset
- POST /step
- GET /state
- GET /tasks
- GET /health
- WS /ws (websocket for persistent sessions)

needs to respond in < 2s for reset, < 1s for step
no heavy computation in the environment itself

---

## Inference script

needs to:
- loop through all 5 tasks
- call LLM for each conflict block
- log [START] / [STEP] / [END] in exact format
- finish in < 20 min
- use OpenAI client with API_BASE_URL, MODEL_NAME, HF_TOKEN env vars

prompt should include: file path, branch names, commit messages, context before/after, ours vs theirs

---

## Deployment

docker → HF spaces. port 7860.
Dockerfile needs to be at root (not in server/) for HF to pick it up — learned this the hard way.

---

## Things that could go wrong

- Docker build fails on HF (dependency version issue)
- inference script hits rate limits / times out
- grader has some edge case that gives weird scores
- HF space goes to sleep mid-evaluation (set sleep to 48h)
