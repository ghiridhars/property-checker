"""
MagicBricks scraper.
Uses the internal JSON search API that the website itself calls.
"""
from __future__ import annotations

import logging
from typing import Any

from config import SEARCH_CONFIG
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# MagicBricks uses a REST-style JSON endpoint for search results.
# city=51 is Thiruvananthapuram in their city code system.
_SEARCH_URL = "https://www.magicbricks.com/mbsrp/propertySearch.html"

_CITY_CODES = {
    "Thiruvananthapuram": "51",
    "Trivandrum": "51",
}


class MagicBricksScraper(BaseScraper):
    source = "magicbricks"

    def fetch_listings(self) -> list[dict[str, Any]]:
        params = {
            "editSearch": "Y",
            "category": "S",           # S = Sale
            "propertyType": "10002",   # 10002 = Apartment/Flat
            "cityId": "51",            # Thiruvananthapuram
            "bedrooms": "2",
            "offset": "0",
            "max": "50",
            "sortBy": "dateposted",
        }

        resp = self.get(_SEARCH_URL, params=params)

        try:
            data = resp.json()
        except ValueError:
            logger.warning("[magicbricks] Response was not JSON — site may have changed.")
            return []

        results = data.get("resultList", [])
        listings = []
        for item in results:
            locality = item.get("localityName", "")
            listing = {
                "property_id": f"mb-{item.get('propId', item.get('id', ''))}",
                "title": item.get("propHeading", ""),
                "description": (
                    f"{item.get('propHeading', '')} "
                    f"{locality} "
                    f"{item.get('features', '')} "
                    f"{item.get('description', '')}"
                ),
                "price_raw": str(item.get("priceDisplay", item.get("price", ""))),
                "url": "https://www.magicbricks.com" + item.get("propUrl", ""),
                "source": self.source,
                "location": locality,
            }
            listings.append(listing)

        return listings
