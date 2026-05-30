# ConvIQ Transformation Plan (Resume-Grade AI/ML Project)

## Goal
Turn ConvIQ from a good prototype into a standout **GenAI / AI Engineer / AI/ML Engineer** project by making it:
- real-time + production-shaped
- evidence-grounded
- measurable with continuous evals
- observable and debuggable end-to-end

---

## Recommended Direction
Build **Real-Time Conversation QA Copilot**:
- Live call transcription + diarization + in-call assist
- Post-call scorecard with evidence-backed coaching
- Continuous evaluation + observability loop

This gives you stronger engineering signal than a batch-only “audio summarizer.”

---

## What To Change

### 1) Real-time + async hybrid architecture
- Keep existing async pipeline for deep post-call analytics.
- Add a real-time lane for live guidance (browser voice via WebRTC).
- Result: product-like system design and lower perceived latency.

### 2) Use current API primitives
- Build new LLM features on **Responses API + tools**.
- Avoid building new logic on Assistants API (deprecated; shutdown on **August 26, 2026**).
- Use tools/function calls for retrieval and workflow actions.

### 3) Evidence-first output policy
- Every suggestion must include:
  - timestamped call evidence (spans)
  - retrieved KB chunk IDs
  - confidence/uncertainty
- If evidence is insufficient, suppress suggestions instead of hallucinating.

### 4) Upgrade diarization and benchmark it
- Replace active heuristic diarization path with proper pyannote pipeline.
- Benchmark DER and compare legacy vs newer pyannote variants on your dataset.

### 5) Make evals first-class
- Auto-run evals on PR/model/prompt changes:
  - WER (ASR)
  - DER (diarization)
  - Dialogue-act F1
  - Groundedness / citation correctness
  - Latency p95 + cost per call
- Track trend over time, not single snapshots.

### 6) Add LLM observability
- Trace ingest → STT → diarization → retrieval → LLM generation.
- Tag failures (citation miss, hallucination, latency breach, speaker mix-up).
- Build a repeatable debugging workflow from traces.

### 7) Ship production concerns
- Auth + multi-tenant isolation
- PII redaction before persistence
- Idempotency and retry strategy
- Dead-letter queue for failed jobs
- Data retention/deletion controls
- SLOs and incident notes for regressions

---

## Resume-Ready Outcomes To Target
- “Built a real-time + async conversation intelligence platform with WebRTC ingestion and staged AI pipeline.”
- “Reduced unsupported coaching outputs by X% with citation-gated generation and retrieval checks.”
- “Implemented continuous evals (WER/DER/F1/groundedness/latency/cost) to prevent model/prompt regressions.”
- “Added end-to-end tracing and reduced mean debugging time from X to Y.”

---

## Suggested Milestones

### Milestone 1 — Real-time lane
- Add real-time ingestion/session flow.
- Emit live partial transcripts and basic agent assist.

### Milestone 2 — Grounded coaching
- Enforce evidence schema for suggestions.
- Add citation validation checks.

### Milestone 3 — Evaluation harness
- Build reproducible datasets and CI eval jobs.
- Publish benchmark table from latest run artifacts.

### Milestone 4 — Observability + hardening
- Full trace coverage and failure taxonomy.
- Add SLO monitors and operational safeguards.

---

## Source Links
- Realtime API with WebRTC: https://platform.openai.com/docs/guides/realtime-webrtc
- Realtime API overview: https://platform.openai.com/docs/guides/realtime/
- Responses tools + remote MCP: https://platform.openai.com/docs/guides/tools?api-mode=responses
- Assistants API deprecation notice: https://platform.openai.com/docs/assistants/tools
- Working with evals: https://platform.openai.com/docs/guides/evals?api-mode=responses
- External model evals: https://platform.openai.com/docs/guides/external-models
- Evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
- Trace grading: https://platform.openai.com/docs/guides/trace-grading
- pyannote speaker-diarization-3.1: https://huggingface.co/pyannote/speaker-diarization-3.1
- pyannote org + benchmark context: https://huggingface.co/pyannote
- Whisper model card: https://github.com/openai/whisper/blob/main/model-card.md
- Langfuse observability overview: https://langfuse.com/docs/observability/overview

