"""
Shared FastAPI dependencies.
"""
from __future__ import annotations

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError

import config as app_config

_PLACEHOLDER_MARKERS = ("<", "xxxxx", "YOUR_")


def _client() -> MongoClient:
    """Create a MongoClient. Raises ConfigurationError for placeholder/missing URIs."""
    if not app_config.MONGO_URI or any(m in app_config.MONGO_URI for m in _PLACEHOLDER_MARKERS):
        raise ConfigurationError("MONGO_URI is not configured.")
    return MongoClient(app_config.MONGO_URI, serverSelectionTimeoutMS=10_000)


def get_listings_col() -> Collection:
    db = _client()[app_config.MONGO_DB_NAME]
    col = db[app_config.MONGO_COLLECTION]
    col.create_index("property_id", unique=True)
    return col


def get_scraper_config_col() -> Collection:
    db = _client()[app_config.MONGO_DB_NAME]
    return db["scraper_config"]
