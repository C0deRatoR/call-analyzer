"""
Speaker Diarization Module
===========================
Identifies and labels different speakers in a transcript using
Whisper's timestamped segments. Uses pause-based heuristics to
detect speaker turns in a two-party conversation (e.g., student + counselor).
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Minimum pause (in seconds) between segments to consider a speaker change
DEFAULT_PAUSE_THRESHOLD = 1.5


def diarize_from_segments(
    segments: List[Dict],
    pause_threshold: float = DEFAULT_PAUSE_THRESHOLD,
    speaker_labels: Optional[List[str]] = None
) -> List[Dict]:
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
    if not segments:
        logger.warning("No segments provided for diarization")
        return []

    if speaker_labels is None:
        speaker_labels = ["Counselor", "Student"]

    if len(speaker_labels) < 2:
        speaker_labels = ["Speaker A", "Speaker B"]

    turns: List[Dict] = []
    current_speaker_idx = 0
    current_turn = {
        "speaker": speaker_labels[current_speaker_idx],
        "text": segments[0]["text"],
        "start": segments[0]["start"],
        "end": segments[0]["end"]
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
                "end": segments[i]["end"]
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


def format_diarized_transcript(turns: List[Dict]) -> str:
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
