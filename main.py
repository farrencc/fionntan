# main.py

import os
from datetime import timedelta  # Add this import
from app import create_app, db
from app.models import User, UserPreference, Podcast, PodcastScript, PodcastAudio, GenerationTask

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Configure session BEFORE app.run() - move these lines up
app.secret_key = os.environ.get('SECRET_KEY', '1aadb9d7c71e3fe371a7cee85fd2a08aa009acc9f88000fea04c01a6716dd75d')  # Fixed quote
app.permanent_session_lifetime = timedelta(minutes=30)

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
    port = 5000
    app.run(host='0.0.0.0', port=port, debug=True)