"""Offline tests for diarization alignment helpers."""

from types import SimpleNamespace

from pipeline.diarization import (
    _annotation_regions,
    assign_speakers_to_segments,
    diarize_from_explicit_speaker_cues,
    diarize_from_segments,
)


def test_assign_speakers_to_segments_uses_max_overlap_and_merges_same_speaker():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Hello"},
        {"start": 1.1, "end": 2.0, "text": "again"},
        {"start": 2.2, "end": 3.0, "text": "Hi there"},
    ]
    regions = [
        {"start": 0.0, "end": 2.0, "speaker": "Counselor"},
        {"start": 2.1, "end": 3.5, "speaker": "Student"},
    ]

    turns = assign_speakers_to_segments(segments, regions, ["Counselor", "Student"])

    assert turns == [
        {"speaker": "Counselor", "text": "Hello again", "start": 0.0, "end": 2.0},
        {"speaker": "Student", "text": "Hi there", "start": 2.2, "end": 3.0},
    ]


def test_pause_heuristic_uses_domain_speaker_labels():
    turns = diarize_from_segments(
        [
            {"start": 0.0, "end": 1.0, "text": "First speaker."},
            {"start": 3.0, "end": 4.0, "text": "Second speaker."},
        ],
        speaker_labels=["Agent", "Customer"],
    )

    assert [turn["speaker"] for turn in turns] == ["Agent", "Customer"]


def test_explicit_speaker_cues_split_generated_sample_transcripts():
    turns = diarize_from_explicit_speaker_cues(
        [
            {
                "start": 0.0,
                "end": 10.0,
                "text": (
                    "Agent speaking, thanks for calling. "
                    "Customer speaking, I need a refund. "
                    "Agent speaking, I can help with that."
                ),
            }
        ],
        speaker_labels=["Agent", "Customer"],
    )

    assert [turn["speaker"] for turn in turns] == ["Agent", "Customer", "Agent"]
    assert [turn["text"] for turn in turns] == [
        "thanks for calling.",
        "I need a refund.",
        "I can help with that.",
    ]
    assert turns[0]["start"] == 0.0
    assert turns[-1]["end"] == 10.0


def test_explicit_speaker_cues_handle_common_asr_label_variants():
    turns = diarize_from_explicit_speaker_cues(
        [
            {
                "start": 0.0,
                "end": 18.0,
                "text": (
                    "Consular speaking, thanks for coming in today. "
                    "Students speaking, I made a timetable. "
                    "Consular speaking, that sounds frustrating. "
                    "Students speaking, I would like that."
                ),
            }
        ],
        speaker_labels=["Counselor", "Student"],
    )

    assert [turn["speaker"] for turn in turns] == [
        "Counselor",
        "Student",
        "Counselor",
        "Student",
    ]
    assert turns[0]["text"] == "thanks for coming in today."
    assert turns[2]["text"] == "that sounds frustrating."


def test_annotation_regions_supports_pyannote_4_diarize_output():
    class Segment:
        start = 0.5
        end = 2.0

    class Annotation:
        def itertracks(self, yield_label: bool):
            assert yield_label is True
            yield Segment(), "_", "SPEAKER_00"

    output = SimpleNamespace(exclusive_speaker_diarization=Annotation())

    assert _annotation_regions(output, ["Counselor", "Student"]) == [
        {"start": 0.5, "end": 2.0, "speaker": "Counselor"}
    ]
