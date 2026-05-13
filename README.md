# Property Watcher

Automated real estate monitor that scrapes Indian property portals, filters listings by your exact preferences, and pushes instant alerts to your phone via Telegram.

Built for personal use — zero cost to run using MongoDB Atlas free tier and GitHub Actions.

## Quickstart

```bash
git clone <your-repo-url> property-checker
cd property-checker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill in your credentials
python scraper.py
```

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Tested on 3.12 |
| MongoDB Atlas | Free M0 cluster — [cloud.mongodb.com](https://cloud.mongodb.com) |
| Telegram bot | Create via [@BotFather](https://t.me/BotFather), get your `chat_id` |

## Running locally

```bash
source .venv/bin/activate
python scraper.py
```

Logs are written to stdout. Each run checks all enabled portals, filters results against your config, and sends a Telegram message per new match.

## Running the web UI

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
# open http://localhost:8000
```

The UI lets you edit keywords, toggle portals, and trigger manual runs without touching any files.

## Automated scheduling

Push to a private GitHub repository. The workflow in `.github/workflows/scraper.yml` runs every 4 hours automatically. Add `MONGO_URI`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` as repository secrets.

## Documentation

| File | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System design, data flow, component overview |
| [docs/configuration.md](docs/configuration.md) | All config options, env vars, search filters |
| [docs/api.md](docs/api.md) | REST API reference for the web UI |
| [docs/development.md](docs/development.md) | Local setup, adding scrapers, portal status |
