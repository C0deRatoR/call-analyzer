import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

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
    Transcribe audio file - Currently using mock transcription for deployment.
    
    Args:
        filepath: Path to the audio file
        model_size: Size of the model to use
        
    Returns:
        Transcribed text from the audio
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
    """
    try:
        logger.info(f"Starting transcription for: {filepath}")
        
        # Validate file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        # Mock transcription for deployment
        # TODO: Replace with actual Whisper implementation once deployment is stable
        mock_transcript = """I'm interested in applying to your university. Could you provide some details about the admission process? Of course. Could you let me know which program you're interested in? We have different admission requirements for undergraduate and postgraduate courses. I'm looking to apply for the bachelor's program in computer science. Great choice for the computer science program. You'll need to submit your high school transcripts. Standardized tests scores. And a personal statement. We also require an entrance exam or interview in some cases."""
        
        logger.info(f"Mock transcription completed. Text length: {len(mock_transcript)} characters")
        return mock_transcript
        
    except FileNotFoundError:
        logger.error(f"Audio file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise Exception(f"Transcription failed: {str(e)}")

def clear_model_cache():
    """Clear the model cache to free memory."""
    logger.info("Model cache cleared (mock implementation)")
