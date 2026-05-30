# ConvIQ Project Guide

## Purpose

ConvIQ is a conversation intelligence backend. A user uploads an audio conversation, chooses a domain such as counseling, sales, or customer support, and receives structured analysis for that call. The project is being rebuilt from an older prototype into a production-shaped AI/ML system with async processing, configurable domains, typed outputs, and measurable quality.

Current status: the FastAPI/Celery/Postgres/Redis scaffold is in place, domain YAML loading works, structured LLM schemas exist, and Redis-backed SSE progress streaming is wired. The worker pipeline is still a deterministic stage-shaped stub; real transcription, diarization, model inference, RAG, evals, and observability are future phases.

## How The Current System Works

1. `POST /calls` receives an audio file and `domain_id`.
2. The API validates the file extension and domain YAML.
3. The upload is saved under the configured uploads directory.
4. A `Call` row is created in Postgres with status `queued`.
5. The API enqueues `conviq.run_pipeline` in Celery.
6. The worker runs fixed stages: `transcribe`, `diarize`, `classify`, `emotion`, `keywords`, `summarize`.
7. Each stage publishes progress to Redis on `pipeline:{call_id}`.
8. `GET /calls/{id}/stream` relays those Redis messages as SSE.
9. The worker writes final status/output or failure details to Postgres.
10. `GET /calls/{id}` returns persisted call status and results.

## Repository Structure

- `apps/api/`: FastAPI app, routers, and API response schemas.
- `apps/worker/`: Celery app and pipeline task orchestration.
- `core/`: shared settings, DB models/sessions, domain loader, LLM schemas, and pipeline contracts.
- `domains/`: YAML configs for counseling, sales, and customer support.
- `infra/`: Docker Compose, Dockerfile, Alembic environment, and migrations.
- `pipeline/`: current analysis modules and prompt/LLM helpers.
- `tests/`: pytest coverage for prompt rendering and pipeline contracts.
- `docs/`: this guide.

Empty future placeholder directories and the stale static frontend were removed. Future phases should recreate `models/`, `knowledge_bases/`, `eval/`, or frontend folders only when they contain real artifacts.

## Important Files

- `pyproject.toml`: project metadata, dependencies, test/lint/type-check config, and build package list.
- `alembic.ini`: Alembic entry config; points migration commands at `infra/alembic`.
- `apps/__init__.py`, `core/__init__.py`, etc.: explicit Python package markers. They are not replaced by `pyproject.toml`; they keep imports such as `apps.api.main` and Celery task discovery stable.
- `core/pipeline.py`: shared API/worker progress contract.
- `apps/worker/tasks/pipeline.py`: current stage-shaped worker stub.
- `apps/api/routers/calls.py`: upload, status, SSE stream, and future export endpoints.

## Development Commands

Use conda for local environments.

```bash
conda create -n conviq python=3.12
conda activate conviq
python -m pip install -e ".[dev,training,eval]"
```

Run locally:

```bash
alembic upgrade head
uvicorn apps.api.main:app --reload
celery -A apps.worker.celery_app:celery_app worker --loglevel=info
```

Run checks:

```bash
pytest
ruff check .
ruff format .
mypy apps core pipeline
```

Run the Docker stack:

```bash
docker compose -f infra/docker-compose.yml up -d --build
docker compose -f infra/docker-compose.yml logs -f api worker
docker compose -f infra/docker-compose.yml down
```

## Coding Guidelines

Use Ruff formatting with 100-character line length and Python 3.11+ syntax. Use `snake_case` for modules, functions, variables, and YAML IDs; use `PascalCase` for classes and Pydantic models. Keep domain-specific labels and prompt behavior in `domains/*.yaml` instead of hardcoding counseling, sales, or support assumptions in pipeline code.

Tests should live in `tests/` and be named `test_*.py`. Prefer offline tests for schema, prompt, domain, and pipeline-contract behavior. Do not require external LLM, Hugging Face, or audio model calls in the default test suite.

Commit messages follow the existing conventional style: `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`, `chore: ...`, `refactor: ...`.

## Target Architecture

The final system is intended to be:

- FastAPI API gateway for uploads, status, streams, domains, and analytics.
- Celery worker for staged post-call analysis.
- Redis for Celery broker/result backend and SSE progress pub/sub.
- Postgres + pgvector for call metadata, turns, analytics, embeddings, and trace links.
- Whisper for transcription.
- pyannote.audio for real speaker diarization.
- Fine-tuned DistilBERT for dialogue-act classification.
- Domain-specific RAG with citations for grounded coaching.
- LLM structured outputs for summaries, sentiment, and suggestions.
- Observability for prompts, latency, tokens, cost, and failures.

## Roadmap

### Phase 0: Foundations - Complete

- Repo restructure.
- `pyproject.toml` package metadata.
- FastAPI skeleton with health, calls, and domains routes.
- Docker Compose with Postgres and Redis.
- Alembic migration for `calls`, `turns`, `analytics`, and `llm_traces`.
- Existing pipeline modules moved under `pipeline/`.

### Phase 1: Domain System + Structured Outputs - Complete

- YAML domain configs in `domains/`.
- Pydantic validation for domain configs.
- Three starter domains: counseling, sales, customer support.
- Structured LLM response schemas.
- Domain-aware prompt renderer.
- `domain_id` form field on `POST /calls`.

### Phase 2: Real Diarization + Async Pipeline - Next

- Replace stub stage bodies with real pipeline implementations.
- Add Whisper transcription from uploaded audio.
- Add pyannote diarization using `HF_TOKEN`.
- Persist stage outputs to Postgres.
- Keep Redis progress events and SSE contract stable.
- Add retry/resume-friendly boundaries around stages.

### Phase 3: Custom Dialogue-Act Model

- Train DistilBERT on DailyDialog dialogue-act labels.
- Compare against zero-shot LLM baseline.
- Add model card and reproducible training/eval scripts.
- Add `pipeline/dialogue_act.py`.
- Use dialogue-act labels in per-speaker analytics.

### Phase 4: RAG + Citations

- Create real domain knowledge bases.
- Add chunking, embedding, indexing, and retrieval.
- Require suggestions to cite retrieved source IDs.
- Add citation metadata to API responses.

### Phase 5: Evaluation Harness

- Add golden audio samples and annotations.
- Track WER, DER, dialogue-act F1, groundedness, latency, and cost.
- Add regression tests or CI jobs for prompt/model/pipeline changes.
- Generate benchmark artifacts for README.

### Phase 6: Observability + Analytics

- Add LLM and pipeline traces.
- Track latency, tokens, cost, and stage failures.
- Add failure taxonomy: hallucination, citation miss, speaker mix-up, latency breach.
- Add analytics endpoints for multi-call comparison.

### Phase 7: Product Polish

- Reintroduce a frontend only after the backend contract is stable.
- Add screenshots, benchmark table, demo video, and final README polish.

## Strategic Transformation Direction

The long-term product direction is a real-time + async conversation QA copilot:

- Keep the async post-call pipeline for deep analysis.
- Add a real-time lane later for browser voice ingestion and live assist.
- Use evidence-first generation: timestamped call spans, retrieved source IDs, and confidence.
- Suppress suggestions when evidence is insufficient.
- Make evals and observability first-class rather than one-off reports.
- Add production hardening later: auth, tenant isolation, PII redaction, retries, dead-letter queues, retention/deletion controls, and SLOs.

## Frontend Direction

The old static frontend was removed because it called legacy Flask endpoints. A future frontend should target the current FastAPI contract:

- `POST /calls`
- `GET /calls/{id}/stream`
- `GET /calls/{id}`
- `GET /domains`

The UI should open the SSE stream immediately after upload, show stage progress from event payloads, and fetch final results only after a `complete` event.

## What Not To Reintroduce Prematurely

- Empty placeholder folders.
- A frontend that targets old `/process_audio` or `/export_pdf` routes.
- Lockfiles or local virtual environments outside the agreed conda workflow.
- Active Docker services for RAG/observability before code uses them.
- Long-lived docs that duplicate this guide.
