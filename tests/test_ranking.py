"""Unit tests for ranking, top 3 comparison, and recommendation generation."""
import pytest
from backend.utils.validator import NormalizedAd, GeminiAnalysisResult, CreativeScore, AnalyzedAd
from backend.scoring.ranker import rank_advertisements, compare_top_ads, generate_strategic_recommendations


def create_dummy_analyzed_ad(internal_id: str, headline: str, total_score: float, hook_score: float) -> AnalyzedAd:
    ad = NormalizedAd(
        internal_id=internal_id,
        ad_id=f"FB_{internal_id}",
        page_name="MySivi",
        ad_library_url="https://facebook.com/ads/library/?id=123",
        primary_text="Primary text content",
        hook="Hook opening",
        headline=headline,
        description="Desc",
        cta="Try For Free",
        landing_page_url="https://sivi.ai"
    )
    analysis = GeminiAnalysisResult(
        hook="Hook opening",
        body="Primary text content",
        headline=headline,
        cta="Try For Free",
        target_audience="Marketers",
        customer_pain_point="Speed",
        value_proposition="2 minute creatives",
        usp="Generative AI",
        marketing_angle="Speed",
        persuasion_techniques="Contrast",
        strengths=["Strong hook"],
        weaknesses=["No testimonials"],
        improvement_suggestions=["Add testimonials"],
        creative_summary="Summary"
    )
    score = CreativeScore(
        hook_effectiveness=hook_score,
        message_clarity=8.0,
        value_prop_usp=8.0,
        target_audience_relevance=8.0,
        trust_social_proof=5.0,
        cta_effectiveness=8.0,
        creative_execution=8.0,
        differentiation=8.0,
        total_score=total_score
    )
    return AnalyzedAd(ad=ad, analysis=analysis, score=score)


def test_ranking_descending_order():
    ad1 = create_dummy_analyzed_ad("AD-1", "Headline Low", 65.0, 6.0)
    ad2 = create_dummy_analyzed_ad("AD-2", "Headline High", 88.5, 9.0)
    ad3 = create_dummy_analyzed_ad("AD-3", "Headline Mid", 75.0, 7.5)

    ranked, top_ad = rank_advertisements([ad1, ad2, ad3])

    assert ranked[0].ad.internal_id == "AD-2"
    assert ranked[0].rank == 1
    assert ranked[0].is_best_creative is True
    assert top_ad.ad.internal_id == "AD-2"

    assert ranked[1].ad.internal_id == "AD-3"
    assert ranked[1].rank == 2
    assert ranked[1].is_best_creative is False

    assert ranked[2].ad.internal_id == "AD-1"
    assert ranked[2].rank == 3


def test_compare_top_ads():
    ad1 = create_dummy_analyzed_ad("AD-1", "Headline 1", 90.0, 9.5)
    ad2 = create_dummy_analyzed_ad("AD-2", "Headline 2", 85.0, 8.5)
    ad3 = create_dummy_analyzed_ad("AD-3", "Headline 3", 80.0, 8.0)

    ranked, _ = rank_advertisements([ad1, ad2, ad3])
    comp = compare_top_ads(ranked)

    assert comp["winner_internal_id"] == "AD-1"
    assert len(comp["top_3_summary"]) == 3
    assert len(comp["winner_justification"]) > 0


def test_generate_strategic_recommendations():
    ad1 = create_dummy_analyzed_ad("AD-1", "Headline 1", 90.0, 9.5)
    common_strats, new_concepts, gaps = generate_strategic_recommendations([ad1])

    assert len(common_strats) >= 3
    assert len(new_concepts) == 3
    assert len(gaps) >= 2
    assert "concept_name" in new_concepts[0]


def test_ranking_tie_breaker_hook_effectiveness():
    # Both have 81.0 total score, but AD-A has higher hook score (9.0 vs 8.0)
    ad_a = create_dummy_analyzed_ad("AD-A", "Marathi Ad", 81.0, 9.0)
    ad_b = create_dummy_analyzed_ad("AD-B", "Bengali Ad", 81.0, 8.0)

    ranked, top_ad = rank_advertisements([ad_b, ad_a])
    assert ranked[0].ad.internal_id == "AD-A"
    assert ranked[0].rank == 1
    assert ranked[1].ad.internal_id == "AD-B"
    assert ranked[1].rank == 2

    comp = compare_top_ads(ranked)
    assert "Secondary Tie-Breaker Resolution" in comp["winner_justification"][0]


def test_ranking_joint_winners_when_all_metrics_equal():
    # Both have 81.0 total score and identical hook score 8.5
    ad_a = create_dummy_analyzed_ad("AD-3", "Marathi Ad", 81.0, 8.5)
    ad_b = create_dummy_analyzed_ad("AD-4", "Bengali Ad", 81.0, 8.5)
    ad_c = create_dummy_analyzed_ad("AD-1", "Hindi Ad", 79.5, 8.0)

    ranked, top_ad = rank_advertisements([ad_a, ad_b, ad_c])
    assert ranked[0].rank == 1
    assert ranked[0].is_best_creative is True
    assert ranked[1].rank == 1
    assert ranked[1].is_best_creative is True
    # Third item gets Rank 3 in standard competition ranking
    assert ranked[2].rank == 3
    assert ranked[2].is_best_creative is False

    comp = compare_top_ads(ranked)
    assert comp["is_joint_winner"] is True
    assert "Joint Rank 1 Co-Winners" in comp["winner_justification"][0]


