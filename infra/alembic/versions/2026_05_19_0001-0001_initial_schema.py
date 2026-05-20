"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-19 00:00:01
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector for per-turn embeddings
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("audio_filename", sa.String(255), nullable=False),
        sa.Column("audio_path", sa.String(512), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("domain_id", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "processing",
                "completed",
                "failed",
                name="call_status",
            ),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment_label", sa.String(20), nullable=True),
        sa.Column("sentiment_compound", sa.Float(), nullable=True),
        sa.Column("dominant_emotion", sa.String(20), nullable=True),
        sa.Column("suggestions_json", postgresql.JSON(), nullable=True),
        sa.Column("keywords_json", postgresql.JSON(), nullable=True),
        sa.Column("emotion_distribution_json", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "turns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(50), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("emotion", sa.String(20), nullable=True),
        sa.Column("emotion_confidence", sa.Float(), nullable=True),
        sa.Column("dialogue_act", sa.String(30), nullable=True),
        sa.Column("dialogue_act_confidence", sa.Float(), nullable=True),
        sa.Column("sentiment_compound", sa.Float(), nullable=True),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id", "index", name="uq_turn_call_index"),
    )

    op.create_table(
        "analytics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_talk_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("secondary_talk_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("talk_time_ratio", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("primary_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("secondary_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_statement_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_acknowledgment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_suggestion_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_scores_json", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id"),
    )

    op.create_table(
        "llm_traces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("langfuse_trace_id", sa.String(100), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("llm_traces")
    op.drop_table("analytics")
    op.drop_table("turns")
    op.drop_table("calls")
    op.execute("DROP TYPE IF EXISTS call_status")
