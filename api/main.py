"""
FastAPI application entry point.

Run:
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import config as config_router
from api.routes import listings as listings_router
from api.routes import scrapers as scrapers_router

app = FastAPI(
    title="Property Watcher",
    description="Personal real estate monitor — configure, run, and review matched listings.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# API routes
app.include_router(config_router.router)
app.include_router(listings_router.router)
app.include_router(scrapers_router.router)

# Serve the Alpine.js UI at /
_static_dir = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
