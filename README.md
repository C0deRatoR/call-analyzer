<div align="center">

# ConvIQ

**Conversation intelligence platform — configurable domain, fine-tuned dialogue-act classification, RAG-grounded coaching, async pipeline, full LLM observability.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-worker-37814A.svg?logo=celery)](https://docs.celeryq.dev/)
[![Postgres + pgvector](https://img.shields.io/badge/Postgres-pgvector-336791.svg?logo=postgresql)](https://github.com/pgvector/pgvector)
[![Whisper](https://img.shields.io/badge/Audio-OpenAI_Whisper-brightgreen.svg)](https://github.com/openai/whisper)
[![pyannote.audio](https://img.shields.io/badge/Diarization-pyannote.audio-orange.svg)](https://github.com/pyannote/pyannote-audio)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.0-yellow.svg)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)

</div>

> Upload any audio conversation, pick a domain (counseling, sales, customer support, or your own), and get a complete analysis: real speaker diarization, turn-level emotion + dialogue-act labels from a custom-trained classifier, per-speaker analytics, and RAG-grounded coaching suggestions with citations — all surfaced live over a streaming async pipeline.

> [!IMPORTANT]
> **Status:** Active rebuild from a Flask prototype into a production-shaped AI/ML system. See [`docs/PLAN.md`](docs/PLAN.md) for the phased roadmap. Phases 0 and 1 are complete (scaffold, domain system, structured Gemini outputs). Phase 2 (real diarization + async pipeline) is next.

---

## Why this project

It's easy to ship a portfolio project that wraps a few AI APIs. This one is deliberately built to demonstrate the skills a hiring AI/ML engineer actually looks for:

- **A custom-trained model**, not just API calls — fine-tuned DistilBERT classifier (Phase 3) with documented training, eval, and HF Hub release.
- **An evaluation framework** — golden audio set with WER, DER, F1, and LLM-as-judge metrics, run as part of the regression suite.
- **Production pipelining** — FastAPI front, Celery workers behind Redis, real-time progress via Server-Sent Events.
- **Grounded generation** — planned RAG over per-domain knowledge bases with citation IDs in every suggestion.
- **Full observability** — planned LLM tracing with token, latency, and cost tracking.
- **Configurability** — domains are YAML files. Add a use case by dropping in a config; no code changes needed.

---

## Benchmarks

> Tracked as the project lands each phase. Phase 5 will add the eval artifacts that regenerate this table.

| Metric | Baseline | ConvIQ | Δ |
|---|---:|---:|---:|
| Dialogue-act macro-F1 (DailyDialog test split) | _zero-shot Gemini: TBD_ | _trained model: TBD_ | TBD |
| Word Error Rate (WER), 15-sample golden set | _Whisper base: TBD_ | _Whisper small: TBD_ | TBD |
| Diarization Error Rate (DER) | _pause-heuristic: TBD_ | _pyannote.audio: TBD_ | TBD |
| End-to-end latency, 10-min audio | _legacy sync: TBD_ | _async pipeline: TBD_ | TBD |
| Cost per call (USD) | _all-Gemini: TBD_ | _routed: TBD_ | TBD |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Frontend (separate)                                                │
│            ─── HTTP + SSE ───                                       │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│  FastAPI                                                            │
│   • POST /calls         upload audio, enqueue, return call_id       │
│   • GET  /calls/{id}    full result + diarized turns + analytics    │
│   • GET  /calls/{id}/stream   SSE pipeline progress                 │
│   • POST /calls/{id}/export   planned report export                 │
│   • GET  /domains       list configurable domains                   │
└────────────────────────────────────────────────────────────────────┘
        │                                  │
        ▼ Redis (queue + pub/sub)          ▼ Postgres + pgvector
┌──────────────────────────────────────────┐
│  Celery worker — per-stage pipeline:     │
│   1. Whisper transcription                │
│   2. pyannote.audio diarization           │
│   3. Custom DistilBERT dialogue-act       │
│   4. HF emotion classifier                │
│   5. VADER + per-speaker analytics        │
│   6. KeyBERT keywords                     │
│   7. RAG retrieval (planned)              │
│   8. Gemini summary + grounded suggestions│
│      (structured outputs, citations)      │
└──────────────────────────────────────────┘
        │                                  │
        ▼ planned tracing                   ▼ planned per-domain KBs
```

---

## Configurable Domains

Each domain is a YAML file under [`domains/`](domains/). Shipped out of the box:

- `counseling` — Counselor + Student
- `sales` — Salesperson + Prospect
- `customer_support` — Agent + Customer

A domain config defines speaker labels, prompt templates, the per-domain rubric (rated by LLM-as-judge), the RAG namespace, and the analytics dimensions surfaced in the dashboard. Drop a new YAML into `domains/` and the system picks it up — no code changes needed.

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- A Google Gemini API key — [get one](https://aistudio.google.com/apikey)
- A HuggingFace account + token, with the `pyannote/speaker-diarization-3.1` license accepted — [link](https://huggingface.co/pyannote/speaker-diarization-3.1)

### Run

```bash
# 1. Configure
cp .env.example .env
# Fill in GEMINI_API_KEY and HF_TOKEN

# 2. Launch the full stack
docker compose -f infra/docker-compose.yml up -d --build

# 3. Open the API docs
open http://localhost:8000/docs
```

The API will be available at `http://localhost:8000`.

> **First launch budget:** ~20–40 min on a good connection. Docker has to pull Postgres/pgvector + Redis, then build the API/worker images, which install large ML wheels (torch, transformers, pyannote.audio, openai-whisper). Once everything is up, the first real ML call also downloads model weights — that hit is per worker, not per call. Subsequent restarts use cached layers and start in seconds.

### Local development (without Docker)

You need Postgres (with pgvector), Redis, and Python 3.12 locally.

```bash
# Create and activate a conda environment
conda create -n conviq python=3.12
conda activate conviq

# Install all deps inside the conda environment
python -m pip install -e ".[dev,training,eval]"

# Apply migrations
alembic upgrade head

# Terminal 1 — API
uvicorn apps.api.main:app --reload

# Terminal 2 — Celery worker
celery -A apps.worker.celery_app:celery_app worker --loglevel=info
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| API | FastAPI · Pydantic v2 · gunicorn + uvicorn workers · SSE-Starlette |
| Queue | Celery · Redis (broker + pub/sub) |
| Storage | Postgres 16 + pgvector |
| Audio ML | OpenAI Whisper · pyannote.audio · HuggingFace transformers · sentence-transformers |
| NLP | KeyBERT · VADER · fine-tuned DistilBERT _(Phase 3)_ |
| LLM | Google Gemini 2.0 with structured outputs |
| Observability | Planned LLM tracing |
| Reporting | Planned export endpoint |
| DX | conda · pip · Ruff · mypy · pytest · Alembic · Docker Compose |

---

## Roadmap

See [`docs/PLAN.md`](docs/PLAN.md) for the full phased plan. Quick view:

- [x] **Phase 0** — Foundations (FastAPI/Celery/Postgres/Redis scaffold, repo restructure, Alembic migrations)
- [x] **Phase 1** — Domain system (YAML loader + 3 configs) + structured Gemini outputs + prompt renderer
- [ ] **Phase 2** — pyannote diarization + real async pipeline + SSE streaming
- [ ] **Phase 3** — ⭐ Custom DistilBERT dialogue-act classifier (training notebook + HF Hub release + benchmark)
- [ ] **Phase 4** — RAG with citations
- [ ] **Phase 5** — Evaluation framework (WER, DER, F1, LLM-as-judge)
- [ ] **Phase 6** — Langfuse observability + multi-call analytics
- [ ] **Phase 7** — Polish (frontend wire-up, benchmark table, demo video)

---

## License

MIT — see [LICENSE](LICENSE).
