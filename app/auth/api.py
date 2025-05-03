"""
API Blueprint

Provides JSON API endpoints for the application, protected with authentication.
"""

from flask import Blueprint, jsonify, request, session, current_app
from datetime import datetime

from . import db
from .models import User
from .middleware import login_required, api_key_required

api_bp = Blueprint('api', __name__)


@api_bp.route('/user')
@login_required
def get_user():
    """Get current user information."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    return jsonify(user.to_dict())


@api_bp.route('/preferences')
@login_required
def get_preferences():
    """Get user research preferences."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    return jsonify(user.research_preferences)


@api_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update user research preferences."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get preferences from request
    data = request.json
    
    # Validate preference data
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid preference format"}), 400
    
    # Update preferences (only allowed fields)
    allowed_fields = {'topics', 'categories', 'authors', 'max_results', 'days_back', 'sort_by'}
    new_prefs = {}
    
    # Copy existing preferences
    for key, value in user.research_preferences.items():
        new_prefs[key] = value
    
    # Update with new values
    for key, value in data.items():
        if key in allowed_fields:
            new_prefs[key] = value
    
    # Basic validation
    if 'max_results' in new_prefs and (not isinstance(new_prefs['max_results'], int) or 
                                      new_prefs['max_results'] <= 0 or 
                                      new_prefs['max_results'] > 100):
        return jsonify({"error": "max_results must be between 1 and 100"}), 400
    
    if 'days_back' in new_prefs and (not isinstance(new_prefs['days_back'], int) or 
                                    new_prefs['days_back'] < 0 or 
                                    new_prefs['days_back'] > 365):
        return jsonify({"error": "days_back must be between 0 and 365"}), 400
    
    if 'sort_by' in new_prefs and new_prefs['sort_by'] not in ['relevance', 'lastUpdatedDate']:
        return jsonify({"error": "sort_by must be 'relevance' or 'lastUpdatedDate'"}), 400
    
    # Update user preferences
    user.research_preferences = new_prefs
    db.session.commit()
    
    return jsonify({"message": "Preferences updated successfully", "preferences": new_prefs})


@api_bp.route('/papers/recent')
@login_required
def get_recent_papers():
    """Get recent papers based on user preferences."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # This endpoint would integrate with the arXiv scraper component
    # For now, return a placeholder response
    return jsonify({
        "message": "This endpoint will return recent papers based on user preferences",
        "preferences": user.research_preferences
    })


@api_bp.route('/health')
def health_check():
    """Health check endpoint (no auth required)."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    })


@api_bp.route('/stats')
@api_key_required
def get_stats():
    """Get application statistics (protected by API key for admin use)."""
    # Count users
    user_count = User.query.count()
    
    return jsonify({
        "user_count": user_count,
        "timestamp": datetime.utcnow().isoformat()
    })