"""Offline tests for the Celery worker pipeline.

External systems are mocked: no Redis, Postgres, Whisper model, Hugging Face,
KeyBERT, Gemini API, or domain files are required for these tests.
"""

import json
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

    def flush(self) -> None:
        return None


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

    def fake_detect_emotions(turns: list[dict]) -> list[dict]:
        emotions = [("joy", 0.9), ("neutral", 0.8)]
        for index, turn in enumerate(turns):
            label, confidence = emotions[index % len(emotions)]
            turn["emotion"] = {
                "primary_emotion": label,
                "confidence": confidence,
                "all_scores": {label: confidence},
            }
        return turns

    def fake_classify_dialogue_acts(turns: list[dict]) -> SimpleNamespace:
        labels = [("question", 0.93), ("statement", 0.84), ("suggestion", 0.76)]
        for index, turn in enumerate(turns):
            label, confidence = labels[index % len(labels)]
            turn["dialogue_act"] = label
            turn["dialogue_act_confidence"] = confidence
        return SimpleNamespace(turns=turns, warning=None)

    monkeypatch.setattr(worker_pipeline, "diarize_with_pyannote", fake_diarize_with_pyannote)
    monkeypatch.setattr(worker_pipeline, "classify_dialogue_acts", fake_classify_dialogue_acts)
    monkeypatch.setattr(worker_pipeline, "detect_emotions_per_turn", fake_detect_emotions)
    monkeypatch.setattr(
        worker_pipeline,
        "extract_keywords",
        lambda transcript: {
            "keywords": [
                {"keyword": "actual audio", "score": 0.91},
                {"keyword": "conversation", "score": 0.72},
            ],
            "top_keywords": ["actual audio", "conversation"],
            "method": "test",
        },
    )
    return worker_pipeline, fake_redis, fake_sessions


def test_pipeline_persists_transcription_analytics_summary_and_sentiment(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, fake_redis, _ = _wire_common_mocks(monkeypatch, call)
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
    assert call.turns[0].emotion == "joy"
    assert call.turns[0].emotion_confidence == pytest.approx(0.9)
    assert call.turns[0].dialogue_act == "question"
    assert call.turns[0].dialogue_act_confidence == pytest.approx(0.93)
    assert call.turns[1].index == 1
    assert call.turns[1].speaker == "Student"
    assert call.turns[1].text == "from the actual audio."
    assert call.turns[1].emotion == "neutral"
    assert call.turns[1].emotion_confidence == pytest.approx(0.8)
    assert call.turns[1].dialogue_act == "statement"
    assert call.turns[1].dialogue_act_confidence == pytest.approx(0.84)
    assert call.dominant_emotion == "joy"
    assert call.emotion_distribution_json == {"joy": 0.5, "neutral": 0.5}
    assert call.keywords_json == [
        {"keyword": "actual audio", "score": 0.91},
        {"keyword": "conversation", "score": 0.72},
    ]
    assert call.analytics is not None
    assert call.analytics.primary_talk_seconds == pytest.approx(1.5)
    assert call.analytics.secondary_talk_seconds == pytest.approx(1.65)
    assert call.analytics.talk_time_ratio == pytest.approx(0.4762)
    assert call.analytics.primary_word_count == 1
    assert call.analytics.secondary_word_count == 4
    assert call.analytics.primary_question_count == 1
    assert call.analytics.primary_statement_count == 0
    assert call.analytics.primary_acknowledgment_count == 0
    assert call.analytics.primary_suggestion_count == 0
    assert call.summary == "Summary for: Hello from the actual audio."
    assert call.sentiment_label == "positive"
    assert call.sentiment_compound == pytest.approx(0.42)
    assert call.suggestions_json is None
    assert call.error_message is None

    stages = [json.loads(data)["stage"] for _, data in fake_redis.published]
    assert "analytics" in stages
    assert stages.index("diarize") < stages.index("analytics") < stages.index("summarize")


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


def test_pipeline_completes_with_warning_when_emotion_analytics_fails(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "Analytics can fail without failing the call.",
            "language": "en",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Analytics can fail"}],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())

    def fail_emotions(turns: list[dict]) -> list[dict]:
        raise RuntimeError("emotion model unavailable")

    monkeypatch.setattr(worker_pipeline, "detect_emotions_per_turn", fail_emotions)

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["status"] == "completed"
    assert result["warnings"] == ["analytics emotion classification failed"]
    assert call.status == CallStatus.COMPLETED
    assert call.current_stage == "complete"
    assert call.error_message == (
        "Pipeline completed with warnings: analytics emotion classification failed"
    )
    assert call.summary == "Summary for: Analytics can fail without failing the call."
    assert call.sentiment_label == "positive"
    assert call.turns[0].emotion is None
    assert call.dominant_emotion is None
    assert call.emotion_distribution_json == {}
    assert call.keywords_json == [
        {"keyword": "actual audio", "score": 0.91},
        {"keyword": "conversation", "score": 0.72},
    ]
    assert call.analytics is not None


def test_pipeline_completes_with_warning_when_dialogue_act_classifier_fails(
    monkeypatch: pytest.MonkeyPatch, call: Call
):
    worker_pipeline, _, _ = _wire_common_mocks(monkeypatch, call)
    monkeypatch.setattr(
        worker_pipeline,
        "transcribe_audio_with_segments",
        lambda path, model_size: {
            "text": "Dialogue act failures should not fail the call.",
            "language": "en",
            "segments": [{"start": 0.0, "end": 2.0, "text": "How are you?"}],
        },
    )
    monkeypatch.setattr(worker_pipeline, "gemini_client", SuccessfulGemini())
    monkeypatch.setattr(
        worker_pipeline,
        "classify_dialogue_acts",
        lambda turns: SimpleNamespace(turns=turns, warning="dialogue act unavailable"),
    )

    result = worker_pipeline._run_pipeline(str(call.id))

    assert result["status"] == "completed"
    assert result["warnings"] == ["dialogue act classification failed"]
    assert call.status == CallStatus.COMPLETED
    assert call.current_stage == "complete"
    assert call.error_message == (
        "Pipeline completed with warnings: dialogue act classification failed"
    )
    assert call.turns[0].dialogue_act is None
    assert call.turns[0].dialogue_act_confidence is None
    assert call.analytics is not None
    assert call.analytics.primary_question_count == 0


def test_speaker_analytics_counts_dialogue_acts_only_for_primary_speaker(monkeypatch):
    from apps.worker.tasks import pipeline as worker_pipeline

    fake_domain = SimpleNamespace(
        speakers=SimpleNamespace(primary="Counselor", secondary="Student")
    )
    monkeypatch.setattr(worker_pipeline, "load_domain", lambda domain_id: fake_domain)

    analytics = worker_pipeline._speaker_analytics(
        str(uuid4()),
        "counseling",
        [
            {
                "speaker": "Counselor",
                "text": "How are you feeling?",
                "start": 0.0,
                "end": 1.0,
                "dialogue_act": "question",
            },
            {
                "speaker": "Counselor",
                "text": "That makes sense.",
                "start": 1.0,
                "end": 2.0,
                "dialogue_act": "acknowledgment",
            },
            {
                "speaker": "Counselor",
                "text": "Try writing the first step down.",
                "start": 2.0,
                "end": 3.0,
                "dialogue_act": "suggestion",
            },
            {
                "speaker": "Student",
                "text": "I have a question.",
                "start": 3.0,
                "end": 4.0,
                "dialogue_act": "question",
            },
            {
                "speaker": "Counselor",
                "text": "We can review it tomorrow.",
                "start": 4.0,
                "end": 5.0,
                "dialogue_act": "statement",
            },
        ],
    )

    assert analytics.primary_question_count == 1
    assert analytics.primary_statement_count == 1
    assert analytics.primary_acknowledgment_count == 1
    assert analytics.primary_suggestion_count == 1


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
