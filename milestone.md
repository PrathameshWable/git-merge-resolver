# Milestones

rough timeline — deadline is April 8, 11:59 PM IST

---

## M1 — models + scaffold
- pyproject, openenv.yaml, all pydantic models
- get basic imports working, make sure the package installs cleanly
- done when: `from git_merge_resolver.models import MergeAction` works

## M2 — environment core
- reset(), step(), state()
- session management
- error handling (invalid id, already resolved, empty)
- done when: can manually run reset → step → done in python shell

## M3 — tasks + graders
- write all 5 conflict scenarios (this is the most time-consuming part)
- make the code look real, not like a textbook example
- grader for each task, verify perfect score with ground truth
- done when: grader returns 1.0 for ground truth, 0.0 for empty

## M4 — tests
- unit tests for models, rewards, graders
- integration test for full episode cycle
- done when: pytest passes

## M5 — inference script
- OpenAI client, env vars, prompt construction
- exact [START]/[STEP]/[END] log format
- done when: script runs end to end without crashing

## M6 — docker
- Dockerfile at root (HF spaces needs it there)
- test locally: build → run → curl /reset
- done when: 200 response from docker container

## M7 — deploy + README
- push to HF spaces
- write README (include openenv yaml frontmatter or it breaks)
- tag with openenv
- done when: space shows Running and /reset returns 200

## M8 — final check + submit
- run inference against deployed space
- submit URL on hackathon platform
- done when: submitted

---

actual time spent was roughly double the estimates on tasks and graders.
the docker root path issue cost about 30 min.
