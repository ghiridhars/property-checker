"""
Shared Pydantic models used by the API routes and the scraper config loader.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SearchConfig(BaseModel):
    locations: list[str] = Field(default_factory=list)
    property_types: list[str] = Field(default_factory=list)
    must_keywords: list[str] = Field(default_factory=list)
    reject_keywords: list[str] = Field(default_factory=list)
    max_price_inr: int = Field(default=0, ge=0)
    enabled_scrapers: list[str] = Field(default_factory=lambda: ["olx"])

    @field_validator("locations", "property_types", "must_keywords", "reject_keywords", mode="before")
    @classmethod
    def strip_and_lower(cls, v: list) -> list:
        return [s.strip().lower() for s in v if isinstance(s, str) and s.strip()]


class ScraperInfo(BaseModel):
    name: str
    enabled: bool
    status: str  # "active" | "js_only" | "blocked"


class ListingOut(BaseModel):
    property_id: str
    title: str
    price: str
    price_inr: Optional[int] = None
    source: str
    url: str
    location: Optional[str] = None
    discovered_at: Optional[str] = None


class ListingsPage(BaseModel):
    total: int
    page: int
    limit: int
    items: list[ListingOut]


class RunStatus(BaseModel):
    running: bool
    last_run_at: Optional[str] = None
    last_run_new_count: int = 0
    last_run_error: Optional[str] = None
