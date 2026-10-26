from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, disasters, ws
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations (see alembic/ and MIGRATIONS.md).
    yield
    await engine.dispose()


app = FastAPI(
    title="Disaster Response Coordination Platform",
    description="Backend API for disaster incidents, resources, reports, and real-time updates.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(disasters.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
