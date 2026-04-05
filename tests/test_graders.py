"""Tests for the deterministic grading system."""

from __future__ import annotations

import pytest

from git_merge_resolver.graders.grader import TaskGrader, build_grader_for_task, grade_episode
from git_merge_resolver.tasks.task_registry import get_all_task_ids, get_task


class TestTaskGrader:
    def setup_method(self):
        """Set up a simple grader for testing."""
        self.ground_truths = {
            "c1": "def foo():\n    cost = 42\n    return cost\n",
            "c2": "import httpx\n",
        }
        self.grader = TaskGrader(task_id="test", ground_truths=self.ground_truths)
        self.grader.set_file_paths({"c1": "src/foo.py", "c2": "src/client.py"})

    def test_perfect_score_with_exact_resolutions(self):
        """Ground truth submitted as agent resolution should score near 1.0."""
        score = self.grader.grade(self.ground_truths)
        assert score >= 0.95

    def test_zero_score_with_empty_resolutions(self):
        """Empty resolutions should score 0.0."""
        score = self.grader.grade({"c1": "", "c2": ""})
        assert score == 0.0

    def test_zero_score_with_no_resolutions(self):
        """No resolutions provided → 0.0."""
        score = self.grader.grade({})
        assert score == 0.0

    def test_partial_score_with_partial_resolutions(self):
        """One correct, one missing → partial score."""
        score = self.grader.grade({"c1": self.ground_truths["c1"]})
        # c1 is correct (≈1.0) and c2 is missing (0.0) → average ≈ 0.5
        assert 0.3 < score < 0.7

    def test_determinism(self):
        """Same inputs always produce same outputs."""
        resolutions = {"c1": "def foo():\n    cost = 42\n", "c2": "import httpx\n"}
        score1 = self.grader.grade(resolutions)
        score2 = self.grader.grade(resolutions)
        assert score1 == score2

    def test_penalty_applied(self):
        """Penalties reduce the final score."""
        score_no_penalty = self.grader.grade(self.ground_truths, penalties=0.0)
        score_with_penalty = self.grader.grade(self.ground_truths, penalties=0.2)
        assert score_with_penalty < score_no_penalty

    def test_penalty_clamped_to_zero(self):
        """Penalties cannot push score below 0.0."""
        score = self.grader.grade(self.ground_truths, penalties=100.0)
        assert score == 0.0

    def test_grade_single_conflict_perfect(self):
        """Single conflict graded correctly."""
        score = self.grader.grade_single_conflict("c1", self.ground_truths["c1"])
        assert score >= 0.9

    def test_grade_single_conflict_unknown_id(self):
        """Unknown conflict_id returns 0.0."""
        score = self.grader.grade_single_conflict("unknown", "any code")
        assert score == 0.0


class TestBuildGraderForTask:
    @pytest.mark.parametrize("task_id", [
        "simple_variable_rename",
        "import_and_usage_update",
        "function_signature_change",
        "class_refactor_vs_feature_addition",
        "multi_file_api_overhaul",
    ])
    def test_grader_builds_for_all_tasks(self, task_id):
        """A grader can be built for every registered task."""
        grader = build_grader_for_task(task_id)
        assert grader.task_id == task_id
        assert len(grader.ground_truths) > 0

    @pytest.mark.parametrize("task_id", [
        "simple_variable_rename",
        "import_and_usage_update",
        "function_signature_change",
        "class_refactor_vs_feature_addition",
        "multi_file_api_overhaul",
    ])
    def test_perfect_grade_with_ground_truth(self, task_id):
        """Submitting the ground truth resolutions should score >= 0.9."""
        task = get_task(task_id)
        grader = build_grader_for_task(task_id)
        score = grader.grade(task["ground_truths"])
        assert score >= 0.84, (
            f"Task {task_id}: expected score >= 0.84 with ground truth, got {score:.3f}"
        )

    def test_unknown_task_raises(self):
        """Unknown task_id raises KeyError."""
        with pytest.raises(KeyError):
            build_grader_for_task("nonexistent_task")


class TestGradeEpisode:
    def test_perfect_episode(self):
        task = get_task("simple_variable_rename")
        score = grade_episode("simple_variable_rename", task["ground_truths"], penalties=0.0)
        assert score >= 0.9

    def test_empty_episode(self):
        score = grade_episode("simple_variable_rename", {}, penalties=0.0)
        assert score == 0.0

    def test_with_penalties(self):
        task = get_task("simple_variable_rename")
        score_clean = grade_episode("simple_variable_rename", task["ground_truths"], penalties=0.0)
        score_penalized = grade_episode("simple_variable_rename", task["ground_truths"], penalties=0.3)
        assert score_penalized < score_clean
