# Competitive Intelligence Scanner

A competitive intelligence scanning app for Augment Code's GTM team. Ingests RSS feeds on a schedule, uses Claude to evaluate competitive developments, and provides a collaborative review workflow.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **LLM:** Anthropic Claude API
- **Database:** PostgreSQL

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
├── backend/          # FastAPI backend
│   ├── main.py       # App entrypoint
│   ├── models/       # SQLAlchemy models
│   ├── routes/       # API route handlers
│   ├── services/     # Business logic
│   └── alembic/      # Database migrations
├── frontend/         # React frontend
│   └── src/
├── Dockerfile        # Multi-stage build
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
