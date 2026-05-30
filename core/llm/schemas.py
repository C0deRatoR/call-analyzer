"""Pydantic v2 schemas for structured Gemini responses.

These are the source of truth for every LLM output shape. Gemini's JSON-mode
uses an OpenAPI subset — keep fields to str/int/float/bool/list[str]/nested
BaseModel. No Union, no discriminated models, no complex Optional chains.
"""

from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    """Structured summary of a call transcript."""

    summary: str = Field(..., description="3-5 sentence professional summary")
    key_topics: list[str] = Field(
        default_factory=list,
        description="Main topics discussed, each as a short phrase",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Action items or follow-ups agreed on",
    )


class Suggestion(BaseModel):
    """One coaching suggestion with citations back to retrieved source chunks."""

    text: str = Field(..., description="The specific, actionable suggestion")
    citations: list[str] = Field(
        default_factory=list,
        description="Source IDs from the retrieved context that ground this suggestion",
    )


class SuggestionsResponse(BaseModel):
    """Coaching suggestions generated from the transcript (and optionally RAG context)."""

    suggestions: list[Suggestion] = Field(
        ...,
        description="3-5 specific, grounded improvement suggestions",
    )


class SentimentResponse(BaseModel):
    """Emotional arc analysis of a call."""

    overall_label: str = Field(..., description="One of: positive, neutral, negative, mixed")
    compound: float = Field(..., ge=-1.0, le=1.0, description="Aggregate sentiment score -1 to 1")
    key_emotions: list[str] = Field(
        default_factory=list,
        description="Dominant emotions detected (e.g. anxiety, hope, frustration)",
    )
    arc_description: str = Field(
        ...,
        description="2-3 sentences describing how sentiment evolved through the call",
    )


class RubricScores(BaseModel):
    """LLM-as-judge rubric scores for a single call.

    Keys match the `rubric` dict in the domain YAML. Values are floats 1-5.
    Built dynamically from the domain config in Phase 5.
    """

    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Map of rubric dimension name -> score (1-5)",
    )
    reasoning: dict[str, str] = Field(
        default_factory=dict,
        description="Brief justification for each rubric score",
    )
