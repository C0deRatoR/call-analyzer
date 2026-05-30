# ConvIQ Project Overview

## What This Project Is

ConvIQ is a conversation intelligence platform. The goal is to let a user upload an audio conversation, choose a domain such as counseling, sales, or customer support, and receive a structured analysis of what happened in the call.

The project is currently a production-shaped rebuild of an older call analyzer prototype. The current system already has the main backend skeleton: FastAPI for the API, Celery for background work, Redis for queues and progress events, Postgres for persistence, Alembic for migrations, and domain-specific YAML configuration.

## Main User Flow

1. A user uploads an audio file through `POST /calls`.
2. The API validates the audio extension and selected domain.
3. The API saves the upload to the configured uploads directory.
4. A `Call` row is created in Postgres with status `queued`.
5. The API enqueues a Celery job named `conviq.run_pipeline`.
6. The worker processes the call through stage-shaped pipeline steps.
7. Progress events are published to Redis on `pipeline:{call_id}`.
8. The API exposes those events through `GET /calls/{id}/stream` as Server-Sent Events.
9. The worker writes final or failed status back to Postgres.
10. The user can fetch the call result with `GET /calls/{id}`.

At the moment, the worker pipeline is still a deterministic stub. It proves that upload, queueing, progress streaming, and persistence are wired correctly. Real transcription, diarization, and ML stages are planned next.

## Repository Layout

- `apps/api/`: FastAPI app, routers, and API response schemas.
- `apps/worker/`: Celery app and worker task orchestration.
- `core/`: shared settings, database models/sessions, domain loading, LLM schemas, and pipeline contracts.
- `pipeline/`: ML and analysis modules such as transcription, diarization, emotion, sentiment, keywords, prompts, LLM calls, and reports.
- `domains/`: YAML domain definitions for counseling, sales, and customer support.
- `infra/`: Docker, Docker Compose, and Alembic migration setup.
- `tests/`: pytest tests for prompt rendering, schemas, and pipeline contracts.
- `web/`: static frontend assets.
- `models/`, `knowledge_bases/`, `eval/`, `notebooks/`: planned areas for model training, RAG content, evaluation, and experiments.

## API Layer

The FastAPI app starts from `apps/api/main.py`. It registers routers for health checks, domains, and calls.

Important endpoints:

- `GET /health`: confirms the service is running.
- `GET /domains`: lists available domain YAML configs.
- `GET /domains/{domain_id}`: returns a full domain config.
- `POST /calls`: uploads audio and queues background processing.
- `GET /calls/{id}`: returns status and available results.
- `GET /calls/{id}/stream`: streams pipeline progress over SSE.
- `POST /calls/{id}/export`: reserved for PDF export; currently returns `501`.

The API uses async SQLAlchemy sessions through `core/db/session.py`.

## Worker And Pipeline

The Celery app lives in `apps/worker/celery_app.py`. It registers the pipeline task from `apps/worker/tasks/pipeline.py`.

The current worker stages are:

- `transcribe`
- `diarize`
- `classify`
- `emotion`
- `keywords`
- `summarize`

These stages are placeholders, but their names and progress event format are now centralized in `core/pipeline.py`. This makes Phase 2 easier: each stub body can be replaced by real logic without changing the API/worker contract.

Celery uses the sync SQLAlchemy session (`SyncSessionLocal`) because worker tasks are synchronous. The API uses async sessions because FastAPI request handlers are async.

## Domain System

The project avoids hardcoded “counselor/student” behavior by using YAML domain configs in `domains/`.

Each domain defines:

- display name and description
- primary and secondary speaker labels
- prompt templates
- rubric dimensions
- RAG namespace
- analytics focus

The loader in `core/domains/loader.py` validates these YAML files with Pydantic schemas. Pipeline prompts are rendered through `pipeline/prompts.py`.

## Data Model

The main tables are defined in `core/db/models.py`:

- `calls`: one uploaded audio file and its aggregate output.
- `turns`: diarized speaker turns with emotion, sentiment, dialogue act, and embedding fields.
- `analytics`: per-call metrics such as talk time and dialogue-act counts.
- `llm_traces`: planned link between internal LLM calls and Langfuse traces.

The database is migrated through Alembic under `infra/alembic/`.

## Current State

Completed:

- FastAPI app skeleton.
- Celery worker skeleton.
- Redis-backed progress event contract.
- SSE endpoint wired to Redis pub/sub.
- Postgres models and Alembic migration.
- Domain YAML loader and three starter domains.
- Structured Gemini response schemas.
- Prompt rendering tests.
- Pipeline contract tests.

Not yet complete:

- Real Whisper transcription in the worker.
- Real pyannote diarization.
- Fine-tuned DistilBERT dialogue-act classifier.
- RAG retrieval and citation validation.
- Evaluation harness for WER, DER, F1, groundedness, latency, and cost.
- Langfuse observability.
- Production auth, PII handling, retries, and retention controls.

## Next Technical Step

The next practical step is Phase 2: replace the stage-shaped worker stub with real transcription and diarization while preserving the existing API, Redis, SSE, and Postgres contracts.
