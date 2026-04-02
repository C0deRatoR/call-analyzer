"""
Topic & Keyword Extraction Module
Uses KeyBERT for BERT-based keyword/keyphrase extraction from transcripts.
Falls back to simple TF-IDF extraction if KeyBERT model fails to load.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Lazy-loaded global model instance
_kw_model = None
_model_load_attempted = False


def _get_model():
    """Lazy-load the KeyBERT model on first use."""
    global _kw_model, _model_load_attempted

    if _model_load_attempted:
        return _kw_model

    _model_load_attempted = True
    try:
        from keybert import KeyBERT
        logger.info("Loading KeyBERT model (all-MiniLM-L6-v2)...")
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        logger.info("KeyBERT model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load KeyBERT model: {e}")
        _kw_model = None

    return _kw_model


def _fallback_tfidf_keywords(text: str, top_n: int = 10) -> List[Tuple[str, float]]:
    """
    Simple TF-based keyword extraction fallback.
    Extracts the most frequent meaningful words from the text.
    """
    # Common English stop words
    stop_words = {
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
        "your", "yours", "yourself", "yourselves", "he", "him", "his",
        "himself", "she", "her", "hers", "herself", "it", "its", "itself",
        "they", "them", "their", "theirs", "themselves", "what", "which",
        "who", "whom", "this", "that", "these", "those", "am", "is", "are",
        "was", "were", "be", "been", "being", "have", "has", "had", "having",
        "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
        "or", "because", "as", "until", "while", "of", "at", "by", "for",
        "with", "about", "against", "between", "through", "during", "before",
        "after", "above", "below", "to", "from", "up", "down", "in", "out",
        "on", "off", "over", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
        "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o",
        "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn",
        "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan",
        "shouldn", "wasn", "weren", "won", "wouldn", "also", "would",
        "could", "might", "shall", "may", "like", "know", "think", "yeah",
        "okay", "ok", "right", "well", "got", "get", "going", "go", "really",
        "um", "uh", "oh", "ah", "hmm", "thing", "things", "one", "much",
        "many", "still", "even", "way", "want", "let", "say", "said",
        "make", "made", "take", "come", "see", "need", "back", "something",
    }

    # Tokenize and clean
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stop_words]

    if not filtered:
        return []

    # Count frequencies and normalize
    counts = Counter(filtered)
    max_count = max(counts.values())
    keywords = [
        (word, round(count / max_count, 4))
        for word, count in counts.most_common(top_n)
    ]
    return keywords


def extract_keywords(
    text: str,
    top_n: int = 10,
    keyphrase_length: Tuple[int, int] = (1, 2),
    diversity: float = 0.5,
) -> Dict:
    """
    Extract keywords and keyphrases from transcript text.

    Args:
        text: The transcript text to extract keywords from.
        top_n: Number of top keywords to return.
        keyphrase_length: Tuple of (min_ngram, max_ngram) for keyphrases.
        diversity: Diversity of results (0-1). Higher = more diverse keywords.

    Returns:
        Dictionary with:
        - keywords: List of {keyword, score} dicts
        - top_keywords: List of top keyword strings (for quick display)
        - method: Which extraction method was used
    """
    if not text or not text.strip():
        return {
            "keywords": [],
            "top_keywords": [],
            "method": "none",
        }

    result_keywords = []
    method = "keybert"

    model = _get_model()

    if model is not None:
        try:
            # Use MMR (Maximal Marginal Relevance) for diverse keywords
            raw_keywords = model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_length,
                stop_words="english",
                use_mmr=True,
                diversity=diversity,
                top_n=top_n,
            )
            result_keywords = [
                {"keyword": kw, "score": round(score, 4)}
                for kw, score in raw_keywords
            ]
        except Exception as e:
            logger.error(f"KeyBERT extraction failed: {e}")
            model = None  # Fall through to fallback

    # Fallback to TF-IDF-like extraction
    if model is None or not result_keywords:
        method = "tfidf_fallback"
        logger.info("Using TF-IDF fallback for keyword extraction.")
        fallback = _fallback_tfidf_keywords(text, top_n)
        result_keywords = [
            {"keyword": kw, "score": score}
            for kw, score in fallback
        ]

    # Sort by score descending
    result_keywords.sort(key=lambda x: x["score"], reverse=True)

    return {
        "keywords": result_keywords,
        "top_keywords": [kw["keyword"] for kw in result_keywords],
        "method": method,
    }
