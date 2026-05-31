#!/usr/bin/env python
"""Run the local three-sample ConvIQ demo benchmark against a live API."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from scripts.score_call_result import score_result

DEFAULT_AUDIO_DIR = Path("test_audio")
DEFAULT_GOLDEN_FILE = Path("eval/golden_samples.json")
DEFAULT_OUT = Path("eval/demo_baseline.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="ConvIQ API base URL")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="JSON artifact to write")
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--golden-file", type=Path, default=DEFAULT_GOLDEN_FILE)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api = args.api.rstrip("/")
    golden = _load_golden(args.golden_file)
    samples = _sample_audio_paths(args.audio_dir, golden)
    started = time.monotonic()
    results: list[dict[str, Any]] = []

    with httpx.Client(base_url=api, timeout=httpx.Timeout(60.0, read=60.0)) as client:
        for audio_path in samples:
            sample = _sample_for_audio(audio_path, golden)
            run = _run_one_sample(
                client=client,
                audio_path=audio_path,
                sample=sample,
                timeout_seconds=args.timeout_seconds,
                poll_seconds=args.poll_seconds,
            )
            results.append(run)
            print(
                f"{run['sample_id']}: {run['status']} "
                f"{run['score']['percent']:.2f}% "
                f"({run['elapsed_seconds']:.1f}s)"
            )

    artifact = {
        "version": 1,
        "kind": "local demo baseline",
        "generated_at": datetime.now(UTC).isoformat(),
        "api": api,
        "sample_count": len(results),
        "audio_dir": str(args.audio_dir),
        "golden_file": str(args.golden_file),
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "average_percent": round(
            sum(item["score"]["percent"] for item in results) / len(results), 2
        ),
        "samples": results,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


def _load_golden(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples") or []
    if not samples:
        raise SystemExit(f"No samples found in {path}")
    return samples


def _sample_audio_paths(audio_dir: Path, golden: list[dict[str, Any]]) -> list[Path]:
    paths = []
    for sample in golden:
        filenames = sample.get("audio_filenames") or []
        if not filenames:
            raise SystemExit(f"Golden sample {sample.get('id')} has no audio_filenames")
        path = audio_dir / filenames[0]
        if not path.exists():
            raise SystemExit(f"Missing sample audio: {path}")
        paths.append(path)
    return paths


def _sample_for_audio(audio_path: Path, golden: list[dict[str, Any]]) -> dict[str, Any]:
    for sample in golden:
        if audio_path.name in set(sample.get("audio_filenames") or []):
            return sample
    raise SystemExit(f"No golden sample matches {audio_path.name}")


def _run_one_sample(
    *,
    client: httpx.Client,
    audio_path: Path,
    sample: dict[str, Any],
    timeout_seconds: int,
    poll_seconds: float,
) -> dict[str, Any]:
    started = time.monotonic()
    with audio_path.open("rb") as audio_file:
        response = client.post(
            "/calls",
            data={"domain_id": "auto"},
            files={"audio": (audio_path.name, audio_file, "audio/mpeg")},
        )
    response.raise_for_status()
    queued = response.json()
    call_id = queued["id"]
    result = _wait_for_completion(client, call_id, timeout_seconds, poll_seconds)
    score = score_result(result, sample)
    if result.get("status") != "completed":
        raise SystemExit(f"{audio_path.name} ended with status {result.get('status')}: {result}")

    return {
        "sample_id": sample["id"],
        "audio_filename": audio_path.name,
        "call_id": call_id,
        "status": result.get("status"),
        "domain_id": result.get("domain_id"),
        "duration_seconds": result.get("duration_seconds"),
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "score": score,
    }


def _wait_for_completion(
    client: httpx.Client,
    call_id: str,
    timeout_seconds: int,
    poll_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = client.get(f"/calls/{call_id}")
        response.raise_for_status()
        last = response.json()
        if last.get("status") in {"completed", "failed"}:
            return last
        time.sleep(poll_seconds)
    raise SystemExit(f"Timed out waiting for call {call_id}; last state: {last}")


if __name__ == "__main__":
    main()
