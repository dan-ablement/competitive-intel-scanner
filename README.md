# Competitive Intelligence Scanner

A competitive intelligence scanning app for Augment Code's GTM team. Monitors competitor activity across **RSS feeds**, **web pages** (via Crawl4AI), and **Twitter/X accounts**, then uses Claude to evaluate developments and surface insights through a collaborative review workflow.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **LLM:** Anthropic Claude API
- **Database:** PostgreSQL
- **Web Scraping:** Crawl4AI + Playwright (headless Chromium)
- **Twitter/X:** X API v2 via httpx

## Source Types

| Type | How it works | Key service |
|------|-------------|-------------|
| **RSS Feed** | Parses standard RSS/Atom feeds on a schedule | `feed_checker.py` |
| **Web Scrape** | Crawls competitor pages with Crawl4AI, extracts article links, and ingests new content | `web_scraper.py` |
| **Twitter/X** | Polls the X API v2 for new tweets from monitored accounts using Bearer token auth | `twitter_ingester.py` |

All three source types feed into the same LLM analysis pipeline — items are scored for relevance and surfaced as analysis cards in the review UI.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

## Quick Start

1. **Clone and configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and secrets
   ```

2. **Start all services:**

   ```bash
   docker-compose up --build
   ```

   This starts:
   - **PostgreSQL** on `localhost:5432`
   - **App** (backend + frontend) on `localhost:8080`

3. **Run database migrations:**

   ```bash
   docker-compose exec app alembic -c backend/alembic/alembic.ini upgrade head
   ```

4. **Open the app:**

   Visit [http://localhost:8080](http://localhost:8080)

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (set automatically in docker-compose) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key for LLM analysis |
| `X_BEARER_TOKEN` | X API Bearer token for Twitter/X monitoring |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID for SSO |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `ALLOWED_DOMAIN` | Allowed email domain for login (e.g., `augmentcode.com`) |
| `SESSION_SECRET` | Secret key for session cookie signing |

## Common Commands

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Stop and remove volumes (resets database)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

## Project Structure

```
├── backend/
│   ├── main.py                        # App entrypoint
│   ├── models/
│   │   ├── feed.py                    # RSS feed / source model
│   │   ├── feed_item.py               # Ingested content items
│   │   ├── twitter_source_config.py   # Twitter/X per-source settings
│   │   ├── analysis_card.py           # LLM-generated analysis cards
│   │   └── ...
│   ├── services/
│   │   ├── feed_checker.py            # RSS feed ingestion
│   │   ├── web_scraper.py             # Crawl4AI web scraping
│   │   ├── twitter_ingester.py        # X API v2 ingestion
│   │   ├── llm_analyzer.py            # Claude analysis pipeline
│   │   └── ...
│   ├── routes/                        # API route handlers
│   └── alembic/                       # Database migrations
├── frontend/                          # React frontend
│   └── src/
├── Dockerfile                         # Multi-stage build (includes Playwright/Chromium)
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Production Deployment

The app is designed to run on **Google Cloud**:

- **Cloud Run** — hosts the containerised app
- **Cloud SQL (PostgreSQL)** — managed database
- **Secret Manager** — stores API keys and credentials
- **Cloud Scheduler** — triggers scheduled feed checks and ingestion runs
