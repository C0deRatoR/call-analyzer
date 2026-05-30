# ConvIQ Execution Backlog (6 Weeks)

## Objective
Deliver a resume-grade, production-shaped **real-time + async conversation intelligence** system with measurable quality, cost, and latency.

---

## Success Criteria (End of Week 6)
- Live call lane works with sub-3s perceived assistant response for short prompts.
- Post-call pipeline produces evidence-backed suggestions with citation checks.
- Automated eval suite runs in CI and blocks regressions.
- End-to-end traces exist for all critical stages with failure taxonomy.
- You can demo one complete workflow live and show metrics/history in README.

---

## Week 1 — Foundation Alignment

### Scope
- Align API contracts and frontend integration path with current FastAPI routes.
- Stabilize upload -> queue -> status flow using real SSE events from Redis pub/sub.
- Keep any future client aligned with the FastAPI `/calls` contract.

### Repo Touchpoints
- `apps/api/routers/calls.py`
- `apps/worker/tasks/pipeline.py`
- `apps/worker/celery_app.py`
- Future client path, once a frontend is reintroduced

### Tasks
- Implement real SSE subscription to `pipeline:{call_id}` channel.
- Standardize stage enum names (`queued`, `transcribe`, `diarize`, etc.).
- Add structured progress payload schema (stage, percent, detail, ts).
- Add API error contract consistency (`detail`, `code`, `stage` optional).

### Acceptance Criteria
- Uploading a file returns `202` with `call_id` and valid `stream_url`.
- Stream shows true worker stage events, not heartbeat stubs.
- `GET /calls/{id}` reflects stage/status transitions correctly.

---

## Week 2 — Real-Time Lane (MVP)

### Scope
- Add browser real-time lane for live transcript and lightweight assist.
- Keep async batch pipeline for full post-call analysis.

### Repo Touchpoints
- New: `apps/api/routers/realtime.py`
- `apps/api/main.py`
- New client code, likely as a separate frontend app

### Tasks
- Add session bootstrap endpoint for real-time client auth/session data.
- Stream partial transcripts/events to UI.
- Add minimal assistant behavior (short in-call suggestions only).
- Add fallback behavior when live model fails (degrade gracefully to transcript-only).

### Acceptance Criteria
- User can start live session and see rolling transcript updates.
- Assistant returns short actionable hints during call.
- Failure in live assist does not kill transcript stream.

---

## Week 3 — Evidence-Grounded Coaching

### Scope
- Enforce evidence-first outputs for suggestions.
- Wire RAG retrieval from per-domain knowledge bases.

### Repo Touchpoints
- `pipeline/llm.py`
- `pipeline/prompts.py`
- New: `pipeline/rag.py`
- `core/llm/schemas.py`
- `domains/*.yaml`

### Tasks
- Add retrieval step (top-k chunks with stable IDs).
- Extend suggestion schema to include `citations`, `evidence_spans`, `confidence`.
- Add citation validation pass (drop unsupported suggestions).
- Store retrieval metadata + citations in DB JSON columns.

### Acceptance Criteria
- Suggestions without valid citations are filtered out.
- Each returned suggestion references at least one existing source chunk ID.
- Response includes confidence and span metadata.

---

## Week 4 — Model Quality + Diarization Upgrade

### Scope
- Replace active heuristic diarization path with pyannote pipeline.
- Integrate dialogue-act model path (initial baseline or fine-tuned checkpoint).

### Repo Touchpoints
- `pipeline/diarization.py`
- `pipeline/transcription.py`
- New: `pipeline/dialogue_act.py`
- `apps/worker/tasks/pipeline.py`

### Tasks
- Add pyannote diarization stage in worker pipeline.
- Align diarized turns with transcript segments deterministically.
- Add dialogue-act labeling per turn.
- Compute per-speaker and per-act analytics for persistence.

### Acceptance Criteria
- Pipeline produces non-empty turns with speaker labels and timestamps.
- Dialogue-act labels persisted per turn.
- Analytics rows generated for completed calls.

---

## Week 5 — Evals + CI Regression Gates

### Scope
- Build continuous evaluation harness and CI checks.
- Track quality + cost + latency trends.

### Repo Touchpoints
- `eval/` (golden data, scripts, results)
- New: `eval/run_eval.py`
- New: `.github/workflows/evals.yml` (if GitHub Actions used)
- `README.md`

### Tasks
- Add reproducible eval commands for:
  - WER
  - DER
  - Dialogue-act F1
  - Citation correctness / groundedness
  - Latency p95 + cost per call
- Persist eval outputs to `eval/results/latest.json`.
- Add CI threshold gates with clear failure messages.

### Acceptance Criteria
- Single command runs full eval suite locally.
- CI fails on threshold regression.
- README benchmark table auto-updates from latest results artifact.

---

## Week 6 — Observability + Hardening + Demo Polish

### Scope
- Instrument traces and operational safeguards.
- Prepare recruiter-facing demo quality.

### Repo Touchpoints
- `pipeline/llm.py`
- `apps/worker/tasks/pipeline.py`
- `core/db/models.py` (if extra trace metadata needed)
- `README.md`
- `infra/docker-compose.yml`

### Tasks
- Add stage-level tracing (inputs redacted, outputs summarized).
- Add failure taxonomy tags (hallucination, citation miss, timeout, diarization mismatch).
- Add idempotency key handling for replays.
- Add retention/deletion notes and minimal privacy policy section.
- Record demo script and expected outputs.

### Acceptance Criteria
- Every completed call has trace coverage across critical stages.
- Known failure types are queryable and countable.
- Demo script runs end-to-end with predictable timing.

---

## Cross-Cutting Technical Standards
- Keep API schemas versioned and explicit.
- Add tests for every new schema and stage contract.
- Ensure deterministic IDs for citations/evidence references.
- Never return ungrounded coaching in “strict mode.”
- Log with structured keys (`call_id`, `stage`, `latency_ms`, `model`, `domain_id`).

---

## Metrics Targets (Initial)
- WER: improve by model selection and preprocessing; document baseline vs current.
- DER: beat pause-heuristic baseline by clear margin on golden set.
- Dialogue-act macro-F1: publish baseline first, then fine-tuned target.
- Grounded suggestion rate: >=90% suggestions with valid citations.
- End-to-end latency: track p50/p95 by audio duration buckets.
- Cost/call: report by stage + total.

---

## Demo Story (For Resume/Interviews)
1. Start live call mode, show streaming transcript and in-call assist.
2. End call, show async stages progressing in real-time.
3. Open completed call: summary, speaker turns, rubric, evidence-backed suggestions.
4. Show trace for one suggestion from prompt -> retrieval -> citation output.
5. Show eval dashboard/table and explain one regression caught by CI.

---

## Resume Bullet Templates (Fill with your numbers)
- Built a real-time + async conversation intelligence platform using FastAPI, Celery, Redis, Postgres/pgvector, and domain-configurable prompting.
- Improved coaching reliability by enforcing citation-gated generation, reducing unsupported suggestions by **X%**.
- Implemented continuous eval gates (WER/DER/F1/groundedness/latency/cost), preventing regressions across model and prompt updates.
- Added end-to-end tracing and failure taxonomy, reducing investigation time from **X min** to **Y min**.
