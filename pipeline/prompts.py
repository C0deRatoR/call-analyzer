"""Domain prompt rendering.

Applies Python str.format() substitution to a prompt template loaded from a
domain YAML file. All placeholder keys must be passed explicitly — there are no
silent defaults. Missing or extra keys raise KeyError / ValueError immediately.

Supported placeholders (callers must always provide all four):
    {primary}           — primary speaker label (e.g. "Counselor")
    {secondary}         — secondary speaker label (e.g. "Student")
    {transcript}        — full call transcript text
    {retrieved_context} — RAG-retrieved excerpts; pass "" until Phase 4
"""

from core.domains.schemas import DomainConfig


def render(
    template: str, *, primary: str, secondary: str, transcript: str, retrieved_context: str
) -> str:
    """Return `template` with all placeholders substituted.

    Raises:
        KeyError:  if the template uses an undeclared placeholder
        ValueError: if any required argument is None
    """
    if any(v is None for v in (primary, secondary, transcript, retrieved_context)):
        raise ValueError("All render() arguments must be non-None strings")

    return template.format(
        primary=primary,
        secondary=secondary,
        transcript=transcript,
        retrieved_context=retrieved_context,
    )


def render_summary(domain: DomainConfig, transcript: str) -> str:
    return render(
        domain.prompts.summary,
        primary=domain.speakers.primary,
        secondary=domain.speakers.secondary,
        transcript=transcript,
        retrieved_context="",
    )


def render_suggestions(domain: DomainConfig, transcript: str, retrieved_context: str = "") -> str:
    return render(
        domain.prompts.suggestions,
        primary=domain.speakers.primary,
        secondary=domain.speakers.secondary,
        transcript=transcript,
        retrieved_context=retrieved_context,
    )


def render_sentiment(domain: DomainConfig, transcript: str) -> str:
    return render(
        domain.prompts.sentiment,
        primary=domain.speakers.primary,
        secondary=domain.speakers.secondary,
        transcript=transcript,
        retrieved_context="",
    )
