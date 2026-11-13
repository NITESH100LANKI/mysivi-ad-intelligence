"""Unit tests for the 100-point rubric scoring engine."""
import pytest
from backend.scoring.scoring_engine import calculate_rubric_score, RUBRIC_WEIGHTS


def test_rubric_weights_sum_to_100():
    total_weight = sum(RUBRIC_WEIGHTS.values())
    assert total_weight == 100, f"Rubric weights must sum to 100, got {total_weight}"


def test_scoring_mathematical_precision():
    # Test all 10s -> must equal 100.0
    perfect_scores = {k: 10.0 for k in RUBRIC_WEIGHTS}
    result_perfect = calculate_rubric_score(perfect_scores, {})
    assert result_perfect.total_score == 100.0

    # Test all 0s -> must equal 0.0
    zero_scores = {k: 0.0 for k in RUBRIC_WEIGHTS}
    result_zero = calculate_rubric_score(zero_scores, {})
    assert result_zero.total_score == 0.0

    # Specific mixed test:
    # hook: 8 (weight 20) -> 160
    # clarity: 9 (weight 15) -> 135
    # value_prop_usp: 8 (weight 15) -> 120
    # target_audience: 7 (weight 10) -> 70
    # trust: 5 (weight 10) -> 50
    # cta: 8 (weight 10) -> 80
    # execution: 8 (weight 10) -> 80
    # differentiation: 9 (weight 10) -> 90
    # Sum: 785 / 10 = 78.5
    mixed_scores = {
        "hook_effectiveness": 8.0,
        "message_clarity": 9.0,
        "value_prop_usp": 8.0,
        "target_audience_relevance": 7.0,
        "trust_social_proof": 5.0,
        "cta_effectiveness": 8.0,
        "creative_execution": 8.0,
        "differentiation": 9.0
    }
    result_mixed = calculate_rubric_score(mixed_scores, {"hook_effectiveness": "Strong hook"})
    assert result_mixed.total_score == 78.5
    assert result_mixed.hook_effectiveness == 8.0
    assert result_mixed.scoring_explanations["hook_effectiveness"] == "Strong hook"


def test_scoring_boundary_clamping():
    # Extreme input values should be clamped to 0.0 - 10.0
    extreme_scores = {
        "hook_effectiveness": 15.0,  # Should clamp to 10.0
        "message_clarity": -5.0,     # Should clamp to 0.0
    }
    result = calculate_rubric_score(extreme_scores, {})
    assert result.hook_effectiveness == 10.0
    assert result.message_clarity == 0.0

