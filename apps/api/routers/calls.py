"""Call endpoints: upload, status, progress stream, and export.

Phase 0 wires the endpoints to Postgres + Celery enqueue but the pipeline
itself is still a stub — see `apps.worker.tasks.pipeline`. Phase 2 fills it in.
"""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from apps.api.schemas import CallEnqueued, CallRead
from apps.worker.tasks.pipeline import run_pipeline
from core.config import settings
from core.db import Call, CallStatus, get_db
from core.domains import DomainNotFoundError, load_domain

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
    audio: UploadFile = File(..., description="Audio file"),
    domain_id: str = Form("counseling"),
    db: AsyncSession = Depends(get_db),
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
    call_id: uuid.UUID, db: AsyncSession = Depends(get_db)
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
async def stream_progress(call_id: uuid.UUID) -> EventSourceResponse:
    """Server-Sent Events stream of pipeline progress.

    Phase 0 emits a stub heartbeat. Phase 2 will subscribe to a Redis
    pub/sub channel `pipeline:{call_id}` and relay every stage event.
    """

    async def event_generator():
        for i in range(5):
            yield {"event": "progress", "data": f'{{"stage":"stub","step":{i}}}'}
            await asyncio.sleep(1)
        yield {"event": "complete", "data": '{"status":"stub"}'}

    return EventSourceResponse(event_generator())


@router.post("/{call_id}/export", status_code=501)
async def export_pdf(call_id: uuid.UUID) -> dict:
    """Generate a PDF report. Wired to `pipeline/report.py` in Phase 4."""
    raise HTTPException(
        status_code=501,
        detail="PDF export will be re-enabled in Phase 4 after the new pipeline lands.",
    )
