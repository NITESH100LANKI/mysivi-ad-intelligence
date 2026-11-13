"""Unit tests for PDF generation service."""
import os
from pathlib import Path
import pytest
from backend.report.pdf_generator import generate_ad_intelligence_pdf
from backend.utils.config import get_settings


def test_pdf_generation_creates_valid_file(tmp_path):
    output_pdf = tmp_path / "test_report.pdf"

    mock_report_data = {
        "execution_mode": "MOCK",
        "collection_summary": {
            "source": "Mock Test Fixture",
            "items_collected": 5,
            "status": "COMPLETED",
            "search_url": "https://facebook.com/ads/library"
        },
        "advertisements": [
            {
                "rank": 1,
                "ad": {
                    "internal_id": "MYSIVI-AD-001",
                    "headline": "Instant AI Graphic Designer",
                    "hook": "Turn any text into stunning banners in 2 minutes flat!",
                    "primary_text": "Full copy message here.",
                    "cta": "Try For Free",
                    "media_type": "image",
                    "landing_page_url": "https://sivi.ai"
                },
                "score": {"total_score": 88.5},
                "analysis": {
                    "target_audience": "Inference: Marketers",
                    "marketing_angle": "Speed & Automation",
                    "persuasion_techniques": "Metric framing",
                    "strengths": ["Clear 2 minute metric"],
                    "weaknesses": ["Needs social proof"],
                    "improvement_suggestions": ["Add user count"]
                }
            }
        ],
        "top_ad": {
            "ad": {
                "internal_id": "MYSIVI-AD-001",
                "headline": "Instant AI Graphic Designer",
                "hook": "Turn any text into stunning banners in 2 minutes flat!",
                "primary_text": "Full copy message here.",
                "cta": "Try For Free",
                "landing_page_url": "https://sivi.ai"
            },
            "score": {"total_score": 88.5},
            "analysis": {
                "target_audience": "Inference: Marketers",
                "marketing_angle": "Speed & Automation",
                "persuasion_techniques": "Metric framing",
                "strengths": ["Clear 2 minute metric"],
                "weaknesses": ["Needs social proof"],
                "improvement_suggestions": ["Add user count"]
            }
        },
        "comparison": {
            "top_3_summary": [],
            "winner_justification": ["Stronger hook stopping power"]
        },
        "marketing_insights": ["Turnaround speed is the primary focus"],
        "recommendations": [
            {
                "concept_name": "Concept 1: Split Screen Video",
                "format": "Video Ad",
                "hook": "3 Days vs 2 Mins",
                "visual_storyboard": "Frustrated designer vs Sivi prompt",
                "strategic_rationale": "High contrast"
            }
        ],
        "limitations": ["Commercial conversion metrics are not provided by Meta Ad Library"]
    }

    result_path = generate_ad_intelligence_pdf(mock_report_data, output_pdf)

    assert result_path.exists()
    assert os.path.getsize(result_path) > 5000  # Multi-page PDF should be at least several KB
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

