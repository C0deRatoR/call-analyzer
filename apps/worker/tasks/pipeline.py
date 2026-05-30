"""Stage-by-stage analysis pipeline.

The first Phase 2 slice replaces the deterministic stub with real Whisper
transcription plus Gemini summary/sentiment enrichment:

    transcribe -> summarize -> sentiment

Diarization, turn persistence, dialogue-act classification, RAG, and analytics
remain future slices. Celery tasks use the sync SQLAlchemy session
(`SyncSessionLocal`) because worker processes do not share FastAPI's async
event loop.
"""

import json
import logging
from uuid import UUID

import redis
from celery import shared_task

from apps.worker.celery_app import celery_app  # noqa: F401  (ensures app is registered)
from core.config import settings
from core.db import Call, CallStatus, SyncSessionLocal
from core.domains.loader import load_domain
from core.pipeline import PIPELINE_STAGES, ProgressEvent, pipeline_channel
from pipeline.llm import gemini_client
from pipeline.transcription import transcribe_audio_with_segments

logger = logging.getLogger(__name__)
_redis = redis.from_url(settings.redis_url, decode_responses=True)


def _publish(
    call_id: str,
    stage: str,
    detail: str = "",
    extra: ProgressEvent | None = None,
) -> None:
    """Publish a progress event to `pipeline:{call_id}` for SSE consumers."""
    payload: ProgressEvent = {"call_id": call_id, "stage": stage, "detail": detail}
    if extra:
        payload.update(extra)
    _redis.publish(pipeline_channel(call_id), json.dumps(payload))


def _get_call(session, call_id: str) -> Call:
    call = session.get(Call, UUID(call_id))
    if call is None:
        raise RuntimeError(f"Call {call_id} not found")
    return call


def _set_stage(call_id: str, stage: str) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.status = CallStatus.PROCESSING
        call.current_stage = stage
        session.commit()


def _get_call_inputs(call_id: str) -> tuple[str, str]:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        return call.audio_path, call.domain_id


def _duration_from_segments(segments: list[dict]) -> float | None:
    ends = [float(segment["end"]) for segment in segments if segment.get("end") is not None]
    return max(ends) if ends else None


def _persist_transcription(call_id: str, result: dict) -> str:
    transcript = str(result.get("text", "")).strip()
    if not transcript:
        raise RuntimeError("Whisper returned an empty transcript")

    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.transcript = transcript
        call.language = result.get("language") or None
        call.duration_seconds = _duration_from_segments(result.get("segments", []))
        session.commit()
    return transcript


def _persist_summary(call_id: str, summary: str) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.summary = summary
        session.commit()


def _persist_sentiment(
    call_id: str,
    *,
    label: str,
    compound: float,
    key_emotions: list[str],
    arc_description: str,
) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.sentiment_label = label
        call.sentiment_compound = compound
        call.emotion_distribution_json = {
            "key_emotions": key_emotions,
            "arc_description": arc_description,
        }
        session.commit()


def _complete_pipeline(call_id: str, warnings: list[str]) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.status = CallStatus.COMPLETED
        call.current_stage = "complete"
        call.error_message = (
            f"LLM enrichment failed: {'; '.join(warnings)}" if warnings else None
        )
        session.commit()


def _mark_failed(call_id: str, error: Exception) -> None:
    with SyncSessionLocal() as session:
        call = session.get(Call, UUID(call_id))
        if call is not None:
            call.status = CallStatus.FAILED
            call.current_stage = "error"
            call.error_message = str(error)
            session.commit()


def _run_summary(call_id: str, domain_id: str, transcript: str, warnings: list[str]) -> None:
    _publish(call_id, "summarize", "Starting summary", {"status": "processing", "stub": False})
    _set_stage(call_id, "summarize")
    try:
        domain = load_domain(domain_id)
        summary = gemini_client.summarize(domain, transcript)
        _persist_summary(call_id, summary.summary)
        _publish(call_id, "summarize", "Completed summary", {"status": "processing", "stub": False})
    except Exception as exc:
        logger.exception("Summary enrichment failed for call %s", call_id)
        warnings.append("summary failed")
        _publish(
            call_id,
            "summarize",
            f"Summary failed: {exc}",
            {"status": "processing", "stub": False},
        )


def _run_sentiment(call_id: str, domain_id: str, transcript: str, warnings: list[str]) -> None:
    _publish(call_id, "sentiment", "Starting sentiment", {"status": "processing", "stub": False})
    _set_stage(call_id, "sentiment")
    try:
        domain = load_domain(domain_id)
        sentiment = gemini_client.analyze_sentiment(domain, transcript)
        _persist_sentiment(
            call_id,
            label=sentiment.overall_label,
            compound=sentiment.compound,
            key_emotions=sentiment.key_emotions,
            arc_description=sentiment.arc_description,
        )
        _publish(
            call_id,
            "sentiment",
            "Completed sentiment",
            {"status": "processing", "stub": False},
        )
    except Exception as exc:
        logger.exception("Sentiment enrichment failed for call %s", call_id)
        warnings.append("sentiment failed")
        _publish(
            call_id,
            "sentiment",
            f"Sentiment failed: {exc}",
            {"status": "processing", "stub": False},
        )


def _run_pipeline(call_id: str) -> dict:
    """Run the first real Phase 2 pipeline slice for one call."""
    logger.info("Pipeline started for call %s", call_id)
    warnings: list[str] = []
    try:
        _set_stage(call_id, "queued")
        _publish(
            call_id,
            "queued",
            "Pipeline received",
            {"status": "queued", "stub": False},
        )

        audio_path, domain_id = _get_call_inputs(call_id)

        _publish(
            call_id,
            "transcribe",
            "Starting transcription",
            {"status": "processing", "stub": False},
        )
        _set_stage(call_id, "transcribe")
        transcription = transcribe_audio_with_segments(audio_path, settings.whisper_model_size)
        transcript = _persist_transcription(call_id, transcription)
        _publish(
            call_id,
            "transcribe",
            "Completed transcription",
            {"status": "processing", "stub": False},
        )

        _run_summary(call_id, domain_id, transcript, warnings)
        _run_sentiment(call_id, domain_id, transcript, warnings)

        _complete_pipeline(call_id, warnings)
        final_payload: ProgressEvent = {"status": "completed", "stub": False}
        if warnings:
            final_payload["detail"] = f"Completed with warnings: {'; '.join(warnings)}"
        _publish(call_id, "complete", "Pipeline finished", final_payload)
        return {
            "call_id": call_id,
            "status": CallStatus.COMPLETED.value,
            "stages": PIPELINE_STAGES,
            "warnings": warnings,
        }

    except Exception as exc:
        logger.exception("Pipeline failed for call %s", call_id)
        try:
            _mark_failed(call_id, exc)
        except Exception:
            logger.exception("Also failed to mark call as FAILED")
        _publish(call_id, "error", str(exc), {"status": "failed", "stub": False})
        raise


@shared_task(name="conviq.run_pipeline", bind=True)
def run_pipeline(self, call_id: str) -> dict:
    return _run_pipeline(call_id)
