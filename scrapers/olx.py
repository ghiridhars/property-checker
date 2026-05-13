"""
OLX scraper (Thiruvananthapuram real estate).
OLX loads listings via a JSON API endpoint.
"""
from __future__ import annotations

import logging
from typing import Any

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# OLX India exposes a public API used by its own SPA.
# category=1500 = Real Estate; sub_category=1501 = For Sale: Houses & Apartments
_API_URL = "https://www.olx.in/api/relevance/v4/search"


class OLXScraper(BaseScraper):
    source = "olx"

    def fetch_listings(self) -> list[dict[str, Any]]:
        # NOTE: OLX's location_id param is unreliable — it does not actually filter
        # results to that city. We include the city name in the query to bias results
        # toward Thiruvananthapuram, and rely on location post-filtering in passes_filters.
        params = {
            "category_id": "1501",
            "query": "2 bhk apartment thiruvananthapuram",
            "page": "1",
            "rows": "40",
        }

        import requests as _requests
        from config import DEFAULT_HEADERS, REQUEST_TIMEOUT

        # OLX API expects these extra headers in addition to the defaults
        merged = {
            **DEFAULT_HEADERS,
            "accept": "application/json",
            "x-panamera-client-id": "olxin-web",
        }
        resp = _requests.get(_API_URL, headers=merged, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            logger.warning("[olx] Response was not JSON — API may have changed.")
            return []

        items = data.get("data", [])
        listings = []
        for item in items:
            prop_id = str(item.get("id", ""))
            title = item.get("title", "")
            price_raw = str(item.get("price", {}).get("value", {}).get("raw", ""))
            url = item.get("url", "")

            # Extract city and sublocality from locations_resolved
            loc_resolved = item.get("locations_resolved") or {}
            city = loc_resolved.get("ADMIN_LEVEL_3_name", "")
            sublocality = loc_resolved.get("SUBLOCALITY_LEVEL_1_name", "")
            location = ", ".join(filter(None, [sublocality, city]))

            description_parts = [item.get("category", {}).get("name", ""), title, location]
            for param in item.get("parameters", []):
                description_parts.append(param.get("value", ""))

            listings.append({
                "property_id": f"olx-{prop_id}",
                "title": title,
                "description": " ".join(filter(None, description_parts)),
                "price_raw": price_raw,
                "url": url,
                "source": self.source,
                "location": location,
            })

        return listings
