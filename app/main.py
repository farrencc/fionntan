"""
Main Application Entry Point

Initializes and runs the Flask application with Google OAuth support.
"""

import os
from dotenv import load_dotenv
from podcast.app_integration import setup_podcast_generator

# Load environment variables from .env file
load_dotenv()

# Import application factory
from auth import create_app
from auth.config import config

# Create app with the appropriate configuration
env = os.environ.get('FLASK_ENV', 'default')
app = create_app(config[env])

# Add a simple index route
@app.route('/')
def index():
    return """
    <h1>Fionntan</h1>
    <p>Welcome to the Fionntan.</p>
    <a href="/auth/login">Login with Google</a>
    """

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
    
    # Set up podcast generator
    setup_podcast_generator(app, {
        'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/your/credentials.json'
    })
    