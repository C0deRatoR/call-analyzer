"""
Whisper Audio Transcription Module
===================================
Uses OpenAI's Whisper model to transcribe audio files locally.
Supports multiple model sizes for speed/accuracy tradeoffs.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading on every request
_whisper_model = None
_current_model_size: Optional[str] = None


def get_available_models() -> Dict[str, str]:
    """Return available Whisper model sizes and descriptions."""
    return {
        "tiny": "Fastest, least accurate (~39 MB)",
        "base": "Good balance of speed and accuracy (~74 MB)",
        "small": "Better accuracy, slower (~244 MB)",
        "medium": "High accuracy, much slower (~769 MB)",
        "large": "Highest accuracy, slowest (~1550 MB)"
    }


def _load_model(model_size: str = "base"):
    """
    Load and cache the Whisper model.
    
    Args:
        model_size: One of 'tiny', 'base', 'small', 'medium', 'large'
    """
    global _whisper_model, _current_model_size

    # Return cached model if same size is requested
    if _whisper_model is not None and _current_model_size == model_size:
        logger.info(f"Using cached Whisper '{model_size}' model")
        return _whisper_model

    try:
        import whisper
        logger.info(f"Loading Whisper '{model_size}' model (this may take a moment on first run)...")
        _whisper_model = whisper.load_model(model_size)
        _current_model_size = model_size
        logger.info(f"Whisper '{model_size}' model loaded successfully")
        return _whisper_model
    except ImportError:
        raise RuntimeError(
            "openai-whisper is not installed. "
            "Install it with: pip install openai-whisper"
        )
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise RuntimeError(f"Failed to load Whisper model: {str(e)}")


def transcribe_audio(filepath: str, model_size: str = "base") -> str:
    """
    Transcribe an audio file using OpenAI Whisper.
    
    Args:
        filepath: Path to the audio file
        model_size: Size of the Whisper model to use
        
    Returns:
        Transcribed text from the audio
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
        RuntimeError: If transcription fails
    """
    try:
        logger.info(f"Starting transcription for: {filepath}")

        # Validate file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        # Validate model size
        valid_sizes = get_available_models().keys()
        if model_size not in valid_sizes:
            logger.warning(f"Invalid model size '{model_size}', falling back to 'base'")
            model_size = "base"

        # Load model
        model = _load_model(model_size)

        # Transcribe
        logger.info("Transcribing audio... (this may take a while for long files)")
        result = model.transcribe(filepath)
        transcript = result.get("text", "").strip()

        if not transcript:
            raise ValueError("Whisper returned an empty transcript")

        logger.info(f"Transcription completed. Length: {len(transcript)} characters")
        return transcript

    except FileNotFoundError:
        logger.error(f"Audio file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {str(e)}")


def transcribe_audio_with_segments(filepath: str, model_size: str = "base") -> Dict:
    """
    Transcribe an audio file and return both full text and timestamped segments.
    
    This is useful for speaker diarization and timeline features later.
    
    Args:
        filepath: Path to the audio file
        model_size: Size of the Whisper model to use
        
    Returns:
        Dictionary with 'text' (full transcript) and 'segments' (list of
        timestamped segments with start, end, and text)
    """
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        model = _load_model(model_size)

        logger.info("Transcribing audio with segments...")
        result = model.transcribe(filepath)

        segments: List[Dict] = []
        for seg in result.get("segments", []):
            segments.append({
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip()
            })

        transcript = result.get("text", "").strip()
        logger.info(f"Transcription completed. {len(segments)} segments found.")

        return {
            "text": transcript,
            "segments": segments,
            "language": result.get("language", "unknown")
        }

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Segmented transcription failed: {e}")
        raise RuntimeError(f"Segmented transcription failed: {str(e)}")


def clear_model_cache():
    """Clear the cached Whisper model to free memory."""
    global _whisper_model, _current_model_size
    _whisper_model = None
    _current_model_size = None
    logger.info("Whisper model cache cleared")
