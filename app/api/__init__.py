# app/api/__init__.py

from flask import Blueprint

# Import all API blueprints
from .auth import auth_bp
from .users import users_bp
from .arxiv import arxiv_bp
from .podcasts import podcasts_bp
from .tasks import tasks_bp
from .health import health_bp

# Export all blueprints
__all__ = [
    'auth_bp',
    'users_bp',
    'arxiv_bp',
    'podcasts_bp',
    'tasks_bp',
    'health_bp'
]

# Optional: Create API root blueprint for versioning
api_v1 = Blueprint('api_v1', __name__)

@api_v1.route('/')
def api_info():
    """API information endpoint."""
    return {
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/v1/auth',
            'users': '/api/v1/users',
            'arxiv': '/api/v1/arxiv',
            'podcasts': '/api/v1/podcasts',
            'tasks': '/api/v1/tasks',
            'health': '/api/v1/health'
        },
        'documentation': '/api/v1/docs'  # If using Swagger/OpenAPI
    }