"""
MongoDB Atlas wrapper.
Handles connection, duplicate checks, and inserts.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

from config import MONGO_COLLECTION, MONGO_DB_NAME, MONGO_URI

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def _get_collection() -> Collection:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10_000)
        _client[MONGO_DB_NAME][MONGO_COLLECTION].create_index("property_id", unique=True)
    col = _client[MONGO_DB_NAME][MONGO_COLLECTION]
    return col


def is_new_listing(property_id: str) -> bool:
    """Return True if the property_id has not been seen before."""
    col = _get_collection()
    return col.find_one({"property_id": property_id}) is None


def save_listing(listing: dict[str, Any]) -> bool:
    """
    Persist a listing.
    Returns True on success, False if it already exists (race condition guard).
    """
    col = _get_collection()
    listing.setdefault("discovered_at", datetime.now(timezone.utc).isoformat())
    try:
        col.insert_one(listing)
        logger.info("Saved new listing: %s", listing.get("property_id"))
        return True
    except pymongo.errors.DuplicateKeyError:
        logger.debug("Duplicate skipped: %s", listing.get("property_id"))
        return False
