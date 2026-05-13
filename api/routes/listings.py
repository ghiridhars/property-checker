"""
GET /api/listings  — paginated list of saved listings, newest first
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.deps import get_listings_col
from models import ListingOut, ListingsPage

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("", response_model=ListingsPage)
def get_listings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None),
) -> ListingsPage:
    try:
        col = get_listings_col()
    except Exception:  # noqa: BLE001
        return ListingsPage(total=0, page=page, limit=limit, items=[])

    query: dict = {}
    if source:
        query["source"] = source

    total = col.count_documents(query)
    skip = (page - 1) * limit

    cursor = col.find(query, {"_id": 0}).sort("discovered_at", -1).skip(skip).limit(limit)

    items = []
    for doc in cursor:
        items.append(
            ListingOut(
                property_id=doc.get("property_id", ""),
                title=doc.get("title", ""),
                price=doc.get("price", "N/A"),
                price_inr=doc.get("price_inr"),
                source=doc.get("source", ""),
                url=doc.get("url", ""),
                location=doc.get("location"),
                discovered_at=doc.get("discovered_at"),
            )
        )

    return ListingsPage(total=total, page=page, limit=limit, items=items)
