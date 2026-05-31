#!/usr/bin/env python
"""Evaluate a saved dialogue-act classifier on DailyDialog."""

from __future__ import annotations

import argparse
import inspect
from pathlib import Path
from typing import Any

from dialogue_act_data import (
    build_dataset,
    compute_metrics_from_logits,
    load_daily_dialog_dataset,
    write_metrics,
)

DEFAULT_MODEL_DIR = "models/dialogue-act/distilbert-dailydialog-app-buckets"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-name", default="daily_dialog")
    parser.add_argument("--model-dir", type=Path, default=Path(DEFAULT_MODEL_DIR))
    parser.add_argument("--metrics-file", type=Path, default=None)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-eval-samples", type=int, default=None)
    parser.add_argument("--max-length", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )

    raw_daily_dialog = load_daily_dialog_dataset(args.dataset_name)
    eval_dataset = build_dataset(raw_daily_dialog[args.split], args.max_eval_samples)
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)

    def tokenize_batch(batch: dict[str, list[str]]) -> dict[str, Any]:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_length,
        )

    tokenized = eval_dataset.map(tokenize_batch, batched=True, remove_columns=["text"])
    model = AutoModelForSequenceClassification.from_pretrained(args.model_dir)

    training_args = TrainingArguments(
        output_dir=str(args.model_dir / "eval-tmp"),
        per_device_eval_batch_size=args.batch_size,
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        **_trainer_tokenizer_kwargs(Trainer, tokenizer),
    )

    prediction_output = trainer.predict(tokenized)
    metrics = compute_metrics_from_logits(
        prediction_output.predictions,
        prediction_output.label_ids,
    )
    metrics["split"] = args.split
    metrics["num_eval_samples"] = len(tokenized)

    metrics_file = args.metrics_file or args.model_dir / f"{args.split}_metrics.json"
    write_metrics(metrics_file, metrics)


def _trainer_tokenizer_kwargs(trainer_cls: type, tokenizer: Any) -> dict[str, Any]:
    signature = inspect.signature(trainer_cls.__init__)
    if "processing_class" in signature.parameters:
        return {"processing_class": tokenizer}
    if "tokenizer" in signature.parameters:
        return {"tokenizer": tokenizer}
    return {}


if __name__ == "__main__":
    main()
