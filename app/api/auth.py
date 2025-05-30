# app/api/auth.py

from flask import Blueprint, request, jsonify, current_app, redirect, url_for, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from authlib.integrations.base_client.errors import OAuthError
from datetime import datetime

from .. import oauth, db
from ..models import User
from ..api.errors import error_response, ApiException

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    """Initiate Google OAuth login."""
    try:
        redirect_uri = url_for('auth.callback', _external=True)
        oauth_client = oauth.create_client('google')
        return oauth_client.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"OAuth login error: {str(e)}")
        return error_response(500, "Failed to initiate OAuth login")

@auth_bp.route('/callback', methods=['GET'])
def callback():
    """Handle OAuth callback."""
    try:
        oauth_client = oauth.create_client('google')
        token = oauth_client.authorize_access_token()
        
        resp = oauth_client.get('https://openidconnect.googleapis.com/v1/userinfo', token=token)
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
            user.name = user_info.get('name', user.name)
            user.email = user_info.get('email', user.email)
            user.profile_pic = user_info.get('picture', user.profile_pic)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # Store in session
        session['access_token'] = access_token
        session['refresh_token'] = refresh_token
        session['user_id'] = user.id
        
        # Redirect to React app on port 5001
        return redirect('http://localhost:5001/auth/success')
        
    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        return redirect('http://localhost:5001/auth/error')

@auth_bp.route('/session/tokens', methods=['GET'])
def get_session_tokens():
    """Get tokens from session."""
    current_app.logger.info(f"Session tokens requested")
    
    access_token = session.get('access_token')
    refresh_token = session.get('refresh_token')
    
    if access_token:
        # Clear tokens from session after retrieval
        session.pop('access_token', None)
        session.pop('refresh_token', None)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token
        })
    else:
        current_app.logger.error("No tokens found in session")
        return error_response(401, "No tokens found")

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token."""
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return jsonify({'access_token': access_token})
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return error_response(401, "Failed to refresh token")

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (invalidate JWT token)."""
    return jsonify({'message': 'Successfully logged out'})