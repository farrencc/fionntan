"""
Main Application Entry Point

Initializes and runs the Flask application with Google OAuth support.
"""

# import os
# from dotenv import load_dotenv
# from podcast.app_integration import setup_podcast_generator

# # Load environment variables from .env file
# load_dotenv()

# # Import application factory
# from auth import create_app
# from auth.config import config

# # Create app with the appropriate configuration
# env = os.environ.get('FLASK_ENV', 'default')
# app = create_app(config[env])

# # Add a simple index route


# if __name__ == '__main__':
#     app.run(debug=app.config['DEBUG'])
    
#     # Set up podcast generator
#     setup_podcast_generator(app, {
#         'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/your/credentials.json'
#     })


# main.py

import os
from app import create_app, db
from app.models import User, UserPreference, Podcast, PodcastScript, PodcastAudio, GenerationTask

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

# @app.route('/')
# def index():
#     return """
#     <h1>Fionntan</h1>
#     <p>Welcome to the Fionntan.</p>
#     <a href="/auth/login">Login with Google</a>
#     """

# Create CLI context
@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'UserPreference': UserPreference,
        'Podcast': Podcast,
        'PodcastScript': PodcastScript,
        'PodcastAudio': PodcastAudio,
        'GenerationTask': GenerationTask
    }

# CLI commands for database management
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command('reset-db')
def reset_db():
    """Reset the database."""
    if input('Are you sure you want to reset the database? (y/n): ').lower() == 'y':
        db.drop_all()
        db.create_all()
        print('Database reset complete.')

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)