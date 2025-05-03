"""
Google OAuth Authentication Module for Research Paper Podcast Generator

This module provides a complete Google OAuth 2.0 implementation for the application,
including user management, token handling, and secure API endpoints.
"""

import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth

# Initialize extensions
db = SQLAlchemy()
oauth = OAuth()

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///app.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        GOOGLE_CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.environ.get('GOOGLE_CLIENT_SECRET'),
        GOOGLE_REDIRECT_URI=os.environ.get('GOOGLE_REDIRECT_URI') or 'http://localhost:5000/auth/google/callback',
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Override config if provided
    if config:
        app.config.from_mapping(config)
    
    # Initialize extensions with app
    db.init_app(app)
    Migrate(app, db)
    oauth.init_app(app)
    
    # Register OAuth providers
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'
        }
    )
    
    # Register blueprints
    from .auth import auth_bp
    from .api import api_bp
    from .profile import profile_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    return app