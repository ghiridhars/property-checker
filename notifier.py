"""
Telegram notification helper.
Sends a plain-text alert for each new property match.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from config import REQUEST_TIMEOUT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, telegram_enabled

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_alert(listing: dict[str, Any]) -> None:
    """Send a Telegram message for a matched listing. No-op if Telegram is not configured."""
    if not telegram_enabled():
        logger.debug("Telegram not configured — skipping alert for %s", listing.get("property_id"))
        return
    price_display = listing.get("price", "N/A")
    message = (
        "New Property Match!\n\n"
        f"Title : {listing.get('title', 'N/A')}\n"
        f"Price : {price_display}\n"
        f"Source: {listing.get('source', 'N/A')}\n"
        f"Link  : {listing.get('url', 'N/A')}"
    )

    url = _TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        logger.info("Telegram alert sent for: %s", listing.get("property_id"))
    except requests.RequestException as exc:
        logger.error("Failed to send Telegram alert: %s", exc)
