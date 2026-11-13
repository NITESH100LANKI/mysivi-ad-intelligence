"""Transparent, mathematically validated scoring engine based on the 100-point rubric."""
from typing import Dict, Any, Tuple
from ..utils.validator import CreativeScore
from ..utils.logger import setup_logger

logger = setup_logger("ScoringEngine")

# Section 7 Rubric Weights
RUBRIC_WEIGHTS = {
    "hook_effectiveness": 20,
    "message_clarity": 15,
    "value_prop_usp": 15,
    "target_audience_relevance": 10,
    "trust_social_proof": 10,
    "cta_effectiveness": 10,
    "creative_execution": 10,
    "differentiation": 10,
}


def calculate_rubric_score(
    raw_scores: Dict[str, float],
    explanations: Dict[str, str]
) -> CreativeScore:
    """
    Calculate the mathematical weighted score for an ad using the exact weights.
    Each criterion is evaluated on a 0-10 scale.
    Formula: Total = sum(criterion_score * weight) / 10
    """
    def sanitize(val: Any) -> float:
        try:
            return max(0.0, min(10.0, round(float(val), 1)))
        except (ValueError, TypeError):
            return 5.0

    hook = sanitize(raw_scores.get("hook_effectiveness", 7.0))
    clarity = sanitize(raw_scores.get("message_clarity", 7.0))
    value_usp = sanitize(raw_scores.get("value_prop_usp", 7.0))
    audience = sanitize(raw_scores.get("target_audience_relevance", 7.0))
    trust = sanitize(raw_scores.get("trust_social_proof", 5.0))
    cta = sanitize(raw_scores.get("cta_effectiveness", 7.0))
    execution = sanitize(raw_scores.get("creative_execution", 7.0))
    diff = sanitize(raw_scores.get("differentiation", 7.0))

    weighted_total = (
        (hook * RUBRIC_WEIGHTS["hook_effectiveness"]) +
        (clarity * RUBRIC_WEIGHTS["message_clarity"]) +
        (value_usp * RUBRIC_WEIGHTS["value_prop_usp"]) +
        (audience * RUBRIC_WEIGHTS["target_audience_relevance"]) +
        (trust * RUBRIC_WEIGHTS["trust_social_proof"]) +
        (cta * RUBRIC_WEIGHTS["cta_effectiveness"]) +
        (execution * RUBRIC_WEIGHTS["creative_execution"]) +
        (diff * RUBRIC_WEIGHTS["differentiation"])
    ) / 10.0

    final_total = round(weighted_total, 2)

    return CreativeScore(
        hook_effectiveness=hook,
        message_clarity=clarity,
        value_prop_usp=value_usp,
        target_audience_relevance=audience,
        trust_social_proof=trust,
        cta_effectiveness=cta,
        creative_execution=execution,
        differentiation=diff,
        total_score=final_total,
        scoring_explanations=explanations
    )

