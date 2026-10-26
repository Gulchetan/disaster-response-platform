# Database migrations (Alembic + Neon PostgreSQL)

Schema changes are managed with **Alembic**. The FastAPI app does **not** call `create_all` on startup.

## 1. Neon setup

1. Create a project at [Neon](https://neon.tech).
2. In the Neon console, enable **PostGIS** for your database (required for `geom` columns and radius search).
3. Copy the connection string (pooled or direct).

## 2. Put the URL in `.env`

You can paste Neon’s URL as-is; the app normalizes it for **asyncpg**:

```env
# Example — use your real host, user, password, and database name
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-xxxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

This becomes `postgresql+asyncpg://...?ssl=require` at runtime.

For migrations, Alembic uses **psycopg3** (`postgresql+psycopg://...?sslmode=require`).

## 3. Install dependencies

```powershell
cd disaster-platform
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH="."
```

## 4. Run migrations

```powershell
alembic upgrade head
```

Check current revision:

```powershell
alembic current
```

Create a new migration after model changes (autogenerate):

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 5. Seed sample data (optional)

```powershell
python -m scripts.seed_data
```

## 6. Start API

```powershell
uvicorn app.main:app --reload
```

## Troubleshooting

| Issue | Fix |
|--------|-----|
| `extension "postgis" is not available` | Enable PostGIS in Neon dashboard for that branch/database |
| SSL errors with asyncpg | Ensure `sslmode=require` in `.env` (auto-converted to `ssl=require`) |
| `type "disaster_status" already exists` | DB was partially created; use a fresh Neon branch or run `alembic downgrade base` then `upgrade head` |
| Pooled vs direct | Migrations work with **pooled** Neon URLs; use the same URL Neon gives you |

## Migration files

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic config |
| `alembic/env.py` | Loads `DATABASE_URL` from `.env` via `app.config` |
| `alembic/versions/20260326_0001_initial_schema.py` | PostGIS + tables + enums |
