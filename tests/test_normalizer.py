"""Unit tests for data normalization and duplicate detection."""
import pytest
from backend.utils.normalizer import (
    clean_text,
    extract_marketing_elements,
    generate_content_hash,
    normalize_advertisements
)


def test_clean_text():
    raw = "<p>Get your <b>AI banners</b> here! &nbsp;\n\n\nFast and easy.   </p>"
    cleaned = clean_text(raw)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "Get your AI banners here!" in cleaned


def test_extract_marketing_elements():
    primary = "Turn any text into stunning banners in 2 minutes flat! Sivi automates graphics."
    title = "Instant AI Designer"
    cta = "Try For Free"

    hook, headline, extracted_cta = extract_marketing_elements(primary, title, cta)
    assert "Turn any text into stunning banners in 2 minutes flat!" in hook
    assert headline == "Instant AI Designer"
    assert extracted_cta == "Try For Free"


def test_normalize_advertisements_deduplication():
    raw_ads = [
        {
            "ad_archive_id": "111",
            "page_name": "MySivi",
            "snapshot": {"body": "Ad text A", "title": "Headline A", "cta_text": "Sign Up"}
        },
        {
            "ad_archive_id": "111",  # Duplicate ad_id
            "page_name": "MySivi",
            "snapshot": {"body": "Ad text A", "title": "Headline A", "cta_text": "Sign Up"}
        },
        {
            "ad_archive_id": "222",
            "page_name": "MySivi",
            "snapshot": {"body": "Ad text A", "title": "Headline A", "cta_text": "Sign Up"}  # Content duplicate
        },
        {
            "ad_archive_id": "333",
            "page_name": "MySivi",
            "snapshot": {"body": "", "title": "", "cta_text": ""}  # Empty ad
        },
        {
            "ad_archive_id": "444",
            "page_name": "MySivi",
            "snapshot": {"body": "Ad text Unique", "title": "Headline Unique", "cta_text": "Learn More"}
        }
    ]

    normalized, skipped = normalize_advertisements(raw_ads)

    # Only 2 unique valid ads should survive (111 and 444)
    assert len(normalized) == 2
    assert normalized[0].ad_id == "111"
    assert normalized[1].ad_id == "444"
    assert len(skipped) == 3

