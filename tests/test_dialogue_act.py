"""Offline tests for dialogue-act runtime classification."""

from __future__ import annotations

import pytest

from pipeline import dialogue_act
from pipeline.dialogue_act import (
    DialogueActPrediction,
    acknowledgment_override,
    classify_dialogue_acts,
    heuristic_dialogue_act,
    map_daily_dialog_act_to_app_bucket,
    normalize_model_label,
)


class StubClassifier:
    def __init__(self, predictions: list[DialogueActPrediction]) -> None:
        self.predictions = predictions
        self.seen_texts: list[str] = []

    def predict_texts(self, texts: list[str]) -> list[DialogueActPrediction]:
        self.seen_texts = texts
        return self.predictions


def test_daily_dialog_labels_map_to_app_buckets():
    assert map_daily_dialog_act_to_app_bucket(1) == "statement"
    assert map_daily_dialog_act_to_app_bucket("inform") == "statement"
    assert map_daily_dialog_act_to_app_bucket(2) == "question"
    assert map_daily_dialog_act_to_app_bucket("directive") == "suggestion"
    assert map_daily_dialog_act_to_app_bucket(4) == "suggestion"
    assert map_daily_dialog_act_to_app_bucket(0) is None


def test_model_labels_normalize_to_app_buckets():
    assert normalize_model_label("LABEL_0") == "statement"
    assert normalize_model_label("LABEL_1") == "question"
    assert normalize_model_label("LABEL_2") == "suggestion"
    assert normalize_model_label("acknowledgment") == "acknowledgment"
    assert normalize_model_label("commissive") == "suggestion"
    assert normalize_model_label("something_else") is None


def test_acknowledgment_override_labels_short_low_content_phrases():
    for text in ("okay", "Yes.", "got it", "thanks a lot", "right", "sounds good"):
        prediction = acknowledgment_override(text)
        assert prediction is not None
        assert prediction.label == "acknowledgment"
        assert prediction.confidence == pytest.approx(0.99)

    assert acknowledgment_override("right now I need another option") is None


def test_heuristic_dialogue_act_labels_common_turn_shapes():
    assert heuristic_dialogue_act("Could you walk me through what happened?").label == "question"
    assert heuristic_dialogue_act("Let us make the plan honest.").label == "suggestion"
    assert heuristic_dialogue_act("The confirmation email said Thursday.").label == "statement"


def test_classify_dialogue_acts_applies_override_and_bounds_model_confidence(
    monkeypatch: pytest.MonkeyPatch,
):
    stub = StubClassifier(
        [
            DialogueActPrediction(label="question", confidence=1.4),
            DialogueActPrediction(label="suggestion", confidence=0.9),
        ]
    )
    monkeypatch.setattr(dialogue_act, "_get_classifier", lambda model_name: stub)

    result = classify_dialogue_acts(
        [
            {"speaker": "Counselor", "text": "Okay."},
            {"speaker": "Counselor", "text": "What feels hardest today?"},
            {"speaker": "Student", "text": "You should try a smaller plan."},
        ]
    )

    assert result.warning is None
    assert stub.seen_texts == ["What feels hardest today?", "You should try a smaller plan."]
    assert result.turns[0]["dialogue_act"] == "acknowledgment"
    assert result.turns[0]["dialogue_act_confidence"] == pytest.approx(0.99)
    assert result.turns[1]["dialogue_act"] == "question"
    assert result.turns[1]["dialogue_act_confidence"] == pytest.approx(1.0)
    assert result.turns[2]["dialogue_act"] == "suggestion"
    assert result.turns[2]["dialogue_act_confidence"] == pytest.approx(0.9)


def test_low_confidence_model_prediction_uses_heuristic_fallback(
    monkeypatch: pytest.MonkeyPatch,
):
    stub = StubClassifier(
        [
            DialogueActPrediction(label="question", confidence=0.35),
            DialogueActPrediction(label="question", confidence=0.35),
            DialogueActPrediction(label="question", confidence=0.35),
        ]
    )
    monkeypatch.setattr(dialogue_act, "_get_classifier", lambda model_name: stub)

    result = classify_dialogue_acts(
        [
            {"speaker": "Agent", "text": "The confirmation email says Thursday."},
            {"speaker": "Customer", "text": "Is it a real refund?"},
            {"speaker": "Agent", "text": "Please reply to the email if it is not visible."},
        ]
    )

    assert [turn["dialogue_act"] for turn in result.turns] == [
        "statement",
        "question",
        "suggestion",
    ]
    assert result.turns[0]["dialogue_act_confidence"] == pytest.approx(0.72)
    assert result.turns[1]["dialogue_act_confidence"] == pytest.approx(0.86)
    assert result.turns[2]["dialogue_act_confidence"] == pytest.approx(0.86)


def test_model_failure_returns_unlabeled_turns_and_warning(monkeypatch: pytest.MonkeyPatch):
    class FailingClassifier:
        def predict_texts(self, texts: list[str]) -> list[DialogueActPrediction]:
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(dialogue_act, "_get_classifier", lambda model_name: FailingClassifier())

    result = classify_dialogue_acts([{"speaker": "Counselor", "text": "How are you feeling?"}])

    assert result.warning == "dialogue act classification failed: model unavailable"
    assert "dialogue_act" not in result.turns[0]
    assert "dialogue_act_confidence" not in result.turns[0]
