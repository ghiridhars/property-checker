"""
Abstract base class for all property scrapers.
Each portal subclass only needs to implement `fetch_listings()`.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import requests

import config as app_config
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT
from scrapers.filters import parse_price_inr, passes_filters

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Contract for a property portal scraper.

    Subclasses must implement `fetch_listings()` which yields raw dicts with
    at minimum these keys:
        property_id : str   – unique identifier from the portal
        title       : str
        description : str   – combined text used for keyword filtering
        price_raw   : str   – raw price string from the portal
        url         : str   – full link to the listing
        source      : str   – portal name (e.g. "magicbricks")
    """

    source: str = "unknown"

    def get(self, url: str, params: dict | None = None) -> requests.Response:
        """Thin HTTP GET with shared headers / timeout."""
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp

    @abstractmethod
    def fetch_listings(self) -> list[dict[str, Any]]:
        """
        Return a list of raw listing dicts from the portal.
        Each dict must include the keys described in the class docstring.
        """

    def run(self) -> list[dict[str, Any]]:
        """
        Fetch, filter, and return only listings that match the configured
        criteria.  Returns a (potentially empty) list of filtered dicts with
        `price_inr` added.
        """
        # Load live config once per run (reads from DB when available)
        live_cfg = app_config.load_search_config()

        try:
            raw = self.fetch_listings()
        except requests.RequestException as exc:
            logger.error("[%s] HTTP error during fetch: %s", self.source, exc)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] Unexpected error: %s", self.source, exc)
            return []

        matched = []
        for listing in raw:
            price_inr = parse_price_inr(listing.get("price_raw", ""))
            listing["price_inr"] = price_inr
            listing["price"] = listing.get("price_raw", "N/A")

            if passes_filters(
                listing.get("title", ""),
                listing.get("description", ""),
                price_inr,
                cfg=live_cfg,
                location=listing.get("location", ""),
            ):
                matched.append(listing)

        logger.info("[%s] %d/%d listings passed filters", self.source, len(matched), len(raw))
        return matched
