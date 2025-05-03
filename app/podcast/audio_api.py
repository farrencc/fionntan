"""
Audio API Routes

Provides Flask API endpoints for generating podcast audio from scripts.
Integrates with the text-to-speech module to create audio files.
"""

from flask import Blueprint, jsonify, request, session, current_app, send_file
import json
import os
from datetime import datetime
import tempfile

from auth.middleware import login_required
from auth.models import User
from auth import db

# Import TTS modules
from text_to_speech import PodcastRenderer, TTSConfig
from podcast_integration import PodcastCreator, PodcastIntegrationError

# Create blueprint
audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

# Initialize TTS renderer singleton for app
_tts_renderer = None


def get_tts_renderer():
    """Get or create TTS renderer singleton."""
    global _tts_renderer
    if _tts_renderer is None:
        # Create TTS configuration
        config = TTSConfig(
            service_account_path=current_app.config.get('GOOGLE_APPLICATION_CREDENTIALS'),
            enable_ssml=True,
            enable_background_music=False,  # Can enable if background music provided
            output_directory=current_app.config.get('AUDIO_OUTPUT_DIR', './audio_output')
        )
        _tts_renderer = PodcastRenderer(config)
    return _tts_renderer


@audio_bp.route('/generate', methods=['POST'])
@login_required
def generate_audio():
    """
    Generate audio from a podcast script.
    
    POST body should include:
    {
        "script_id": "ID of previously generated script",  # Optional
        "script": {}, # Optional - script JSON directly
        "gender_preference": "male|female|mixed", # Optional
        "include_intro_outro": true, # Optional
        "background_music": true # Optional
    }
    
    Returns the generated audio file.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    try:
        # Get request data
        data = request.json or {}
        
        # Get script either from ID or direct JSON
        script_id = data.get('script_id')
        script_data = data.get('script')
        
        if not script_id and not script_data:
            return jsonify({"error": "Either script_id or script data must be provided"}), 400
        
        # Load script from ID if provided
        if script_id:
            scripts_dir = current_app.config.get('PODCAST_SCRIPTS_DIR', 'scripts')
            script_path = os.path.join(scripts_dir, f"{script_id}.json")
            
            if not os.path.exists(script_path):
                return jsonify({"error": "Script not found"}), 404
            
            with open(script_path, 'r', encoding='utf-8') as f:
                full_script = json.load(f)
                script_data = full_script.get('script', {})
        
        # Get optional parameters
        gender_preference = data.get('gender_preference', 'mixed')
        include_intro_outro = data.get('include_intro_outro', True)
        include_background_music = data.get('background_music', False)
        
        # Update renderer config for this request
        renderer = get_tts_renderer()
        renderer.config.add_transitions = True
        
        # Generate audio
        output_path = renderer.render_podcast(
            script_data,
            gender_preference=gender_preference
        )
        
        # Create a more user-friendly filename
        script_title = script_data.get('title', 'podcast')
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in script_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_filename = f"{safe_title}_{timestamp}.mp3"
        
        # Save audio file to user's directory
        user_audio_dir = os.path.join(current_app.config.get('AUDIO_OUTPUT_DIR', './audio_output'), str(user_id))
        os.makedirs(user_audio_dir, exist_ok=True)
        
        final_path = os.path.join(user_audio_dir, user_filename)
        
        # Copy to user directory with user-friendly filename
        import shutil
        shutil.copy2(output_path, final_path)
        
        # Return the audio file
        return send_file(
            final_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=user_filename
        )
    
    except Exception as e:
        current_app.logger.error(f"Error generating audio: {str(e)}")
        return jsonify({"error": "An error occurred during audio generation"}), 500


@audio_bp.route('/stream', methods=['POST'])
@login_required
def stream_audio():
    """
    Stream generated audio instead of downloading.
    
    POST body should include:
    {
        "script_id": "ID of previously generated script",
        "gender_preference": "male|female|mixed" # Optional
    }
    
    Returns audio stream.
    """
    user_id = session.get('user_id')
    
    try:
        # Get request data
        data = request.json or {}
        script_id = data.get('script_id')
        
        if not script_id:
            return jsonify({"error": "script_id is required"}), 400
        
        # Load script
        scripts_dir = current_app.config.get('PODCAST_SCRIPTS_DIR', 'scripts')
        script_path = os.path.join(scripts_dir, f"{script_id}.json")
        
        if not os.path.exists(script_path):
            return jsonify({"error": "Script not found"}), 404
        
        with open(script_path, 'r', encoding='utf-8') as f:
            full_script = json.load(f)
            script_data = full_script.get('script', {})
        
        # Generate temporary audio
        renderer = get_tts_renderer()
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            output_path = renderer.render_podcast(
                script_data,
                gender_preference=data.get('gender_preference', 'mixed'),
                output_path=tmp_path
            )
            
            # Stream the file
            return send_file(
                output_path,
                mimetype='audio/mpeg',
                as_attachment=False
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    current_app.logger.warning(f"Could not delete temporary file: {e}")
    
    except Exception as e:
        current_app.logger.error(f"Error streaming audio: {str(e)}")
        return jsonify({"error": "An error occurred during audio streaming"}), 500


@audio_bp.route('/voices', methods=['GET'])
@login_required
def list_voices():
    """
    List available TTS voices.
    
    Returns available voice descriptions.
    """
    try:
        renderer = get_tts_renderer()
        voices = renderer.voice_manager.available_voices
        
        # Format voices for frontend
        formatted_voices = []
        for voice in voices:
            formatted_voices.append({
                "name": voice.get("name", "Unknown"),
                "language": voice.get("language_codes", ["unknown"])[0] if voice.get("language_codes") else "unknown",
                "gender": voice.get("gender", "UNKNOWN").lower(),
                "is_premium": voice.get("name", "").startswith("en-US-Neural2") or voice.get("name", "").startswith("en-US-Studio")
            })
        
        return jsonify({"voices": formatted_voices})
    
    except Exception as e:
        current_app.logger.error(f"Error listing voices: {str(e)}")
        return jsonify({"error": "Error retrieving available voices"}), 500


@audio_bp.route('/test-voice', methods=['POST'])
@login_required
def test_voice():
    """
    Test a specific voice with sample text.
    
    POST body should include:
    {
        "voice_name": "en-US-Neural2-D",
        "text": "This is a test.",
        "gender": "male|female|neutral"
    }
    
    Returns generated audio sample.
    """
    try:
        # Get request data
        data = request.json or {}
        voice_name = data.get('voice_name')
        text = data.get('text', 'This is a test of this voice.')
        gender = data.get('gender', 'neutral')
        
        if not voice_name:
            return jsonify({"error": "voice_name is required"}), 400
        
        # Create renderer with specific voice configuration
        renderer = get_tts_renderer()
        
        # Create temporary file for test audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Create test script
            test_script = {
                "title": "Voice Test",
                "sections": [
                    {
                        "title": "TEST",
                        "segments": [
                            {
                                "speaker": "test",
                                "text": text
                            }
                        ]
                    }
                ]
            }
            
            # Override voice config for test
            original_configs = renderer.config.voice_configs
            from text_to_speech import VoiceConfig, Gender
            try:
                gender_enum = Gender[gender.upper()] if gender.upper() in Gender.__members__ else Gender.NEUTRAL
            except:
                gender_enum = Gender.NEUTRAL
            
            test_voice_config = {
                "test": VoiceConfig(
                    name=voice_name,
                    gender=gender_enum
                )
            }
            renderer.config.voice_configs = test_voice_config
            
            # Generate test audio
            output_path = renderer.render_podcast(
                test_script,
                output_path=tmp_path
            )
            
            # Restore original configs
            renderer.config.voice_configs = original_configs
            
            # Stream the test audio
            return send_file(
                output_path,
                mimetype='audio/mpeg',
                as_attachment=False
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    current_app.logger.warning(f"Could not delete temporary file: {e}")
    
    except Exception as e:
        current_app.logger.error(f"Error testing voice: {str(e)}")
        return jsonify({"error": "Error testing voice"}), 500


@audio_bp.route('/history', methods=['GET'])
@login_required
def audio_history():
    """
    Get user's generated audio files.
    
    Returns list of generated audio files for the user.
    """
    user_id = session.get('user_id')
    
    try:
        # Get user's audio directory
        user_audio_dir = os.path.join(current_app.config.get('AUDIO_OUTPUT_DIR', './audio_output'), str(user_id))
        
        if not os.path.exists(user_audio_dir):
            return jsonify({"audio_files": []})
        
        # List audio files
        audio_files = []
        for filename in os.listdir(user_audio_dir):
            if filename.endswith('.mp3'):
                file_path = os.path.join(user_audio_dir, filename)
                file_stats = os.stat(file_path)
                
                audio_files.append({
                    "filename": filename,
                    "size_bytes": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "download_url": f"/audio/download/{filename}"
                })
        
        # Sort by creation time (newest first)
        audio_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({"audio_files": audio_files})
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving audio history: {str(e)}")
        return jsonify({"error": "Error retrieving audio history"}), 500


@audio_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_audio(filename):
    """
    Download a previously generated audio file.
    
    Args:
        filename: Name of the audio file to download
        
    Returns the audio file.
    """
    user_id = session.get('user_id')
    
    try:
        # Sanitize filename to prevent directory traversal
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        
        # Get user's audio directory
        user_audio_dir = os.path.join(current_app.config.get('AUDIO_OUTPUT_DIR', './audio_output'), str(user_id))
        file_path = os.path.join(user_audio_dir, safe_filename)
        
        # Verify file exists and is accessible
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Send file
        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=safe_filename
        )
    
    except Exception as e:
        current_app.logger.error(f"Error downloading audio file: {str(e)}")
        return jsonify({"error": "Error downloading audio file"}), 500