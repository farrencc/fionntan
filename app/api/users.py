# app/api/users.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError

from .. import db
from ..models import User, UserPreference
from ..api.errors import error_response

users_bp = Blueprint('users', __name__)

# Schemas for request validation
class PreferenceSchema(Schema):
    topics = fields.List(fields.String(), missing=[])
    categories = fields.List(fields.String(), missing=[])
    authors = fields.List(fields.String(), missing=[])
    max_results = fields.Integer(validate=validate.Range(min=1, max=100), missing=50)
    days_back = fields.Integer(validate=validate.Range(min=0, max=365), missing=30)
    sort_by = fields.String(validate=validate.OneOf(['relevance', 'lastUpdatedDate']), missing='relevance')

preference_schema = PreferenceSchema()

def get_current_user():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        raise Exception("User not found")
    return user

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current user information."""
    try:
        user = get_current_user()
        return jsonify(user.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return error_response(404, "User not found")

@users_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user research preferences."""
    try:
        user = get_current_user()
        
        if not user.preferences:
            # Create default preferences if they don't exist
            preferences = UserPreference(user_id=user.id)
            db.session.add(preferences)
            db.session.commit()
            user.preferences = preferences
        
        return jsonify(user.preferences.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error getting preferences: {str(e)}")
        return error_response(500, "Failed to retrieve preferences")

@users_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Update user research preferences."""
    try:
        user = get_current_user()
        
        # Validate request data
        try:
            data = preference_schema.load(request.json)
        except ValidationError as err:
            return error_response(400, err.messages)
        
        # Get or create preferences
        if not user.preferences:
            preferences = UserPreference(user_id=user.id)
            db.session.add(preferences)
        else:
            preferences = user.preferences
        
        # Update preferences
        for key, value in data.items():
            setattr(preferences, key, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating preferences: {str(e)}")
        db.session.rollback()
        return error_response(500, "Failed to update preferences")

@users_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get user dashboard data with stats."""
    try:
        user = get_current_user()
        
        # Get podcast statistics
        total_podcasts = user.podcasts.count()
        completed_podcasts = user.podcasts.filter_by(status='completed').count()
        processing_podcasts = user.podcasts.filter_by(status='processing').count()
        failed_podcasts = user.podcasts.filter_by(status='failed').count()
        
        # Get recent podcasts
        recent_podcasts = user.podcasts.order_by(user.podcasts.created_at.desc()).limit(5).all()
        
        return jsonify({
            'user': user.to_dict(),
            'stats': {
                'total_podcasts': total_podcasts,
                'completed_podcasts': completed_podcasts,
                'processing_podcasts': processing_podcasts,
                'failed_podcasts': failed_podcasts
            },
            'recent_podcasts': [podcast.to_dict() for podcast in recent_podcasts]
        })
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard data: {str(e)}")
        return error_response(500, "Failed to retrieve dashboard data")