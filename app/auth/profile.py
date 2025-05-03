"""
User Profile Management

Routes for managing user profile and research preferences.
"""

from flask import Blueprint, jsonify, request, session, render_template
from . import db
from .models import User
from .middleware import login_required

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
@login_required
def profile_page():
    """Render the profile page."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    return render_template('profile.html', user=user)


@profile_bp.route('/data')
@login_required
def get_profile():
    """Get user profile and preferences as JSON."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    return jsonify(user.to_dict())


@profile_bp.route('/preferences', methods=['PUT'])
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