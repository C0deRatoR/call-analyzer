import logging
from typing import Dict, List, Optional
from faster_whisper import WhisperModel
import os

logger = logging.getLogger(__name__)

# Global model cache
_model_cache: Dict[str, WhisperModel] = {}

def get_available_models() -> Dict[str, str]:
    """Return available Whisper model sizes and descriptions."""
    return {
        "tiny": "Fastest, least accurate (~39 MB)",
        "base": "Good balance of speed and accuracy (~74 MB)", 
        "small": "Better accuracy, slower (~244 MB)",
        "medium": "High accuracy, much slower (~769 MB)",
        "large": "Highest accuracy, slowest (~1550 MB)"
    }

def transcribe_audio(filepath: str, model_size: str = "base") -> str:
    """
    Transcribe audio file using Faster Whisper.
    
    Args:
        filepath: Path to the audio file
        model_size: Size of the model to use
        
    Returns:
        Transcribed text from the audio
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
        Exception: If transcription fails
    """
    try:
        logger.info(f"Starting transcription for: {filepath}")
        
        # Validate file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        # Validate model size
        available_models = get_available_models()
        if model_size not in available_models:
            logger.warning(f"Unknown model size '{model_size}', using 'base' instead")
            model_size = "base"
        
        # Load model (with caching)
        model = _load_model(model_size)
        
        # Transcribe audio
        logger.info("Running Faster Whisper transcription...")
        segments, info = model.transcribe(
            filepath, 
            beam_size=5,
            language="en",  # Auto-detect language, fallback to English
            vad_filter=True  # Voice activity detection
        )
        
        # Combine segments into transcript
        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())
        
        transcript = " ".join(transcript_parts).strip()
        
        if not transcript:
            logger.warning("Transcription returned empty result")
            return "No speech detected in the audio file."
        
        logger.info(f"Transcription completed. Text length: {len(transcript)} characters")
        return transcript
        
    except FileNotFoundError:
        logger.error(f"Audio file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise Exception(f"Transcription failed: {str(e)}")

def _load_model(model_size: str) -> WhisperModel:
    """
    Load and cache Whisper model for reuse.
    
    Args:
        model_size: Size of the model to load
        
    Returns:
        Loaded WhisperModel instance
    """
    if model_size not in _model_cache:
        logger.info(f"Loading Faster Whisper model: {model_size}")
        try:
            _model_cache[model_size] = WhisperModel(
                model_size, 
                device="cpu",  # Use CPU for better compatibility
                compute_type="int8"  # Optimized for speed and memory
            )
            logger.info(f"Faster Whisper model loaded successfully: {model_size}")
        except Exception as e:
            logger.error(f"Failed to load model {model_size}: {e}")
            raise Exception(f"Failed to load Whisper model: {str(e)}")
    
    return _model_cache[model_size]

def clear_model_cache():
    """Clear the model cache to free memory."""
    global _model_cache
    _model_cache.clear()
    logger.info("Model cache cleared")
