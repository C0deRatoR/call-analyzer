"""SQLAlchemy ORM models for ConvIQ.

Schema overview:
- `calls`         one row per uploaded audio file + denormalized aggregate output
- `turns`         per-speaker turn with emotion / dialogue-act / per-turn embedding
- `analytics`     computed metrics per call (talk-time, question ratio, rubric scores)
- `llm_traces`    one row per LLM call, cross-referenced to Langfuse for cost/latency
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core.config import settings


class Base(DeclarativeBase):
    pass


class CallStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Audio
    audio_filename: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str] = mapped_column(String(512))
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Domain config used for this run
    domain_id: Mapped[str] = mapped_column(String(50))

    # Status
    status: Mapped[CallStatus] = mapped_column(
        SAEnum(CallStatus, name="call_status"), default=CallStatus.QUEUED
    )
    current_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Aggregate outputs (denormalized for one-shot retrieval)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sentiment_compound: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_emotion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    suggestions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    keywords_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    emotion_distribution_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    turns: Mapped[list["Turn"]] = relationship(
        back_populates="call", cascade="all, delete-orphan", order_by="Turn.index"
    )
    analytics: Mapped["Analytics | None"] = relationship(
        back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    llm_traces: Mapped[list["LLMTrace"]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("call_id", "index", name="uq_turn_call_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE")
    )
    index: Mapped[int] = mapped_column(Integer)

    speaker: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    start_seconds: Mapped[float] = mapped_column(Float)
    end_seconds: Mapped[float] = mapped_column(Float)

    # Per-turn classification outputs
    emotion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emotion_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    dialogue_act: Mapped[str | None] = mapped_column(String(30), nullable=True)
    dialogue_act_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_compound: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Embedding for similarity search across calls
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )

    call: Mapped["Call"] = relationship(back_populates="turns")


class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        unique=True,
    )

    # Per-speaker talk-time
    primary_talk_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    secondary_talk_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    talk_time_ratio: Mapped[float] = mapped_column(Float, default=0.5)

    primary_word_count: Mapped[int] = mapped_column(Integer, default=0)
    secondary_word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Dialogue-act-derived counts (for the primary speaker)
    primary_question_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_statement_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_acknowledgment_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_suggestion_count: Mapped[int] = mapped_column(Integer, default=0)

    # Domain-specific rubric scores (filled per domain's `rubric` keys)
    quality_scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    call: Mapped["Call"] = relationship(back_populates="analytics")


class LLMTrace(Base):
    __tablename__ = "llm_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE")
    )
    stage: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))

    langfuse_trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call: Mapped["Call"] = relationship(back_populates="llm_traces")
