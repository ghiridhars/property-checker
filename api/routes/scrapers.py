"""
GET  /api/scrapers          — list all scrapers + enabled state
PUT  /api/scrapers/{name}   — toggle a scraper on/off
POST /api/run               — trigger an immediate run (background task)
GET  /api/run/status        — last run metadata
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from api.deps import get_scraper_config_col
from models import RunStatus, ScraperInfo
from scrapers import ALL_SCRAPERS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["scrapers"])

_CONFIG_DOC_ID = "active"

# In-memory run state (single-process, sufficient for a personal tool)
_run_lock = threading.Lock()
_run_state: dict[str, Any] = {
    "running": False,
    "last_run_at": None,
    "last_run_new_count": 0,
    "last_run_error": None,
}

# Static metadata per scraper — not persisted, just informational
_SCRAPER_META: dict[str, str] = {
    "olx": "active",
    "magicbricks": "js_only",
    "99acres": "blocked",
}


# ── helpers ────────────────────────────────────────────────────────────────

def _get_enabled(col=None) -> list[str]:
    if col is None:
        return ["olx"]
    try:
        doc = col.find_one({"_id": _CONFIG_DOC_ID})
        if doc:
            return doc.get("enabled_scrapers", ["olx"])
    except Exception:  # noqa: BLE001
        pass
    return ["olx"]


def _set_enabled(col, name: str, enabled: bool) -> None:
    col.update_one(
        {"_id": _CONFIG_DOC_ID},
        {"$set": {"enabled_scrapers." + name: enabled}} if False  # workaround below
        else (
            {"$addToSet": {"enabled_scrapers": name}}
            if enabled
            else {"$pull": {"enabled_scrapers": name}}
        ),
        upsert=True,
    )


# ── routes ──────────────────────────────────────────────────────────────────

@router.get("/api/scrapers", response_model=list[ScraperInfo])
def list_scrapers() -> list[ScraperInfo]:
    try:
        col = get_scraper_config_col()
        enabled = _get_enabled(col)
    except Exception:  # noqa: BLE001
        enabled = _get_enabled(None)
    return [
        ScraperInfo(
            name=cls.source,
            enabled=cls.source in enabled,
            status=_SCRAPER_META.get(cls.source, "unknown"),
        )
        for cls in ALL_SCRAPERS
    ]


class ToggleBody(BaseModel):
    enabled: bool


@router.put("/api/scrapers/{name}", response_model=dict)
def toggle_scraper(name: str, body: ToggleBody) -> dict:
    known = {cls.source for cls in ALL_SCRAPERS}
    if name not in known:
        raise HTTPException(status_code=404, detail=f"Scraper '{name}' not found.")
    if _SCRAPER_META.get(name, "unknown") != "active" and body.enabled:
        raise HTTPException(status_code=400, detail=f"Scraper '{name}' cannot be enabled: status is '{_SCRAPER_META.get(name)}'.")
    try:
        col = get_scraper_config_col()
        _set_enabled(col, name, body.enabled)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    return {"ok": True, "name": name, "enabled": body.enabled}


@router.get("/api/run/status", response_model=RunStatus)
def run_status() -> RunStatus:
    return RunStatus(**_run_state)


@router.post("/api/run", status_code=202, response_model=dict)
def trigger_run(background_tasks: BackgroundTasks) -> dict:
    if _run_state["running"]:
        raise HTTPException(status_code=409, detail="A scraper run is already in progress.")
    background_tasks.add_task(_do_run)
    return {"started": True}


# ── background task ─────────────────────────────────────────────────────────

def _do_run() -> None:
    with _run_lock:
        _run_state["running"] = True
        _run_state["last_run_error"] = None

    try:
        # Import here to avoid a circular dep at module load time
        from db import is_new_listing, save_listing
        from notifier import send_alert
        from api.deps import get_scraper_config_col

        col = get_scraper_config_col()
        enabled = _get_enabled(col)

        total_new = 0
        for ScraperClass in ALL_SCRAPERS:
            if ScraperClass.source not in enabled:
                continue
            scraper = ScraperClass()
            matched = scraper.run()
            for listing in matched:
                prop_id = listing.get("property_id", "")
                if prop_id and is_new_listing(prop_id):
                    if save_listing(listing):
                        send_alert(listing)
                        total_new += 1

        _run_state["last_run_new_count"] = total_new
        _run_state["last_run_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Manual run complete. %d new listing(s).", total_new)

    except Exception as exc:  # noqa: BLE001
        _run_state["last_run_error"] = str(exc)
        logger.exception("Manual run failed: %s", exc)
    finally:
        _run_state["running"] = False
