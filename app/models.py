# app/models.py

from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from . import db

class User(db.Model):
    """User model."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    profile_pic = db.Column(db.String(255))
    google_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    tokens = db.Column(JSONB)
    token_expiry = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(50), default='user')
    
    # Relationships
    preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    podcasts = db.relationship('Podcast', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('GenerationTask', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'role': self.role
        }

class UserPreference(db.Model):
    """User research preferences."""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    topics = db.Column(ARRAY(db.String), default=list)
    categories = db.Column(ARRAY(db.String), default=list)
    authors = db.Column(ARRAY(db.String), default=list)
    max_results = db.Column(db.Integer, default=50)
    days_back = db.Column(db.Integer, default=30)
    sort_by = db.Column(db.String(50), default='relevance')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert preferences to dictionary."""
        return {
            'topics': self.topics,
            'categories': self.categories,
            'authors': self.authors,
            'max_results': self.max_results,
            'days_back': self.days_back,
            'sort_by': self.sort_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Podcast(db.Model):
    """Podcast model."""
    __tablename__ = 'podcasts'
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default=STATUS_PENDING)
    technical_level = db.Column(db.String(50), default='intermediate')
    target_length = db.Column(db.Integer, default=15)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    extra_data = db.Column(JSONB)
    
    # Relationships
    script = db.relationship('PodcastScript', backref='podcast', uselist=False, cascade='all, delete-orphan')
    audio = db.relationship('PodcastAudio', backref='podcast', uselist=False, cascade='all, delete-orphan')
    tasks = db.relationship('GenerationTask', backref='podcast', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert podcast to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'technical_level': self.technical_level,
            'target_length': self.target_length,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'script': self.script.to_dict() if self.script else None,
            'audio': self.audio.to_dict() if self.audio else None,
            'extra_data': self.extra_data 
        }

class PodcastScript(db.Model):
    """Podcast script model."""
    __tablename__ = 'podcast_scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    podcast_id = db.Column(db.Integer, db.ForeignKey('podcasts.id', ondelete='CASCADE'))
    script_content = db.Column(JSONB, nullable=False)
    paper_ids = db.Column(ARRAY(db.String), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert script to dictionary."""
        return {
            'id': self.id,
            'script_content': self.script_content,
            'paper_ids': self.paper_ids,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

class PodcastAudio(db.Model):
    """Podcast audio model."""
    __tablename__ = 'podcast_audio'
    
    id = db.Column(db.Integer, primary_key=True)
    podcast_id = db.Column(db.Integer, db.ForeignKey('podcasts.id', ondelete='CASCADE'))
    file_url = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    duration = db.Column(db.Integer)  # in seconds
    audio_format = db.Column(db.String(50))
    voice_config = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert audio to dictionary."""
        return {
            'id': self.id,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'duration': self.duration,
            'audio_format': self.audio_format,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GenerationTask(db.Model):
    """Task tracking model."""
    __tablename__ = 'generation_tasks'
    
    # Task type constants
    TYPE_SCRIPT_GENERATION = 'script_generation'
    TYPE_AUDIO_GENERATION = 'audio_generation'
    
    # Status constants
    STATUS_QUEUED = 'queued'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    podcast_id = db.Column(db.Integer, db.ForeignKey('podcasts.id', ondelete='CASCADE'))
    task_id = db.Column(db.String(100), unique=True, nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default=STATUS_QUEUED)
    progress = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    task_data = db.Column(JSONB)
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'task_data': self.task_data
        }