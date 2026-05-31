#!/usr/bin/env python
"""Score a ConvIQ call result against local golden sample expectations."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.request import urlopen

DEFAULT_GOLDEN_FILE = Path("eval/golden_samples.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--result-json", type=Path, help="Saved GET /calls/{id} JSON payload")
    source.add_argument("--call-id", help="Fetch GET /calls/{id} from --base-url")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--golden-file", type=Path, default=DEFAULT_GOLDEN_FILE)
    parser.add_argument("--sample-id", help="Override automatic sample matching")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = _load_result(args)
    sample = _find_sample(result, args.golden_file, args.sample_id)
    report = score_result(result, sample)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)


def score_result(result: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    turns = _turns(result)
    transcript = _transcript_text(result, turns)
    warning_text = str(result.get("error_message") or "")

    checks = [
        _domain_check(result, sample),
        _speaker_check(turns, sample),
        _turn_count_check(turns, sample),
        _speaker_switch_check(turns, sample),
        _phrase_recall_check(transcript, sample),
        _forbidden_phrase_check(transcript, sample),
        _dialogue_act_coverage_check(turns, sample),
        _warning_check(warning_text, sample),
    ]

    score = round(sum(check["score"] for check in checks), 2)
    max_score = sum(check["weight"] for check in checks)
    return {
        "sample_id": sample["id"],
        "audio_filename": result.get("audio_filename"),
        "call_id": result.get("id"),
        "status": result.get("status"),
        "score": score,
        "max_score": max_score,
        "percent": round(score / max_score * 100, 2) if max_score else 0.0,
        "turn_count": len(turns),
        "speaker_switches": _speaker_switches(turns),
        "checks": checks,
    }


def _load_result(args: argparse.Namespace) -> dict[str, Any]:
    if args.result_json:
        return json.loads(args.result_json.read_text(encoding="utf-8"))

    url = f"{args.base_url.rstrip('/')}/calls/{args.call_id}"
    with urlopen(url, timeout=20) as response:
        return json.load(response)


def _find_sample(
    result: dict[str, Any],
    golden_file: Path,
    sample_id: str | None,
) -> dict[str, Any]:
    golden = json.loads(golden_file.read_text(encoding="utf-8"))
    samples = list(golden.get("samples") or [])

    if sample_id:
        for sample in samples:
            if sample.get("id") == sample_id:
                return sample
        raise SystemExit(f"Sample id {sample_id!r} was not found in {golden_file}")

    filename = Path(str(result.get("audio_filename") or "")).name
    for sample in samples:
        if filename in set(sample.get("audio_filenames") or []):
            return sample

    raise SystemExit(
        f"No golden sample matched audio filename {filename!r}; use --sample-id to choose one"
    )


def _turns(result: dict[str, Any]) -> list[dict[str, Any]]:
    raw_turns = result.get("turns") or result.get("diarized_turns") or []
    return [turn for turn in raw_turns if isinstance(turn, dict)]


def _transcript_text(result: dict[str, Any], turns: list[dict[str, Any]]) -> str:
    transcript = str(result.get("transcript") or "").strip()
    if transcript:
        return transcript
    return " ".join(str(turn.get("text") or "") for turn in turns)


def _domain_check(result: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    expected = sample.get("expected_domain_id")
    actual = result.get("domain_id")
    passed = actual == expected
    return _check(
        "domain",
        10,
        10 if passed else 0,
        passed,
        f"expected {expected}, got {actual}",
    )


def _speaker_check(turns: list[dict[str, Any]], sample: dict[str, Any]) -> dict[str, Any]:
    expected = set(sample.get("expected_speakers") or [])
    actual = {str(turn.get("speaker") or "") for turn in turns}
    missing = sorted(expected - actual)
    passed = not missing
    return _check(
        "speaker_labels",
        15,
        15 if passed else 15 * (len(expected) - len(missing)) / max(len(expected), 1),
        passed,
        f"missing {missing}" if missing else f"found {sorted(actual)}",
    )


def _turn_count_check(turns: list[dict[str, Any]], sample: dict[str, Any]) -> dict[str, Any]:
    minimum = int(sample.get("min_turns") or 0)
    actual = len(turns)
    ratio = min(actual / minimum, 1.0) if minimum else 1.0
    return _check(
        "turn_count",
        15,
        15 * ratio,
        actual >= minimum,
        f"expected >= {minimum}, got {actual}",
    )


def _speaker_switch_check(turns: list[dict[str, Any]], sample: dict[str, Any]) -> dict[str, Any]:
    minimum = int(sample.get("min_speaker_switches") or 0)
    actual = _speaker_switches(turns)
    ratio = min(actual / minimum, 1.0) if minimum else 1.0
    return _check(
        "speaker_switches",
        15,
        15 * ratio,
        actual >= minimum,
        f"expected >= {minimum}, got {actual}",
    )


def _phrase_recall_check(transcript: str, sample: dict[str, Any]) -> dict[str, Any]:
    phrases = [str(phrase) for phrase in sample.get("required_phrases") or []]
    if not phrases:
        return _check("required_phrases", 15, 15, True, "no required phrases configured")

    normalized = _normalize(transcript)
    found = [phrase for phrase in phrases if _normalize(phrase) in normalized]
    missing = [phrase for phrase in phrases if phrase not in found]
    score = 15 * len(found) / len(phrases)
    return _check(
        "required_phrases",
        15,
        score,
        not missing,
        f"missing {missing}" if missing else f"found {len(found)}/{len(phrases)}",
    )


def _forbidden_phrase_check(transcript: str, sample: dict[str, Any]) -> dict[str, Any]:
    phrases = [str(phrase) for phrase in sample.get("forbidden_phrases") or []]
    if not phrases:
        return _check("forbidden_phrases", 10, 10, True, "none configured")

    normalized = _normalize(transcript)
    found = [phrase for phrase in phrases if _normalize(phrase) in normalized]
    return _check(
        "forbidden_phrases",
        10,
        0 if found else 10,
        not found,
        f"found {found}" if found else "none found",
    )


def _dialogue_act_coverage_check(
    turns: list[dict[str, Any]],
    sample: dict[str, Any],
) -> dict[str, Any]:
    minimum = float(sample.get("min_dialogue_act_coverage") or 0.0)
    if not turns:
        coverage = 0.0
    else:
        labeled = sum(1 for turn in turns if turn.get("dialogue_act"))
        coverage = labeled / len(turns)
    ratio = min(coverage / minimum, 1.0) if minimum else 1.0
    return _check(
        "dialogue_act_coverage",
        10,
        10 * ratio,
        coverage >= minimum,
        f"expected >= {minimum:.2f}, got {coverage:.2f}",
    )


def _warning_check(warning_text: str, sample: dict[str, Any]) -> dict[str, Any]:
    allowed = [str(warning) for warning in sample.get("allowed_warnings") or []]
    if not warning_text:
        return _check("warnings", 10, 10, True, "none")

    unexpected = warning_text
    for warning in allowed:
        unexpected = unexpected.replace(warning, "")
    unexpected = re.sub(r"Pipeline completed with warnings:\s*", "", unexpected).strip(" ;")
    passed = not unexpected
    return _check(
        "warnings",
        10,
        10 if passed else 0,
        passed,
        warning_text,
    )


def _speaker_switches(turns: list[dict[str, Any]]) -> int:
    switches = 0
    previous = None
    for turn in turns:
        speaker = turn.get("speaker")
        if previous is not None and speaker != previous:
            switches += 1
        previous = speaker
    return switches


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.$]+", " ", text.lower())).strip()


def _check(
    name: str,
    weight: int,
    score: float,
    passed: bool,
    detail: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "score": round(score, 2),
        "weight": weight,
        "detail": detail,
    }


def _print_report(report: dict[str, Any]) -> None:
    print(
        f"{report['sample_id']} "
        f"{report['percent']:.2f}% "
        f"({report['score']:.2f}/{report['max_score']})"
    )
    print(f"turns={report['turn_count']} switches={report['speaker_switches']}")
    for check in report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"{status:4} {check['name']}: {check['score']}/{check['weight']} - {check['detail']}")


if __name__ == "__main__":
    main()
