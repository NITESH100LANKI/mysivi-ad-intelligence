"""Apify Facebook Ad Library Scraper integration client."""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from ..utils.config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger("ApifyScraper")


class ApifyScraperClient:
    """Client for triggering Apify Actor and fetching Facebook Ad Library results."""

    def __init__(self, token: Optional[str] = None, actor_id: Optional[str] = None):
        self.settings = get_settings()
        self.token = token or self.settings.APIFY_API_TOKEN
        self.actor_id = actor_id or self.settings.APIFY_ACTOR_ID
        self.base_url = "https://api.apify.com/v2"

    def run_actor_and_fetch_ads(
        self,
        search_url: Optional[str] = None,
        max_items: Optional[int] = None,
        force_mock: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute the Apify Facebook Ads Scraper actor and return collected items.
        Falls back to local mock fixtures if token is absent or force_mock=True.
        """
        # 1. Check if mock mode is requested or credentials are not configured
        if force_mock or not self.token or self.token == "your_apify_api_token_here":
            logger.info("Executing in MOCK / FIXTURE MODE (No Apify credentials provided).")
            return self._load_fixture_data()

        target_url = search_url or self.settings.FB_SEARCH_URL
        items_limit = max_items or self.settings.FB_MAX_ITEMS

        # 2. Build Apify Actor input strictly matching latest schema
        actor_input = {
            "startUrls": [{"url": target_url}],
            "resultsLimit": items_limit,
            "maxItems": items_limit,
            "isDetailsPerAd": False,
            "enrichWithEcommerceData": False
        }

        logger.info(f"Triggering Apify Actor '{self.actor_id}' with resultsLimit={items_limit} (Cost capped to $0.10 max)...")
        
        try:
            # POST /acts/{actorId}/runs?maxTotalChargeUsd=0.10
            run_url = f"{self.base_url}/acts/{self.actor_id.replace('/', '~')}/runs?token={self.token}&maxTotalChargeUsd=0.10"
            start_response = requests.post(
                run_url,
                json=actor_input,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if start_response.status_code not in (200, 201):
                logger.error(f"Apify API run start failed ({start_response.status_code}): {start_response.text}")
                logger.warning("Falling back to local validated mock fixture to preserve pipeline continuity.")
                return self._load_fixture_data(error_note=f"Apify API returned HTTP {start_response.status_code}")

            run_data = start_response.json().get("data", {})
            run_id = run_data.get("id")
            dataset_id = run_data.get("defaultDatasetId")
            logger.info(f"Actor run initiated successfully. Run ID: {run_id}, Dataset ID: {dataset_id}")

            # 3. Poll for completion (with 180s timeout limit)
            max_wait_seconds = 180
            poll_interval = 6
            elapsed = 0
            status = run_data.get("status")

            while status not in ("SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED") and elapsed < max_wait_seconds:
                time.sleep(poll_interval)
                elapsed += poll_interval
                status_res = requests.get(f"{self.base_url}/actor-runs/{run_id}?token={self.token}", timeout=20)
                if status_res.status_code == 200:
                    status = status_res.json().get("data", {}).get("status")
                    logger.info(f"Apify run {run_id} status: {status} (elapsed: {elapsed}s)")
                else:
                    logger.warning(f"Error checking run status: {status_res.status_code}")

            if status != "SUCCEEDED":
                logger.error(f"Apify run finished with non-successful status: {status}")
                return self._load_fixture_data(error_note=f"Apify Actor run status: {status}")

            # 4. Fetch dataset items
            dataset_url = f"{self.base_url}/datasets/{dataset_id}/items?token={self.token}&limit={items_limit}"
            items_res = requests.get(dataset_url, timeout=30)
            if items_res.status_code == 200:
                raw_items = items_res.json()
                logger.info(f"Retrieved {len(raw_items)} raw ad records from Apify dataset.")
                
                # Save raw output
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                raw_file = self.settings.RAW_DATA_DIR / f"raw_ads_live_{timestamp}.json"
                with open(raw_file, "w", encoding="utf-8") as f:
                    json.dump(raw_items, f, indent=2)

                collection_summary = {
                    "source": "Apify Facebook Ad Library Scraper (LIVE)",
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "status": "SUCCEEDED",
                    "items_collected": len(raw_items),
                    "search_url": target_url,
                    "timestamp": datetime.now().isoformat()
                }
                return raw_items, collection_summary
            else:
                logger.error(f"Failed to fetch dataset items: {items_res.status_code}")
                return self._load_fixture_data(error_note=f"Dataset fetch HTTP {items_res.status_code}")

        except Exception as e:
            logger.error(f"Exception during Apify scraping execution: {e}")
            return self._load_fixture_data(error_note=f"Exception: {str(e)}")

    def _load_fixture_data(self, error_note: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Load offline validated mock fixtures."""
        fixture_path = self.settings.FIXTURES_DATA_DIR / "sample_mysivi_raw_ads.json"
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

        with open(fixture_path, "r", encoding="utf-8") as f:
            raw_items = json.load(f)

        logger.info(f"Loaded {len(raw_items)} fixture records for offline mock testing.")
        
        # Save copy to raw_data_dir for traceability
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = self.settings.RAW_DATA_DIR / f"raw_ads_mock_{timestamp}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(raw_items, f, indent=2)

        collection_summary = {
            "source": "Local Validated Test Fixtures (MOCK MODE)",
            "status": "MOCK_SUCCESS",
            "items_collected": len(raw_items),
            "search_url": self.settings.FB_SEARCH_URL,
            "timestamp": datetime.now().isoformat(),
            "note": error_note or "Executed in mock mode. Set APIFY_API_TOKEN in .env for live Meta Ad Library collection."
        }
        return raw_items, collection_summary
