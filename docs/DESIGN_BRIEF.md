# ConvIQ — Frontend Design Brief

> **Heads up — significant API change vs. the previous brief.** The backend was a sync Flask app with one blocking endpoint. It is being rebuilt as an async FastAPI + Celery pipeline behind a server-sent-events progress stream. The contract below is the **new** one — do not pull from the old brief.

## What this app does

Users upload an audio conversation, pick a **domain** (counseling / sales / customer support / a custom one), and receive a complete analysis: speaker-diarized transcript, per-turn emotion + dialogue-act labels (from a fine-tuned classifier), per-speaker analytics, RAG-grounded coaching suggestions with citations, sentiment + keywords + a downloadable PDF report.

There is no auth, no multi-page routing. The app is single-page.

---

## Backend API (FastAPI)

Base URL in dev: `http://localhost:8000`. All endpoints return JSON unless noted. Interactive docs auto-generated at `/docs`.

### `GET /health`

```json
{
  "status": "healthy",
  "service": "ConvIQ",
  "version": "0.1.0",
  "environment": "development"
}
```

### `GET /domains`

Returns the list of configured domains. Display these in the upload screen as a picker (radio cards work well).

```json
[
  {
    "id": "counseling",
    "display_name": "Counseling Session",
    "description": "Therapy / counseling / coaching conversations…",
    "primary_speaker": "Counselor",
    "secondary_speaker": "Student"
  },
  {
    "id": "sales",
    "display_name": "Sales Call",
    "description": "Outbound or inbound sales conversations…",
    "primary_speaker": "Salesperson",
    "secondary_speaker": "Prospect"
  },
  {
    "id": "customer_support",
    "display_name": "Customer Support Call",
    "description": "Inbound customer support conversations…",
    "primary_speaker": "Agent",
    "secondary_speaker": "Customer"
  }
]
```

### `GET /domains/{id}`

Full domain config: prompts, rubric dimensions, RAG namespace, analytics focus. Useful if the dashboard wants to show "what's being scored" per call.

```json
{
  "id": "counseling",
  "display_name": "Counseling Session",
  "description": "…",
  "speakers": { "primary": "Counselor", "secondary": "Student" },
  "prompts": { "summary": "…", "suggestions": "…", "sentiment": "…" },
  "rubric": {
    "empathy": "Does the Counselor reflect…",
    "open_questions": "What fraction…",
    "active_listening": "…",
    "actionability": "…"
  },
  "rag": { "namespace": "counseling_best_practices", "source_label": "Counseling Research" },
  "analytics_focus": ["talk_time_ratio", "question_ratio", "acknowledgment_ratio", "suggestion_ratio"]
}
```

### `POST /calls` — kick off an analysis

**Request:** `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `audio` | file | MP3, WAV, M4A, FLAC, OGG, AAC. Max 100 MB. |
| `domain_id` | string | One of the IDs from `GET /domains`. Defaults to `"counseling"`. |

**Response:** `202 Accepted`

```json
{
  "id": "9b7d6f1e-…",                       // UUID
  "status": "queued",
  "stream_url": "/calls/9b7d6f1e-…/stream"  // open this immediately for live progress
}
```

> **Important:** this endpoint returns *fast* and does not contain the analysis. Open `stream_url` immediately for live updates, and call `GET /calls/{id}` when the stream emits a `complete` event.

### `GET /calls/{id}/stream` — Server-Sent Events progress

Open with `EventSource` (vanilla JS native). The stream emits SSE events with `event:` types and JSON `data:` payloads.

Event types:

| Event | Payload |
|---|---|
| `progress` | `{"stage": "transcribe", "detail": "Starting transcribe"}` |
| `complete` | `{"stage": "complete", "detail": "Pipeline finished"}` |
| `error` | `{"stage": "error", "detail": "<error message>"}` |

Stages emitted in order: `queued`, `transcribe`, `diarize`, `classify`, `emotion`, `summarize`, `complete` (or `error` at any point). Each stage may emit multiple `progress` events ("Starting …" and "Completed …").

```js
const es = new EventSource(streamUrl);
es.addEventListener("progress", (e) => {
  const { stage, detail } = JSON.parse(e.data);
  updateProgressUI(stage, detail);
});
es.addEventListener("complete", () => {
  es.close();
  fetch(`/calls/${id}`).then(/* render results */);
});
es.addEventListener("error", (e) => {
  // network error vs. server-sent error event — check e.data
});
```

### `GET /calls/{id}` — full result

Returns the complete `CallRead` payload. Poll once after `complete`, or re-poll if the user revisits.

```json
{
  "id": "9b7d6f1e-…",
  "created_at": "2026-05-19T23:50:00Z",
  "updated_at": "2026-05-19T23:51:42Z",
  "audio_filename": "session-2026-05-19.mp3",
  "duration_seconds": 612.4,
  "language": "en",
  "domain_id": "counseling",
  "status": "completed",
  "current_stage": "complete",
  "error_message": null,

  "transcript": "Full raw transcript as a single string.",
  "summary": "The student expressed exam anxiety…",
  "sentiment_label": "positive",
  "sentiment_compound": 0.312,
  "dominant_emotion": "neutral",

  "emotion_distribution_json": {
    "neutral": 0.4286,
    "fear": 0.2857,
    "joy": 0.1429,
    "sadness": 0.1429
  },

  "suggestions_json": [
    {
      "suggestion": "When the student mentioned feeling overwhelmed, try reflecting…",
      "citations": ["counseling_best_practices/active_listening.md#para-3"]
    },
    { "suggestion": "Use more open-ended questions…", "citations": ["counseling_best_practices/spin_questions.md"] }
  ],

  "keywords_json": [
    { "keyword": "exam anxiety", "score": 0.8921 },
    { "keyword": "sleep issues", "score": 0.7643 },
    { "keyword": "relaxation techniques", "score": 0.7102 }
  ],

  "turns": [
    {
      "index": 0,
      "speaker": "Counselor",
      "text": "Hello, how are you feeling today?",
      "start_seconds": 0.0,
      "end_seconds": 3.2,
      "emotion": "neutral",
      "emotion_confidence": 0.87,
      "dialogue_act": "Question",
      "dialogue_act_confidence": 0.92,
      "sentiment_compound": 0.05
    },
    {
      "index": 1,
      "speaker": "Student",
      "text": "I've been really anxious about my exams.",
      "start_seconds": 4.8,
      "end_seconds": 7.5,
      "emotion": "fear",
      "emotion_confidence": 0.74,
      "dialogue_act": "Statement",
      "dialogue_act_confidence": 0.88,
      "sentiment_compound": -0.42
    }
  ],

  "analytics": {
    "primary_talk_seconds": 287.4,
    "secondary_talk_seconds": 325.0,
    "talk_time_ratio": 0.469,
    "primary_word_count": 412,
    "secondary_word_count": 538,
    "primary_question_count": 18,
    "primary_statement_count": 22,
    "primary_acknowledgment_count": 14,
    "primary_suggestion_count": 9,
    "quality_scores_json": {
      "empathy": 4.2,
      "open_questions": 3.8,
      "active_listening": 4.0,
      "actionability": 3.5
    }
  }
}
```

`status` is one of: `queued`, `processing`, `completed`, `failed`. If `failed`, `error_message` will be populated.

### `POST /calls/{id}/export`

Returns the PDF report as `application/pdf` with `Content-Disposition: attachment`. Frontend downloads as a Blob.

---

## App States & Flow

The page transitions through five states. Only one is visible at a time.

1. **Domain selection** — load `GET /domains` on mount, render the list as picker cards. User selects one (default selection is fine).
2. **Upload** — drop zone or file picker. Validates extension client-side. The "Analyze" button stays disabled until both (a) a file is selected and (b) a domain is picked.
3. **Processing** — after `POST /calls`, immediately switch to this state and open the SSE stream. Show a progress indicator that maps stages to UI:
    - `queued` → "Waiting in queue…"
    - `transcribe` → "Transcribing audio…"
    - `diarize` → "Identifying speakers…"
    - `classify` → "Classifying dialogue acts…"
    - `emotion` → "Detecting emotion…"
    - `summarize` → "Generating summary + suggestions…"
    - `complete` → trigger fetch of `/calls/{id}`
    - `error` → switch to error state
4. **Results** — full `CallRead`. Same card-and-dashboard structure as the previous design works well; layouts below.
5. **Error** — display `error_message` from the call record (or the SSE error event), with a "Try Again" button that resets to State 2.

### Cards in the Results view

Same overall structure as before, but new data is available:

1. **Transcript** — diarized turns. **Each turn now has a `dialogue_act` label** — surface it as a small tag next to the emotion tag (e.g., "❓ Question", "💬 Statement", "✓ Acknowledgment", "💡 Suggestion").
2. **Summary** — `summary` text.
3. **Sentiment Analysis** — `sentiment_label` badge, `sentiment_compound` compound score, the Gemini narrative (will move into a dedicated `sentiment` field in Phase 1; for now derive from `summary` or treat as missing).
4. **Emotion Analysis** — `dominant_emotion` + `emotion_distribution_json` as bars + emotion timeline reconstructed from `turns[].emotion`.
5. **Keywords & Topics** — `keywords_json` as a tag cloud with relevance scores.
6. **Per-speaker Analytics** *(NEW card)* — from the `analytics` object: talk-time ratio donut, dialogue-act mix bar chart (Question / Statement / Acknowledgment / Suggestion counts for the primary speaker), rubric quality scores radar chart.
7. **AI Suggestions** — `suggestions_json` as numbered list. **Each suggestion now has a `citations` array of source IDs** — show them as small badges next to each suggestion (clicking could open the source excerpt; for v1 just display them).

### Dashboard tab charts

Same as before plus a new one for dialogue acts:

- Sentiment doughnut
- Emotion distribution bar
- Emotion timeline (line chart of emotion-over-time, dots colored by emotion)
- Keyword relevance horizontal bar
- **Dialogue-act distribution** *(NEW)* — stacked bar showing each speaker's mix of Question/Statement/Acknowledgment/Suggestion

---

## Stages → User-Facing Labels

| Backend stage | UI label | Approximate share of total time |
|---|---|---|
| `queued` | Waiting in queue… | < 1% |
| `transcribe` | Transcribing audio (Whisper) | ~40% |
| `diarize` | Identifying speakers (pyannote.audio) | ~10% |
| `classify` | Classifying dialogue acts | ~5% |
| `emotion` | Detecting emotion | ~5% |
| `summarize` | Generating summary + grounded suggestions (Gemini) | ~40% |

(Times vary by audio length and model size; treat as rough proportions for the progress bar.)

---

## Data Reference

### Emotion labels

Exactly seven: `anger`, `disgust`, `fear`, `joy`, `neutral`, `sadness`, `surprise`.

Color/emoji suggestions:

| Emotion | Color | Emoji |
|---|---|---|
| joy | `#22c55e` | 😊 |
| anger | `#ef4444` | 😠 |
| sadness | `#3b82f6` | 😢 |
| fear | `#a855f7` | 😰 |
| surprise | `#f59e0b` | 😮 |
| disgust | `#84cc16` | 🤢 |
| neutral | `#6b7280` | 😐 |

### Dialogue-act labels *(NEW)*

Four classes from the fine-tuned classifier:

| Act | Description | Color | Emoji |
|---|---|---|---|
| `Question` | Asking for info | `#3b82f6` | ❓ |
| `Statement` | Sharing info / opinion | `#6b7280` | 💬 |
| `Acknowledgment` | Validating / agreeing | `#22c55e` | ✓ |
| `Suggestion` | Proposing action / advice | `#f59e0b` | 💡 |

### Sentiment labels

`very_positive`, `positive`, `neutral`, `negative`, `very_negative` — derived from `sentiment_compound` (the VADER compound score, range −1 to +1).

### Speaker labels

**No longer hardcoded.** Pulled from `GET /domains/{domain_id}.speakers`. The two values depend on the selected domain — e.g., `Counselor`/`Student`, `Salesperson`/`Prospect`, `Agent`/`Customer`. Style speakers by *role* (primary vs. secondary) rather than by literal string match.

### Call status

`queued`, `processing`, `completed`, `failed`.

---

## Implementation Constraints

- **Tech:** React/Next.js, Vue, Svelte, vanilla JS — all fine. The backend is API-only and lives at `http://localhost:8000`.
- **CORS:** allowed from any origin in dev; `allow_credentials=false` (no cookies needed; no auth in v1).
- **State management:** the only meaningful state is the current call (id + status + cached result). LocalStorage-persisted "recent calls" list is a nice-to-have.
- **Theme persistence:** dark/light via `localStorage`.
- **Error handling:** every endpoint returns `{"detail": "<message>"}` on failure with an appropriate HTTP status. Show the `detail` field to the user.
- **No auth yet** — single-user mental model. Auth lands in a later phase.

---

## What's intentionally missing / coming later

- `sentiment.gemini_analysis` narrative as a dedicated field — currently rolled into `summary`. Phase 1 will split it out.
- Multi-call history page — Postgres + pgvector are wired but no UI for cross-call comparison yet. Phase 6.
- Citation source viewer — when a suggestion cites `counseling_best_practices/active_listening.md#para-3`, we'd love a hover-card showing the actual excerpt. Phase 4 wires the data; UI is a stretch.

If the design accommodates a "show citation source" interaction (modal / hover-card / side panel), great. If it just shows badges, also great.
