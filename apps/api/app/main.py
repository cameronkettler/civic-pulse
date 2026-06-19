from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.routes import router
from packages.db import create_schema, session_scope
from packages.db.models import UserInterest
from packages.shared.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_schema()
    seed_interests()
    yield


def seed_interests() -> None:
    settings = get_settings()
    with session_scope() as db:
        existing = {row.topic for row in db.query(UserInterest).all()}
        for topic in settings.topics:
            if topic not in existing:
                db.add(UserInterest(topic=topic, enabled=True))


app = FastAPI(
    title="Civic Pulse API",
    description="Agentic civic intelligence for federal legislation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "civic-pulse-api"}
