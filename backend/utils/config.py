"""Configuration management for MySivi Ad Intelligence System."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Base Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    RESULTS_DATA_DIR: Path = BASE_DIR / "data" / "results"
    FIXTURES_DATA_DIR: Path = BASE_DIR / "data" / "fixtures"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    N8N_DIR: Path = BASE_DIR / "n8n"

    # API Credentials
    GOOGLE_GEMINI_API_KEY: Optional[str] = os.getenv("GOOGLE_GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    APIFY_API_TOKEN: Optional[str] = os.getenv("APIFY_API_TOKEN")
    APIFY_ACTOR_ID: str = os.getenv("APIFY_ACTOR_ID", "apify/facebook-ads-scraper")

    # Facebook Scraping Query Config
    FB_SEARCH_KEYWORD: str = os.getenv("FB_SEARCH_KEYWORD", "MySivi")
    FB_COUNTRY: str = os.getenv("FB_COUNTRY", "IN")
    FB_MAX_ITEMS: int = int(os.getenv("FB_MAX_ITEMS", "10"))
    FB_SEARCH_URL: str = os.getenv(
        "FB_SEARCH_URL",
        "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&q=%22MySivi%22&search_type=keyword_exact_phrase&sort_data[mode]=total_impressions&sort_data[direction]=desc"
    )

    # Runtime Execution Mode: "live" or "mock"
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "mock").lower()

    # Network / Service Ports
    PORT_REPORT_SERVICE: int = int(os.getenv("PORT_REPORT_SERVICE", "5000"))
    PORT_N8N: int = int(os.getenv("PORT_N8N", "5678"))

    def ensure_directories(self):
        """Ensure all required workspace directories exist."""
        for directory in [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.RESULTS_DATA_DIR,
            self.FIXTURES_DATA_DIR,
            self.REPORTS_DIR,
            self.N8N_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def has_gemini_credentials(self) -> bool:
        return bool(self.GOOGLE_GEMINI_API_KEY and self.GOOGLE_GEMINI_API_KEY != "your_gemini_api_key_here")

    @property
    def has_apify_credentials(self) -> bool:
        return bool(self.APIFY_API_TOKEN and self.APIFY_API_TOKEN != "your_apify_api_token_here")


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Return singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        _settings_instance.ensure_directories()
    return _settings_instance

