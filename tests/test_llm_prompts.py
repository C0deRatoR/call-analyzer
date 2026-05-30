"""Offline tests for LLM schemas and prompt rendering.

No network calls. Verifies:
  - render() substitutes all placeholders correctly
  - render() raises on missing/extra keys
  - All three domain YAMLs can have their prompts rendered without KeyError
  - Response schemas accept well-formed payloads
  - Response schemas reject missing required fields
"""

import pytest
from pydantic import ValidationError

from core.domains.loader import list_domains, load_domain
from core.llm.schemas import SentimentResponse, Suggestion, SuggestionsResponse, SummaryResponse
from pipeline.prompts import render, render_sentiment, render_suggestions, render_summary

SAMPLE_TRANSCRIPT = (
    "Counselor: How have you been feeling this week?\n"
    "Student: Pretty anxious honestly. Finals are coming up.\n"
    "Counselor: That sounds stressful. What specifically is worrying you most?\n"
    "Student: I'm scared I'll fail statistics.\n"
    "Counselor: Let's break that down together and make a study plan."
)

RENDER_KWARGS = dict(
    primary="Counselor",
    secondary="Student",
    transcript=SAMPLE_TRANSCRIPT,
    retrieved_context="[src-1] Active listening involves paraphrasing before responding.",
)


# ---------------------------------------------------------------------------
# render() unit tests
# ---------------------------------------------------------------------------


def test_render_substitutes_all_placeholders():
    template = "Hello {primary}, your client is {secondary}. Transcript: {transcript}. Context: {retrieved_context}."
    result = render(template, **RENDER_KWARGS)
    assert "Counselor" in result
    assert "Student" in result
    assert SAMPLE_TRANSCRIPT in result
    assert "[src-1]" in result


def test_render_raises_on_unknown_placeholder():
    template = "Hello {primary} and {unknown_key}."
    with pytest.raises(KeyError):
        render(template, **RENDER_KWARGS)


def test_render_raises_on_none_argument():
    with pytest.raises(ValueError, match="non-None"):
        render("{primary}", primary=None, secondary="S", transcript="T", retrieved_context="")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Per-domain prompt rendering (catches YAML typos in placeholder names)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain_id", [d.id for d in list_domains()])
def test_domain_summary_prompt_renders(domain_id: str):
    domain = load_domain(domain_id)
    rendered = render_summary(domain, SAMPLE_TRANSCRIPT)
    assert domain.speakers.primary in rendered
    assert domain.speakers.secondary in rendered
    assert SAMPLE_TRANSCRIPT in rendered


@pytest.mark.parametrize("domain_id", [d.id for d in list_domains()])
def test_domain_suggestions_prompt_renders(domain_id: str):
    domain = load_domain(domain_id)
    rendered = render_suggestions(
        domain, SAMPLE_TRANSCRIPT, retrieved_context="[src-1] Some excerpt."
    )
    assert domain.speakers.primary in rendered


@pytest.mark.parametrize("domain_id", [d.id for d in list_domains()])
def test_domain_sentiment_prompt_renders(domain_id: str):
    domain = load_domain(domain_id)
    if not domain.prompts.sentiment:
        pytest.skip(f"{domain_id} has no sentiment prompt")
    rendered = render_sentiment(domain, SAMPLE_TRANSCRIPT)
    assert domain.speakers.primary in rendered


# ---------------------------------------------------------------------------
# Response schema validation
# ---------------------------------------------------------------------------


def test_summary_response_valid():
    payload = {
        "summary": "The student discussed exam anxiety.",
        "key_topics": ["exam stress", "study planning"],
        "next_steps": ["Create a study schedule"],
    }
    r = SummaryResponse.model_validate(payload)
    assert r.summary == payload["summary"]
    assert len(r.key_topics) == 2


def test_summary_response_missing_required_field():
    with pytest.raises(ValidationError):
        SummaryResponse.model_validate({"key_topics": []})


def test_suggestions_response_valid():
    payload = {
        "suggestions": [
            {"text": "Use more open-ended questions.", "citations": ["src-1"]},
            {"text": "Paraphrase before advising.", "citations": []},
        ]
    }
    r = SuggestionsResponse.model_validate(payload)
    assert len(r.suggestions) == 2
    assert isinstance(r.suggestions[0], Suggestion)


def test_sentiment_response_valid():
    payload = {
        "overall_label": "mixed",
        "compound": -0.15,
        "key_emotions": ["anxiety", "hope"],
        "arc_description": "Started with high anxiety, ended with cautious optimism.",
    }
    r = SentimentResponse.model_validate(payload)
    assert r.overall_label == "mixed"
    assert r.compound == pytest.approx(-0.15)


def test_sentiment_response_compound_out_of_range():
    """compound must be within -1..1 per schema Field constraint."""
    payload = {
        "overall_label": "positive",
        "compound": 1.5,  # invalid
        "key_emotions": [],
        "arc_description": "All good.",
    }
    with pytest.raises(ValidationError):
        SentimentResponse.model_validate(payload)
