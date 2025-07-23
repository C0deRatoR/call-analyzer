import os
import logging
from typing import Optional, Dict, Any
import whisper

# Configure logging
logger = logging.getLogger(__name__)

# Global model cache
_whisper_model: Optional[Any] = None
_current_model_size: str = "base"

def get_whisper_model(model_size: str = "base") -> Any:
    """
    Get cached Whisper model or load if not cached.
    
    Args:
        model_size: Size of the model to load (tiny, base, small, medium, large)
        
    Returns:
        Loaded Whisper model
    """
    global _whisper_model, _current_model_size
    
    # Load model if not cached or different size requested
    if _whisper_model is None or _current_model_size != model_size:
        try:
            logger.info(f"Loading Whisper model: {model_size}")
            _whisper_model = whisper.load_model(model_size)
            _current_model_size = model_size
            logger.info(f"Whisper model loaded successfully: {model_size}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Failed to load Whisper model '{model_size}': {str(e)}")
    
    return _whisper_model

def validate_audio_file(audio_path: str) -> None:
    """Validate audio file before transcription."""
    if not audio_path:
        raise ValueError("Audio path cannot be empty")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    if not os.path.isfile(audio_path):
        raise ValueError(f"Path is not a file: {audio_path}")
    
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        raise ValueError("Audio file is empty")
    
    # Check if file is too large (500MB limit for transcription)
    max_size = 500 * 1024 * 1024  # 500MB
    if file_size > max_size:
        logger.warning(f"Large file detected: {file_size / (1024*1024):.1f}MB")

def transcribe_audio(audio_path: str, model_size: str = "base", **kwargs) -> str:
    """
    Transcribe audio file using OpenAI Whisper.
    
    Args:
        audio_path: Path to the audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        **kwargs: Additional arguments for transcribe method
        
    Returns:
        Transcribed text
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If file is invalid
        RuntimeError: If transcription fails
    """
    try:
        logger.info(f"Starting transcription for: {audio_path}")
        
        # Validate input
        validate_audio_file(audio_path)
        
        # Get cached model
        model = get_whisper_model(model_size)
        
        # Set default transcription options
        transcribe_options = {
            "language": kwargs.get("language", None),  # Auto-detect if None
            "task": kwargs.get("task", "transcribe"),
            "temperature": kwargs.get("temperature", 0.0),
            "word_timestamps": kwargs.get("word_timestamps", False),
            "no_speech_threshold": kwargs.get("no_speech_threshold", 0.6),
            "logprob_threshold": kwargs.get("logprob_threshold", -1.0),
        }
        
        # Remove None values
        transcribe_options = {k: v for k, v in transcribe_options.items() if v is not None}
        
        # Transcribe audio
        logger.info("Running Whisper transcription...")
        result = model.transcribe(audio_path, **transcribe_options)
        
        if not result or "text" not in result:
            raise RuntimeError("Transcription failed: No result returned")
        
        transcript = result["text"].strip()
        
        if not transcript:
            logger.warning("Transcription resulted in empty text")
            return "No speech detected in audio file."
        
        logger.info(f"Transcription completed. Text length: {len(transcript)} characters")
        return transcript
        
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def get_available_models() -> Dict[str, str]:
    """Get list of available Whisper models with descriptions."""
    return {
        "tiny": "Fastest, least accurate (39 MB)",
        "base": "Good balance of speed and accuracy (74 MB)",
        "small": "Better accuracy, slower (244 MB)", 
        "medium": "High accuracy, slower (769 MB)",
        "large": "Best accuracy, slowest (1550 MB)"
    }

def clear_model_cache() -> None:
    """Clear the cached Whisper model to free memory."""
    global _whisper_model, _current_model_size
    if _whisper_model is not None:
        logger.info(f"Clearing Whisper model cache: {_current_model_size}")
        _whisper_model = None
        _current_model_size = ""
