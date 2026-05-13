# Development Guide

## Local setup

```bash
git clone <your-repo-url> property-checker
cd property-checker

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env               # fill in MONGO_URI, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Running the scraper

```bash
source .venv/bin/activate
python scraper.py
```

Logs are written to stdout in ISO 8601 format. A run that finds nothing is silent (only an INFO summary line).

## Running the web UI

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000`. Changes to Python files reload automatically.

## Smoke tests

Run the built-in logic tests (no credentials or network needed):

```bash
source .venv/bin/activate
python - <<'EOF'
from scrapers.filters import passes_filters, parse_price_inr
from scrapers import ALL_SCRAPERS

assert passes_filters("2 BHK Manacaud", "east facing vastu", 4_500_000)
assert not passes_filters("2 BHK flat", "vastu east facing", 7_100_000)
assert parse_price_inr("45 Lac") == 4_500_000
assert parse_price_inr("1.5 Cr") == 15_000_000
print("OK — scrapers:", [cls.source for cls in ALL_SCRAPERS])
EOF
```

## Adding a new scraper

1. Create `scrapers/<portalname>.py`
2. Subclass `BaseScraper` and implement `fetch_listings()`
3. Register it in `scrapers/__init__.py`

### `fetch_listings()` contract

Return a list of dicts. Every dict **must** include these keys:

| Key | Type | Description |
|---|---|---|
| `property_id` | `str` | Portal-unique identifier. Prefix with your source name, e.g. `"mb-123456"` |
| `title` | `str` | Listing headline |
| `description` | `str` | All text used for keyword matching (title + features + highlights) |
| `price_raw` | `str` | Price exactly as it appears on the portal |
| `url` | `str` | Full URL to the listing page |
| `source` | `str` | Matches your `source` class attribute |

Filtering, price parsing, deduplication, and Telegram delivery are all handled by the framework. The scraper only needs to fetch and parse.

### Minimal example

```python
# scrapers/newportal.py
from scrapers.base import BaseScraper

class NewPortalScraper(BaseScraper):
    source = "newportal"

    def fetch_listings(self):
        resp = self.get("https://newportal.com/search?city=trivandrum&bhk=2")
        items = resp.json().get("results", [])
        return [
            {
                "property_id": f"np-{item['id']}",
                "title": item["heading"],
                "description": f"{item['heading']} {item.get('features', '')}",
                "price_raw": item.get("price", ""),
                "url": f"https://newportal.com/property/{item['id']}",
                "source": self.source,
            }
            for item in items
        ]
```

Then add it to `scrapers/__init__.py`:

```python
from scrapers.newportal import NewPortalScraper

ALL_SCRAPERS = [MagicBricksScraper, NinetyNineAcresScraper, OLXScraper, NewPortalScraper]
```

---

## Portal status and known limitations

| Portal | Current state | Root cause | Path forward |
|---|---|---|---|
| **OLX** | ✓ Working | Public JSON API, no auth | No action needed |
| **MagicBricks** | ⚠ JS-rendered | React SPA — requests return a maintenance stub | Replace `fetch_listings()` with Playwright (headless browser) |
| **99acres** | ⚠ Blocked | Akamai WAF returns 403 | Playwright with a real browser fingerprint, or use their official developer API if available |

### Adding Playwright support (future)

For portals that require JavaScript, swap the `requests` call for a Playwright page load:

```python
# pip install playwright && playwright install chromium
from playwright.sync_api import sync_playwright

def fetch_listings(self):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.magicbricks.com/...")
        page.wait_for_selector("div.mb-srp__card", timeout=15_000)
        html = page.content()
        browser.close()
    soup = BeautifulSoup(html, "lxml")
    # parse cards...
```

Add `playwright` to `requirements.txt` and run `playwright install chromium` once during setup.

---

## Project structure

```
property-checker/
├── .github/
│   └── workflows/
│       └── scraper.yml        GitHub Actions — runs every 4 hours
├── api/                       FastAPI web UI backend
│   ├── main.py
│   ├── deps.py
│   └── routes/
│       ├── config.py
│       ├── listings.py
│       └── scrapers.py
├── docs/                      Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── configuration.md
│   └── development.md
├── models.py                  Pydantic schemas
├── scrapers/                  Per-portal scraper modules
│   ├── __init__.py
│   ├── base.py
│   ├── filters.py
│   ├── magicbricks.py
│   ├── ninety9acres.py
│   └── olx.py
├── static/                    Alpine.js frontend assets
│   ├── index.html
│   ├── app.js
│   └── style.css
├── config.py                  Secrets + SEARCH_CONFIG defaults
├── db.py                      MongoDB helpers
├── notifier.py                Telegram alert sender
├── scraper.py                 CLI entry point
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP requests in all scrapers |
| `beautifulsoup4` + `lxml` | HTML parsing (99acres, MagicBricks HTML fallback) |
| `pymongo` | MongoDB Atlas driver |
| `python-dotenv` | Loads `.env` file into environment |
| `fastapi` | REST API for the web UI |
| `uvicorn` | ASGI server for FastAPI |

## GitHub Actions setup

1. Push your code to a **private** GitHub repository.
2. Add the three secrets under **Settings → Secrets and variables → Actions**.
3. The workflow runs automatically. Trigger a manual run via **Actions → Property Scraper → Run workflow**.

The job whitelist in MongoDB Atlas must include `0.0.0.0/0` since GitHub Actions uses dynamic IP addresses.
