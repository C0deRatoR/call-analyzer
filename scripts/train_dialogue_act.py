#!/usr/bin/env python
"""Fine-tune DistilBERT on DailyDialog app-bucket dialogue acts."""

from __future__ import annotations

import argparse
import inspect
import os
from pathlib import Path
from typing import Any

from dialogue_act_data import (
    ID2LABEL,
    LABEL2ID,
    build_dataset,
    compute_metrics_from_logits,
    load_daily_dialog_dataset,
    write_metrics,
)

DEFAULT_OUTPUT_DIR = "models/dialogue-act/distilbert-dailydialog-app-buckets"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-name", default="daily_dialog")
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--metrics-file", type=Path, default=None)
    parser.add_argument("--num-train-epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--train-batch-size", type=int, default=16)
    parser.add_argument("--eval-batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-eval-samples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--push-to-hub", action="store_true")
    parser.add_argument("--hub-model-id", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from datasets import DatasetDict
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )

    if args.push_to_hub:
        _validate_hub_env()

    raw_daily_dialog = load_daily_dialog_dataset(args.dataset_name)
    raw_datasets = DatasetDict(
        {
            "train": build_dataset(raw_daily_dialog["train"], args.max_train_samples),
            "validation": build_dataset(raw_daily_dialog["validation"], args.max_eval_samples),
            "test": build_dataset(raw_daily_dialog["test"], args.max_eval_samples),
        }
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_batch(batch: dict[str, list[str]]) -> dict[str, Any]:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_length,
        )

    tokenized = raw_datasets.map(tokenize_batch, batched=True, remove_columns=["text"])
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    training_args = _build_training_args(args, TrainingArguments)

    def compute_metrics(eval_pred: Any) -> dict[str, Any]:
        return compute_metrics_from_logits(eval_pred.predictions, eval_pred.label_ids)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
        **_trainer_tokenizer_kwargs(Trainer, tokenizer),
    )

    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    prediction_output = trainer.predict(tokenized["test"])
    metrics = compute_metrics_from_logits(
        prediction_output.predictions,
        prediction_output.label_ids,
    )
    metrics["num_train_samples"] = len(tokenized["train"])
    metrics["num_validation_samples"] = len(tokenized["validation"])
    metrics["num_test_samples"] = len(tokenized["test"])

    metrics_file = args.metrics_file or args.output_dir / "eval_metrics.json"
    write_metrics(metrics_file, metrics)

    if args.push_to_hub:
        trainer.push_to_hub(commit_message="Train DailyDialog dialogue-act classifier")


def _build_training_args(args: argparse.Namespace, training_arguments_cls: type) -> Any:
    kwargs: dict[str, Any] = {
        "output_dir": str(args.output_dir),
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.train_batch_size,
        "per_device_eval_batch_size": args.eval_batch_size,
        "num_train_epochs": args.num_train_epochs,
        "weight_decay": 0.01,
        "save_strategy": "epoch",
        "logging_steps": 25,
        "report_to": [],
        "seed": args.seed,
        "push_to_hub": args.push_to_hub,
    }

    signature = inspect.signature(training_arguments_cls.__init__)
    eval_strategy_key = (
        "eval_strategy" if "eval_strategy" in signature.parameters else "evaluation_strategy"
    )
    kwargs[eval_strategy_key] = "epoch"

    if args.push_to_hub:
        kwargs["hub_model_id"] = _hub_model_id(args)
        hub_token = os.environ.get("HF_TOKEN")
        if "hub_token" in signature.parameters and hub_token:
            kwargs["hub_token"] = hub_token

    return training_arguments_cls(**kwargs)


def _trainer_tokenizer_kwargs(trainer_cls: type, tokenizer: Any) -> dict[str, Any]:
    signature = inspect.signature(trainer_cls.__init__)
    if "processing_class" in signature.parameters:
        return {"processing_class": tokenizer}
    if "tokenizer" in signature.parameters:
        return {"tokenizer": tokenizer}
    return {}


def _validate_hub_env() -> None:
    missing = [name for name in ("HF_TOKEN", "HF_USERNAME") if not os.environ.get(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"--push-to-hub requires {joined} to be set")


def _hub_model_id(args: argparse.Namespace) -> str:
    if args.hub_model_id:
        return str(args.hub_model_id)
    return f"{os.environ['HF_USERNAME']}/distilbert-dailydialog-app-buckets"


if __name__ == "__main__":
    main()
