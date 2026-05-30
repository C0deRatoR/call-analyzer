"""Call endpoints: upload, status, progress stream, and export.

Phase 0 wires the endpoints to Postgres + Celery enqueue but the pipeline
itself is still a stub — see `apps.worker.tasks.pipeline`. Phase 2 fills it in.
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from apps.api.schemas import CallEnqueued, CallRead
from apps.worker.tasks.pipeline import run_pipeline
from core.config import settings
from core.db import Call, CallStatus, get_db
from core.domains import DomainNotFoundError, load_domain
from core.pipeline import pipeline_channel

router = APIRouter(prefix="/calls", tags=["calls"])


def _validate_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_audio_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported audio format '.{ext}'. "
                f"Allowed: {', '.join(settings.allowed_audio_extensions)}"
            ),
        )
    return ext


async def _save_upload(file: UploadFile, ext: str) -> Path:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    target = settings.uploads_dir / f"{uuid.uuid4().hex}.{ext}"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    written = 0
    with target.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.max_upload_mb} MB limit",
                )
            f.write(chunk)
    return target


@router.post("", response_model=CallEnqueued, status_code=202)
async def create_call(
    audio: Annotated[UploadFile, File(description="Audio file")],
    db: Annotated[AsyncSession, Depends(get_db)],
    domain_id: Annotated[str, Form()] = "counseling",
) -> CallEnqueued:
    """Upload an audio file and enqueue it for analysis.

    Returns 202 Accepted with the call id and the SSE stream URL to watch
    pipeline progress. Poll `GET /calls/{id}` for the full result once
    `status == "completed"`.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = _validate_extension(audio.filename)

    try:
        load_domain(domain_id)
    except DomainNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    saved_path = await _save_upload(audio, ext)

    call = Call(
        audio_filename=audio.filename,
        audio_path=str(saved_path),
        domain_id=domain_id,
        status=CallStatus.QUEUED,
    )
    db.add(call)
    await db.flush()
    call_id = call.id  # capture before commit closes the session
    await db.commit()

    run_pipeline.delay(str(call_id))

    return CallEnqueued(
        id=call_id,
        status=CallStatus.QUEUED.value,
        stream_url=f"/calls/{call_id}/stream",
    )


@router.get("/{call_id}", response_model=CallRead)
async def get_call(
    call_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CallRead:
    stmt = (
        select(Call)
        .where(Call.id == call_id)
        .options(selectinload(Call.turns), selectinload(Call.analytics))
    )
    result = await db.execute(stmt)
    call = result.scalar_one_or_none()
    if call is None:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return CallRead.model_validate(call)


@router.get("/{call_id}/stream")
async def stream_progress(
    call_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventSourceResponse:
    """Server-Sent Events stream of pipeline progress.

    Relays Redis pub/sub events from `pipeline:{call_id}`. The worker is still
    using deterministic stub stages, but the streaming contract is the same one
    the real Phase 2 pipeline will use.
    """
    call = await db.get(Call, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")

    async def event_generator():
        initial = {
            "call_id": str(call_id),
            "status": call.status.value,
            "stage": call.current_stage,
        }
        yield {"event": "status", "data": json.dumps(initial)}

        if call.status in {CallStatus.COMPLETED, CallStatus.FAILED}:
            terminal_event = "complete" if call.status == CallStatus.COMPLETED else "error"
            yield {"event": terminal_event, "data": json.dumps(initial)}
            return

        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(pipeline_channel(str(call_id)))
        try:
            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    await db.refresh(call)
                    if call.status in {CallStatus.COMPLETED, CallStatus.FAILED}:
                        terminal = {
                            "call_id": str(call_id),
                            "status": call.status.value,
                            "stage": call.current_stage,
                        }
                        terminal_event = (
                            "complete" if call.status == CallStatus.COMPLETED else "error"
                        )
                        yield {"event": terminal_event, "data": json.dumps(terminal)}
                        break
                    yield {"event": "heartbeat", "data": "{}"}
                    await asyncio.sleep(0.2)
                    continue

                data = message["data"]
                event_name = "progress"
                try:
                    payload = json.loads(data)
                    if payload.get("stage") == "complete" or payload.get("status") == "completed":
                        event_name = "complete"
                    elif payload.get("stage") == "error" or payload.get("status") == "failed":
                        event_name = "error"
                except json.JSONDecodeError:
                    payload = {"detail": data}
                    data = json.dumps(payload)

                yield {"event": event_name, "data": data}
                if event_name in {"complete", "error"}:
                    break
        finally:
            await pubsub.unsubscribe(pipeline_channel(str(call_id)))
            await pubsub.close()
            await redis_client.close()

    return EventSourceResponse(event_generator())


@router.post("/{call_id}/export", status_code=501)
async def export_pdf(call_id: uuid.UUID) -> dict:
    """Generate a PDF report after the new pipeline result shape is finalized."""
    raise HTTPException(
        status_code=501,
        detail="PDF export will be re-enabled in Phase 4 after the new pipeline lands.",
    )
