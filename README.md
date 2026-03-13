# 🔗 URL Shortener

A clean, production-minded URL shortening service built with **FastAPI** and **SQLite**, developed using a **test-driven development (TDD)** workflow with AI-assisted tooling.

---

## What It Does

- Shorten any valid HTTP/HTTPS URL into a 6-character alphanumeric code
- Redirect short links to their original destination (tracks click count)
- View per-link statistics: original URL, click count, creation date, last updated
- Soft delete support — links can be deactivated without data loss
- In-memory rate limiting on the `/shorten` endpoint
- Structured logging to stdout
- Simple web interface — no frontend framework required
- Health check endpoint for container orchestration

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.111 |
| Database | SQLite via SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Testing | Pytest + HTTPX TestClient |
| Container | Docker (multi-stage build) |
| CI/CD | GitHub Actions |

---

## Running Locally

### Option 1 — Python (direct)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn app.main:app --reload
```

The database tables are created automatically on startup via FastAPI's `lifespan` event — no manual init step required.

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Option 2 — Docker Compose (recommended)

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

SQLite data is persisted in a named Docker volume (`url_data`) so your links survive container restarts.

### Environment variables

Create a `.env` file in the project root to override defaults:

```env
APP_VERSION=1.0.0
DATABASE_URL=sqlite:///./urls.db
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

---

## Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

All tests use an **in-memory SQLite database** — no setup required, no state left behind.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web interface |
| `GET` | `/health` | Health check |
| `POST` | `/shorten` | Shorten a URL |
| `GET` | `/{code}` | Redirect to original URL |
| `GET` | `/stats/{code}` | View link statistics |

**POST /shorten — Request body:**
```json
{ "url": "https://your-long-url.com/some/path" }
```

**POST /shorten — Response (201):**
```json
{
  "short_code": "aB3kLm",
  "short_url": "http://localhost:8000/aB3kLm",
  "original_url": "https://your-long-url.com/some/path"
}
```

**GET /stats/{code} — Response (200):**
```json
{
  "short_code": "aB3kLm",
  "original_url": "https://your-long-url.com/some/path",
  "click_count": 7,
  "is_deleted": false,
  "created_at": "2024-05-01T12:00:00Z",
  "updated_at": "2024-05-01T14:00:00Z"
}
```

Rate limit: `POST /shorten` is limited to **10 requests per 60 seconds** per IP (configurable via `.env`). Exceeding the limit returns `429 Too Many Requests`.

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
TDD_project/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware, startup
│   ├── config.py            # Settings loaded from environment / .env
│   ├── constants.py         # Shared error message strings
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models.py            # ORM model (URL table)
│   ├── middleware/
│   │   └── rate_limit.py    # In-memory sliding-window rate limiter
│   ├── routes/
│   │   ├── health.py        # GET /health
│   │   └── urls.py          # POST /shorten, GET /{code}, GET /stats/{code}
│   ├── schemas/
│   │   ├── url.py           # ShortenRequest / ShortenResponse
│   │   ├── stats.py         # StatsResponse
│   │   └── health.py        # HealthResponse
│   └── services/
│       └── shortener.py     # Core business logic (code generation, DB ops)
├── scripts/
│   └── init_db.py           # Optional standalone DB initialisation script
├── tests/
│   ├── conftest.py          # Shared fixtures (in-memory DB, TestClient, rate limiter reset)
│   ├── test_health.py
│   ├── test_shorten.py
│   ├── test_redirect.py
│   ├── test_stats.py
│   ├── test_rate_limit.py
│   └── test_shortener_service.py  # Unit tests for service layer
├── static/
│   └── index.html           # Frontend (vanilla JS, no framework)
├── .github/
│   └── workflows/
│       ├── ci.yml           # Run tests on every push
│       └── docker.yml       # Build & push Docker image on merge to main
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Local Docker development
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

---

## Design Decisions

**SQLite over PostgreSQL** — sufficient for this scope and keeps the project zero-dependency to run. The SQLAlchemy abstraction means switching to Postgres is a one-line `DATABASE_URL` change.

**Lifespan for DB init** — database tables are created inside FastAPI's `lifespan` async context manager on startup. This is the idiomatic FastAPI pattern and ensures tables exist before any request is handled.

**Schemas split by domain** — `schemas/url.py`, `schemas/stats.py`, `schemas/health.py` instead of a single `schemas.py`. Easier to navigate and extend as the API grows.

**Service layer separation** — `app/services/shortener.py` contains all business logic independently from HTTP concerns. This makes unit testing straightforward without spinning up a full HTTP stack.

**Collision handling via IntegrityError** — short code uniqueness is enforced by a DB-level unique constraint. On collision, the service catches `IntegrityError`, rolls back, and retries — safer than a pre-check query which is vulnerable to race conditions.

**Soft delete** — `is_deleted` flag instead of hard deletes. Preserves click history and makes accidental deletions recoverable.

**DB-level timestamps** — `created_at` and `updated_at` use `server_default=func.now()` and `onupdate=func.now()`, so timestamps are managed by the database engine rather than application code.

**In-memory rate limiter** — sliding window counter per IP, applied only to `POST /shorten`. No external dependency (no Redis). Configurable via environment variables.

**Config from environment** — `app/config.py` reads all tuneable values from environment variables with sensible defaults. No hardcoded values in application code.

**In-memory DB for tests** — each test function gets a fresh SQLite in-memory database with a transaction that is rolled back after the test. The rate limiter state is also reset before each test via an `autouse` fixture.

**Multi-stage Docker build** — builder stage installs dependencies; runtime stage copies only what is needed. The final image runs as a non-root user.

**6-character alphanumeric codes** — 62^6 ≈ 56 billion possible codes. Collision is handled via `IntegrityError` retry (up to 10 attempts).

---

## What I Would Improve With More Time

- **Alembic migrations** — full migration history instead of lifespan `create_all`
- **Custom aliases** — let users specify their own short code
- **Expiration** — optional TTL per link
- **DELETE /links/{code}** — expose soft delete via API endpoint
- **PostgreSQL** — for production multi-instance deployments
- **Redis rate limiting** — distributed rate limiting across multiple instances
- **Terraform** — IaC for cloud deployment (GCP Cloud Run or AWS ECS)
- **Prometheus metrics** — expose `/metrics` for observability
- **Authentication** — API keys so users can manage only their own links

---

## CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `ci.yml` | Every push / PR | Install → Test → Coverage report |
| `docker.yml` | Push to `main` / release | Build → Push to GHCR |