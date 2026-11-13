"""Unit tests for Gemini prompt construction and analysis client."""
import pytest
from backend.utils.validator import NormalizedAd
from backend.analysis.prompt_builder import build_ad_analysis_prompt
from backend.analysis.gemini_client import GeminiAnalysisClient


def test_build_ad_analysis_prompt():
    ad = NormalizedAd(
        internal_id="MYSIVI-AD-001",
        ad_id="12345678",
        page_name="MySivi",
        ad_library_url="https://facebook.com/ads/library/?id=12345678",
        primary_text="Stop paying $500 on freelance designers.",
        hook="Stop paying $500 on freelance designers.",
        headline="AI Banner Generator",
        description="sivi.ai",
        cta="Try For Free",
        landing_page_url="https://sivi.ai"
    )
    prompt = build_ad_analysis_prompt(ad)

    assert "MYSIVI-AD-001" in prompt
    assert "Stop paying $500 on freelance designers." in prompt
    assert "rubric_scores" in prompt
    assert "target_audience" in prompt


def test_gemini_client_mock_heuristic():
    client = GeminiAnalysisClient(api_key="mock_key")
    ad = NormalizedAd(
        internal_id="MYSIVI-AD-001",
        ad_id="12345678",
        page_name="MySivi",
        ad_library_url="https://facebook.com/ads/library/?id=12345678",
        primary_text="Stop spending $500 every month on freelance banner designers. Sivi generates banners in 2 minutes flat.",
        hook="Stop spending $500 every month on freelance banner designers.",
        headline="Instant AI Graphic Designer",
        description="sivi.ai",
        cta="Try For Free",
        landing_page_url="https://sivi.ai"
    )

    analysis, score = client.analyze_ad(ad, force_mock=True)

    assert analysis is not None
    assert score is not None
    assert score.total_score > 60.0
    assert "Stop spending $500" in analysis.hook
    assert len(analysis.strengths) >= 2
    assert len(analysis.weaknesses) >= 1

