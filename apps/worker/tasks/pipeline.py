"""Stage-by-stage analysis pipeline.

The first Phase 2 slice replaces the deterministic stub with real Whisper
transcription plus Gemini summary/sentiment enrichment:

    transcribe -> diarize -> summarize -> sentiment

Dialogue-act classification, RAG, and analytics remain future slices. Celery
tasks use the sync SQLAlchemy session (`SyncSessionLocal`) because worker
processes do not share FastAPI's async event loop.
"""

import json
import logging
from typing import Any
from uuid import UUID

import redis
from celery import shared_task

from apps.worker.celery_app import celery_app  # noqa: F401  (ensures app is registered)
from core.config import settings
from core.db import Call, CallStatus, SyncSessionLocal, Turn
from core.domains.auto import AUTO_DOMAIN_ID, infer_domain_id
from core.domains.loader import load_domain
from core.pipeline import PIPELINE_STAGES, ProgressEvent, pipeline_channel
from pipeline.diarization import diarize_from_segments, diarize_with_pyannote
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


def _get_call_inputs(call_id: str) -> tuple[str, str, str]:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        return call.audio_path, call.audio_filename, call.domain_id


def _duration_from_segments(segments: list[dict]) -> float | None:
    ends = [float(segment["end"]) for segment in segments if segment.get("end") is not None]
    return max(ends) if ends else None


def _speaker_labels_for_domain(domain_id: str) -> list[str]:
    domain = load_domain(domain_id)
    return [domain.speakers.primary, domain.speakers.secondary]


def _resolve_domain_id(
    call_id: str,
    requested_domain_id: str,
    transcript: str,
    audio_filename: str,
) -> str:
    if requested_domain_id != AUTO_DOMAIN_ID:
        return requested_domain_id

    selected_domain_id = infer_domain_id(transcript, audio_filename)
    domain = load_domain(selected_domain_id)
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.domain_id = selected_domain_id
        session.commit()
    _publish(
        call_id,
        "transcribe",
        f"Auto-selected domain: {domain.display_name}",
        {"status": "processing", "stub": False},
    )
    return selected_domain_id


def _float_value(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _turn_emotion(turn: dict[str, Any]) -> tuple[str | None, float | None]:
    emotion = turn.get("emotion")
    if isinstance(emotion, dict):
        confidence = emotion.get("confidence")
        return (
            str(emotion.get("primary_emotion")) if emotion.get("primary_emotion") else None,
            _float_value(confidence) if confidence is not None else None,
        )
    if emotion:
        return str(emotion), _float_value(turn.get("emotion_confidence"))
    return None, None


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


def _persist_turns(call_id: str, turns: list[dict[str, Any]]) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        persisted_turns: list[Turn] = []
        for index, turn in enumerate(turns):
            start = _float_value(turn.get("start"))
            end = max(_float_value(turn.get("end"), start), start)
            emotion, emotion_confidence = _turn_emotion(turn)
            text = str(turn.get("text", "")).strip()
            if not text:
                continue
            persisted_turns.append(
                Turn(
                    index=index,
                    speaker=str(turn.get("speaker") or f"Speaker {index + 1}"),
                    text=text,
                    start_seconds=start,
                    end_seconds=end,
                    emotion=emotion,
                    emotion_confidence=emotion_confidence,
                )
            )

        call.turns = persisted_turns
        session.commit()


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


def _warning_message(warnings: list[str]) -> str | None:
    if not warnings:
        return None
    if set(warnings).issubset({"summary failed", "sentiment failed"}):
        return f"LLM enrichment failed: {'; '.join(warnings)}"
    return f"Pipeline completed with warnings: {'; '.join(warnings)}"


def _complete_pipeline(call_id: str, warnings: list[str]) -> None:
    with SyncSessionLocal() as session:
        call = _get_call(session, call_id)
        call.status = CallStatus.COMPLETED
        call.current_stage = "complete"
        call.error_message = _warning_message(warnings)
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


def _transcript_fallback_turn(transcription: dict, speaker_label: str) -> list[dict[str, Any]]:
    transcript = str(transcription.get("text", "")).strip()
    if not transcript:
        return []

    duration = _duration_from_segments(transcription.get("segments", [])) or 0.0
    return [
        {
            "speaker": speaker_label,
            "text": transcript,
            "start": 0.0,
            "end": duration,
        }
    ]


def _run_diarization(
    call_id: str,
    domain_id: str,
    audio_path: str,
    transcription: dict,
    warnings: list[str],
) -> list[dict[str, Any]]:
    _publish(call_id, "diarize", "Starting diarization", {"status": "processing", "stub": False})
    _set_stage(call_id, "diarize")

    speaker_labels = _speaker_labels_for_domain(domain_id)
    segments = transcription.get("segments", [])
    turns: list[dict[str, Any]] = []

    if settings.hf_token.strip():
        try:
            turns = diarize_with_pyannote(
                audio_path,
                segments,
                settings.hf_token,
                speaker_labels=speaker_labels,
                model_name=settings.pyannote_model,
                num_speakers=len(speaker_labels),
            )
            if not turns:
                warnings.append("diarization used pause heuristic")
                _publish(
                    call_id,
                    "diarize",
                    "pyannote returned no turns; using pause heuristic",
                    {"status": "processing", "stub": False},
                )
                turns = diarize_from_segments(segments, speaker_labels=speaker_labels)
        except Exception as exc:
            logger.exception("pyannote diarization failed for call %s", call_id)
            warnings.append("diarization used pause heuristic")
            _publish(
                call_id,
                "diarize",
                f"pyannote failed; using pause heuristic: {exc}",
                {"status": "processing", "stub": False},
            )
            turns = diarize_from_segments(segments, speaker_labels=speaker_labels)
    else:
        warnings.append("diarization used pause heuristic")
        _publish(
            call_id,
            "diarize",
            "HF_TOKEN is not set; using pause heuristic",
            {"status": "processing", "stub": False},
        )
        turns = diarize_from_segments(segments, speaker_labels=speaker_labels)

    if not turns:
        warnings.append("diarization produced transcript-only turn")
        turns = _transcript_fallback_turn(transcription, speaker_labels[0])

    _persist_turns(call_id, turns)
    _publish(
        call_id,
        "diarize",
        f"Completed diarization with {len(turns)} turns",
        {"status": "processing", "stub": False},
    )
    return turns


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

        audio_path, audio_filename, domain_id = _get_call_inputs(call_id)

        _publish(
            call_id,
            "transcribe",
            "Starting transcription",
            {"status": "processing", "stub": False},
        )
        _set_stage(call_id, "transcribe")
        transcription = transcribe_audio_with_segments(audio_path, settings.whisper_model_size)
        transcript = _persist_transcription(call_id, transcription)
        domain_id = _resolve_domain_id(call_id, domain_id, transcript, audio_filename)
        _publish(
            call_id,
            "transcribe",
            "Completed transcription",
            {"status": "processing", "stub": False},
        )

        _run_diarization(call_id, domain_id, audio_path, transcription, warnings)
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
