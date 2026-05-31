"""Offline tests for the Celery worker pipeline.

External systems are mocked: no Redis, Postgres, Whisper model, Gemini API, or
domain files are required for these tests.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from core.db import Call, CallStatus
from core.domains.auto import AUTO_DOMAIN_ID
from core.llm.schemas import SentimentResponse, SummaryResponse


class FakeRedis:
    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []

    def publish(self, channel: str, data: str) -> None:
        self.published.append((channel, data))


class FakeSession:
    def __init__(self, call: Call) -> None:
        self.call = call
        self.commits = 0

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, model: type[Call], key: object) -> Call | None:
        if model is Call and key == self.call.id:
            return self.call
        return None

    def commit(self) -> None:
        self.commits += 1


class FakeSessionLocal:
    def __init__(self, call: Call) -> None:
        self.call = call
        self.sessions: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        session = FakeSession(self.call)
        self.sessions.append(session)
        return session


class SuccessfulGemini:
    def summarize(self, domain: object, transcript: str) -> SummaryResponse:
        return SummaryResponse(
            summary=f"Summary for: {transcript}",
            key_topics=["topic"],
            next_steps=["next"],
        )

    def analyze_sentiment(self, domain: object, transcript: str) -> SentimentResponse:
        return SentimentResponse(
            overall_label="positive",
            compound=0.42,
            key_emotions=["hope"],
            arc_description="The call became more constructive.",
        )


class FailingGemini:
    def summarize(self, domain: object, transcript: str) -> SummaryResponse:
        raise RuntimeError("summary API down")

    def analyze_sentiment(self, domain: object, transcript: str) -> SentimentResponse:
        raise RuntimeError("sentiment API down")


@pytest.fixture
def call() -> Call:
    return Call(
        id=uuid4(),
        audio_filename="sample.wav",
        audio_path="/tmp/sample.wav",
        domain_id="counseling",
        status=CallStatus.QUEUED,
    )


def _wire_common_mocks(monkeypatch: pytest.MonkeyPatch, call: Call):
    from apps.worker.tasks import pipeline as worker_pipeline

    fake_redis = FakeRedis()
    fake_sessions = FakeSessionLocal(call)
    fake_domain = SimpleNamespace(
        speakers=SimpleNamespace(primary="Counselor", secondary="Student")
    )
    monkeypatch.setattr(worker_pipeline, "_redis", fake_redis)
    monkeypatch.setattr(worker_pipeline, "SyncSessionLocal", fake_sessions)
    monkeypatch.setattr(worker_pipeline, "load_domain", lambda domain_id: fake_domain)
    monkeypatch.setattr(worker_pipeline.settings, "whisper_model_size", "tiny")
    monkeypatch.setattr(worker_pipeline.settings, "hf_token", "hf_test")
    monkeypatch.setattr(worker_pipeline.settings, "pyannote_model", "test-pyannote")

    def fake_diarize_with_pyannote(
        path: str,
        segments: list[dict],
        hf_token: str,
        speaker_labels: list[str],
        model_name: str,
        num_speakers: int,
    ) -> list[dict]:
        return [
            {
                "speaker": speaker_labels[index % len(speaker_labels)],
                "text": segment["text"],
                "start": segment["start"],
                "end": segment["end"],
            }
            for index, segment in enumerate(segments)
        ]

    monkeypatch.setattr(worker_pipeline, "diarize_with_pyannote", fake_diarize_with_pyannote)
    return worker_pipeline, fake_redis, fake_sessions


def test_pipeline_persists_transcription_summary_and_sentiment(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "Hello from the actual audio.",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "Hello"},
                {"start": 1.6, "end": 3.25, "text": "from the actual audio."},
            ],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["status"] == "completed"
    assert result["warnings"] == []
    assert call.status == CallStatus.COMPLETED
    assert call.current_stage == "complete"
    assert call.transcript == "Hello from the actual audio."
    assert call.language == "en"
    assert call.duration_seconds == pytest.approx(3.25)
    assert len(call.turns) == 2
    assert call.turns[0].index == 0
    assert call.turns[0].speaker == "Counselor"
    assert call.turns[0].text == "Hello"
    assert call.turns[0].start_seconds == pytest.approx(0.0)
    assert call.turns[0].end_seconds == pytest.approx(1.5)
    assert call.turns[1].index == 1
    assert call.turns[1].speaker == "Student"
    assert call.turns[1].text == "from the actual audio."
    assert call.summary == "Summary for: Hello from the actual audio."
    assert call.sentiment_label == "positive"
    assert call.sentiment_compound == pytest.approx(0.42)
    assert call.emotion_distribution_json == {
        "key_emotions": ["hope"],
        "arc_description": "The call became more constructive.",
    }
    assert call.error_message is None


def test_pipeline_auto_selects_domain_after_transcription(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    call.domain_id = AUTO_DOMAIN_ID
    call.audio_filename = "ambiguous_upload.wav"

    domains = {
        "sales": SimpleNamespace(
            display_name="Sales Call",
            speakers=SimpleNamespace(primary="Salesperson", secondary="Prospect"),
        )
    }
    monkeypatch.setattr(worker_pipeline, "load_domain", lambda domain_id: domains[domain_id])
    monkeypatch.setattr(worker_pipeline, "infer_domain_id", lambda transcript, filename: "sales")
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "The prospect asked about budget and a pilot.",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "The prospect asked about budget."},
                {"start": 1.6, "end": 3.25, "text": "A pilot is the next step."},
            ],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["status"] == "completed"
    assert call.domain_id == "sales"
    assert [turn.speaker for turn in call.turns] == ["Salesperson", "Prospect"]
    assert call.summary == "Summary for: The prospect asked about budget and a pilot."


def test_pipeline_fails_when_transcription_fails(monkeypatch: pytest.MonkeyPatch, call: Call):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)

    def fail_transcription(path: str, model_size: str) -> dict:
        raise RuntimeError("audio decode failed")

    monkeypatch.setattr(worker_pipeline, "transcribe_audio_with_segments", fail_transcription)
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())

    with pytest.raises(RuntimeError, match="audio decode failed"):
        worker_pipeline._run_pipeline(str(call.id))

    assert call.status == CallStatus.FAILED
    assert call.current_stage == "error"
    assert call.error_message == "audio decode failed"


def test_pipeline_completes_with_transcript_when_gemini_fails(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "Transcript survives LLM failure.",
            "language": "en",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Transcript"}],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", FailingGemini())

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["status"] == "completed"
    assert result["warnings"] == ["summary failed", "sentiment failed"]
    assert call.status == CallStatus.COMPLETED
    assert call.current_stage == "complete"
    assert call.transcript == "Transcript survives LLM failure."
    assert call.summary is None
    assert call.sentiment_label is None
    assert call.error_message == "LLM enrichment failed: summary failed; sentiment failed"


def test_pipeline_falls_back_to_pause_diarization_without_hf_token(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    monkeypatch.setattr(worker_pipeline.settings, "hf_token", "")
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "Counselor starts. Student answers.",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Counselor starts."},
                {"start": 3.0, "end": 4.0, "text": "Student answers."},
            ],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["warnings"] == ["diarization used pause heuristic"]
    assert call.status == CallStatus.COMPLETED
    assert call.error_message == (
        "Pipeline completed with warnings: diarization used pause heuristic"
    )
    assert [turn.speaker for turn in call.turns] == ["Counselor", "Student"]
    assert [turn.text for turn in call.turns] == ["Counselor starts.", "Student answers."]
