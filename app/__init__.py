# app/__init__.py

import os
import logging
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from celery import Celery

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)
celery = Celery()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)
    
    # Initialize Celery
    celery.conf.update(app.config)
    celery.Task = make_celery(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure logging
    configure_logging(app)
    
    # Register OAuth providers
    register_oauth_providers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
    return app

def make_celery(app):
    """Create Celery task base class."""
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    return ContextTask

def configure_logging(app):
    """Configure application logging."""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

def register_oauth_providers(app):
    """Register OAuth providers."""
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
        client_kwargs={'scope': 'openid email profile'},
    )

def register_blueprints(app):
    """Register application blueprints."""
    from .api import auth_bp, users_bp, arxiv_bp, podcasts_bp, tasks_bp, health_bp
    
    # API blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(arxiv_bp, url_prefix='/api/v1/arxiv')
    app.register_blueprint(podcasts_bp, url_prefix='/api/v1/podcasts')
    app.register_blueprint(tasks_bp, url_prefix='/api/v1/tasks')
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')

def register_error_handlers(app):
    """Register error handlers."""
    from .api.errors import register_error_handlers as register_handlers
    register_handlers(app)