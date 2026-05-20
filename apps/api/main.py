"""FastAPI application factory.

Entry points:
- `uvicorn apps.api.main:app` (development)
- `gunicorn -k uvicorn.workers.UvicornWorker apps.api.main:app` (production)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import calls, domains, health
from core.config import settings

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger("conviq.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Starting %s (env=%s, db=%s)",
        settings.app_name,
        settings.app_env,
        settings.database_url.split("@")[-1],  # don't log creds
    )
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Conversation intelligence platform: configurable-domain analysis "
            "with fine-tuned dialogue-act classification, RAG-grounded coaching, "
            "and full LLM observability."
        ),
        lifespan=lifespan,
    )

    # Phase 0: no auth yet, so wildcard origin is safe. When auth lands, set
    # allow_credentials=True and replace the wildcard with explicit origins —
    # browsers reject `*` + credentials per the CORS spec.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(domains.router)
    app.include_router(calls.router)

    return app


app = create_app()
