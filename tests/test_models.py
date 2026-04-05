"""Tests for Pydantic model instantiation and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from git_merge_resolver.models import (
    ConflictBlock,
    MergeAction,
    MergeObservation,
    MergeReward,
    MergeState,
    ResetRequest,
    StepRequest,
    StepResponse,
)


class TestConflictBlock:
    def test_basic_instantiation(self):
        block = ConflictBlock(
            conflict_id="conflict_001",
            file_path="src/utils/calc.py",
            ours_content="x = 1\n",
            theirs_content="x = 2\n",
        )
        assert block.conflict_id == "conflict_001"
        assert block.file_path == "src/utils/calc.py"
        assert block.ours_branch_name == "main"
        assert block.theirs_branch_name == "feature-branch"

    def test_custom_branch_names(self):
        block = ConflictBlock(
            conflict_id="c1",
            file_path="a.py",
            ours_content="a",
            theirs_content="b",
            ours_branch_name="develop",
            theirs_branch_name="feature/xyz",
        )
        assert block.ours_branch_name == "develop"
        assert block.theirs_branch_name == "feature/xyz"

    def test_serialization(self):
        block = ConflictBlock(
            conflict_id="c1",
            file_path="a.py",
            ours_content="a",
            theirs_content="b",
        )
        data = block.model_dump()
        assert data["conflict_id"] == "c1"
        assert "surrounding_context_before" in data
        assert "surrounding_context_after" in data


class TestMergeObservation:
    def test_basic_instantiation(self):
        obs = MergeObservation(
            task_id="test_task",
            task_description="A test task",
            difficulty="easy",
            ours_commit_message="fix: something",
            theirs_commit_message="feat: something else",
            num_conflicts_remaining=1,
            num_conflicts_total=1,
            step_number=1,
            max_steps=5,
        )
        assert obs.task_id == "test_task"
        assert obs.difficulty == "easy"
        assert obs.done is False
        assert obs.previous_feedback is None

    def test_with_conflict_blocks(self):
        block = ConflictBlock(
            conflict_id="c1",
            file_path="a.py",
            ours_content="a",
            theirs_content="b",
        )
        obs = MergeObservation(
            task_id="t1",
            task_description="desc",
            difficulty="medium",
            conflict_blocks=[block],
            ours_commit_message="ours",
            theirs_commit_message="theirs",
            num_conflicts_remaining=1,
            num_conflicts_total=1,
            step_number=0,
            max_steps=10,
        )
        assert len(obs.conflict_blocks) == 1
        assert obs.conflict_blocks[0].conflict_id == "c1"

    def test_serialization_roundtrip(self):
        obs = MergeObservation(
            task_id="t1",
            task_description="d",
            difficulty="hard",
            ours_commit_message="o",
            theirs_commit_message="t",
            num_conflicts_remaining=0,
            num_conflicts_total=3,
            step_number=3,
            max_steps=15,
            done=True,
        )
        data = obs.model_dump()
        obs2 = MergeObservation(**data)
        assert obs2.task_id == obs.task_id
        assert obs2.done == obs.done


class TestMergeAction:
    def test_basic_instantiation(self):
        action = MergeAction(
            conflict_id="conflict_001",
            resolved_content="def foo():\n    return 42\n",
        )
        assert action.conflict_id == "conflict_001"
        assert action.explanation is None

    def test_with_explanation(self):
        action = MergeAction(
            conflict_id="c1",
            resolved_content="code",
            explanation="Using the new naming convention from main branch",
        )
        assert action.explanation is not None
        assert "naming" in action.explanation

    def test_empty_resolved_content_allowed(self):
        # The model allows empty string — the environment validates it
        action = MergeAction(conflict_id="c1", resolved_content="")
        assert action.resolved_content == ""


class TestMergeReward:
    def test_basic_instantiation(self):
        reward = MergeReward(
            total_reward=0.85,
            conflict_resolution_score=0.35,
            syntax_validity_score=0.25,
            consistency_score=0.18,
            explanation_bonus=0.07,
        )
        assert reward.total_reward == 0.85

    def test_bounds_validation(self):
        with pytest.raises(ValidationError):
            MergeReward(
                total_reward=1.5,  # > 1.0 → invalid
                conflict_resolution_score=0.4,
                syntax_validity_score=0.3,
                consistency_score=0.2,
                explanation_bonus=0.1,
            )

    def test_zero_reward(self):
        reward = MergeReward(
            total_reward=0.0,
            conflict_resolution_score=0.0,
            syntax_validity_score=0.0,
            consistency_score=0.0,
            explanation_bonus=0.0,
        )
        assert reward.total_reward == 0.0


class TestMergeState:
    def test_basic_instantiation(self):
        state = MergeState(
            episode_id="abc-123",
            task_id="task1",
            step_count=2,
            resolved_conflicts={"c1": "code"},
            pending_conflicts=["c2"],
            cumulative_reward=0.75,
        )
        assert state.episode_id == "abc-123"
        assert state.done is False
        assert len(state.resolved_conflicts) == 1

    def test_serialization(self):
        state = MergeState(
            episode_id="xyz",
            task_id="t1",
            step_count=0,
            cumulative_reward=0.0,
        )
        data = state.model_dump()
        assert "episode_id" in data
        assert "pending_conflicts" in data
        assert data["pending_conflicts"] == []
