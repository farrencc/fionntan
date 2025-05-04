# app/api/errors.py

from flask import jsonify, current_app
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import HTTPException

class ApiException(Exception):
    """Custom API exception."""
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def error_response(status_code, message):
    """Generate error response."""
    payload = {
        'error': True,
        'message': message,
        'status_code': status_code
    }
    response = jsonify(payload)
    response.status_code = status_code
    return response

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(ApiException)
    def handle_api_exception(error):
        """Handle custom API exceptions."""
        current_app.logger.error(f"API Exception: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        current_app.logger.error(f"HTTP Exception: {error.description}")
        return error_response(error.code, error.description)
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exception(error):
        """Handle JWT-related errors."""
        current_app.logger.error(f"JWT Exception: {str(error)}")
        return error_response(401, "Authentication error")
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return error_response(404, "Resource not found")
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors."""
        return error_response(405, "Method not allowed")
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        current_app.logger.error(f"Server Error: {str(error)}")
        return error_response(500, "Internal server error")
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle rate limit errors."""
        return error_response(429, f"Rate limit exceeded: {error.description}")
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file size limit errors."""
        return error_response(413, f"File too large. Maximum size: {app.config['MAX_CONTENT_LENGTH']} bytes")
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        current_app.logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return error_response(500, "An unexpected error occurred")