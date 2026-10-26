# Disaster Response Coordination Platform

Backend API for creating disaster incidents, resolving locations from natural-language descriptions (Groq + geocoding), finding nearby resources (PostgreSQL + PostGIS), fetching cached community reports, and broadcasting real-time updates over WebSockets.

This repository is the submission for the **Founding Engineer** take-home assignment. The API is enough to demonstrate every required capability — Swagger UI and a Postman collection are included instead of a polished frontend.

---

## What to push to GitHub (required vs do not commit)

Push **`disaster-platform/` as the repository root** (not the parent `founding/` folder). That parent folder contains assignment documents and local secrets that reviewers do not need.

### Must commit (project will not run without these)

| Path | Why it is required |
|------|--------------------|
| `app/` | FastAPI application: routes, services, auth, schemas, DB models |
| `alembic/` + `alembic.ini` | Creates PostGIS tables (`disasters`, `resources`, `external_cache`) |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Documents every environment variable (no secrets) |
| `.gitignore` | Prevents `.env` and `.venv/` from being committed |
| `scripts/seed_data.py` | Loads the Manhattan flood demo disaster + 5 resources |
| `docker-compose.yml` | Optional local PostGIS if you are not using Neon |

### Should commit (reviewers need these)

| Path | Why |
|------|-----|
| `README.md` | Setup, architecture, flow, decisions, trade-offs |
| `MIGRATIONS.md` | Neon + Alembic walkthrough |
| `SETUP_WINDOWS.md` | Windows / SSL / venv troubleshooting |
| `postman/Disaster-Platform.postman_collection.json` | API demo without a frontend |
| `scripts/ws_demo_client.py` | WebSocket event demo |
| `scripts/setup.ps1` | One-shot Windows install |
| `tests/` + `pytest.ini` | Required assignment tests |

### Never commit (breaks security or bloats the repo)

| Path | Why |
|------|-----|
| `.env` | Contains `DATABASE_URL`, `GROQ_API_KEY`, `JWT_SECRET` |
| `.venv/` / `venv/` | Local virtualenv (hundreds of MB; install from `requirements.txt`) |
| `__pycache__/`, `.pytest_cache/` | Generated |
| `pgdata/` | Local Docker Postgres volume |

Reviewers clone the repo, copy `.env.example` → `.env`, add their own Neon URL / Groq key, run migrations + seed, then start the API.

---

## Prerequisites

- **Python 3.10+** (3.11 recommended; 3.14 is not required)
- **PostgreSQL with PostGIS** — [Neon](https://neon.tech) (recommended) or local Docker
- Optional: a [Groq](https://console.groq.com) API key for live location extraction

---

## Setup — run locally

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd disaster-platform
```

### 2. Create `.env` from the example

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:

```env
# Neon connection string from the console (sslmode=require is OK)
DATABASE_URL=postgresql://USER:PASSWORD@ep-xxxx-pooler.REGION.aws.neon.tech/neondb?sslmode=require

# Leave empty and set mocks to true if you do not have a Groq key
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=change-me-in-production-use-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CACHE_TTL_SECONDS=300
NOMINATIM_USER_AGENT=disaster-platform-assignment/1.0
USE_MOCK_GEOCODING=false
USE_MOCK_LLM=false
```

**No Groq key?** Set `USE_MOCK_LLM=true` and `USE_MOCK_GEOCODING=true`. Location still resolves for known places (Manhattan, Mumbai, Delhi, …).

**Neon:** enable the **PostGIS** extension on that database in the Neon console before running migrations.

**Local Docker instead of Neon:**

```bash
docker compose up -d
```

Then in `.env` use:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/disaster_db
```

### 3. Install, migrate, seed, start

**Windows (PowerShell) — use the venv interpreter:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed_data
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Or run `.\scripts\setup.ps1` first if `pip` fails TLS on a corporate network. See [SETUP_WINDOWS.md](./SETUP_WINDOWS.md).

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
alembic upgrade head
python -m scripts.seed_data
uvicorn app.main:app --reload
```

### 4. Open the API

| Resource | URL |
|----------|-----|
| Health | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| Swagger UI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| OpenAPI JSON | [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) |
| Postman | Import `postman/Disaster-Platform.postman_collection.json` |

Migrations detail: [MIGRATIONS.md](./MIGRATIONS.md).

---

## Mock users

| Username | Password | Role | Can |
|----------|----------|------|-----|
| `admin` | `admin123` | admin | Create, update, **delete** |
| `contributor` | `contrib123` | contributor | Create and update only |

```http
POST /auth/token
Content-Type: application/json

{"username": "admin", "password": "admin123"}
```

Use the returned `access_token` as `Authorization: Bearer <token>` (or click **Authorize** in Swagger).

---

## Process flow

### End-to-end request path

```mermaid
flowchart TB
  subgraph Client
    HTTP[HTTP client / Swagger / Postman]
    WS[WebSocket client]
  end

  subgraph FastAPI
    Auth["/auth/token"]
    CRUD["/disasters CRUD"]
    Nearby["/disasters/:id/resources"]
    Reports["/disasters/:id/reports"]
    Hub["/ws/disasters"]
  end

  subgraph Services
    Loc[LocationService]
    Ds[DisasterService]
    Cache[CacheService]
    Social[ReportsService]
    RT[RealtimeHub]
  end

  subgraph External
    Groq[Groq llama-3.3-70b]
    Nom[Nominatim OSM]
    Probe[httpbin mock social probe]
  end

  PG[(PostgreSQL + PostGIS)]

  HTTP --> Auth
  HTTP --> CRUD
  HTTP --> Nearby
  HTTP --> Reports
  WS --> Hub

  Auth --> JWT[JWT + mock users]
  CRUD --> Loc
  Loc --> Groq
  Loc --> Nom
  CRUD --> Ds
  Ds --> PG
  CRUD --> RT
  RT --> Hub
  Nearby --> Ds
  Ds --> PG
  Reports --> Cache
  Cache --> PG
  Reports --> Social
  Social --> Probe
```

### 1. Authentication

```
POST /auth/token  { username, password }
        │
        ▼
  Look up MOCK_USERS
        │
   valid? ──no──► 401 Invalid credentials
        │ yes
        ▼
  JWT { sub, role, exp } signed with JWT_SECRET
        │
        ▼
  Return { access_token, token_type, role }
```

Protected routes call `HTTPBearer` → decode JWT → check role:

- `require_contributor_or_admin` — `POST` / `PATCH`
- `require_admin` — `DELETE`
- List / get / resources / reports are public (read-only)

### 2. Create a disaster (location resolution)

Example description: `"Heavy flooding has affected Manhattan, NYC."`

```
POST /disasters  + Bearer token (contributor or admin)
        │
        ▼
  Validate body (title ≥ 3, description ≥ 10, tags normalized)
        │
        ▼
  LocationService.resolve_from_description(description)
        │
        ├─ USE_MOCK_LLM=true or no Groq key
        │     └─ keyword / "in|at|near <place>" extract
        │
        └─ Groq llama-3.3-70b-versatile
              "Return ONLY JSON { location: 'City, Region' }"
              parse JSON ──fail──► mock extract
        │
        ▼
  Geocode the place name
        │
        ├─ USE_MOCK_GEOCODING=true
        │     └─ MOCK_GEOCODE map (Manhattan → 40.7831, -73.9712)
        │
        └─ Nominatim GET /search?q=...
              fail or empty ──► same mock map (fuzzy match)
        │
        ▼
  INSERT disasters
    geom = geography POINT(lng lat) SRID 4326  (null if unresolved)
        │
        ▼
  Broadcast WebSocket  { event: "disaster_created", data: {...} }
        │
        ▼
  201 + DisasterResponse (id, coords, tags, status, created_by, …)
```

`PATCH /disasters/:id` re-runs this location pipeline when `description` changes, then emits `disaster_updated`.  
`DELETE /disasters/:id` is admin-only and emits `disaster_deleted`.

Unresolved descriptions (no place name) still save the disaster; `latitude` / `longitude` are `null`.

### 3. Nearby resources (PostGIS)

```
GET /disasters/:id/resources?lat=40.7831&lng=-73.9712&radius=5
        │
        ▼
  404 if disaster missing
        │
        ▼
  SQL (meters = radius_km * 1000):

    SELECT resource, ST_Distance(geom, center) / 1000 AS distance_km
    FROM resources
    WHERE disaster_id = :id
      AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(lng, lat), 4326), radius_m)
    ORDER BY ST_Distance(...)
        │
        ▼
  JSON list: name, type, lat, lng, distance_km
```

Search is **database-side** on `geography(POINT, 4326)`. The app does not load every resource into memory. Seed data attaches five Manhattan resources (shelter, hospital, food, water, rescue) to the demo flood incident.

### 4. Community reports + cache

```
GET /disasters/:id/reports
        │
        ▼
  cache_key = "reports:{disaster_id}"
        │
        ▼
  SELECT external_cache WHERE key = ? AND expires_at > now()
        │
   hit? ──yes──► return reports with "source": "cache"
        │ no
        ▼
  ReportsService.fetch_reports()
        │
        ├─ HTTP GET https://httpbin.org/get   (proves external-call pattern)
        │     success ──► synthesize 3 citizen reports from location_name
        │     HTTP fail ──► 1 degraded system report (API still 200)
        │
        ▼
  INSERT/UPDATE external_cache  TTL = CACHE_TTL_SECONDS (default 300s)
        │
        ▼
  return reports with "source": "external"
```

This is the assignment cache contract: **request → cache → hit return / miss external → store → return**.

### 5. Real-time updates

```
Client ──WS──► GET /ws/disasters  (RealtimeHub accepts + stores socket)
                      │
  create / update / delete disaster
                      │
              broadcast JSON to all sockets
                      │
                      ▼
  { "event": "disaster_created" | "disaster_updated" | "disaster_deleted",
    "data": { ... } }
```

Demo listener (API must already be running):

```powershell
.\.venv\Scripts\python.exe -m scripts.ws_demo_client
```

Then create or update a disaster in Swagger / Postman and watch the event print in that terminal.

---

## Architecture

```
app/
  main.py                 FastAPI app, /health, routers
  config.py               .env + Neon URL normalization (asyncpg / Alembic)
  api/
    deps.py               DB session + JWT role guards
    routes/
      auth.py             POST /auth/token
      disasters.py        CRUD, resources, reports
      ws.py               WS /ws/disasters
  auth/
    users.py              Mock admin / contributor
    jwt.py                HS256 issue / verify
  schemas/                Pydantic request / response models
  db/
    models.py             Disaster, Resource, ExternalCacheEntry
    session.py            async SQLAlchemy engine
  services/
    location.py           Groq extract → Nominatim / mock geocode
    disasters.py          Persistence + ST_DWithin search
    reports.py            Mock social feed + failure fallback
    cache.py              PostgreSQL TTL cache
    realtime.py           In-memory WebSocket hub
alembic/versions/         Initial PostGIS schema
scripts/                  seed, WS demo, Windows setup
tests/                    unit + optional integration
```

---

## API summary

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | — |
| POST | `/auth/token` | — |
| POST | `/disasters` | contributor or admin |
| GET | `/disasters?tag=` | — |
| GET | `/disasters/{id}` | — |
| PATCH | `/disasters/{id}` | contributor or admin |
| DELETE | `/disasters/{id}` | admin only |
| GET | `/disasters/{id}/resources?lat&lng&radius` | — |
| GET | `/disasters/{id}/reports` | — |
| WS | `/ws/disasters` | — |

Errors: **401** missing/invalid JWT, **403** wrong role, **404** unknown disaster, **422** validation.

---

## Technical decisions

### Why PostgreSQL + PostGIS

Disasters and resources store locations as `geography(POINT, 4326)`. Radius search uses `ST_DWithin` (meters) and orders by `ST_Distance`. Geospatial work stays in the database (indexes, correct spheroid distance) instead of filtering points in Python.

### How location resolution works

1. **Groq** (`llama-3.3-70b-versatile`) extracts a place name as JSON.
2. **Nominatim** geocodes that name when `USE_MOCK_GEOCODING=false`.
3. **Fallback:** keyword map (Manhattan, New York, Mumbai, Delhi, Los Angeles) plus a simple `in|at|near` regex if the LLM or geocoder fails.

`app/config.py` rewrites Neon URLs for **asyncpg** (`ssl=require`, drops `channel_binding`) and for Alembic **psycopg3** (`sslmode=require`).

### How caching works

Community reports are stored in `external_cache` (`cache_key`, JSON `payload`, `expires_at`). Default TTL is 300 seconds. Cached rows are returned with `"source": "cache"`. No Redis process is required.

### How external failures are handled

| Dependency | On failure |
|------------|------------|
| Groq | Fall back to mock place extraction |
| Nominatim | Fall back to mock coordinates |
| Social probe (httpbin) | Return one degraded report; endpoint stays 200 |
| Unresolvable location | Disaster is still created without coordinates |

The API prefers **degraded success** over failing an incident create because a geocoder is down.

---

## Testing

Unit tests (no database, mocks forced in `tests/conftest.py`):

```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest -q
```

| File | Assignment coverage |
|------|---------------------|
| `tests/test_validation.py` | Validation / error scenario |
| `tests/test_location.py` | Business rule: Manhattan text → coordinates |
| `tests/test_auth.py` | Auth + role on JWT |
| `tests/test_reports_cache.py` | External integration + cache write |
| `tests/test_api_integration.py` | Full HTTP API (opt-in) |

Integration tests need a live PostGIS database:

```powershell
$env:RUN_INTEGRATION="1"
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest tests/test_api_integration.py -q
```

---

## Trade-offs

- JWT + two in-memory mock users — not production IAM.
- Reports are synthesized after an HTTP probe, not parsed from Twitter/X.
- PostgreSQL cache instead of Redis — simpler deploy, slightly higher read latency.
- WebSocket hub is in-process and unauthenticated (fine for a single-worker demo).
- Nominatim is not rate-limited (would queue / cache in production).
- Disaster list hydrates coordinates per row (fine at assignment scale).

---

## AI usage

| | |
|---|---|
| **Tool used** | Cursor |
| **Helped with** | FastAPI module layout, PostGIS query shape, tests, documentation |
| **Manual / reviewed** | Architecture, Groq + fallback chain, auth matrix, cache TTL in Postgres, seed data, Neon URL handling, trade-offs |

Reviewers should treat this as understood, owned code — especially `app/services/location.py`, `app/services/disasters.py` (`nearby_resources`), and the reports cache path in `app/api/routes/disasters.py`.
