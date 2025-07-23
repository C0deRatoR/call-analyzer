import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import tempfile
import json
from typing import Dict, Any

# Import your modules
from main import process_audio, validate_audio_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application for production deployment."""
    
    # Configure paths for production deployment
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.abspath(os.path.join(base_dir, '..', 'web'))
    static_dir = os.path.abspath(os.path.join(base_dir, '..', 'web'))
    
    # Create Flask app with proper configuration
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='')
    
    # Production configuration
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'call-analyzer-secret-key-change-in-production')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'}
    
    def allowed_file(filename: str) -> bool:
        """Check if the uploaded file has an allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def generate_secure_filename(filename: str) -> str:
        """Generate a secure filename for uploaded files."""
        if not filename:
            return 'audio_file'
        
        # Use werkzeug's secure_filename and add timestamp for uniqueness
        import time
        secure_name = secure_filename(filename)
        if not secure_name:
            secure_name = 'audio_file'
        
        # Add timestamp to prevent conflicts
        name, ext = os.path.splitext(secure_name)
        timestamp = str(int(time.time()))
        return f"{name}_{timestamp}{ext}"
    
    @app.route('/')
    def index():
        """Render the main application page."""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index page: {e}")
            return f"Error loading application: {str(e)}", 500
    
    @app.route('/styles/<path:filename>')
    def serve_styles(filename):
        """Serve CSS files."""
        try:
            styles_dir = os.path.join(app.static_folder, 'styles')
            return send_from_directory(styles_dir, filename)
        except Exception as e:
            logger.error(f"Error serving style file {filename}: {e}")
            return f"Style file not found: {filename}", 404
    
    @app.route('/scripts/<path:filename>')  
    def serve_scripts(filename):
        """Serve JavaScript files."""
        try:
            scripts_dir = os.path.join(app.static_folder, 'scripts')
            return send_from_directory(scripts_dir, filename)
        except Exception as e:
            logger.error(f"Error serving script file {filename}: {e}")
            return f"Script file not found: {filename}", 404
    
    @app.route('/process_audio', methods=['POST'])
    def process_audio_route():
        """Process uploaded audio file and return analysis results."""
        temp_file_path = None
        
        try:
            # Check if file is present in request
            if 'audio_file' not in request.files:
                logger.warning("No audio file provided in request")
                return jsonify({'error': 'No audio file provided'}), 400
            
            file = request.files['audio_file']
            
            # Check if file is selected
            if file.filename == '':
                logger.warning("No file selected")
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file type
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                return jsonify({
                    'error': f'Invalid file type. Supported formats: {", ".join(ALLOWED_EXTENSIONS).upper()}'
                }), 400
            
            # Generate secure filename
            secure_name = generate_secure_filename(file.filename)
            temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
            
            # Save uploaded file
            logger.info(f"Saving uploaded file: {secure_name}")
            file.save(temp_file_path)
            
            # Validate the saved file
            validate_audio_file(temp_file_path)
            
            # Process the audio file
            logger.info(f"Processing audio file: {secure_name}")
            result = process_audio(temp_file_path)
            
            # Check if processing was successful
            if 'error' in result:
                logger.error(f"Audio processing failed: {result['error']}")
                return jsonify(result), 500
            
            logger.info(f"Successfully processed audio file: {secure_name}")
            return jsonify(result)
        
        except RequestEntityTooLarge:
            logger.error("File too large")
            return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413
        
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return jsonify({'error': f'File not found: {str(e)}'}), 404
        
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        
        except Exception as e:
            logger.error(f"Unexpected error processing audio: {e}")
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        try:
            return jsonify({
                'status': 'healthy',
                'service': 'Call Analyzer',
                'version': '2.1.0'
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        logger.warning(f"404 error: {request.url}")
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"500 error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        """Handle file too large errors."""
        logger.warning("File upload too large")
        return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413
    
    # Log successful app creation
    logger.info("Flask app created successfully")
    logger.info(f"Template folder: {template_dir}")
    logger.info(f"Static folder: {static_dir}")
    
    return app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Production configuration for Railway deployment
    port = int(os.environ.get('PORT', 5000))
    
    # Determine if we're in production
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or \
                   os.environ.get('FLASK_ENV') == 'production'
    
    # Configure logging for production
    if is_production:
        logging.getLogger().setLevel(logging.INFO)
        logger.info("Starting Call Analyzer in PRODUCTION mode")
    else:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Starting Call Analyzer in DEVELOPMENT mode")
    
    logger.info(f"Starting server on port {port}")
    logger.info(f"Production mode: {is_production}")
    
    # Start the Flask application
    app.run(
        host='0.0.0.0',  # Required for Railway deployment
        port=port,
        debug=not is_production,  # Disable debug in production
        threaded=True  # Enable threading for better performance
    )
