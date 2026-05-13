# Architecture

## Overview

Property Watcher is a pipeline of four loosely-coupled stages. Each stage is independently replaceable.

```
GitHub Actions (cron / manual)
        │
        ▼
   scraper.py  ←──────────────────────── MongoDB scraper_config
        │                                (live config edited via UI)
        ▼
  scrapers/  (per-portal modules)
        │
        ├── BaseScraper.fetch_listings()   HTTP request to portal
        │
        └── BaseScraper.run()             apply filters
              │
              ├── passes_filters()        keyword + price check
              └── parse_price_inr()       normalise price string
                      │
                      ▼
                   db.py
              is_new_listing()  ──→  MongoDB Atlas (listings collection)
              save_listing()
                      │
                      ▼
               notifier.py
              send_alert()  ──→  Telegram Bot API  ──→  Phone
```

## Components

### `scraper.py` — Entry point
Orchestrates a full run: iterates over all enabled scrapers, calls `db.is_new_listing()` per matched result, saves new ones, and fires Telegram alerts. Used both locally and by GitHub Actions.

### `config.py` — Configuration
Holds two kinds of state:
- **Secrets** — loaded from environment variables (`.env` locally, GitHub Secrets in CI). Never hardcoded.
- **`SEARCH_CONFIG`** — the default filter ruleset. The running system reads this from MongoDB (`scraper_config` collection) if available, falling back to these hardcoded defaults.

### `scrapers/` — Portal modules

| File | Portal | Method | Status |
|---|---|---|---|
| `magicbricks.py` | MagicBricks | HTML (BeautifulSoup) | ⚠ Returns maintenance page — needs Playwright |
| `ninety9acres.py` | 99acres | HTML (BeautifulSoup) | ⚠ Blocked by WAF (403) |
| `olx.py` | OLX India | JSON API | ✓ Working |

All scrapers inherit from `BaseScraper` and only need to implement `fetch_listings()`. Filtering and error handling are provided by the base class.

### `scrapers/filters.py` — Filter engine
Stateless functions consumed by `BaseScraper.run()`.
- `passes_filters(title, description, price_inr)` — applies the four filter rules.
- `parse_price_inr(raw)` — converts Indian price strings (₹45,00,000 / 45 Lac / 1.5 Cr) to a plain integer.

### `db.py` — MongoDB wrapper
Two public functions: `is_new_listing(property_id)` and `save_listing(listing)`. A unique index on `property_id` is created on first connect, providing a hard deduplication guarantee even under concurrent runs.

### `notifier.py` — Telegram alerts
Sends a formatted plain-text message per new listing to the configured `chat_id`. Errors are logged but never crash the pipeline.

## Data model

### `listings` collection

```json
{
  "_id": "<ObjectId>",
  "property_id": "olx-1234567890",
  "title": "2 BHK Apartment Manacaud",
  "price": "45 Lac",
  "price_inr": 4500000,
  "source": "olx",
  "url": "https://www.olx.in/item/...",
  "location": "Manacaud, Thiruvananthapuram",
  "description": "...",
  "discovered_at": "2026-05-13T10:22:49Z"
}
```

A unique index on `property_id` prevents duplicate entries.

### `scraper_config` collection (added by UI)

```json
{
  "_id": "active",
  "locations": ["Trivandrum", "Manacaud"],
  "property_types": ["2 bhk", "2bhk"],
  "must_keywords": ["vastu", "east facing"],
  "reject_keywords": ["pg", "hostel"],
  "max_price_inr": 6000000,
  "enabled_scrapers": ["olx"],
  "updated_at": "2026-05-13T10:00:00Z"
}
```

There is always exactly one document (upserted with `_id = "active"`).

## Web UI layer (planned)

A FastAPI backend mounts a static Alpine.js frontend. The backend exposes a REST API for reading/writing `scraper_config` and triggering manual runs. See [api.md](api.md).

```
Browser  ──→  GET /          static HTML + Alpine.js
         ──→  GET /api/*     FastAPI routes
                   │
                   ├── reads/writes MongoDB scraper_config
                   └── triggers scraper.main() as background task
```

## Scheduling

GitHub Actions runs `.github/workflows/scraper.yml` on a `cron: "0 */4 * * *"` schedule (every 4 hours). The workflow checks out the repo, installs dependencies, and calls `python scraper.py`. Runtime config is read from MongoDB, so filter changes made via the UI take effect on the next scheduled run — no code changes or re-deployment needed.
