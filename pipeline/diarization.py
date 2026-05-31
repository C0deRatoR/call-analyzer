"""
Speaker Diarization Module
===========================
Identifies and labels different speakers in a transcript.

The production path runs pyannote.audio on the uploaded audio, then maps
Whisper's timestamped transcript segments onto the detected speaker regions.
The older pause-based segment heuristic remains as a local fallback for
development and offline tests when a HuggingFace token is not available.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Minimum pause (in seconds) between segments to consider a speaker change
DEFAULT_PAUSE_THRESHOLD = 1.5
DEFAULT_PYANNOTE_MODEL = "pyannote/speaker-diarization-3.1"
DEFAULT_SPEAKER_LABELS = ["Speaker 1", "Speaker 2"]
MERGE_SAME_SPEAKER_GAP_SECONDS = 0.75
_pyannote_pipeline_cache: dict[tuple[str, str], Any] = {}

_SPEAKER_LABEL_ALIASES: dict[str, tuple[str, ...]] = {
    "agent": ("agent", "agents"),
    "customer": ("customer", "customers", "caller"),
    "counselor": ("counselor", "counsellor", "consular", "counselor's"),
    "student": ("student", "students"),
    "salesperson": ("salesperson", "sales person", "sales rep", "seller"),
    "prospect": ("prospect", "prospects", "buyer"),
}


def _normalize_speaker_labels(speaker_labels: list[str] | None = None) -> list[str]:
    labels = [label.strip() for label in speaker_labels or [] if label.strip()]
    if len(labels) >= 2:
        return labels
    return DEFAULT_SPEAKER_LABELS.copy()


def _clean_segment(segment: dict[str, Any]) -> dict[str, Any] | None:
    text = str(segment.get("text", "")).strip()
    if not text:
        return None

    try:
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
    except (TypeError, ValueError):
        logger.warning("Skipping transcript segment with invalid timestamps: %s", segment)
        return None

    if end < start:
        start, end = end, start

    return {"start": start, "end": end, "text": text}


def _clean_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = [_clean_segment(segment) for segment in segments]
    return [segment for segment in cleaned if segment is not None]


def _load_pyannote_pipeline(model_name: str, hf_token: str):
    if not hf_token.strip():
        raise RuntimeError("HF_TOKEN is required for pyannote diarization")

    cache_key = (model_name, hf_token)
    if cache_key in _pyannote_pipeline_cache:
        return _pyannote_pipeline_cache[cache_key]

    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise RuntimeError(
            "pyannote.audio and torch are required for real diarization"
        ) from exc

    pipeline = Pipeline.from_pretrained(model_name, token=hf_token)
    if pipeline is None:
        raise RuntimeError(
            f"Could not load pyannote pipeline '{model_name}'. "
            "Check HF_TOKEN and accept the model license on HuggingFace."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if hasattr(pipeline, "to"):
        pipeline.to(device)
    logger.info("Loaded pyannote diarization pipeline %s on %s", model_name, device)
    _pyannote_pipeline_cache[cache_key] = pipeline
    return pipeline


def _extract_annotation(output: Any) -> Any:
    """Return a pyannote.core.Annotation from pyannote 3.x or 4.x output."""
    if hasattr(output, "exclusive_speaker_diarization"):
        return output.exclusive_speaker_diarization
    if hasattr(output, "speaker_diarization"):
        return output.speaker_diarization
    return output


def _annotation_regions(annotation: Any, speaker_labels: list[str]) -> list[dict[str, Any]]:
    annotation = _extract_annotation(annotation)
    raw_regions: list[dict[str, Any]] = []
    for segment, _track, raw_speaker in annotation.itertracks(yield_label=True):
        raw_regions.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "raw_speaker": str(raw_speaker),
            }
        )

    raw_regions.sort(key=lambda item: (item["start"], item["end"], item["raw_speaker"]))
    raw_to_label: dict[str, str] = {}
    for region in raw_regions:
        raw = str(region["raw_speaker"])
        if raw not in raw_to_label:
            next_index = len(raw_to_label)
            raw_to_label[raw] = (
                speaker_labels[next_index]
                if next_index < len(speaker_labels)
                else f"Speaker {next_index + 1}"
            )

    return [
        {
            "start": region["start"],
            "end": region["end"],
            "speaker": raw_to_label[str(region["raw_speaker"])],
        }
        for region in raw_regions
    ]


def _overlap_seconds(
    segment: dict[str, Any],
    region: dict[str, Any],
) -> float:
    return max(0.0, min(segment["end"], region["end"]) - max(segment["start"], region["start"]))


def _nearest_region_speaker(
    segment: dict[str, Any],
    regions: list[dict[str, Any]],
    default_speaker: str,
) -> str:
    if not regions:
        return default_speaker

    midpoint = (segment["start"] + segment["end"]) / 2

    def distance(region: dict[str, Any]) -> float:
        if region["start"] <= midpoint <= region["end"]:
            return 0.0
        return min(abs(midpoint - region["start"]), abs(midpoint - region["end"]))

    return str(min(regions, key=distance)["speaker"])


def _speaker_for_segment(
    segment: dict[str, Any],
    regions: list[dict[str, Any]],
    default_speaker: str,
) -> str:
    overlap_by_speaker: dict[str, float] = {}
    for region in regions:
        overlap = _overlap_seconds(segment, region)
        if overlap > 0:
            speaker = str(region["speaker"])
            overlap_by_speaker[speaker] = overlap_by_speaker.get(speaker, 0.0) + overlap

    if overlap_by_speaker:
        return max(overlap_by_speaker.items(), key=lambda item: item[1])[0]

    return _nearest_region_speaker(segment, regions, default_speaker)


def _merge_same_speaker_segments(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for turn in turns:
        if (
            merged
            and merged[-1]["speaker"] == turn["speaker"]
            and turn["start"] - merged[-1]["end"] <= MERGE_SAME_SPEAKER_GAP_SECONDS
        ):
            merged[-1]["text"] = f"{merged[-1]['text']} {turn['text']}".strip()
            merged[-1]["end"] = max(float(merged[-1]["end"]), float(turn["end"]))
            continue
        merged.append(turn.copy())
    return merged


def _speaker_label_aliases(speaker_labels: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for label in speaker_labels:
        normalized_label = label.lower()
        variants = {label, f"{label}s", f"{label}'s"}
        variants.update(_SPEAKER_LABEL_ALIASES.get(normalized_label, ()))
        for variant in variants:
            normalized_variant = re.sub(r"\s+", " ", variant.strip().lower())
            aliases[normalized_variant] = label
    return aliases


def _speaker_cue_pattern(speaker_labels: list[str]) -> re.Pattern[str]:
    aliases = sorted(
        (re.escape(alias) for alias in _speaker_label_aliases(speaker_labels)),
        key=len,
        reverse=True,
    )
    return re.compile(
        rf"\b(?P<label>{'|'.join(aliases)})\s+(?:speaking|says|said)\s*[:,.-]?\s*",
        re.IGNORECASE,
    )


def _append_turn(
    turns: list[dict[str, Any]],
    *,
    speaker: str,
    text: str,
    start: float,
    end: float,
) -> None:
    text = text.strip(" ,")
    if not text:
        return

    end_value = max(end, start)
    if (
        turns
        and turns[-1]["speaker"] == speaker
        and start - turns[-1]["end"] <= MERGE_SAME_SPEAKER_GAP_SECONDS
    ):
        turns[-1]["text"] = f"{turns[-1]['text']} {text}".strip()
        turns[-1]["end"] = max(float(turns[-1]["end"]), end_value)
        return

    turns.append({"speaker": speaker, "text": text, "start": start, "end": end_value})


def diarize_from_explicit_speaker_cues(
    segments: list[dict[str, Any]],
    speaker_labels: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Split generated/sample transcripts that include spoken speaker cues.

    Some local demo audio says phrases such as "Agent speaking" and
    "Customer speaking" before each utterance. When pyannote cannot run, these
    cues are stronger than pause timing and prevent the whole transcript from
    being collapsed into one turn.
    """
    segments = _clean_segments(segments)
    if not segments:
        return []

    labels = _normalize_speaker_labels(speaker_labels)
    canonical_by_lower = _speaker_label_aliases(labels)
    cue_pattern = _speaker_cue_pattern(labels)

    turns: list[dict[str, Any]] = []
    current_speaker: str | None = None
    saw_cue = False

    for segment in segments:
        text = segment["text"]
        matches = list(cue_pattern.finditer(text))
        segment_start = float(segment["start"])
        segment_end = float(segment["end"])
        segment_duration = max(segment_end - segment_start, 0.0)
        text_length = max(len(text), 1)

        if not matches:
            if current_speaker is not None:
                _append_turn(
                    turns,
                    speaker=current_speaker,
                    text=text,
                    start=segment_start,
                    end=segment_end,
                )
            continue

        if current_speaker is not None and matches[0].start() > 0:
            prefix_end = segment_start + segment_duration * (matches[0].start() / text_length)
            _append_turn(
                turns,
                speaker=current_speaker,
                text=text[: matches[0].start()],
                start=segment_start,
                end=prefix_end,
            )

        for index, match in enumerate(matches):
            saw_cue = True
            raw_label = re.sub(r"\s+", " ", match.group("label").lower())
            current_speaker = canonical_by_lower[raw_label]
            content_start = match.end()
            content_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            turn_start = segment_start + segment_duration * (match.start() / text_length)
            turn_end = segment_start + segment_duration * (content_end / text_length)
            _append_turn(
                turns,
                speaker=current_speaker,
                text=text[content_start:content_end],
                start=turn_start,
                end=turn_end,
            )

    if saw_cue:
        logger.info("Speaker-cue diarization complete: %d speaker turns detected", len(turns))
        return turns
    return []


def assign_speakers_to_segments(
    segments: list[dict[str, Any]],
    regions: list[dict[str, Any]],
    speaker_labels: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Assign speaker labels from pyannote regions to Whisper segments."""
    labels = _normalize_speaker_labels(speaker_labels)
    cleaned_segments = _clean_segments(segments)
    if not cleaned_segments:
        return []

    assigned = [
        {
            "speaker": _speaker_for_segment(segment, regions, labels[0]),
            "text": segment["text"],
            "start": segment["start"],
            "end": segment["end"],
        }
        for segment in cleaned_segments
    ]
    return _merge_same_speaker_segments(assigned)


def diarize_with_pyannote(
    audio_path: str | Path,
    segments: list[dict[str, Any]],
    hf_token: str,
    speaker_labels: list[str] | None = None,
    model_name: str = DEFAULT_PYANNOTE_MODEL,
    num_speakers: int | None = None,
) -> list[dict[str, Any]]:
    """Run pyannote diarization and align detected speakers to transcript segments."""
    cleaned_segments = _clean_segments(segments)
    if not cleaned_segments:
        logger.warning("No transcript segments available for pyannote alignment")
        return []

    labels = _normalize_speaker_labels(speaker_labels)
    pipeline = _load_pyannote_pipeline(model_name, hf_token)
    speaker_count = num_speakers or len(labels)

    try:
        annotation = pipeline(str(audio_path), num_speakers=speaker_count)
    except TypeError as exc:
        if "num_speakers" not in str(exc):
            raise
        logger.warning("pyannote pipeline does not accept num_speakers; retrying without it")
        annotation = pipeline(str(audio_path))

    regions = _annotation_regions(annotation, labels)
    if not regions:
        logger.warning("pyannote returned no speaker regions")
        return []

    turns = assign_speakers_to_segments(cleaned_segments, regions, labels)
    logger.info("pyannote diarization complete: %d speaker turns detected", len(turns))
    return turns


def diarize_from_segments(
    segments: list[dict],
    pause_threshold: float = DEFAULT_PAUSE_THRESHOLD,
    speaker_labels: list[str] | None = None,
) -> list[dict]:
    """
    Assign speaker labels to transcript segments based on pause detection.

    When there's a gap of >= pause_threshold seconds between two consecutive
    segments, we assume the speaker has changed.

    Args:
        segments: List of segment dicts from Whisper, each with
                  'start', 'end', and 'text' keys.
        pause_threshold: Minimum gap (seconds) to trigger a speaker switch.
        speaker_labels: Custom speaker names. Defaults to
                        ['Counselor', 'Student'].

    Returns:
        List of diarized turn dicts, each containing:
        - 'speaker': speaker label
        - 'text': combined text for this turn
        - 'start': start time of the turn
        - 'end': end time of the turn
    """
    segments = _clean_segments(segments)
    if not segments:
        logger.warning("No segments provided for diarization")
        return []

    speaker_labels = _normalize_speaker_labels(speaker_labels)

    turns: list[dict] = []
    current_speaker_idx = 0
    current_turn = {
        "speaker": speaker_labels[current_speaker_idx],
        "text": segments[0]["text"],
        "start": segments[0]["start"],
        "end": segments[0]["end"],
    }

    for i in range(1, len(segments)):
        prev_end = segments[i - 1]["end"]
        curr_start = segments[i]["start"]
        gap = curr_start - prev_end

        if gap >= pause_threshold:
            # Speaker change detected — save current turn and switch
            turns.append(current_turn)
            current_speaker_idx = (current_speaker_idx + 1) % len(speaker_labels)
            current_turn = {
                "speaker": speaker_labels[current_speaker_idx],
                "text": segments[i]["text"],
                "start": segments[i]["start"],
                "end": segments[i]["end"],
            }
        else:
            # Same speaker continues — merge text
            current_turn["text"] += " " + segments[i]["text"]
            current_turn["end"] = segments[i]["end"]

    # Don't forget the last turn
    turns.append(current_turn)

    logger.info(f"Diarization complete: {len(turns)} speaker turns detected")
    return turns


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_diarized_transcript(turns: list[dict]) -> str:
    """
    Format diarized turns into a readable string transcript.

    Args:
        turns: List of diarized turn dicts from diarize_from_segments()

    Returns:
        Human-readable formatted transcript string
    """
    lines = []
    for turn in turns:
        timestamp = format_timestamp(turn["start"])
        lines.append(f"[{timestamp}] {turn['speaker']}: {turn['text']}")
    return "\n\n".join(lines)
