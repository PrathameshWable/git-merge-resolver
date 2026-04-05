"""Tests for the reward computation functions."""

from __future__ import annotations

import pytest

from git_merge_resolver.rewards.reward import (
    compute_conflict_reward,
    compute_episode_reward,
    compute_explanation_bonus,
    compute_match_score,
    compute_no_markers_score,
    compute_semantic_score,
    compute_syntax_score,
)


class TestMatchScore:
    def test_exact_match(self):
        code = "def foo():\n    return 42\n"
        assert compute_match_score(code, code) == 1.0

    def test_whitespace_normalized_match(self):
        a = "def foo():\n    return 42\n"
        b = "def foo():\n  return 42\n"  # different indentation
        score = compute_match_score(a, b)
        assert score > 0.7  # High but not perfect after normalization

    def test_completely_different(self):
        a = "x = 1\n"
        b = "class FooBarBazQux:\n    pass\n" * 5
        score = compute_match_score(a, b)
        assert score < 0.5

    def test_empty_ground_truth(self):
        score = compute_match_score("", "")
        assert score == 1.0

    def test_partial_match(self):
        a = "def foo():\n    x = 1\n    return x\n"
        b = "def foo():\n    x = 2\n    return x\n"
        score = compute_match_score(a, b)
        assert 0.5 < score < 1.0


class TestSyntaxScore:
    def test_valid_python(self):
        code = "def hello():\n    return 'world'\n"
        score = compute_syntax_score(code, "src/utils.py")
        assert score == 1.0

    def test_invalid_python(self):
        code = "def hello(\n    return 'world'"  # syntax error
        score = compute_syntax_score(code, "src/utils.py")
        assert score < 1.0

    def test_non_python_file_always_full_score(self):
        code = "this is not python but it doesn't matter"
        score = compute_syntax_score(code, "config.yaml")
        assert score == 1.0

    def test_non_python_file_even_with_errors(self):
        score = compute_syntax_score("{{invalid yaml: }}", "config.yaml")
        assert score == 1.0


class TestSemanticScore:
    def test_all_elements_present(self):
        gt = "def calculate_cost(price, tax_rate):\n    return price * (1 + tax_rate)\n"
        agent = "def calculate_cost(price, tax_rate):\n    result = price * (1 + tax_rate)\n    return result\n"
        score = compute_semantic_score(agent, gt)
        assert score > 0.7

    def test_missing_key_elements(self):
        gt = "def calculate_cost(price, tax_rate):\n    return price * (1 + tax_rate)\n"
        agent = "def compute_value(x, y):\n    return x + y\n"
        score = compute_semantic_score(agent, gt)
        assert score < 0.5

    def test_empty_ground_truth(self):
        score = compute_semantic_score("anything", "")
        assert score == 1.0


class TestNoMarkersScore:
    def test_no_markers(self):
        code = "def foo():\n    return 1\n"
        assert compute_no_markers_score(code) == 1.0

    def test_has_start_marker(self):
        code = "<<<<<<< main\ndef foo():\n    return 1\n"
        assert compute_no_markers_score(code) == 0.0

    def test_has_sep_marker(self):
        code = "def foo():\n=======\n    return 1\n"
        assert compute_no_markers_score(code) == 0.0

    def test_has_end_marker(self):
        code = "def foo():\n    return 1\n>>>>>>> feature\n"
        assert compute_no_markers_score(code) == 0.0


class TestExplanationBonus:
    def test_no_explanation(self):
        bonus = compute_explanation_bonus(None, "def foo(): pass")
        assert bonus == 0.0

    def test_short_explanation(self):
        bonus = compute_explanation_bonus("Yes", "def foo(): pass")
        assert bonus == 0.0  # Too short

    def test_meaningful_explanation(self):
        gt = "def calculate_cost(price, tax_rate):\n    return price * (1 + tax_rate)\n"
        explanation = "Using calculate_cost with tax_rate as per the main branch refactoring"
        bonus = compute_explanation_bonus(explanation, gt)
        assert bonus > 0.0

    def test_explanation_cap(self):
        gt = "def foo(): pass"
        explanation = "This is a meaningful explanation that mentions foo function"
        bonus = compute_explanation_bonus(explanation, gt)
        assert bonus <= 0.05  # Max explanation bonus


class TestComputeConflictReward:
    def test_perfect_resolution(self):
        code = "def foo():\n    cost = base * 1.1\n    return cost\n"
        reward = compute_conflict_reward(code, code, "src/calc.py")
        assert reward.total_reward > 0.9
        assert reward.conflict_resolution_score == pytest.approx(0.4, abs=0.01)

    def test_empty_resolution(self):
        reward = compute_conflict_reward("", "def foo(): pass\n", "src/calc.py")
        assert reward.total_reward == 0.0

    def test_resolution_with_markers(self):
        bad_resolution = "<<<<<<< main\ndef foo(): pass\n>>>>>>> feature"
        reward = compute_conflict_reward(
            bad_resolution, "def foo(): pass\n", "src/calc.py"
        )
        assert reward.explanation_bonus == 0.0
        # No-markers component should be 0
        assert reward.total_reward < 0.9

    def test_partial_credit(self):
        gt = "def calculate_cost(price, tax_rate):\n    return price * (1 + tax_rate)\n"
        # Agent uses completely wrong implementation
        agent = "class FooBar:\n    x = 99\n    y = 'hello'\n    z = None\n"
        reward = compute_conflict_reward(agent, gt, "src/calc.py")
        # Very different code should score lower than perfect but above 0
        assert reward.total_reward < 0.9


class TestEpisodeReward:
    def test_all_perfect(self):
        score = compute_episode_reward([1.0, 1.0, 1.0], penalties=0.0)
        assert score == 1.0

    def test_all_zero(self):
        score = compute_episode_reward([0.0, 0.0, 0.0], penalties=0.0)
        assert score == 0.0

    def test_with_penalties(self):
        score = compute_episode_reward([1.0, 1.0], penalties=0.5)
        assert score == pytest.approx(0.5, abs=0.01)

    def test_clamped_to_zero(self):
        score = compute_episode_reward([0.1], penalties=10.0)
        assert score == 0.0

    def test_empty_rewards(self):
        score = compute_episode_reward([], penalties=0.0)
        assert score == 0.0

    def test_average_computation(self):
        score = compute_episode_reward([0.8, 0.6, 1.0], penalties=0.0)
        assert score == pytest.approx(0.8, abs=0.01)
