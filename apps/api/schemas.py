"""Pydantic response schemas for the FastAPI layer."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class DomainSummary(BaseModel):
    id: str
    display_name: str
    description: str
    primary_speaker: str
    secondary_speaker: str


class TurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    index: int
    speaker: str
    text: str
    start_seconds: float
    end_seconds: float
    emotion: str | None = None
    emotion_confidence: float | None = None
    dialogue_act: str | None = None
    dialogue_act_confidence: float | None = None
    sentiment_compound: float | None = None


class AnalyticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    primary_talk_seconds: float
    secondary_talk_seconds: float
    talk_time_ratio: float
    primary_word_count: int
    secondary_word_count: int
    primary_question_count: int
    primary_statement_count: int
    primary_acknowledgment_count: int
    primary_suggestion_count: int
    quality_scores_json: dict | None = None


class CallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    audio_filename: str
    duration_seconds: float | None
    language: str | None
    domain_id: str
    status: str
    current_stage: str | None
    error_message: str | None

    transcript: str | None
    summary: str | None
    sentiment_label: str | None
    sentiment_compound: float | None
    dominant_emotion: str | None
    emotion_distribution_json: dict | None
    suggestions_json: list | None
    keywords_json: list | None

    turns: list[TurnRead] = []
    analytics: AnalyticsRead | None = None


class CallEnqueued(BaseModel):
    id: UUID
    status: str
    stream_url: str


class ErrorResponse(BaseModel):
    detail: str
