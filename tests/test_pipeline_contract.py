"""Tests for the shared API/worker pipeline progress contract."""

import json

from core.pipeline import PIPELINE_STAGES, pipeline_channel


def test_pipeline_channel_is_stable():
    assert pipeline_channel("call-123") == "pipeline:call-123"


def test_pipeline_stages_match_current_contract():
    assert PIPELINE_STAGES == (
        "transcribe",
        "summarize",
        "sentiment",
    )


def test_worker_publish_uses_shared_channel(monkeypatch):
    from apps.worker.tasks import pipeline as worker_pipeline

    published: list[tuple[str, str]] = []

    class FakeRedis:
        def publish(self, channel: str, data: str) -> None:
            published.append((channel, data))

    monkeypatch.setattr(worker_pipeline, "_redis", FakeRedis())

    worker_pipeline._publish(
        "call-123",
        "transcribe",
        "Starting transcribe",
        {"status": "processing", "stub": False},
    )

    assert published
    channel, data = published[0]
    assert channel == "pipeline:call-123"
    payload = json.loads(data)
    assert payload == {
        "call_id": "call-123",
        "stage": "transcribe",
        "detail": "Starting transcribe",
        "status": "processing",
        "stub": False,
    }
