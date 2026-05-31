"""Deterministic domain inference for uploaded conversations."""

from __future__ import annotations

import re
from collections.abc import Iterable

AUTO_DOMAIN_ID = "auto"
DEFAULT_AUTO_DOMAIN_ID = "counseling"

_DOMAIN_KEYWORDS: dict[str, tuple[tuple[str, int], ...]] = {
    "counseling": (
        ("counseling", 7),
        ("counselor", 7),
        ("therapy", 5),
        ("student", 4),
        ("anxiety", 6),
        ("panic", 5),
        ("exam", 5),
        ("study", 4),
        ("sleep", 4),
        ("overwhelmed", 4),
        ("breathe", 4),
        ("breathing", 4),
        ("feelings", 3),
        ("parents", 3),
        ("school", 3),
        ("grounding", 3),
        ("homework", 2),
        ("session", 2),
    ),
    "customer_support": (
        ("customer support", 8),
        ("support call", 6),
        ("agent", 6),
        ("customer", 5),
        ("refund", 7),
        ("booking", 6),
        ("reservation", 6),
        ("cancellation", 6),
        ("confirmation email", 6),
        ("confirmation", 4),
        ("voucher", 5),
        ("payment", 5),
        ("card", 3),
        ("policy", 4),
        ("case", 4),
        ("ticket", 4),
        ("troubleshoot", 4),
        ("escalate", 3),
        ("resolved", 3),
    ),
    "sales": (
        ("sales", 8),
        ("salesperson", 8),
        ("prospect", 7),
        ("discovery call", 7),
        ("demo", 6),
        ("pilot", 6),
        ("deal", 5),
        ("proposal", 5),
        ("contract", 5),
        ("buying process", 6),
        ("budget", 5),
        ("finance", 4),
        ("security", 4),
        ("stakeholder", 4),
        ("vendor", 4),
        ("implementation", 4),
        ("integration", 4),
        ("ticket volume", 5),
        ("deflection", 5),
        ("csat", 5),
        ("workshop", 4),
    ),
}


def _normalize(text: str) -> str:
    text = text.lower().replace("_", " ").replace("-", " ").replace(".", " ")
    return re.sub(r"\s+", " ", text).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = re.escape(_normalize(phrase)).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9]){normalized_phrase}(?![a-z0-9])", text) is not None


def _score(text: str, weighted_keywords: Iterable[tuple[str, int]]) -> int:
    normalized_text = _normalize(text)
    if not normalized_text:
        return 0
    return sum(weight for keyword, weight in weighted_keywords if _contains_phrase(normalized_text, keyword))


def infer_domain_id(transcript: str, filename: str | None = None) -> str:
    """Infer one of the built-in domain ids from transcript text and filename hints."""
    scores: dict[str, int] = {}
    for domain_id, keywords in _DOMAIN_KEYWORDS.items():
        scores[domain_id] = _score(transcript, keywords)
        if filename:
            scores[domain_id] += 2 * _score(filename, keywords)

    selected_domain_id, selected_score = max(
        scores.items(),
        key=lambda item: (item[1], item[0] == DEFAULT_AUTO_DOMAIN_ID),
    )
    if selected_score <= 0:
        return DEFAULT_AUTO_DOMAIN_ID
    return selected_domain_id
