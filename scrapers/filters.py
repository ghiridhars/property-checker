"""
Shared filtering logic for all scrapers.
"""
from __future__ import annotations

import re
from typing import Any

import config as app_config


def _normalise(text: str) -> str:
    return text.lower()


def passes_filters(
    title: str,
    description: str,
    price_inr: int | None,
    cfg: dict | None = None,
    location: str = "",
) -> bool:
    """
    Return True if the listing matches ALL of the following:
    - At least one configured location appears in title/description/location
      (scrapers search at city level; this enforces neighbourhood filtering).
    - At least one property type keyword is present.
    - At least one must_keyword is present.
    - No reject_keywords are present.
    - Price is within the configured ceiling (if provided).

    `cfg` is the live search config dict.  If omitted, the module-level
    SEARCH_CONFIG default is used (for backward-compat and unit tests).
    """
    if cfg is None:
        cfg = app_config.SEARCH_CONFIG

    combined = _normalise(f"{title} {description} {location}")

    locations = cfg.get("locations", [])
    if locations and not any(loc in combined for loc in locations):
        return False

    property_types = cfg.get("property_types", [])
    if property_types and not any(pt in combined for pt in property_types):
        return False

    must_keywords = cfg.get("must_keywords", [])
    if must_keywords and not any(kw in combined for kw in must_keywords):
        return False

    if any(kw in combined for kw in cfg.get("reject_keywords", [])):
        return False

    max_price = cfg.get("max_price_inr", 0)
    if max_price and price_inr is not None and price_inr > max_price:
        return False

    return True


def parse_price_inr(raw: str) -> int | None:
    """
    Convert a human-readable Indian price string to an integer.
    Examples: "₹45,00,000", "45 Lac", "4500000", "45L"
    Returns None if parsing fails.
    """
    raw = raw.replace(",", "").replace("₹", "").replace(" ", "").lower()

    lakh_match = re.search(r"([\d.]+)\s*l(?:ac|akh)?", raw)
    crore_match = re.search(r"([\d.]+)\s*(?:crore|cr)\b", raw)
    plain_match = re.search(r"(\d+)", raw)

    if crore_match:
        return int(float(crore_match.group(1)) * 1_00_00_000)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 1_00_000)
    if plain_match:
        return int(plain_match.group(1))

    return None
