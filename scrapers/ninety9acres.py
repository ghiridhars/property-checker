"""
99acres scraper.
Parses search results using BeautifulSoup.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.99acres.com"
# Thiruvananthapuram residential apartments for sale, 2 BHK
_SEARCH_URL = (
    "https://www.99acres.com/2-bhk-flat-for-sale-in-thiruvananthapuram-ffid"
    "?city=62&preference=S&area_unit=1&res_com=R&bedrooms=2&property_type=10001"
)


class NinetyNineAcresScraper(BaseScraper):
    source = "99acres"

    def fetch_listings(self) -> list[dict[str, Any]]:
        resp = self.get(_SEARCH_URL)
        soup = BeautifulSoup(resp.text, "lxml")

        listings = []

        # 99acres wraps each listing in a <div> with data-id attribute
        cards = soup.select("div[data-id]")
        if not cards:
            # Fallback selector — site layout can change
            cards = soup.select("div.propertyCard__mainContent, article.srpTuple__propertyDetail")

        for card in cards:
            prop_id = card.get("data-id") or card.get("data-listing-id", "")
            if not prop_id:
                continue

            title_el = card.select_one("a.srpTuple__propType, h2.srpTuple__propHeading, [data-label='PROP_HEADING']")
            price_el = card.select_one("span[data-label='PRICE_OVERALL'], .srpTuple__price")
            desc_el = card.select_one("div.srpTuple__highlights, div[data-label='HIGHLIGHTS']")
            loc_el = card.select_one("[data-label='LOCALITY_TITLE'], span.srpTuple__locationName, .srpTuple__location")
            link_el = card.select_one("a[href*='/property-detail/']")

            title = title_el.get_text(strip=True) if title_el else ""
            price_raw = price_el.get_text(strip=True) if price_el else ""
            description = desc_el.get_text(" ", strip=True) if desc_el else ""
            location = loc_el.get_text(strip=True) if loc_el else ""
            href = link_el["href"] if link_el and link_el.get("href") else ""
            url = urljoin(_BASE_URL, href) if href else ""

            if not title:
                continue

            listings.append({
                "property_id": f"99a-{prop_id}",
                "title": title,
                "description": " ".join(filter(None, [title, location, description])),
                "price_raw": price_raw,
                "url": url,
                "source": self.source,
                "location": location,
            })

        return listings
