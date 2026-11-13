"""Data cleaning, deduplication, and normalization layer for Facebook Ad Library."""
import hashlib
import re
from typing import List, Dict, Any, Tuple, Optional
from .validator import NormalizedAd
from .logger import setup_logger

logger = setup_logger("AdNormalizer")


def clean_text(text: Optional[str]) -> str:
    """Normalize text whitespace, strip HTML tags, and clean up formatting."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", " ", str(text))
    # Replace weird unicode spaces and characters
    clean = clean.replace("\u200b", "").replace("\xa0", " ")
    # Collapse multiple whitespaces
    clean = re.sub(r"[ \t]+", " ", clean)
    clean = re.sub(r"\n\s*\n+", "\n\n", clean)
    return clean.strip()


def extract_marketing_elements(primary_text: str, title: str, cta_text: str) -> Tuple[str, str, str]:
    """Extract hook, headline, and CTA from cleaned text fields."""
    cleaned_primary = clean_text(primary_text)
    cleaned_title = clean_text(title)
    cleaned_cta = clean_text(cta_text)

    # Hook extraction: Grab the first punchy sentence or line
    hook = ""
    if cleaned_primary:
        # Split on newlines or sentence endings
        lines = [line.strip() for line in cleaned_primary.split("\n") if line.strip()]
        if lines:
            first_line = lines[0]
            # If the first line is reasonably short, use it as hook; otherwise split sentence
            sentence_match = re.split(r"(?<=[.!?])\s+", first_line)
            hook = sentence_match[0] if sentence_match else first_line
    if not hook:
        hook = cleaned_title if cleaned_title else "No explicit hook detected in creative copy"

    # Headline: Use title or fallback to first 8 words of primary text
    headline = cleaned_title if cleaned_title else (hook[:60] + "..." if len(hook) > 60 else hook)
    
    # CTA: Use cta_text or identify "Unavailable"
    cta = cleaned_cta if cleaned_cta else "Unavailable"

    return hook, headline, cta


def generate_content_hash(primary_text: str, headline: str, page_name: str) -> str:
    """Compute a deterministic hash for deduplication when ad ID is missing or identical."""
    payload = f"{clean_text(page_name).lower()}|{clean_text(headline).lower()}|{clean_text(primary_text)[:200].lower()}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def normalize_advertisements(raw_items: List[Dict[str, Any]]) -> Tuple[List[NormalizedAd], List[Dict[str, Any]]]:
    """
    Deduplicate and normalize raw ads scraped from Apify Facebook Ad Library actor.
    Returns:
        (normalized_ads, skipped_records_log)
    """
    seen_ids = set()
    seen_hashes = set()
    normalized_ads: List[NormalizedAd] = []
    skipped_records: List[Dict[str, Any]] = []

    for index, raw in enumerate(raw_items):
        try:
            # 1. Extract identification
            ad_id = str(
                raw.get("ad_archive_id")
                or raw.get("adArchiveID")
                or raw.get("ad_id")
                or raw.get("id")
                or f"UNKNOWN_{index}"
            )
            page_name = str(raw.get("page_name") or raw.get("pageName") or "MySivi / Sivi.ai").strip()
            page_id = str(raw.get("page_id") or raw.get("pageId") or "Unavailable")

            # 2. Extract snapshot data (Apify structure: nested in snapshot or flat)
            snapshot = raw.get("snapshot") or {}
            cards = snapshot.get("cards") or []
            first_card = cards[0] if (isinstance(cards, list) and len(cards) > 0 and isinstance(cards[0], dict)) else {}
            
            # Primary text extraction
            raw_body = (
                snapshot.get("body")
                or first_card.get("body")
                or raw.get("body")
                or raw.get("ad_creative_body")
                or ""
            )
            if isinstance(raw_body, dict):
                primary_text = raw_body.get("text") or raw_body.get("markup", {}).get("__html") or ""
            else:
                primary_text = str(raw_body)
            primary_text = clean_text(primary_text)

            # Title / Headline extraction
            raw_title = (
                snapshot.get("title")
                or first_card.get("title")
                or raw.get("title")
                or raw.get("headline")
                or ""
            )
            headline_raw = clean_text(raw_title)

            # Caption / Description
            raw_caption = (
                snapshot.get("caption")
                or snapshot.get("link_description")
                or snapshot.get("linkDescription")
                or first_card.get("caption")
                or first_card.get("linkDescription")
                or raw.get("caption")
                or raw.get("description")
                or ""
            )
            description = clean_text(raw_caption)

            # CTA text (handles snake_case and camelCase)
            cta_raw = (
                snapshot.get("cta_text")
                or snapshot.get("ctaText")
                or snapshot.get("cta_type")
                or snapshot.get("ctaType")
                or first_card.get("ctaText")
                or first_card.get("ctaType")
                or raw.get("cta_text")
                or raw.get("call_to_action")
                or ""
            )
            
            # Validate non-empty copy content
            if not primary_text and not headline_raw:
                skipped_records.append({
                    "raw_index": index,
                    "ad_id": ad_id,
                    "reason": "Skipped: Both primary text and headline are completely empty."
                })
                logger.warning(f"Skipping record {index} (ID: {ad_id}): missing copy text.")
                continue

            # Extract Hook, Headline, and CTA
            hook, headline, cta = extract_marketing_elements(primary_text, headline_raw, cta_raw)

            # Deduplication checks
            content_hash = generate_content_hash(primary_text, headline, page_name)
            if ad_id != f"UNKNOWN_{index}" and ad_id in seen_ids:
                skipped_records.append({
                    "raw_index": index,
                    "ad_id": ad_id,
                    "reason": f"Skipped duplicate ad ID: {ad_id}"
                })
                logger.info(f"Deduplicated ad with duplicate ad ID: {ad_id}")
                continue

            if content_hash in seen_hashes:
                skipped_records.append({
                    "raw_index": index,
                    "ad_id": ad_id,
                    "reason": f"Skipped duplicate content hash: {content_hash}"
                })
                logger.info(f"Deduplicated ad with identical copy/headline: {ad_id}")
                continue

            seen_ids.add(ad_id)
            seen_hashes.add(content_hash)

            # 3. Media URLs extraction
            image_urls: List[str] = []
            video_urls: List[str] = []
            media_type = "image"

            # Check snapshot images
            for img in snapshot.get("images", []) or raw.get("images", []):
                if isinstance(img, dict):
                    url = (
                        img.get("original_image_url")
                        or img.get("resized_image_url")
                        or img.get("url")
                    )
                    if url:
                        image_urls.append(url)
                elif isinstance(img, str):
                    image_urls.append(img)

            # Check snapshot videos
            for vid in snapshot.get("videos", []) or raw.get("videos", []):
                if isinstance(vid, dict):
                    url = (
                        vid.get("video_hd_url")
                        or vid.get("video_sd_url")
                        or vid.get("video_preview_image_url")
                        or vid.get("url")
                    )
                    if url:
                        video_urls.append(url)
                elif isinstance(vid, str):
                    video_urls.append(vid)

            # Check cards (carousel / video cards)
            for card in snapshot.get("cards", []) or raw.get("cards", []):
                if isinstance(card, dict):
                    c_img = (
                        card.get("image_url")
                        or card.get("originalImageUrl")
                        or card.get("resizedImageUrl")
                        or card.get("videoPreviewImageUrl")
                    )
                    if c_img and c_img not in image_urls:
                        image_urls.append(c_img)
                    c_vid = (
                        card.get("video_url")
                        or card.get("videoHdUrl")
                        or card.get("videoSdUrl")
                    )
                    if c_vid and c_vid not in video_urls:
                        video_urls.append(c_vid)

            if video_urls:
                media_type = "video"
            elif len(image_urls) > 1:
                media_type = "carousel"
            elif image_urls:
                media_type = "image"
            else:
                media_type = "text_only"

            # 4. Links and dates
            landing_page = (
                snapshot.get("link_url")
                or raw.get("link_url")
                or raw.get("destination_url")
                or "https://sivi.ai"
            )
            ad_library_url = (
                raw.get("ad_library_url")
                or f"https://www.facebook.com/ads/library/?id={ad_id}"
            )
            start_date = str(raw.get("start_date") or snapshot.get("creation_time") or "Unavailable")
            end_date = str(raw.get("end_date") or "Active (No end date specified)")
            is_active = bool(raw.get("is_active", True))

            platforms = raw.get("publisher_platforms") or raw.get("platforms") or ["facebook", "instagram"]
            if isinstance(platforms, str):
                platforms = [p.strip() for p in platforms.split(",")]

            internal_id = f"MYSIVI-AD-{len(normalized_ads) + 1:03d}"

            normalized = NormalizedAd(
                internal_id=internal_id,
                ad_id=ad_id,
                page_name=page_name,
                page_id=page_id,
                ad_library_url=ad_library_url,
                primary_text=primary_text,
                hook=hook,
                headline=headline,
                description=description,
                cta=cta,
                landing_page_url=landing_page,
                image_urls=image_urls,
                video_urls=video_urls,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                publisher_platforms=platforms,
                impression_info="Unavailable in standard commercial ad library view",
                media_type=media_type,
                raw_snapshot=snapshot if snapshot else raw
            )
            normalized_ads.append(normalized)

        except Exception as e:
            skipped_records.append({
                "raw_index": index,
                "error": str(e),
                "reason": f"Normalization exception: {str(e)}"
            })
            logger.error(f"Error normalizing record {index}: {e}")

    logger.info(f"Normalization complete: {len(normalized_ads)} valid ads processed, {len(skipped_records)} skipped/deduplicated.")
    return normalized_ads, skipped_records
