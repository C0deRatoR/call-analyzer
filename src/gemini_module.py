import os
import time
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Gemini API
try:
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not found")
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    raise

# Global model cache
_gemini_model: Optional[genai.GenerativeModel] = None

def get_gemini_model() -> genai.GenerativeModel:
    """Get cached Gemini model or create if not cached."""
    global _gemini_model
    
    if _gemini_model is None:
        try:
            _gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("Gemini model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise RuntimeError(f"Failed to initialize Gemini model: {str(e)}")
    
    return _gemini_model

def validate_transcript(transcript: str) -> None:
    """Validate transcript input."""
    if not transcript:
        raise ValueError("Transcript cannot be empty")
    
    if not isinstance(transcript, str):
        raise ValueError("Transcript must be a string")
    
    transcript = transcript.strip()
    if len(transcript) < 10:
        raise ValueError("Transcript too short for meaningful analysis")
    
    # Check for reasonable length (Gemini has token limits)
    max_length = 30000  # Approximate character limit
    if len(transcript) > max_length:
        logger.warning(f"Transcript is very long ({len(transcript)} chars), may be truncated")

def generate_text_with_retry(prompt: str, max_retries: int = 3, delay: float = 1.0) -> str:
    """
    Generate text using Gemini API with retry logic.
    
    Args:
        prompt: The prompt to send to the model
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Generated text response
        
    Raises:
        RuntimeError: If all retries fail
    """
    model = get_gemini_model()
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Generating text (attempt {attempt + 1}/{max_retries + 1})")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1000,
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"API call failed (attempt {attempt + 1}): {error_msg}")
            
            # Don't retry on certain errors
            if "API_KEY" in error_msg.upper() or "PERMISSION" in error_msg.upper():
                raise RuntimeError(f"API authentication error: {error_msg}")
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise RuntimeError(f"Failed to generate text after {max_retries + 1} attempts: {error_msg}")

def summarize_transcript(transcript: str) -> str:
    """
    Generate a summary of the call transcript.
    
    Args:
        transcript: The call transcript to summarize
        
    Returns:
        Summary text
    """
    try:
        validate_transcript(transcript)
        
        prompt = f"""
        You are an expert summarizer specializing in call analysis. 
        Please provide a concise summary of the following call transcript between a student and a counsellor. 
        Focus on:
        1. Key topics discussed
        2. Main concerns raised by the student
        3. Advice or actions suggested by the counsellor
        4. Any follow-up items or next steps
        
        Keep the summary to 3-5 sentences and maintain a professional tone.

        Transcript:
        {transcript}
        
        Summary:
        """
        
        return generate_text_with_retry(prompt)
        
    except Exception as e:
        error_msg = f"Summary generation failed: {str(e)}"
        logger.error(error_msg)
        return f"Unable to generate summary: {str(e)}"

def analyze_sentiment(transcript: str) -> str:
    """
    Analyze the sentiment of the call transcript.
    
    Args:
        transcript: The call transcript to analyze
        
    Returns:
        Sentiment analysis text
    """
    try:
        validate_transcript(transcript)
        
        prompt = f"""
        You are an expert in sentiment analysis and emotional intelligence. 
        Analyze the following call transcript and provide insights about:
        
        1. Overall emotional tone of the student's responses
        2. Key emotions present (frustration, sadness, hope, anxiety, etc.)
        3. Any notable changes in sentiment throughout the conversation
        4. The counsellor's emotional approach and effectiveness
        
        Provide your analysis in 3-5 sentences with specific examples from the conversation.

        Transcript:
        {transcript}
        
        Sentiment Analysis:
        """
        
        return generate_text_with_retry(prompt)
        
    except Exception as e:
        error_msg = f"Sentiment analysis failed: {str(e)}"
        logger.error(error_msg)
        return f"Unable to analyze sentiment: {str(e)}"

def suggest_counsellor_response(transcript: str) -> str:
    """
    Suggest improved counsellor responses.
    
    Args:
        transcript: The call transcript to analyze
        
    Returns:
        Suggestions text
    """
    try:
        validate_transcript(transcript)
        
        prompt = f"""
        You are an experienced counsellor and communication coach with expertise in student guidance. 
        Review the following call transcript between a student and a counsellor.
        
        Based on the conversation, suggest 3-5 specific improvements or alternative responses 
        that the counsellor could have used to provide better guidance. Focus on:
        
        1. More empathetic responses
        2. Better questioning techniques
        3. Clearer guidance or action items
        4. Improved emotional support
        5. More effective communication strategies
        
        Format your response as numbered points, each being 1-2 sentences.

        Transcript:
        {transcript}
        
        Counsellor Response Suggestions:
        """
        
        return generate_text_with_retry(prompt)
        
    except Exception as e:
        error_msg = f"Suggestion generation failed: {str(e)}"
        logger.error(error_msg)
        return f"Unable to generate suggestions: {str(e)}"

def test_api_connection() -> bool:
    """Test if the Gemini API is working properly."""
    try:
        test_prompt = "Respond with 'API test successful'"
        response = generate_text_with_retry(test_prompt, max_retries=1)
        return "successful" in response.lower()
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False
