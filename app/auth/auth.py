"""
Authentication Blueprint

Handles routes related to Google OAuth authentication.
"""

from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app, flash
from authlib.integrations.base_client.errors import OAuthError
from datetime import datetime

from . import oauth, db
from .models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login flow."""
    # Generate a secure state parameter
    session['oauth_state'] = current_app.config.get('SECRET_KEY')
    
    # Redirect to Google's OAuth authorization endpoint
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def callback():
    """Handle callback from Google OAuth."""
    try:
        # Get token from Google
        token = oauth.google.authorize_access_token()
        
        # Get user info from Google
        resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
        
        # Find or create user
        user = User.query.filter_by(google_id=user_info['sub']).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=user_info['sub'],
                email=user_info['email'],
                name=user_info.get('name', ''),
                profile_pic=user_info.get('picture', '')
            )
            db.session.add(user)
        else:
            # Update existing user info
            user.name = user_info.get('name', user.name)
            user.email = user_info.get('email', user.email)
            user.profile_pic = user_info.get('picture', user.profile_pic)
        
        # Store tokens
        user.set_tokens(token)
        user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Store user ID in session
        session['user_id'] = user.id
        
        # Redirect to profile page or specified next URL
        next_url = session.pop('next_url', '/profile')
        return redirect(next_url)
    
    except OAuthError as e:
        # Handle OAuth errors
        current_app.logger.error(f"OAuth error: {str(e)}")
        flash(f"Authentication error: {str(e)}", 'error')
        return redirect(url_for('index'))


@auth_bp.route('/logout')
def logout():
    """Log user out."""
    # Clear session
    session.pop('user_id', None)
    session.clear()
    
    return redirect(url_for('index'))


@auth_bp.route('/refresh-token')
def refresh_token():
    """Refresh the OAuth token if expired."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    # Check if token needs refreshing
    if user.token_expired() and 'refresh_token' in user.tokens:
        try:
            # Attempt token refresh
            token = oauth.google.refresh_token(user.tokens['refresh_token'])
            user.set_tokens(token)
            db.session.commit()
            return jsonify({"message": "Token refreshed successfully"})
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return jsonify({"error": "Failed to refresh token"}), 500
    
    return jsonify({"message": "Token valid"})