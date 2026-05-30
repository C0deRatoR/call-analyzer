# Call Analyzer — Full Rebuild Plan

## Target Outcome

A flagship portfolio project demonstrating end-to-end AI/ML engineering skills for a 3rd-year student targeting AI/ML engineer roles.

**The resume bullet this project should produce:**

> Built **ConvIQ**, an end-to-end conversation intelligence platform with a configurable domain system (counseling, sales, customer support). Fine-tuned DistilBERT for dialogue-act classification (82% macro-F1 on DailyDialog, +14pp over zero-shot Gemini baseline). Real-time speaker diarization with pyannote.audio. RAG-grounded coaching suggestions with citations over domain knowledge bases (Chroma). Asynchronous processing pipeline (FastAPI, Celery, Redis) with SSE-streamed progress. Full LLM observability via Langfuse (traces, costs, latencies). Postgres + pgvector persistence. Dockerized.

---

## What Changes vs. Current State

| Current | New |
|---|---|
| Flask sync server | FastAPI + Celery worker + Redis broker |
| Fake `setTimeout` progress bar | Server-Sent Events with real pipeline stage updates |
| Pause-heuristic diarization | pyannote.audio (real speaker diarization) |
| Free-text Gemini outputs | Pydantic-validated structured outputs |
| Hardcoded counseling prompts | YAML-configurable domain system (counseling / sales / support / custom) |
| Off-the-shelf models only | **One fine-tuned DistilBERT classifier** (the trained-model story) |
| Suggestions hallucinate freely | RAG-grounded suggestions with cited sources |
| No persistence | Postgres for calls + pgvector for embeddings |
| No evaluation | Golden eval set + WER + F1 + LLM-as-judge with rubrics |
| Zero observability | Langfuse self-hosted (every LLM call traced) |
| No analytics | Per-speaker analytics + dialogue-act-derived metrics |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend (built separately)                       │
│              ─────── HTTP + SSE ───────                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI (API gateway)                                               │
│  • POST /calls         (upload audio → enqueue job)                  │
│  • GET  /calls/{id}    (status + final result)                       │
│  • GET  /calls/{id}/stream  (SSE: live progress events)              │
│  • POST /calls/{id}/export (PDF generation)                          │
│  • GET  /analytics     (multi-call dashboard queries)                │
└─────────────────────────────────────────────────────────────────────┘
        │                                              │
        ▼ Redis (queue + pub/sub for SSE)              ▼ Postgres + pgvector
┌────────────────────────────────────────┐
│  Celery Worker                          │
│   ┌─────────────────────────────────┐   │
│   │  PIPELINE (per domain config)   │   │
│   │  1. Whisper transcription        │   │
│   │  2. pyannote diarization         │   │
│   │  3. Custom DistilBERT dialog-act │   │ ← fine-tuned model
│   │  4. HF emotion classifier        │   │
│   │  5. VADER + per-speaker analytics│   │
│   │  6. KeyBERT keywords             │   │
│   │  7. RAG retrieval (Chroma)       │   │
│   │  8. Gemini summary (structured)  │   │
│   │  9. Gemini grounded suggestions  │   │
│   │     (with citations from RAG)    │   │
│   └─────────────────────────────────┘   │
└────────────────────────────────────────┘
        │                          │
        ▼ Langfuse                  ▼ Chroma (per-domain knowledge bases)
   (LLM tracing)
```

---

## The Configurable Domain System

Each domain is a YAML config file under `domains/`:

```yaml
# domains/counseling.yaml
id: counseling
display_name: "Counseling Session"
speakers:
  primary: "Counselor"     # asks questions, gives advice
  secondary: "Student"     # presents problem, receives advice
prompts:
  summary: |
    Summarize this counseling conversation between {primary} and {secondary}.
    Focus on: presented concerns, advice given, agreed next steps.
  suggestions: |
    You are an expert counselor coach. Review this call and suggest 3-5
    specific improvements the {primary} could have made. Ground every
    suggestion in the retrieved best-practice excerpts. Cite sources.
rubric:
  empathy: "Does the {primary} reflect feelings before offering solutions?"
  open_questions: "Ratio of open vs. closed questions asked."
  actionability: "Are concrete next steps suggested?"
rag:
  namespace: "counseling_best_practices"
  source_label: "Counseling Research"
analytics_focus:
  - talk_time_ratio
  - question_ratio
  - validation_ratio
  - advice_ratio
```

Other domains shipped in v1: `sales.yaml`, `customer_support.yaml`. Custom domains can be added by dropping a YAML file in the folder — no code changes needed.

User selects domain at upload. Backend resolves all prompts, RAG namespace, rubric, and analytics from that config.

---

## The Fine-Tuned Model (The Resume Centerpiece)

**Task:** Dialogue Act Classification — assign each turn a tag from {Question, Statement, Acknowledgment, Suggestion}.

**Dataset:** [DailyDialog](https://huggingface.co/datasets/daily_dialog) — 13K open-domain dialogues with 4-class act labels. Released under CC BY-NC-SA.

**Base model:** `distilbert-base-uncased` (66M params, fits in 8GB VRAM with batch_size=32).

**Training setup:**
- Environment: local on RTX 4060 Laptop (8GB VRAM is plenty)
- Library: HuggingFace `transformers` + `datasets` + `evaluate`
- Hyperparameters: lr=2e-5, batch=32, epochs=3, warmup=10%
- Expected runtime: ~15 minutes
- Baseline to beat: zero-shot Gemini-2.0-Flash on same test split

**Deliverables:**
- `models/dialogue_act/` — training notebook + scripts
- `models/dialogue_act/train.py` — reproducible training run
- `models/dialogue_act/eval.py` — produces benchmark table
- HuggingFace Hub upload: `<your-username>/conviq-dialogue-act-distilbert`
- Model card with metrics, training details, intended use, limitations

**How it's used at inference:**
Each diarized turn gets a dialogue-act label appended. These labels power the per-domain analytics (question ratio, advice ratio, validation ratio, etc.).

**Stretch (if v1 ships fast):** Add a second fine-tune — empathy regression on the EPITOME dataset (counseling-specific). Optional.

---

## RAG with Citations

**Vector store:** Chroma (embedded, no external service needed in v1).

**Knowledge bases (one collection per domain):**
- `counseling_best_practices` — curated excerpts from active-listening guides, motivational interviewing techniques, SAMHSA materials (~50-100 chunks)
- `sales_methodology` — SPIN selling, Challenger sale, MEDDIC excerpts (~50 chunks)
- `customer_support_best_practices` — empathy frameworks, de-escalation patterns (~50 chunks)

**Indexing:** `sentence-transformers/all-MiniLM-L6-v2` embeddings (already a dependency via KeyBERT).

**Retrieval:** Top-5 by cosine similarity, optional reranking with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`).

**Generation:** Gemini suggestion prompt includes the retrieved chunks; output schema requires `[{"suggestion": str, "citations": [chunk_id]}]`. Frontend renders citation badges that link to the source chunks.

---

## Evaluation Framework

`eval/` directory with:

**1. Transcription quality**
- 10-15 golden audio samples with hand-curated ground-truth transcripts
- Metric: Word Error Rate (WER) via `jiwer`
- Tracked across Whisper model sizes (tiny / base / small)

**2. Diarization quality**
- Same golden samples annotated with speaker turns
- Metric: Diarization Error Rate (DER) via `pyannote.metrics`
- Compare: pyannote.audio vs. the legacy pause-heuristic

**3. Custom model**
- DailyDialog test split
- Metric: macro-F1 + per-class precision/recall + confusion matrix
- Baseline: zero-shot Gemini-2.0-Flash on the same test split (prove the fine-tune is worth it)

**4. LLM output quality** (LLM-as-judge)
- 20 sample calls + expected summary characteristics (faithfulness, completeness, actionability)
- Judge: GPT-4o or Claude scoring each axis 1-5 with reasoning
- Tracked per prompt version (lets you iterate on prompts with hard numbers)

**5. End-to-end regression suite**
- `pytest eval/test_regression.py` runs the full pipeline on golden samples and asserts metrics stay above baselines

All numbers land in `eval/results/latest.json` and feed into a README benchmark table.

---

## Production Engineering

**FastAPI app** (`apps/api/`):
- Async endpoints
- Pydantic v2 models for every request + response
- OpenAPI docs auto-generated at `/docs`

**Celery worker** (`apps/worker/`):
- One task per pipeline stage (transcription, diarization, classification, ...)
- Stages publish progress events to Redis pub/sub → SSE relays them to the frontend
- Each stage's result is persisted to Postgres so partial failures can resume

**Postgres schema:**
- `calls` — call metadata, audio path, domain, status
- `turns` — diarized turns with emotion + dialogue act + per-turn embedding (pgvector)
- `analytics` — computed metrics per call
- `llm_traces` — Langfuse trace IDs for cross-referencing

**Langfuse:**
- Self-hosted via Docker Compose (free, OSS)
- Every Gemini call wrapped with `@observe` decorator
- Tracks tokens, latency, cost, full prompt + response
- README includes a screenshot of the dashboard

**Docker Compose** (`infra/docker-compose.yml`):
- Services: `api`, `worker`, `redis`, `postgres`, `langfuse`, `chroma`
- One command launches the whole stack: `docker compose up`

---

## Repo Structure

```
call-analyzer/
├── apps/
│   ├── api/          # FastAPI (replaces src/app.py)
│   └── worker/       # Celery tasks (the pipeline)
├── pipeline/
│   ├── transcription.py
│   ├── diarization.py        # current heuristic; pyannote lands in Phase 2
│   ├── emotion.py
│   ├── sentiment.py
│   ├── keywords.py
│   ├── prompts.py            # domain-aware prompt rendering
│   ├── report.py             # PDF report generation
│   └── llm.py                # Gemini + structured outputs
├── domains/
│   ├── counseling.yaml
│   ├── sales.yaml
│   └── customer_support.yaml
├── knowledge_bases/          # source documents for RAG
│   ├── counseling/
│   ├── sales/
│   └── customer_support/
├── models/
│   └── dialogue_act/
│       ├── train.py
│       ├── eval.py
│       ├── notebook.ipynb
│       └── model_card.md
├── eval/
│   ├── golden/               # audio + ground-truth annotations
│   ├── metrics/
│   ├── test_regression.py
│   └── results/
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile            # multi-target image for API and worker
│   └── alembic/
├── notebooks/                # data exploration, training, analysis
├── tests/
├── docs/
│   └── PLAN.md               # this file
├── README.md                 # the recruiter-facing one
└── pyproject.toml            # poetry or uv
```

---

## Phased Execution Plan

Estimated total: **10-14 days of focused work** for a student doing this part-time alongside classes.

### Phase 0 — Foundations ✅ COMPLETE
- [x] Repo restructure to the layout above
- [x] Switch from `requirements.txt` to `pyproject.toml` (uv)
- [x] FastAPI skeleton with `/health`, `/calls`, `/domains` endpoints (Pydantic models)
- [x] Docker Compose with Postgres + Redis + Chroma
- [x] Alembic migrations for the schema above (`calls`, `turns`, `analytics`, `llm_traces`)
- [x] Move existing pipeline modules into `pipeline/` unchanged

### Phase 1 — Domain System + Structured Outputs ✅ COMPLETE
- [x] `domains/` YAML loader with Pydantic validation (`core/domains/loader.py`)
- [x] Three domain configs: `counseling.yaml`, `sales.yaml`, `customer_support.yaml`
- [x] Gemini client rewritten with structured outputs (Pydantic schemas, JSON mode)
- [x] Domain prompt renderer (`pipeline/prompts.py`)
- [x] `domain` form field on `POST /calls` selects which config to use

### Phase 2 — Real Diarization + Async Pipeline (2 days)
- [ ] pyannote.audio integration (requires HF token + accept license)
- [ ] Replace the stage-shaped Celery stub with real stage implementations
- [ ] Split pipeline orchestration so stages can be retried/resumed cleanly
- [x] Redis pub/sub progress event contract
- [x] SSE endpoint `GET /calls/{id}/stream`
- [ ] Per-stage results persisted to Postgres

### Phase 3 — Custom Model Training (1-2 days) ★ The Centerpiece
- [ ] Load DailyDialog from HF Datasets
- [ ] Train DistilBERT classifier on RTX 4060 (notebook + script)
- [ ] Evaluate vs. zero-shot Gemini baseline
- [ ] Model card + push to HF Hub
- [ ] Add `pipeline/dialogue_act.py` and wire it to use the trained model
- [ ] Add dialogue-act-derived analytics

### Phase 4 — RAG + Citations (2 days)
- [ ] Curate knowledge base content (Markdown excerpts per domain)
- [ ] Indexing script (chunk → embed → upsert to Chroma)
- [ ] Retrieval module with optional cross-encoder reranking
- [ ] Suggestion prompt rewritten to require citations
- [ ] API response includes citation metadata; design frontend to show them

### Phase 5 — Evaluation Framework (2 days)
- [ ] Record/source 10-15 golden audio samples (LibriSpeech + free counseling/sales sample recordings)
- [ ] Hand-annotate ground truth for each
- [ ] WER + DER metric scripts
- [ ] LLM-as-judge rubric scoring
- [ ] `pytest` regression suite
- [ ] Benchmark table generation → README

### Phase 6 — Observability + Analytics Dashboard (1-2 days)
- [ ] Langfuse self-hosted, wired in
- [ ] Cost/latency tracking surfaced via `/analytics` endpoint
- [ ] Multi-call comparison queries
- [ ] Per-speaker analytics endpoint

### Phase 7 — Polish (1-2 days)
- [ ] README rewrite with:
  - Architecture diagram (mermaid → exported to PNG)
  - Headline benchmark table (custom-model F1, WER, DER, latency, cost-per-call)
  - One-command quickstart
  - Screenshots of Langfuse + the new frontend
  - Link to HF model
- [ ] 60-second demo Loom recording
- [ ] Optional: technical blog post (devto / Medium / personal site) linked in README
- [ ] Wire up the new frontend you're building separately

---

## Stretch Goals (if any phase ships ahead of schedule)

- **Second fine-tune:** Empathy regression on EPITOME counseling dataset
- **Speaker enrollment:** Identify the same speaker across multiple calls (pyannote embeddings + nearest-neighbor)
- **Real-time mode:** Streaming Whisper + live dialogue-act tagging during the call
- **LLM router:** Cheap model for cheap tasks (summary), strong model for hard tasks (suggestions). Track cost savings in the README.
- **A/B prompt testing:** Multiple prompt variants logged, judged by LLM-as-judge, winning variant promoted automatically.
- **Conversation embeddings + similarity search:** "Find calls similar to this one" using pgvector.

---

## Resolved Decisions

- **Project name:** ConvIQ (repo stays `call-analyzer` for now; display name is ConvIQ)
- **Dependency manager:** `uv` with `pyproject.toml`
- **License:** MIT for application code; trained model will use CC BY-NC-SA (matches DailyDialog dataset)
- **GPU:** RTX 4060 Laptop (8 GB VRAM) for local DistilBERT training; Kaggle T4 as fallback
- **HF account:** required for pyannote license acceptance and model publishing
