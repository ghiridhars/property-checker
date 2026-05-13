# Configuration Reference

## Environment variables

These are secrets. Set them in `.env` for local runs and in GitHub repository secrets for CI.

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB Atlas connection string. Format: `mongodb+srv://<user>:<password>@cluster.xxxxx.mongodb.net/` |
| `TELEGRAM_BOT_TOKEN` | Yes | Token from [@BotFather](https://t.me/BotFather). Format: `123456789:AAxxxxxxxx...` |
| `TELEGRAM_CHAT_ID` | Yes | Your personal Telegram user ID. Get it from [@userinfobot](https://t.me/userinfobot) |

### Setting up locally

```bash
cp .env.example .env
# edit .env with real values
```

The app loads `.env` automatically via `python-dotenv`. The `.env` file is in `.gitignore` and must never be committed.

### Setting up for GitHub Actions

In your repository: **Settings → Secrets and variables → Actions → New repository secret**. Add each variable above.

---

## Search configuration (`SEARCH_CONFIG`)

Defined in `config.py`. When the web UI is running, these values are read from MongoDB (`scraper_config` collection) and the hardcoded defaults act as a fallback.

### `locations`
List of location strings baked into each scraper's search URL. Used to scope the portal search geographically.

```python
"locations": ["Trivandrum", "Thiruvananthapuram", "Manacaud", "Attukal"]
```

Note: each scraper uses these to construct the correct search URL for that portal. Adding a location here only takes effect if the scraper for that portal handles it (see [development.md](development.md)).

### `property_types`
Case-insensitive substrings. At least one must appear in the listing title or description. Used to filter out studios, 3 BHK, plots, etc.

```python
"property_types": ["2 bhk", "2bhk"]
```

### `must_keywords`
Case-insensitive substrings. At least **one** must appear in the listing title or description. A listing that matches no must-keyword is rejected.

```python
"must_keywords": ["vastu", "east facing", "east-facing", "puja room", "pooja room", "unfurnished"]
```

### `reject_keywords`
Case-insensitive substrings. If **any** of these appear in the listing, it is rejected regardless of other matches.

```python
"reject_keywords": ["pg", "hostel", "commercial", "office", "shop"]
```

### `max_price_inr`
Integer price ceiling in Indian Rupees. Set to `0` to disable the price filter.

```python
"max_price_inr": 6_000_000   # ₹60 lakh
```

---

## Price string formats

The `parse_price_inr()` function normalises all of the following to a plain integer:

| Input | Parsed value |
|---|---|
| `₹45,00,000` | 4 500 000 |
| `45 Lac` | 4 500 000 |
| `45L` | 4 500 000 |
| `45 lakh` | 4 500 000 |
| `1.5 Cr` | 15 000 000 |
| `4500000` | 4 500 000 |
| `Rs 60 lakh` | 6 000 000 |

---

## HTTP settings

These are internal constants in `config.py`, not environment variables.

| Constant | Default | Description |
|---|---|---|
| `REQUEST_TIMEOUT` | `30` seconds | Applied to all outbound HTTP requests |
| `DEFAULT_HEADERS` | Chrome 124 UA + `en-IN` language | Sent with every scraper request |

---

## MongoDB collections

| Collection | Purpose |
|---|---|
| `listings` | All matched and saved property listings |
| `scraper_config` | Single-document live config edited by the UI (upserted with `_id = "active"`) |

Database name: `property_watcher` (set by `MONGO_DB_NAME` in `config.py`).
