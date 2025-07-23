import os
import json
import argparse
import logging
from typing import Dict, Optional
from gemini_module import summarize_transcript, analyze_sentiment, suggest_counsellor_response
from whisper_module import transcribe_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_audio_file(filepath: str) -> None:
    """Validate audio file exists and is accessible."""
    if not filepath:
        raise ValueError("No file path provided")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")
    
    if not os.path.isfile(filepath):
        raise ValueError(f"Path is not a file: {filepath}")
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        raise ValueError("Audio file is empty")
    
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        raise ValueError(f"File too large. Maximum size: {max_size // (1024*1024)}MB")
    
    # Check file extension
    valid_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    file_ext = os.path.splitext(filepath.lower())[1]
    if file_ext not in valid_extensions:
        raise ValueError(f"Unsupported file format. Supported: {valid_extensions}")

def process_audio(filepath: str) -> Dict[str, str]:
    """
    Process audio file through transcription and AI analysis pipeline.
    
    Args:
        filepath: Path to the audio file to process
        
    Returns:
        Dictionary containing transcript, summary, sentiment, and suggestions
    """
    try:
        logger.info(f"Starting audio processing for: {filepath}")
        
        # Step 1: Validate input
        validate_audio_file(filepath)
        
        # Step 2: Transcribe audio using Whisper
        logger.info("Starting transcription...")
        transcript = transcribe_audio(filepath)
        
        if not transcript or transcript.strip() == "":
            raise ValueError("Transcription failed or returned empty result")
        
        logger.info(f"Transcription completed. Length: {len(transcript)} characters")
        
        # Step 3: AI Analysis with error handling
        summary = ""
        sentiment = ""
        suggestions = ""
        
        try:
            logger.info("Starting AI analysis...")
            summary = summarize_transcript(transcript)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            summary = f"Summary generation failed: {str(e)}"
        
        try:
            sentiment = analyze_sentiment(transcript)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            sentiment = f"Sentiment analysis failed: {str(e)}"
        
        try:
            suggestions = suggest_counsellor_response(transcript)
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            suggestions = f"Suggestion generation failed: {str(e)}"
        
        response = {
            "transcript": transcript,
            "summary": summary,
            "sentiment": sentiment,
            "suggestion": suggestions
        }
        
        logger.info("Audio processing completed successfully")
        return response
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except ValueError as e:
        error_msg = f"Invalid input: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process an audio file and output the summary, sentiment, and response suggestions"
    )
    parser.add_argument("audio_file", help="Path to the audio file to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        result = process_audio(args.audio_file)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            exit(1)
        
        print(json.dumps(result, indent=2))
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)
