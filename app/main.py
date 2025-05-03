"""
Main Application Entry Point

Initializes and runs the Flask application with Google OAuth support.
"""

import os
from dotenv import load_dotenv

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
    <h1>Research Paper Podcast Generator</h1>
    <p>Welcome to the Research Paper Podcast Generator.</p>
    <a href="/auth/login">Login with Google</a>
    """

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])