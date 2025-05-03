"""
Application Integration

This module integrates the podcast generation functionality with the Flask application.
It configures the app with the required settings and registers the podcast API routes.
"""

import os
import logging
from typing import Dict, Any

from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app_integration")


def configure_podcast_generator(app: Flask, config: Dict[str, Any] = None) -> None:
    """
    Configure the podcast generator in the Flask application.
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    # Set default configuration
    app.config.setdefault('PODCAST_CONFIG_PATH', os.path.join(app.instance_path, 'podcast_config.json'))
    app.config.setdefault('PODCAST_SCRIPTS_DIR', os.path.join(app.instance_path, 'scripts'))
    
    # Override with provided config
    if config:
        for key, value in config.items():
            app.config[key] = value
    
    # Ensure instance path and scripts directory exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['PODCAST_SCRIPTS_DIR'], exist_ok=True)
    
    # Add Google AI API key to environment if provided
    if 'GOOGLE_APPLICATION_CREDENTIALS' in app.config:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = app.config['GOOGLE_APPLICATION_CREDENTIALS']
    
    logger.info("Podcast generator configured")


def register_podcast_blueprint(app: Flask) -> None:
    """
    Register the podcast blueprint with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Import here to avoid circular imports
    from podcast_api import podcast_bp
    from audio_api import audio_bp
    
    # Register blueprints
    app.register_blueprint(podcast_bp)
    app.register_blueprint(audio_bp)
    logger.info("Podcast and audio blueprints registered")


def setup_podcast_generator(app: Flask, config: Dict[str, Any] = None) -> None:
    """
    Set up the podcast generator in the Flask application.
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    # Configure the podcast generator
    configure_podcast_generator(app, config)
    
    # Register the podcast blueprint
    register_podcast_blueprint(app)
    
    logger.info("Podcast generator setup complete")


def get_gemini_credentials():
    """
    Helper function to get Google Gemini API credentials path.
    Can be used in your main.py file.
    
    Returns:
        Path to credentials file or None if not found
    """
    # Common locations for credentials
    possible_paths = [
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
        './credentials.json',
        './config/credentials.json',
        os.path.expanduser('~/.config/google/credentials.json'),
    ]
    
    # Return the first valid path
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None


# Example usage in main.py:
"""
from app_integration import setup_podcast_generator, get_gemini_credentials

# After creating your Flask app:
setup_podcast_generator(app, {
    'PODCAST_CONFIG_PATH': './config/podcast_config.json',
    'PODCAST_SCRIPTS_DIR': './data/scripts',
    'GOOGLE_APPLICATION_CREDENTIALS': get_gemini_credentials()
})
"""