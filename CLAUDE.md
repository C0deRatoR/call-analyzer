# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Project status:** Mid-rebuild from a Flask prototype into a production AI/ML system called **ConvIQ**. The phased plan is in [`PLAN.md`](PLAN.md). Phases 0 and 1 are complete: the FastAPI / Celery / Postgres / Redis / Chroma scaffold is in place, the configurable domain system is live (YAML loader + three domain configs + prompt renderer), and Gemini structured outputs are wired. The Celery pipeline worker is still a stub — Phase 2 will replace it with real diarization and ML stages.

## Commands

```bash
# ---- Local dev ----
uv sync --all-extras                # install main + dev + training + eval deps
uv run alembic upgrade head         # apply migrations
uv run uvicorn apps.api.main:app --reload    # API (terminal 1)
uv run celery -A apps.worker.celery_app:celery_app worker --loglevel=info   # worker (terminal 2)

# ---- Docker (full stack) ----
docker compose -f infra/docker-compose.yml up -d --build
docker compose -f infra/docker-compose.yml logs -f api worker
docker compose -f infra/docker-compose.yml down

# ---- Tests / lint / types ----
uv run pytest
uv run pytest tests/test_domains.py -v       # single file
uv run ruff check .
uv run ruff format .
uv run mypy apps core pipeline

# ---- Migrations ----
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

**Required env vars:** `GEMINI_API_KEY` (LLM), `HF_TOKEN` (pyannote license + model uploads). Copy `.env.example` to `.env` and fill in. See the full list in [`core/config.py`](core/config.py).

**System dependency:** `ffmpeg` is required by openai-whisper. Already installed in the Docker images.

---

## Repo layout

```
apps/
├── api/         FastAPI app (entry: apps.api.main:app)
│   ├── main.py
│   ├── routers/         calls, domains, health
│   └── schemas.py
└── worker/      Celery worker
    ├── celery_app.py
    └── tasks/pipeline.py    (stage-shaped stub; real stage bodies land Phase 2)

core/            Shared library imported by both apps
├── config.py    pydantic-settings (env vars, paths)
├── db/          SQLAlchemy models + async session factory
└── domains/     YAML loader + Pydantic schemas

pipeline/        ML pipeline modules (migrated from legacy; being wired into the Celery worker)
├── transcription.py    Whisper wrapper
├── diarization.py      pause-heuristic (replaced by pyannote in Phase 2)
├── emotion.py          HF emotion classifier
├── sentiment.py        VADER sentiment + per-speaker analytics
├── keywords.py         KeyBERT keyword extraction
├── llm.py              Gemini structured-output client (updated Phase 1)
├── prompts.py          domain prompt renderer (new Phase 1)
└── report.py           PDF report generator

domains/         YAML configs — one file per use case (counseling, sales, customer_support)
knowledge_bases/ Source docs for per-domain RAG (filled in Phase 4)
models/          Custom-trained model artifacts (Phase 3: dialogue_act DistilBERT)
eval/            Golden audio + metric scripts + results (Phase 5)
infra/           docker-compose, Dockerfiles, alembic
notebooks/       Training + analysis notebooks
tests/
web/             Frontend (untouched in Phase 0; new one comes from claude design)
```

## Architecture

**Two processes, one codebase:**

- `apps/api` (FastAPI) accepts uploads, persists `Call` rows to Postgres, enqueues a Celery job, and exposes an SSE stream that relays progress events.
- `apps/worker` (Celery) consumes jobs, runs the stage-shaped pipeline, publishes progress to a Redis pub/sub channel `pipeline:{call_id}`, and writes results back to Postgres.

Both processes import `apps.worker.tasks.pipeline.run_pipeline` so the task name is registered everywhere.

**Data flow:**

```
POST /calls         → save upload, create Call row, enqueue run_pipeline.delay(call_id)
GET /calls/{id}/stream → subscribe to Redis channel pipeline:{call_id}, relay as SSE
GET /calls/{id}     → read full Call + turns + analytics from Postgres
```

**Configurable domain system:** every analysis is parameterized by a `domain_id` (form field on upload). The pipeline loads `domains/<domain_id>.yaml` and uses its prompts, rubric, speaker labels, RAG namespace, and analytics focus. This lets the same backend serve counseling / sales / support / custom use cases.

**Custom model (Phase 3):** DistilBERT fine-tuned on DailyDialog for dialogue-act classification (Question / Statement / Acknowledgment / Suggestion). Each turn gets a label which powers the per-domain analytics (question ratio, advice ratio, etc.).

**RAG (Phase 4):** per-domain Chroma collection. Suggestion prompts include retrieved excerpts and structured-output schemas force the LLM to cite source IDs.

**Observability (Phase 6):** Every LLM call wrapped by Langfuse `@observe` decorator. Tokens, latency, and cost are written to the `llm_traces` table.

### Key design details

- **Pipeline stub:** `apps/worker/tasks/pipeline.py` walks deterministic stage names with `time.sleep`, publishes Redis progress events, and writes placeholder output. End-to-end flow (upload → Redis → SSE → status query) works; real ML doesn't run yet. Phase 2 replaces the stub stage bodies with real Whisper + pyannote + the full stage chain.
- **Model caching:** Whisper / HuggingFace pipeline / KeyBERT models are module-level globals in `pipeline/*.py`. First request is slow.
- **Embedding dim:** pgvector column `Turn.embedding` is hard-coded to 384 (matches `sentence-transformers/all-MiniLM-L6-v2`). Change `Settings.embedding_dim` + run a migration if switching models.
- **API + Celery DB sessions:** FastAPI uses the async SQLAlchemy session. Celery tasks use `SyncSessionLocal` with psycopg2 so worker tasks do not reuse async connection pools across event loops.
- **Migrations:** the API container's entrypoint (`infra/entrypoint-api.sh`) runs `alembic upgrade head` before launching gunicorn, so schema is always current.
- **Why no global counseling/student bias:** the legacy code hardcoded those labels. The new pipeline pulls speaker labels from `DomainConfig.speakers` per call.

## What's where (handy index)

- API entry: `apps/api/main.py`
- Celery entry: `apps/worker/celery_app.py`
- Pipeline stub (Phase 2 target): `apps/worker/tasks/pipeline.py`
- Settings: `core/config.py`
- DB models: `core/db/models.py`
- Domain loader: `core/domains/loader.py`
- Domain configs: `domains/*.yaml`
- Initial migration: `infra/alembic/versions/2026_05_19_0001-0001_initial_schema.py`
- Compose stack: `infra/docker-compose.yml`
- Frontend brief (for separate claude design work): `DESIGN_BRIEF.md`
