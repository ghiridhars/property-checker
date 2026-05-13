"""
Centralised configuration.
All search preferences and filter rules live here.
Runtime secrets are read from environment variables (set via .env locally
or GitHub repository secrets in CI).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Secrets (injected via env / GitHub Actions secrets)
# Validation is deferred to runtime so modules can be safely imported without
# secrets present (e.g. during testing or smoke-checks).
# ---------------------------------------------------------------------------
MONGO_URI: str = os.environ.get("MONGO_URI", "")
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")


def validate_secrets() -> None:
    """Call this once at startup (in scraper.py) to fail fast if secrets are missing or still set to placeholder values."""
    secrets = {
        "MONGO_URI": MONGO_URI,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    # Detect empty strings or obvious .env.example placeholders
    _placeholder_markers = ("<", "xxxxx", "YOUR_", "123456789:")
    bad = [
        k for k, v in secrets.items()
        if not v or any(marker in v for marker in _placeholder_markers)
    ]
    if bad:
        raise EnvironmentError(
            f"The following secrets are missing or still set to placeholder values: "
            f"{', '.join(bad)}\n"
            f"Copy .env.example → .env and fill in real credentials."
        )

# ---------------------------------------------------------------------------
# Search configuration
# ---------------------------------------------------------------------------
SEARCH_CONFIG = {
    "locations": [
        "Trivandrum",
        "Thiruvananthapuram",
        "Manacaud",
        "Attukal",
        "Pettah",
        "Vanchiyoor",
        "Thampanoor",
    ],
    # Property types to accept  (case-insensitive substring match in title/desc)
    "property_types": [
        "2 bhk",
        "2bhk",
    ],
    # Positive keywords — at least ONE must appear to pass the filter
    "must_keywords": [
        "vastu",
        "east facing",
        "east-facing",
        "puja room",
        "pooja room",
        "unfurnished",
    ],
    # Negative keywords — listing is rejected if ANY of these appear
    "reject_keywords": [
        "pg",
        "hostel",
        "commercial",
        "office",
        "shop",
    ],
    # Price ceiling in INR (0 = no limit)
    "max_price_inr": 6_000_000,  # ₹60 lakh
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
MONGO_DB_NAME = "property_watcher"
MONGO_COLLECTION = "listings"


def load_search_config() -> dict:
    """
    Return the active search config.
    Reads from MongoDB `scraper_config` collection when a real MONGO_URI is
    available; falls back to the hardcoded SEARCH_CONFIG defaults otherwise.
    This is called at the start of each scraper run so UI changes are picked
    up without any code deployment.
    """
    if not MONGO_URI or any(m in MONGO_URI for m in ("<", "xxxxx")):
        return SEARCH_CONFIG

    try:
        from pymongo import MongoClient  # local import to keep startup fast
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5_000)
        doc = client[MONGO_DB_NAME]["scraper_config"].find_one({"_id": "active"})
        if doc:
            doc.pop("_id", None)
            doc.pop("updated_at", None)
            return {**SEARCH_CONFIG, **doc}
    except Exception:  # noqa: BLE001
        pass  # fall back to defaults silently

    return SEARCH_CONFIG

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 30  # seconds
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}
