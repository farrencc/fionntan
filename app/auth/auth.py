# app/auth/auth.py

from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app
from authlib.integrations.base_client.errors import OAuthError
from datetime import datetime
import logging

from .. import oauth, db
from ..models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login flow."""
    try:
        # Generate and store state parameter
        session['oauth_state'] = current_app.config.get('SECRET_KEY')
        
        # Get redirect URI from config
        redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI')
        
        # Initialize OAuth client
        oauth_client = oauth.create_client('google')
        if not oauth_client:
            logger.error("Failed to create OAuth client")
            return jsonify({"error": "OAuth configuration error"}), 500
        
        # Start authorization flow
        return oauth_client.authorize_redirect(redirect_uri)
    
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        return jsonify({"error": "Failed to initiate OAuth login"}), 500

@auth_bp.route('/callback')
def callback():
    """Handle callback from Google OAuth."""
    try:
        # Get OAuth client
        oauth_client = oauth.create_client('google')
        if not oauth_client:
            logger.error("Failed to create OAuth client for callback")
            return jsonify({"error": "OAuth configuration error"}), 500
        
        # Get token
        token = oauth_client.authorize_access_token()
        if not token:
            logger.error("No token received in callback")
            return jsonify({"error": "No token received"}), 401
        
        # Get user info
        userinfo_endpoint = 'https://www.googleapis.com/oauth2/v3/userinfo'
        resp = oauth_client.get(userinfo_endpoint)
        if not resp:
            logger.error("Failed to get user info")
            return jsonify({"error": "Failed to get user info"}), 500
        
        user_info = resp.json()
        
        # Find or create user
        user = User.query.filter_by(google_id=user_info['sub']).first()
        
        if not user:
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
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session['user_id'] = user.id
        session.permanent = True
        
        # Redirect to frontend with tokens
        frontend_url = current_app.config['CORS_ORIGINS'][0]
        return redirect(f"{frontend_url}/auth/success?token={token['access_token']}")
    
    except OAuthError as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 401
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh OAuth token."""
    try:
        oauth_client = oauth.create_client('google')
        if not oauth_client:
            return jsonify({"error": "OAuth configuration error"}), 500
        
        refresh_token = request.json.get('refresh_token')
        if not refresh_token:
            return jsonify({"error": "No refresh token provided"}), 400
        
        token = oauth_client.refresh_token(refresh_token)
        return jsonify({"access_token": token['access_token']})
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"error": "Failed to refresh token"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log user out."""
    session.clear()
    return jsonify({"message": "Successfully logged out"})

@auth_bp.errorhandler(Exception)
def handle_error(error):
    """Global error handler for auth routes."""
    logger.error(f"Auth error: {str(error)}")
    return jsonify({"error": "Authentication error"}), 500