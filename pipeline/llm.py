"""Structured Gemini client for ConvIQ pipeline stages.

Each public method:
  1. Renders the domain-specific prompt template
  2. Calls Gemini with JSON-mode + response_schema
  3. Validates the raw JSON into a Pydantic model
  4. Retries up to MAX_RETRIES on transient failures

NOTE: `retrieved_context` is passed as "" until Phase 4 (RAG) wires in real
retrieval. Suggestions will be produced but are not grounded in source excerpts
until then — this is expected and documented per PLAN.md.

Langfuse @observe wrapping is reserved for Phase 6 — add one decorator per
method when that phase lands. The class boundaries are designed for it.
"""

import json
import logging
import time
from typing import Type, TypeVar

import google.generativeai as genai
from pydantic import BaseModel, ValidationError

from core.config import settings
from core.domains.schemas import DomainConfig
from core.llm.schemas import SentimentResponse, SuggestionsResponse, SummaryResponse
from pipeline.prompts import render_sentiment, render_suggestions, render_summary

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
_BASE_DELAY = 1.0

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Thread-safe, lazily-initialized Gemini client.

    One instance is safe to share across the worker process. The underlying
    `genai.GenerativeModel` is cached after first use.
    """

    def __init__(self) -> None:
        self._model: genai.GenerativeModel | None = None

    def _get_model(self) -> genai.GenerativeModel:
        if self._model is None:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is not set")
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)
            logger.info("Gemini model initialised: %s", settings.gemini_model)
        return self._model

    def _call(
        self,
        prompt: str,
        response_schema: Type[T],
        *,
        temperature: float = 0.2,
    ) -> T:
        """Call Gemini in JSON mode and validate the response against `response_schema`.

        Retries up to MAX_RETRIES times with exponential backoff on transient
        errors or JSON/validation failures. Raises RuntimeError if all attempts fail.
        """
        model = self._get_model()
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,  # pass class directly; SDK handles $ref flattening
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = model.generate_content(prompt, generation_config=generation_config)
                raw = response.text
                if not raw:
                    raise ValueError("Empty response from Gemini")

                data = json.loads(raw)
                return response_schema.model_validate(data)

            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "Gemini response parse failed (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
            except Exception as exc:
                last_error = exc
                error_str = str(exc).upper()
                if "API_KEY" in error_str or "PERMISSION" in error_str or "QUOTA" in error_str:
                    raise RuntimeError(f"Gemini auth/quota error — not retrying: {exc}") from exc
                logger.warning(
                    "Gemini call failed (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )

            if attempt < MAX_RETRIES - 1:
                time.sleep(_BASE_DELAY * (2 ** attempt))

        raise RuntimeError(
            f"Gemini call failed after {MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Public pipeline methods
    # ------------------------------------------------------------------

    def summarize(self, domain: DomainConfig, transcript: str) -> SummaryResponse:
        """Generate a structured call summary driven by the domain prompt template."""
        prompt = render_summary(domain, transcript)
        return self._call(prompt, SummaryResponse)

    def generate_suggestions(
        self,
        domain: DomainConfig,
        transcript: str,
        retrieved_context: str = "",
    ) -> SuggestionsResponse:
        """Generate coaching suggestions.

        `retrieved_context` is "" until Phase 4 (RAG). Suggestions will be
        produced but will not cite real source documents until then.
        """
        prompt = render_suggestions(domain, transcript, retrieved_context)
        return self._call(prompt, SuggestionsResponse)

    def analyze_sentiment(self, domain: DomainConfig, transcript: str) -> SentimentResponse:
        """Analyse the emotional arc of a call using the domain's sentiment prompt."""
        prompt = render_sentiment(domain, transcript)
        return self._call(prompt, SentimentResponse)


# Module-level singleton — imported by pipeline stages.
# Reset in tests by calling GeminiClient() directly.
gemini_client = GeminiClient()
