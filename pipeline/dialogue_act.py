"""Dialogue-act classification for diarized speaker turns.

The runtime-facing taxonomy is intentionally small:

- question
- statement
- acknowledgment
- suggestion

DailyDialog does not provide an acknowledgment class, so short low-content
acknowledgments are handled with a deterministic override. The DistilBERT model
is expected to predict the remaining buckets.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from core.config import PROJECT_ROOT, settings

logger = logging.getLogger(__name__)

DialogueActLabel = Literal["question", "statement", "acknowledgment", "suggestion"]

APP_BUCKETS: tuple[DialogueActLabel, ...] = (
    "question",
    "statement",
    "acknowledgment",
    "suggestion",
)
TRAINED_MODEL_BUCKETS: tuple[DialogueActLabel, ...] = ("statement", "question", "suggestion")

DAILY_DIALOG_ID_TO_APP_BUCKET: dict[int, DialogueActLabel] = {
    1: "statement",  # inform
    2: "question",
    3: "suggestion",  # directive
    4: "suggestion",  # commissive
}
DAILY_DIALOG_NAME_TO_APP_BUCKET: dict[str, DialogueActLabel] = {
    "inform": "statement",
    "statement": "statement",
    "question": "question",
    "directive": "suggestion",
    "commissive": "suggestion",
    "suggestion": "suggestion",
}
MODEL_LABEL_ID_TO_APP_BUCKET: dict[int, DialogueActLabel] = {
    0: "statement",
    1: "question",
    2: "suggestion",
    3: "acknowledgment",
}

ACKNOWLEDGMENT_CONFIDENCE = 0.99
RULE_CONFIDENCE = 0.86
STATEMENT_RULE_CONFIDENCE = 0.72
MODEL_CONFIDENCE_FALLBACK_THRESHOLD = 0.55
MODEL_TEXT_MAX_CHARS = 2_000

_ACK_CLEAN_RE = re.compile(r"[^a-z0-9']+")
_LABEL_ID_RE = re.compile(r"^(?:label_)?(\d+)$", re.IGNORECASE)
_QUESTION_START_RE = re.compile(
    r"^(?:who|what|when|where|why|how|can|could|would|will|do|does|did|"
    r"is|are|am|was|were|have|has|had|should)\b",
    re.IGNORECASE,
)
_SUGGESTION_RE = re.compile(
    r"\b(?:let's|let us|i suggest|i recommend|you should|we should|should try|"
    r"try to|try this|you may want to|you need to|you could|we can|we could|"
    r"please|make sure|next step|for the next|start with)\b",
    re.IGNORECASE,
)

_ACKNOWLEDGMENT_PHRASES = {
    "absolutely",
    "agreed",
    "ah",
    "alright",
    "awesome",
    "correct",
    "exactly",
    "fine",
    "good",
    "got it",
    "great",
    "i see",
    "makes sense",
    "mhm",
    "mm hmm",
    "okay",
    "ok",
    "perfect",
    "right",
    "sounds good",
    "sure",
    "thank you",
    "thanks",
    "thanks a lot",
    "that makes sense",
    "uh huh",
    "understood",
    "yes",
    "yeah",
    "yep",
}
_ACKNOWLEDGMENT_TOKENS = {
    "absolutely",
    "agreed",
    "alright",
    "correct",
    "exactly",
    "fine",
    "good",
    "great",
    "mhm",
    "okay",
    "ok",
    "perfect",
    "right",
    "sure",
    "thanks",
    "understood",
    "yes",
    "yeah",
    "yep",
}


@dataclass(frozen=True)
class DialogueActPrediction:
    label: DialogueActLabel | None
    confidence: float | None
    source: str = "model"


@dataclass(frozen=True)
class DialogueActBatchResult:
    turns: list[dict[str, Any]]
    warning: str | None = None


class DialogueActClassifier:
    """Lazy Hugging Face sequence-classification wrapper."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name
        self._pipeline: Any | None = None

    def predict_texts(self, texts: list[str]) -> list[DialogueActPrediction]:
        if not texts:
            return []

        classifier = self._load_pipeline()
        raw_outputs = classifier([text[:MODEL_TEXT_MAX_CHARS] for text in texts])
        if isinstance(raw_outputs, dict):
            raw_items: list[Any] = [raw_outputs]
        else:
            raw_items = list(raw_outputs)

        predictions: list[DialogueActPrediction] = []
        for raw_item in raw_items:
            output = _best_pipeline_output(raw_item)
            label = normalize_model_label(output.get("label"))
            confidence = _bounded_confidence(output.get("score")) if label is not None else None
            predictions.append(DialogueActPrediction(label=label, confidence=confidence))

        return predictions

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        model_ref = _resolve_model_ref(self.model_name or settings.dialogue_act_model)
        try:
            from transformers import pipeline

            logger.info("Loading dialogue-act model: %s", model_ref)
            self._pipeline = pipeline(
                "text-classification",
                model=model_ref,
                tokenizer=model_ref,
                truncation=True,
            )
            return self._pipeline
        except Exception as exc:
            raise RuntimeError(f"failed to load dialogue-act model '{model_ref}': {exc}") from exc


_CLASSIFIER_CACHE: dict[str, DialogueActClassifier] = {}


def map_daily_dialog_act_to_app_bucket(label: int | str) -> DialogueActLabel | None:
    """Map DailyDialog act labels to ConvIQ app buckets."""
    if isinstance(label, int):
        return DAILY_DIALOG_ID_TO_APP_BUCKET.get(label)

    normalized = _normalize_label_text(label)
    if normalized.isdigit():
        return DAILY_DIALOG_ID_TO_APP_BUCKET.get(int(normalized))
    return DAILY_DIALOG_NAME_TO_APP_BUCKET.get(normalized)


def normalize_model_label(label: Any) -> DialogueActLabel | None:
    """Normalize a model-emitted label into one app bucket."""
    normalized = _normalize_label_text(label)
    if normalized in APP_BUCKETS:
        return cast(DialogueActLabel, normalized)
    if normalized in DAILY_DIALOG_NAME_TO_APP_BUCKET:
        return DAILY_DIALOG_NAME_TO_APP_BUCKET[normalized]

    match = _LABEL_ID_RE.match(normalized)
    if match:
        return MODEL_LABEL_ID_TO_APP_BUCKET.get(int(match.group(1)))

    return None


def acknowledgment_override(text: str) -> DialogueActPrediction | None:
    """Return a deterministic acknowledgment prediction for short phrases."""
    normalized = _normalize_short_text(text)
    if not normalized:
        return None

    tokens = normalized.split()
    if len(tokens) > 5:
        return None

    if normalized in _ACKNOWLEDGMENT_PHRASES:
        return DialogueActPrediction(
            label="acknowledgment",
            confidence=ACKNOWLEDGMENT_CONFIDENCE,
            source="rule",
        )

    if len(tokens) <= 3 and all(token in _ACKNOWLEDGMENT_TOKENS for token in tokens):
        return DialogueActPrediction(
            label="acknowledgment",
            confidence=ACKNOWLEDGMENT_CONFIDENCE,
            source="rule",
        )

    return None


def heuristic_dialogue_act(text: str) -> DialogueActPrediction:
    """Deterministic backup for weak model predictions.

    This is intentionally conservative: it only marks obvious questions and
    suggestions, leaves short acknowledgments to the stronger override above,
    and treats everything else as a statement.
    """
    override = acknowledgment_override(text)
    if override is not None:
        return override

    stripped = text.strip()
    normalized = _normalize_short_text(stripped)

    if stripped.endswith("?") or _QUESTION_START_RE.match(normalized):
        return DialogueActPrediction(label="question", confidence=RULE_CONFIDENCE, source="rule")

    if _SUGGESTION_RE.search(normalized):
        return DialogueActPrediction(label="suggestion", confidence=RULE_CONFIDENCE, source="rule")

    return DialogueActPrediction(
        label="statement",
        confidence=STATEMENT_RULE_CONFIDENCE,
        source="rule",
    )


def classify_dialogue_acts(
    turns: list[dict[str, Any]],
    *,
    model_name: str | None = None,
) -> DialogueActBatchResult:
    """Classify diarized turns, returning annotated copies plus an optional warning."""
    annotated_turns = [dict(turn) for turn in turns]
    model_indices: list[int] = []
    model_texts: list[str] = []

    for index, turn in enumerate(annotated_turns):
        text = str(turn.get("text") or "").strip()
        if not text:
            continue

        override = acknowledgment_override(text)
        if override is not None:
            _apply_prediction(turn, override)
            continue

        model_indices.append(index)
        model_texts.append(text)

    if not model_texts:
        return DialogueActBatchResult(turns=annotated_turns)

    try:
        predictions = _get_classifier(model_name).predict_texts(model_texts)
    except Exception as exc:
        logger.warning("Dialogue-act classification failed: %s", exc)
        return DialogueActBatchResult(
            turns=annotated_turns,
            warning=f"dialogue act classification failed: {exc}",
        )

    for index, prediction, text in zip(model_indices, predictions, model_texts, strict=False):
        if _should_use_heuristic(prediction):
            prediction = heuristic_dialogue_act(text)
        _apply_prediction(annotated_turns[index], prediction)

    return DialogueActBatchResult(turns=annotated_turns)


def clear_model_cache() -> None:
    _CLASSIFIER_CACHE.clear()


def _get_classifier(model_name: str | None) -> DialogueActClassifier:
    cache_key = model_name or settings.dialogue_act_model
    if cache_key not in _CLASSIFIER_CACHE:
        _CLASSIFIER_CACHE[cache_key] = DialogueActClassifier(model_name)
    return _CLASSIFIER_CACHE[cache_key]


def _apply_prediction(turn: dict[str, Any], prediction: DialogueActPrediction) -> None:
    if prediction.label is None:
        return

    turn["dialogue_act"] = prediction.label
    if prediction.confidence is not None:
        turn["dialogue_act_confidence"] = _bounded_confidence(prediction.confidence)


def _should_use_heuristic(prediction: DialogueActPrediction) -> bool:
    if prediction.label is None or prediction.confidence is None:
        return True
    return prediction.confidence < MODEL_CONFIDENCE_FALLBACK_THRESHOLD


def _best_pipeline_output(raw_item: Any) -> dict[str, Any]:
    if isinstance(raw_item, list):
        candidates = [item for item in raw_item if isinstance(item, dict)]
        if not candidates:
            return {}
        return max(candidates, key=lambda item: float(item.get("score") or 0.0))

    if isinstance(raw_item, dict):
        return raw_item

    return {}


def _bounded_confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return round(min(1.0, max(0.0, score)), 4)


def _normalize_label_text(label: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(label or "").strip().lower()).strip("_")


def _normalize_short_text(text: str) -> str:
    cleaned = _ACK_CLEAN_RE.sub(" ", text.strip().lower().replace("\u2019", "'"))
    return re.sub(r"\s+", " ", cleaned).strip()


def _resolve_model_ref(model_ref: str) -> str:
    if _looks_like_local_model_ref(model_ref):
        path = Path(model_ref).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            raise RuntimeError(f"local dialogue-act model artifact not found at {path}")
        return str(path)

    return model_ref


def _looks_like_local_model_ref(model_ref: str) -> bool:
    return (
        model_ref.startswith(("/", "./", "../", "~"))
        or model_ref == "models"
        or model_ref.startswith("models/")
    )
