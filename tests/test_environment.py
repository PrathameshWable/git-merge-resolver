"""
Integration tests for the full environment lifecycle.

Tests the complete reset() → step() → done cycle for each task,
as well as error handling for invalid actions.
"""

from __future__ import annotations

import pytest

from git_merge_resolver.environment import GitMergeResolverEnvironment
from git_merge_resolver.models import MergeAction
from git_merge_resolver.tasks.task_registry import get_all_task_ids, get_task


@pytest.fixture
def env():
    """Create a fresh environment for each test."""
    return GitMergeResolverEnvironment()


class TestReset:
    def test_reset_with_task_id(self, env):
        obs = env.reset("simple_variable_rename")
        assert obs.task_id == "simple_variable_rename"
        assert obs.done is False
        assert len(obs.conflict_blocks) > 0
        assert obs.num_conflicts_remaining > 0
        assert obs.step_number == 0

    def test_reset_with_random_task(self, env):
        obs = env.reset()
        assert obs.task_id in get_all_task_ids()
        assert obs.done is False

    def test_reset_invalid_task_raises(self, env):
        with pytest.raises(KeyError):
            env.reset("nonexistent_task")

    def test_reset_creates_new_episode(self, env):
        obs1 = env.reset("simple_variable_rename")
        obs2 = env.reset("import_and_usage_update")
        # New episode → different task
        assert obs2.task_id != obs1.task_id

    def test_reset_sets_correct_metadata(self, env):
        obs = env.reset("simple_variable_rename")
        assert obs.difficulty == "easy"
        assert obs.max_steps == 5
        assert obs.num_conflicts_total == 1


class TestStep:
    def test_valid_step_reduces_pending_count(self, env):
        task = get_task("simple_variable_rename")
        obs = env.reset("simple_variable_rename")
        initial_remaining = obs.num_conflicts_remaining

        action = MergeAction(
            conflict_id="conflict_001",
            resolved_content=task["ground_truths"]["conflict_001"],
        )
        obs2, reward, done, info = env.step(action)

        assert obs2.num_conflicts_remaining == initial_remaining - 1

    def test_valid_step_returns_reward(self, env):
        task = get_task("simple_variable_rename")
        env.reset("simple_variable_rename")
        action = MergeAction(
            conflict_id="conflict_001",
            resolved_content=task["ground_truths"]["conflict_001"],
        )
        _, reward, _, _ = env.step(action)
        assert 0.0 <= reward.total_reward <= 1.0

    def test_resolving_all_conflicts_sets_done(self, env):
        task = get_task("simple_variable_rename")
        env.reset("simple_variable_rename")

        for conflict_id, resolution in task["ground_truths"].items():
            action = MergeAction(conflict_id=conflict_id, resolved_content=resolution)
            obs, reward, done, info = env.step(action)

        assert done is True
        assert obs.done is True

    def test_invalid_conflict_id_penalizes(self, env):
        env.reset("simple_variable_rename")
        action = MergeAction(
            conflict_id="nonexistent_conflict",
            resolved_content="some code",
        )
        obs, reward, done, info = env.step(action)
        assert reward.total_reward == 0.0
        assert "feedback" in info
        assert "Invalid" in info["feedback"] or "invalid" in info["feedback"].lower()

    def test_empty_resolution_penalizes(self, env):
        env.reset("simple_variable_rename")
        action = MergeAction(conflict_id="conflict_001", resolved_content="")
        obs, reward, done, info = env.step(action)
        assert reward.total_reward == 0.0

    def test_already_resolved_conflict_penalizes(self, env):
        task = get_task("simple_variable_rename")
        env.reset("simple_variable_rename")

        # Resolve it once (correctly)
        action = MergeAction(
            conflict_id="conflict_001",
            resolved_content=task["ground_truths"]["conflict_001"],
        )
        env.step(action)

        # Reset manually by resetting episode state
        env.reset("simple_variable_rename")
        task2 = get_task("import_and_usage_update")
        env.reset("import_and_usage_update")

        # Resolve first conflict
        action1 = MergeAction(
            conflict_id="conflict_001",
            resolved_content=task2["ground_truths"]["conflict_001"],
        )
        env.step(action1)

        # Try to resolve the same conflict again
        obs, reward, done, info = env.step(action1)
        assert reward.total_reward == 0.0
        assert "already" in info.get("feedback", "").lower()

    def test_step_after_done_returns_done(self, env):
        task = get_task("simple_variable_rename")
        env.reset("simple_variable_rename")

        # Complete the episode
        for cid, res in task["ground_truths"].items():
            env.step(MergeAction(conflict_id=cid, resolved_content=res))

        # Another step should return done=True
        obs, reward, done, info = env.step(
            MergeAction(conflict_id="conflict_001", resolved_content="x")
        )
        assert done is True

    def test_max_steps_terminates_episode(self, env):
        env.reset("simple_variable_rename")
        done = False
        steps = 0

        while not done and steps < 20:
            obs, reward, done, info = env.step(
                MergeAction(conflict_id="conflict_001", resolved_content="code")
            )
            steps += 1

        assert done is True
        assert steps <= 5 + 1  # max_steps=5, but first resolution marks done


class TestState:
    def test_state_before_reset_raises(self):
        env = GitMergeResolverEnvironment()
        with pytest.raises(RuntimeError):
            env.state()

    def test_state_after_reset(self, env):
        env.reset("simple_variable_rename")
        state = env.state()
        assert state.task_id == "simple_variable_rename"
        assert state.step_count == 0
        assert state.done is False
        assert len(state.pending_conflicts) == 1

    def test_state_updates_after_step(self, env):
        task = get_task("simple_variable_rename")
        env.reset("simple_variable_rename")

        action = MergeAction(
            conflict_id="conflict_001",
            resolved_content=task["ground_truths"]["conflict_001"],
        )
        env.step(action)

        state = env.state()
        assert state.step_count == 1
        assert "conflict_001" in state.resolved_conflicts
        assert state.cumulative_reward > 0.0


class TestFullEpisodePerTask:
    @pytest.mark.parametrize("task_id", [
        "simple_variable_rename",
        "import_and_usage_update",
        "function_signature_change",
        "class_refactor_vs_feature_addition",
        "multi_file_api_overhaul",
    ])
    def test_full_episode_with_ground_truth(self, task_id):
        """Submitting ground truth resolutions should complete episode with high score."""
        env = GitMergeResolverEnvironment()
        task = get_task(task_id)

        obs = env.reset(task_id)
        assert obs.task_id == task_id
        assert not obs.done

        done = False
        total_reward = 0.0
        steps = 0

        for conflict_id, resolution in task["ground_truths"].items():
            if done:
                break
            action = MergeAction(conflict_id=conflict_id, resolved_content=resolution)
            obs, reward, done, info = env.step(action)
            total_reward += reward.total_reward
            steps += 1

        assert done is True, f"Episode not done after submitting all {steps} resolutions"

        final_score = env.final_score()
        assert final_score >= 0.8, (
            f"Task {task_id}: expected final score >= 0.8 with ground truth, "
            f"got {final_score:.3f}"
        )
