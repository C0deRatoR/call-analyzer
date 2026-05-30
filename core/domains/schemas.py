"""Pydantic schemas for domain configuration YAML files."""

from pydantic import BaseModel, ConfigDict, Field


class DomainSpeakers(BaseModel):
    """Two-speaker labels for diarization output."""

    primary: str = Field(..., description="The professional / leading speaker (e.g. Counselor)")
    secondary: str = Field(..., description="The client / responding speaker (e.g. Student)")


class DomainPrompts(BaseModel):
    """LLM prompt templates. Use {primary} / {secondary} placeholders."""

    summary: str
    suggestions: str
    sentiment: str = ""


class DomainRAG(BaseModel):
    """Per-domain knowledge base reference."""

    namespace: str = Field(..., description="Future RAG collection name")
    source_label: str = Field("", description="Human-friendly source name for citations")


class DomainConfig(BaseModel):
    """Top-level domain configuration loaded from `domains/<id>.yaml`."""

    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str
    description: str = ""
    speakers: DomainSpeakers
    prompts: DomainPrompts
    rubric: dict[str, str] = Field(
        default_factory=dict,
        description="Map of rubric dimension -> evaluation prompt fragment",
    )
    rag: DomainRAG | None = None
    analytics_focus: list[str] = Field(default_factory=list)
