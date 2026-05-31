"""Shared DailyDialog helpers for dialogue-act training and evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.dialogue_act import (  # noqa: E402
    TRAINED_MODEL_BUCKETS,
    map_daily_dialog_act_to_app_bucket,
)

LABELS = list(TRAINED_MODEL_BUCKETS)
LABEL2ID = {label: index for index, label in enumerate(LABELS)}
ID2LABEL = {index: label for label, index in LABEL2ID.items()}
DAILY_DIALOG_FALLBACK_DATASET = "roskoN/dailydialog"


def load_daily_dialog_dataset(dataset_name: str = "daily_dialog") -> Any:
    from datasets import load_dataset

    try:
        return load_dataset(dataset_name, trust_remote_code=True)
    except Exception as exc:
        if dataset_name != "daily_dialog":
            raise
        print(
            f"Loading daily_dialog failed ({exc}); "
            f"falling back to {DAILY_DIALOG_FALLBACK_DATASET}"
        )
        return load_dataset(DAILY_DIALOG_FALLBACK_DATASET, trust_remote_code=True)


def flatten_daily_dialog_split(split: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for example in split:
        utterances = example.get("dialog") or example.get("utterances") or []
        acts = example.get("dialogue_act") or example.get("act") or example.get("acts") or []
        for text, act in zip(utterances, acts, strict=False):
            bucket = map_daily_dialog_act_to_app_bucket(act)
            text_value = str(text or "").strip()
            if not text_value or bucket not in LABEL2ID:
                continue
            rows.append({"text": text_value, "label": LABEL2ID[bucket]})
    return rows


def build_dataset(split: Any, max_samples: int | None = None) -> Any:
    from datasets import Dataset

    rows = flatten_daily_dialog_split(split)
    if max_samples is not None:
        rows = rows[:max_samples]
    if not rows:
        raise RuntimeError("DailyDialog split produced no trainable utterances")
    return Dataset.from_list(rows)


def compute_metrics_from_logits(logits: Any, labels: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import accuracy_score, f1_score

    predictions = np.argmax(logits, axis=-1)
    per_class = f1_score(
        labels,
        predictions,
        labels=list(range(len(LABELS))),
        average=None,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(labels, predictions, average="weighted", zero_division=0)),
        "per_class_f1": {
            label: float(score) for label, score in zip(LABELS, per_class, strict=True)
        },
    }


def write_metrics(path: Path, metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
