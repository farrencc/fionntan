"""
Podcast API Routes

Provides Flask API endpoints for generating podcast scripts.
Integrates with the existing Flask application authentication system.
"""

from flask import Blueprint, jsonify, request, session, current_app
import json
import os
from datetime import datetime

from auth.middleware import login_required
from auth.models import User
from auth import db

# Import podcast generator modules
from podcast_integration import PodcastCreator, PodcastIntegrationError

# Create blueprint
podcast_bp = Blueprint('podcast', __name__, url_prefix='/podcast')

# Initialize podcast creator (singleton for app)
_podcast_creator = None

def get_podcast_creator():
    """Get or create podcast creator singleton."""
    global _podcast_creator
    if _podcast_creator is None:
        config_path = current_app.config.get('PODCAST_CONFIG_PATH')
        _podcast_creator = PodcastCreator(config_path)
    return _podcast_creator


@podcast_bp.route('/generate', methods=['POST'])
@login_required
def generate_podcast():
    """
    Generate a podcast script based on user preferences.
    
    POST body should include:
    {
        "title": "Optional custom title",
        "technical_level": "beginner|intermediate|advanced",
        "target_length": 15,  # minutes
        "use_preferences": true  # whether to use stored user preferences
    }
    
    Returns the generated script and metadata.
    """
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        # Get podcast parameters
        title = data.get('title')
        technical_level = data.get('technical_level', 'intermediate')
        target_length = int(data.get('target_length', 15))
        use_preferences = data.get('use_preferences', True)
        
        # Validate technical level
        if technical_level not in ['beginner', 'intermediate', 'advanced']:
            return jsonify({"error": "Invalid technical_level. Must be beginner, intermediate, or advanced"}), 400
        
        # Validate target length
        if target_length < 5 or target_length > 60:
            return jsonify({"error": "Invalid target_length. Must be between 5 and 60 minutes"}), 400
        
        # Get podcast creator
        creator = get_podcast_creator()
        
        # Generate script based on user preferences or request data
        if use_preferences:
            # Use stored user preferences
            preferences = user.research_preferences
            
            if not preferences or not preferences.get('topics'):
                return jsonify({
                    "error": "No research preferences found. Please set your preferences first."
                }), 400
            
            result = creator.generate_from_user_preferences(
                user_preferences=preferences,
                podcast_title=title,
                technical_level=technical_level,
                target_length=target_length
            )
        else:
            # Use request-specific preferences
            custom_prefs = data.get('preferences', {})
            
            if not custom_prefs or not custom_prefs.get('topics'):
                return jsonify({"error": "Missing research topics in preferences"}), 400
            
            result = creator.generate_from_user_preferences(
                user_preferences=custom_prefs,
                podcast_title=title,
                technical_level=technical_level,
                target_length=target_length
            )
        
        # Return the result
        return jsonify(result)
    
    except PodcastIntegrationError as e:
        current_app.logger.error(f"Podcast generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error in podcast generation: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@podcast_bp.route('/generate-from-papers', methods=['POST'])
@login_required
def generate_from_papers():
    """
    Generate a podcast script from specific arXiv paper IDs.
    
    POST body should include:
    {
        "paper_ids": ["2305.12140", "2305.14314"],
        "title": "Optional custom title",
        "technical_level": "beginner|intermediate|advanced",
        "target_length": 15  # minutes
    }
    
    Returns the generated script and metadata.
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        # Get paper IDs
        paper_ids = data.get('paper_ids')
        if not paper_ids or not isinstance(paper_ids, list):
            return jsonify({"error": "Missing or invalid paper_ids. Must be a list of arXiv IDs"}), 400
        
        # Get podcast parameters
        title = data.get('title')
        technical_level = data.get('technical_level', 'intermediate')
        target_length = int(data.get('target_length', 15))
        
        # Validate technical level
        if technical_level not in ['beginner', 'intermediate', 'advanced']:
            return jsonify({"error": "Invalid technical_level. Must be beginner, intermediate, or advanced"}), 400
        
        # Validate target length
        if target_length < 5 or target_length > 60:
            return jsonify({"error": "Invalid target_length. Must be between 5 and 60 minutes"}), 400
        
        # Get podcast creator
        creator = get_podcast_creator()
        
        # Generate script based on paper IDs
        result = creator.generate_from_paper_ids(
            paper_ids=paper_ids,
            podcast_title=title,
            technical_level=technical_level,
            target_length=target_length
        )
        
        # Return the result
        return jsonify(result)
    
    except PodcastIntegrationError as e:
        current_app.logger.error(f"Podcast generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error in podcast generation: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@podcast_bp.route('/script/<script_id>', methods=['GET'])
@login_required
def get_script(script_id):
    """
    Get a previously generated podcast script by ID.
    
    Returns the script in JSON format.
    """
    try:
        # Define script storage path
        scripts_dir = current_app.config.get('PODCAST_SCRIPTS_DIR', 'scripts')
        script_path = os.path.join(scripts_dir, f"{script_id}.json")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            return jsonify({"error": "Script not found"}), 404
        
        # Read the script
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        
        return jsonify(script)
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving script {script_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve script"}), 500


@podcast_bp.route('/text-script/<script_id>', methods=['GET'])
@login_required
def get_text_script(script_id):
    """
    Get a previously generated podcast script by ID as formatted text.
    
    Returns the script in plain text format for reading or TTS.
    """
    try:
        # Define script storage path
        scripts_dir = current_app.config.get('PODCAST_SCRIPTS_DIR', 'scripts')
        script_path = os.path.join(scripts_dir, f"{script_id}.json")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            return jsonify({"error": "Script not found"}), 404
        
        # Read the script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        # Get podcast creator
        creator = get_podcast_creator()
        
        # Generate text script
        text_script = creator.generate_text_script(script_data)
        
        # Return as text
        return text_script, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving text script {script_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve text script"}), 500


@podcast_bp.route('/scripts', methods=['GET'])
@login_required
def list_scripts():
    """
    List all generated podcast scripts for the current user.
    
    Returns a list of script metadata.
    """
    try:
        # Get user ID
        user_id = session.get('user_id')
        
        # Define script storage path
        scripts_dir = current_app.config.get('PODCAST_SCRIPTS_DIR', 'scripts')
        user_scripts_dir = os.path.join(scripts_dir, str(user_id))
        
        # Check if the directory exists
        if not os.path.exists(user_scripts_dir):
            return jsonify({"scripts": []})
        
        # Get all script files
        script_files = [f for f in os.listdir(user_scripts_dir) if f.endswith('.json')]
        scripts = []
        
        for script_file in script_files:
            script_path = os.path.join(user_scripts_dir, script_file)
            
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                # Extract script metadata
                script_id = os.path.splitext(script_file)[0]
                metadata = script_data.get('metadata', {})
                script_info = {
                    'id': script_id,
                    'title': script_data.get('script', {}).get('title', 'Untitled Podcast'),
                    'generated_at': metadata.get('generated_at'),
                    'paper_count': metadata.get('paper_count', 0),
                    'topics': metadata.get('topics', []),
                }
                
                scripts.append(script_info)
            
            except Exception as e:
                current_app.logger.warning(f"Error reading script {script_file}: {e}")
                continue
        
        # Sort by generated_at (newest first)
        scripts.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        return jsonify({"scripts": scripts})
    
    except Exception as e:
        current_app.logger.error(f"Error listing scripts: {str(e)}")
        return jsonify({"error": "Failed to list scripts"}), 500