# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask dev server (from repo root)
python src/app.py

# Run CLI pipeline directly on an audio file
python src/main.py path/to/audio.mp3 --verbose

# Lint
flake8 src/

# Type check
mypy src/

# Run tests
pytest

# Run a single test file
pytest tests/test_sentiment_analyzer.py -v

# Docker
docker compose up -d           # Start with .env file
docker compose up -d --build   # Rebuild after code changes
docker compose down
docker compose logs -f
```

**Required env var:** `API_KEY` (Google Gemini API key). Copy `.env.example` to `.env` and set it, or export it in your shell.

**System dependency:** `ffmpeg` must be installed — Whisper uses it for audio decoding.

---

## Architecture

The app is a Flask web server (`src/app.py`) that exposes a single main endpoint `POST /process_audio`. When an audio file is uploaded, it runs through a sequential pipeline orchestrated by `src/main.py:process_audio()`:

```
Audio file
  → whisper_module.py     transcribes to text + timestamped segments
  → diarization.py        assigns speaker labels (Counselor / Student) using pause-gap heuristics on Whisper segments
  → emotion_detector.py   per-turn emotion classification (HuggingFace: j-hartmann/emotion-english-distilroberta-base)
  → topic_extractor.py    keyword extraction (KeyBERT → TF-IDF fallback)
  → sentiment_analyzer.py VADER sentiment scoring + emotional indicator regex matching
  → gemini_module.py      three Gemini 2.0 Flash calls: summary, sentiment narrative, counselor suggestions
  → unified JSON response
```

The frontend is plain HTML/CSS/JS in `web/` — no build step. `web/index.html` is the single-page app served from Flask's template folder. Chart.js renders the sentiment and emotion timeline charts client-side from the JSON response.

**PDF export** is a separate endpoint (`POST /export_pdf`) that takes the same JSON object from the frontend and generates a report via `src/report_generator.py` using FPDF2.

### Key design details

- **Model caching:** Whisper, the HuggingFace emotion pipeline, and the KeyBERT model are each cached in module-level globals (`_whisper_model`, `_emotion_pipeline`, `_kw_model`) to avoid reloading on every request. First request after startup will be slow.
- **Diarization approach:** There is no actual speaker diarization model — speaker turns are detected purely by silence gaps between Whisper segments (`DEFAULT_PAUSE_THRESHOLD = 1.5s`). It assumes a two-party conversation and alternates labels starting with "Counselor".
- **Gemini calls:** `gemini_module.py` makes three separate API calls (summary, sentiment, suggestions) with exponential-backoff retry. Model is `gemini-2.0-flash-exp`. The module raises at import time if `API_KEY` is missing.
- **Flask app factory:** `app.py` uses `create_app()` and uploads go to `tempfile.gettempdir()`, cleaned up in a `finally` block after processing.
- **Gunicorn in production:** The Dockerfile runs `gunicorn --workers 2 --threads 4 --timeout 300 --chdir src app:app`. Long timeouts exist because model inference is slow.
