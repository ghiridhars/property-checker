"""
GET /api/config  — read current search config from DB (or defaults)
PUT /api/config  — save updated config to DB
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.deps import get_scraper_config_col
from models import SearchConfig
import config as app_config

router = APIRouter(prefix="/api/config", tags=["config"])

_CONFIG_DOC_ID = "active"


def _defaults() -> dict:
    return {
        **app_config.SEARCH_CONFIG,
        "enabled_scrapers": ["olx"],
    }


@router.get("", response_model=SearchConfig)
def get_config() -> SearchConfig:
    try:
        col = get_scraper_config_col()
        doc = col.find_one({"_id": _CONFIG_DOC_ID})
        if doc:
            doc.pop("_id", None)
            doc.pop("updated_at", None)
            return SearchConfig(**doc)
    except Exception:  # noqa: BLE001
        pass  # DB unavailable — return hardcoded defaults
    return SearchConfig(**_defaults())


@router.put("", response_model=dict)
def put_config(body: SearchConfig) -> JSONResponse:
    try:
        col = get_scraper_config_col()
        payload = body.model_dump()
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        col.update_one(
            {"_id": _CONFIG_DOC_ID},
            {"$set": payload},
            upsert=True,
        )
    except Exception as exc:  # noqa: BLE001
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    return {"ok": True}
