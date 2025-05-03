"""
Authentication Middleware

Provides decorators to protect routes that require authentication.
"""

from functools import wraps
from flask import request, jsonify, session, redirect, url_for, current_app
from datetime import datetime

from . import db, oauth
from .models import User


def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            # For API endpoints, return 401
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            
            # For web routes, redirect to login
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        
        # Get user and check token expiry
        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)
            return jsonify({"error": "User not found"}), 404
        
        # Check if token needs refresh
        if user.token_expired() and 'refresh_token' in user.tokens:
            try:
                token = oauth.google.refresh_token(user.tokens['refresh_token'])
                user.set_tokens(token)
                user.last_login = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Token refresh error in middleware: {str(e)}")
                # If refresh fails, clear session and redirect to login
                session.pop('user_id', None)
                
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication expired"}), 401
                
                session['next_url'] = request.url
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def api_key_required(f):
    """Decorator to require API key for routes.
    Use this for machine-to-machine API calls.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        
        # Check if API key is valid
        if api_key != current_app.config.get('API_KEY'):
            return jsonify({"error": "Invalid API key"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function