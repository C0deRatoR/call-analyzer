import os
import uuid
import logging
import werkzeug.utils
from flask import Flask, render_template, request, jsonify
from main import process_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="../web", static_folder="../web")

# Configuration
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

def validate_audio_file(file):
    """Validate uploaded audio file for security and format."""
    if not file or not file.filename:
        raise ValueError("No file selected")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    if file_size == 0:
        raise ValueError("File is empty")
    
    # Basic magic byte validation for common audio formats
    header = file.read(12)
    file.seek(0)
    
    valid_headers = [
        b'RIFF',      # WAV
        b'ID3',       # MP3
        b'\xff\xfb',  # MP3
        b'\xff\xf3',  # MP3
        b'fLaC',      # FLAC
        b'ftypM4A'    # M4A
    ]
    
    if not any(header.startswith(h) for h in valid_headers):
        raise ValueError("File appears to be corrupted or not a valid audio file")
    
    return True

def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure unique filename."""
    file_ext = os.path.splitext(original_filename.lower())[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    return unique_filename

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process_audio", methods=["POST"])
def process_audio_request():
    file_path = None
    try:
        # Validate request
        if "audio_file" not in request.files:
            logger.warning("No file uploaded in request")
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["audio_file"]
        logger.info(f"Processing upload: {file.filename}")
        
        # Validate file
        validate_audio_file(file)
        
        # Generate secure filename
        secure_filename = generate_secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename)
        
        # Save file securely
        file.save(file_path)
        logger.info(f"File saved: {secure_filename}")
        
        # Process audio with error handling
        response = process_audio(file_path)
        
        if "error" in response:
            logger.error(f"Processing error: {response['error']}")
            return jsonify(response), 500
            
        logger.info("Audio processing completed successfully")
        return jsonify(response)
        
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    finally:
        # Always clean up uploaded file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file: {cleanup_error}")

if __name__ == "__main__":
    # Production-safe settings
    app.run(debug=False, host='127.0.0.1', port=5000)
