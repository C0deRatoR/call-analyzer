"""Shared pipeline contracts used by the API and Celery worker."""

from __future__ import annotations

from typing import Literal, TypedDict

PipelineStatus = Literal["queued", "processing", "completed", "failed"]

PIPELINE_STAGES: tuple[str, ...] = (
    "transcribe",
    "diarize",
    "summarize",
    "sentiment",
)

STUB_PIPELINE_STAGES: tuple[str, ...] = PIPELINE_STAGES


class ProgressEvent(TypedDict, total=False):
    call_id: str
    status: PipelineStatus
    stage: str
    detail: str
    stub: bool


def pipeline_channel(call_id: str) -> str:
    """Return the Redis pub/sub channel for a call pipeline."""
    return f"pipeline:{call_id}"
