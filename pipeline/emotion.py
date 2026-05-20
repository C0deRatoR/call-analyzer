"""
Emotion Detection Module
=========================
Uses a pre-trained HuggingFace transformer model to classify text
into emotions: anger, disgust, fear, joy, neutral, sadness, surprise.

Model: j-hartmann/emotion-english-distilroberta-base
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Global pipeline cache
_emotion_pipeline = None


def _load_pipeline():
    """Load and cache the emotion classification pipeline."""
    global _emotion_pipeline

    if _emotion_pipeline is not None:
        return _emotion_pipeline

    try:
        from transformers import pipeline
        logger.info("Loading emotion detection model (first run may download ~300MB)...")
        _emotion_pipeline = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,  # Return all emotion scores
            truncation=True
        )
        logger.info("Emotion detection model loaded successfully")
        return _emotion_pipeline
    except ImportError:
        raise RuntimeError(
            "transformers is not installed. "
            "Install it with: pip install transformers torch"
        )
    except Exception as e:
        logger.error(f"Failed to load emotion model: {e}")
        raise RuntimeError(f"Failed to load emotion model: {str(e)}")


def detect_emotions(text: str) -> Dict[str, Any]:
    """
    Detect emotions in a single piece of text.

    Args:
        text: The text to analyze.

    Returns:
        Dict with 'primary_emotion', 'confidence', and 'all_scores'.
    """
    try:
        pipe = _load_pipeline()
        # Truncate very long text to avoid token limit issues
        truncated = text[:512]
        results = pipe(truncated)[0]  # list of {label, score} dicts

        # Sort by score descending
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        primary = sorted_results[0]

        return {
            "primary_emotion": primary["label"],
            "confidence": round(primary["score"], 4),
            "all_scores": {
                r["label"]: round(r["score"], 4) for r in sorted_results
            }
        }
    except Exception as e:
        logger.error(f"Emotion detection failed: {e}")
        return {
            "primary_emotion": "unknown",
            "confidence": 0.0,
            "all_scores": {},
            "error": str(e)
        }


def detect_emotions_per_turn(turns: List[Dict]) -> List[Dict]:
    """
    Detect emotions for each speaker turn from diarization.

    Args:
        turns: List of diarized turn dicts, each with 'speaker', 'text',
               'start', 'end'.

    Returns:
        The same list of turns, each augmented with an 'emotion' key
        containing the detection result.
    """
    try:
        pipe = _load_pipeline()
    except Exception as e:
        logger.error(f"Cannot load emotion pipeline: {e}")
        for turn in turns:
            turn["emotion"] = {
                "primary_emotion": "unknown",
                "confidence": 0.0,
                "all_scores": {},
                "error": str(e)
            }
        return turns

    for i, turn in enumerate(turns):
        text = turn.get("text", "")
        if not text.strip():
            turn["emotion"] = {
                "primary_emotion": "neutral",
                "confidence": 1.0,
                "all_scores": {"neutral": 1.0}
            }
            continue

        try:
            truncated = text[:512]
            results = pipe(truncated)[0]
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            primary = sorted_results[0]

            turn["emotion"] = {
                "primary_emotion": primary["label"],
                "confidence": round(primary["score"], 4),
                "all_scores": {
                    r["label"]: round(r["score"], 4) for r in sorted_results
                }
            }
        except Exception as e:
            logger.error(f"Emotion detection failed for turn {i}: {e}")
            turn["emotion"] = {
                "primary_emotion": "unknown",
                "confidence": 0.0,
                "all_scores": {},
                "error": str(e)
            }

    logger.info(f"Emotion detection completed for {len(turns)} turns")
    return turns


def get_emotion_summary(turns: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate emotion data across all turns into a summary.

    Args:
        turns: List of turn dicts that already have 'emotion' keys
               (from detect_emotions_per_turn).

    Returns:
        Dict with 'dominant_emotion', 'emotion_distribution', and
        'emotion_timeline'.
    """
    if not turns:
        return {"dominant_emotion": "unknown", "emotion_distribution": {}, "emotion_timeline": []}

    # Count primary emotions
    emotion_counts: Dict[str, int] = {}
    timeline: List[Dict] = []

    for turn in turns:
        emotion_data = turn.get("emotion", {})
        primary = emotion_data.get("primary_emotion", "unknown")
        confidence = emotion_data.get("confidence", 0.0)

        emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
        timeline.append({
            "speaker": turn.get("speaker", "Unknown"),
            "start": turn.get("start", 0),
            "emotion": primary,
            "confidence": confidence
        })

    # Calculate distribution as percentages
    total = len(turns)
    distribution = {
        emotion: round(count / total, 4)
        for emotion, count in sorted(
            emotion_counts.items(), key=lambda x: x[1], reverse=True
        )
    }

    # Dominant emotion
    dominant = max(emotion_counts, key=lambda k: emotion_counts[k])

    return {
        "dominant_emotion": dominant,
        "emotion_distribution": distribution,
        "emotion_timeline": timeline
    }


def clear_model_cache():
    """Clear the cached emotion model to free memory."""
    global _emotion_pipeline
    _emotion_pipeline = None
    logger.info("Emotion detection model cache cleared")
