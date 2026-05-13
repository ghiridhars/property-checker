"""
scraper.py — main entry point.
Run locally:   python scraper.py
Run in CI:     triggered by GitHub Actions (see .github/workflows/scraper.yml)
"""
from __future__ import annotations

import logging
import sys

from config import validate_secrets
from db import is_new_listing, save_listing
from notifier import send_alert
from scrapers import ALL_SCRAPERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("scraper")


def main() -> None:
    validate_secrets()
    total_new = 0

    for ScraperClass in ALL_SCRAPERS:
        scraper = ScraperClass()
        logger.info("Running scraper: %s", scraper.source)
        matched = scraper.run()

        for listing in matched:
            prop_id = listing.get("property_id", "")
            if not prop_id:
                continue

            if is_new_listing(prop_id):
                saved = save_listing(listing)
                if saved:
                    send_alert(listing)
                    total_new += 1
            else:
                logger.debug("Already seen: %s", prop_id)

    logger.info("Done. %d new listing(s) found and notified.", total_new)


if __name__ == "__main__":
    main()
