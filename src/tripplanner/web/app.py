from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tripplanner.core.config import get_settings
from tripplanner.db.crud import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.db_factory = await init_db(settings.database_url)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TripPlanner API",
        version="0.1.0",
        lifespan=lifespan,
    )

    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from tripplanner.web.routers import chat, plans, trips

    app.include_router(trips.router, prefix="/api")
    app.include_router(plans.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")

    return app
