# ConvIQ Project Guide

## Purpose

ConvIQ is a conversation intelligence backend. A user uploads an audio conversation, ConvIQ auto-selects a domain such as counseling, sales, or customer support, and receives structured analysis for that call. The project is being rebuilt from an older prototype into a production-shaped AI/ML system with async processing, configurable domains, typed outputs, and measurable quality.

Current status: the FastAPI/Celery/Postgres/Redis scaffold is in place, domain YAML loading works, structured LLM schemas exist, Redis-backed SSE progress streaming is wired, and the clean frontend has been manually tested against the current backend contract. The Phase 2 worker now runs Whisper transcription, pyannote.audio diarization when `HF_TOKEN` has access to the required pyannote model gates, persisted turn rows, and Gemini 2.5 Flash summary/sentiment enrichment. Dialogue-act classification, RAG, evals, and observability are future phases.

Latest verified baseline: manual frontend testing has been completed against the FastAPI/SSE contract. A local backend smoke run with Postgres, Redis, FastAPI, Celery, Whisper `tiny`, pyannote.audio, Gemini 2.5 Flash, and `HF_TOKEN` access for `pyannote/speaker-diarization-3.1`, `pyannote/segmentation-3.0`, and `pyannote/speaker-diarization-community-1` completed successfully through upload -> transcription -> pyannote diarization -> turn persistence -> summary -> sentiment -> persisted completed call. The verified sample produced 2 persisted turns, summary, mixed sentiment, and no pipeline warnings. Without model access, local runs intentionally fall back to the pause heuristic and persist turns with a warning.

## How The Current System Works

1. `POST /calls` receives an audio file and optional `domain_id` form field.
2. The API validates the file extension and validates `domain_id` unless it is `auto`.
3. The upload is saved under the configured uploads directory.
4. A `Call` row is created in Postgres with status `queued`.
5. The API enqueues `conviq.run_pipeline` in Celery.
6. The worker runs fixed stages: `transcribe`, `diarize`, `summarize`, `sentiment`.
7. When `domain_id=auto`, the worker infers the domain after transcription, persists the selected `domain_id`, and uses that domain for speaker labels and LLM prompts.
8. Each stage publishes progress to Redis on `pipeline:{call_id}`.
9. `GET /calls/{id}/stream` relays those Redis messages as SSE.
10. The worker writes final status/output, diarized turns, or failure details to Postgres.
11. `GET /calls/{id}` returns persisted call status, results, and turn rows.

## Repository Structure

- `apps/api/`: FastAPI app, routers, and API response schemas.
- `apps/worker/`: Celery app and pipeline task orchestration.
- `core/`: shared settings, DB models/sessions, domain loader/auto-inference, LLM schemas, and pipeline contracts.
- `domains/`: YAML configs for counseling, sales, and customer support.
- `infra/`: Docker Compose, Dockerfile, Alembic environment, and migrations.
- `pipeline/`: current analysis modules and prompt/LLM helpers.
- `tests/`: pytest coverage for prompt rendering and pipeline contracts.
- `docs/`: this guide.
- `frontend/`: clean manual-testing frontend targeting the current FastAPI/SSE contract.

Empty future placeholder directories and the stale static frontend were removed. Future phases should recreate `models/`, `knowledge_bases/`, or `eval/` only when they contain real artifacts.

## Important Files

- `pyproject.toml`: project metadata, dependencies, test/lint/type-check config, and build package list.
- `alembic.ini`: Alembic entry config; points migration commands at `infra/alembic`.
- `apps/__init__.py`, `core/__init__.py`, etc.: explicit Python package markers. They are not replaced by `pyproject.toml`; they keep imports such as `apps.api.main` and Celery task discovery stable.
- `core/pipeline.py`: shared API/worker progress contract.
- `apps/worker/tasks/pipeline.py`: current stage-shaped worker pipeline.
- `apps/api/routers/calls.py`: upload, status, SSE stream, and future export endpoints.
- `pipeline/diarization.py`: pyannote diarization alignment plus pause-heuristic fallback.
- `frontend/app.js`: manual-testing UI wired to `POST /calls`, `GET /calls/{id}/stream`, and `GET /calls/{id}`.

## Development Commands

Use conda for local environments.

```bash
conda create -n conviq python=3.12
conda activate conviq
python -m pip install -e ".[dev,training,eval]"
```

Run locally:

```bash
./scripts/dev-local.sh
```

This machine-local launcher starts Docker Postgres/Redis, runs migrations through
the Miniforge `ai` env, starts FastAPI, starts the Celery worker, serves the
frontend, and opens the browser. Press `Ctrl+C` in that terminal to stop
everything.

Manual equivalent:

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

## Local Handoff Notes

Preferred local workflow for this machine:

- Use the Miniforge/conda environment for Python commands. The tested environment is `ai`.
- One-command local startup:

```bash
./scripts/dev-local.sh
```

- Start only Postgres and Redis with Docker when running the API and worker directly:

```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
```

- Run migrations before manual backend testing:

```bash
PYTHONPATH=. /home/k0de/miniforge3/bin/conda run -n ai alembic upgrade head
```

- Run the API locally:

```bash
PYTHONPATH=. /home/k0de/miniforge3/envs/ai/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --log-level info
```

- Run the worker locally:

```bash
PYTHONPATH=. /home/k0de/miniforge3/envs/ai/bin/celery -A apps.worker.celery_app:celery_app worker --loglevel=info --concurrency=1
```

- Run quality checks through conda:

```bash
PYTHONPATH=. /home/k0de/miniforge3/bin/conda run -n ai pytest
PYTHONPATH=. /home/k0de/miniforge3/bin/conda run -n ai ruff check .
PYTHONPATH=. /home/k0de/miniforge3/bin/conda run -n ai mypy apps core pipeline
```

Next-session prompt: continue from the latest `dev` branch. Manual frontend testing is done, pyannote-backed validation works after `HF_TOKEN` access was configured, and the UI now submits `domain_id=auto`. Continue toward dialogue-act labels and per-speaker analytics after verifying the latest manual frontend run.

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
- `domain_id` form field on `POST /calls`, now optional for clients that want automatic domain selection.

### Phase 2: Real Diarization + Async Pipeline - In Progress

- Replace stub stage bodies with real pipeline implementations. First slice complete and locally verified: Whisper transcription plus Gemini 2.5 Flash summary/sentiment.
- Add Whisper transcription from uploaded audio. Complete for the first worker slice.
- Build and manually validate the clean frontend against the FastAPI/SSE contract. Complete.
- Add pyannote diarization using `HF_TOKEN`. Complete and locally verified after Hugging Face access was accepted for `pyannote/speaker-diarization-3.1`, `pyannote/segmentation-3.0`, and `pyannote/speaker-diarization-community-1`; the pause-heuristic fallback remains for missing model access or runtime failures.
- Persist stage outputs to Postgres. Complete for call-level transcript/summary/sentiment and turn rows.
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

- Expand the frontend beyond the manual-testing workflow after the backend contract is stable.
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

The old static frontend was removed because it called legacy Flask endpoints. The current clean frontend targets the FastAPI contract:

- `POST /calls`
- `GET /calls/{id}/stream`
- `GET /calls/{id}`

The UI should open the SSE stream immediately after upload, show stage progress from event payloads, and fetch final results only after a `complete` event.

Near-term frontend goal: complete the clean modern UI for manual Phase 2 testing first. This is done for automatic domain selection, audio upload, live pipeline progress, and final transcript/summary/sentiment display. The frontend now consumes persisted backend turn rows when present; richer analytics should remain placeholder-free until the backend starts persisting those outputs.

## Future Hosting Direction

The intended hosted shape is split by responsibility:

- Vercel for the future clean modern frontend.
- A container platform such as Render, Railway, Fly.io, or a VPS for the FastAPI API.
- A separate worker service on the same container platform for Celery.
- Supabase Postgres with pgvector for the main database and later vector search.
- Upstash Redis, Render Redis, Railway Redis, or another managed Redis provider for Celery broker/result storage and progress pub/sub.
- Supabase Storage or Cloudflare R2 for uploaded audio files once the app leaves local development.

Do not try to run the whole system on Vercel. The FastAPI API and especially the Celery worker need long-running Python/ML execution for Whisper, diarization, and model inference. Vercel is a good frontend host, but it is not the right primary runtime for the async ML worker.

The current local implementation stores uploads on local disk. That is fine during Phase 2 development, but production deployment should move uploaded audio to object storage so the API and worker do not depend on sharing the same filesystem.

## What Not To Reintroduce Prematurely

- Empty placeholder folders.
- A frontend that targets old `/process_audio` or `/export_pdf` routes.
- Lockfiles or local virtual environments outside the agreed conda workflow.
- Active Docker services for RAG/observability before code uses them.
- Long-lived docs that duplicate this guide.
