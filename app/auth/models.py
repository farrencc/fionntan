"""
User Model for Google OAuth Authentication
"""

from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import JSONB
from . import db

class User(db.Model):
    """User model that stores Google OAuth information and research preferences."""
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # OAuth tokens - using JSONB for PostgreSQL or fallback to JSON for SQLite
    tokens = db.Column(db.JSON, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    
    # User preferences for paper searches
    research_preferences = db.Column(db.JSON, default=lambda: {
        'topics': [],
        'categories': [],
        'authors': [],
        'max_results': 50,
        'days_back': 30,
        'sort_by': 'relevance'
    })
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_tokens(self, tokens):
        """Store OAuth tokens securely."""
        self.tokens = tokens
        # Calculate token expiry time
        if 'expires_in' in tokens:
            self.token_expiry = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
        else:
            # Default expiry of 1 hour if not specified
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
    
    def token_expired(self):
        """Check if the access token has expired."""
        if not self.token_expiry:
            return True
        return datetime.utcnow() > self.token_expiry
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive information)."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
            'research_preferences': self.research_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }