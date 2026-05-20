"""Stage-by-stage analysis pipeline.

Phase 0 ships a stub that walks through fake stage names so the upload →
SSE stream → status flow can be demonstrated end-to-end. Phase 2 replaces
the stub with the real pipeline:

    transcribe → diarize → classify (dialogue act) → emotion → analytics →
    keywords → RAG retrieval → summarize → grounded suggestions

Celery tasks use the **sync** SQLAlchemy session (`SyncSessionLocal`) — never
the async one. Mixing async engines with `asyncio.run()` across multiple
Celery tasks silently breaks the connection pool.
"""

import json
import logging
import time
from uuid import UUID

import redis
from celery import shared_task

from apps.worker.celery_app import celery_app  # noqa: F401  (ensures app is registered)
from core.config import settings
from core.db import Call, CallStatus, SyncSessionLocal

logger = logging.getLogger(__name__)
_redis = redis.from_url(settings.redis_url, decode_responses=True)


def _publish(call_id: str, stage: str, detail: str = "", extra: dict | None = None) -> None:
    """Publish a progress event to `pipeline:{call_id}` for SSE consumers."""
    payload = {"stage": stage, "detail": detail, **(extra or {})}
    _redis.publish(f"pipeline:{call_id}", json.dumps(payload))


def _set_stage(call_id: str, stage: str) -> None:
    with SyncSessionLocal() as session:
        call = session.get(Call, UUID(call_id))
        if call is None:
            raise RuntimeError(f"Call {call_id} disappeared mid-pipeline")
        call.status = CallStatus.PROCESSING
        call.current_stage = stage
        session.commit()


@shared_task(name="conviq.run_pipeline", bind=True)
def run_pipeline(self, call_id: str) -> dict:
    """Run the analysis pipeline for one call. Phase 0 stub."""
    logger.info("Pipeline stub started for call %s", call_id)
    try:
        _set_stage(call_id, "queued")
        _publish(call_id, "queued", "Pipeline received")

        for stage in ("transcribe", "diarize", "classify", "emotion", "summarize"):
            _publish(call_id, stage, f"Starting {stage}")
            _set_stage(call_id, stage)
            time.sleep(1)  # placeholder for real stage work
            _publish(call_id, stage, f"Completed {stage}")

        with SyncSessionLocal() as session:
            call = session.get(Call, UUID(call_id))
            if call is None:
                raise RuntimeError(f"Call {call_id} disappeared at completion")
            call.status = CallStatus.COMPLETED
            call.current_stage = "complete"
            call.transcript = "[stub] Phase 0 — real pipeline lands in Phase 2."
            call.summary = "[stub] Pipeline scaffolding works; transcription not yet wired."
            session.commit()

        _publish(call_id, "complete", "Pipeline finished")
        return {"call_id": call_id, "status": CallStatus.COMPLETED.value, "stub": True}

    except Exception as e:
        logger.exception("Pipeline failed for call %s", call_id)
        try:
            with SyncSessionLocal() as session:
                call = session.get(Call, UUID(call_id))
                if call is not None:
                    call.status = CallStatus.FAILED
                    call.error_message = str(e)
                    session.commit()
        except Exception:
            logger.exception("Also failed to mark call as FAILED")
        _publish(call_id, "error", str(e))
        raise
