# app/api/podcasts.py

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
import uuid
from datetime import datetime

from .. import db, celery
from ..models import User, Podcast, GenerationTask
from ..services.storage_service import StorageService
from ..api.errors import error_response
from ..tasks.podcast_tasks import generate_podcast_script, generate_podcast_audio

podcasts_bp = Blueprint('podcasts', __name__)

# Schemas for request validation
class PodcastCreateSchema(Schema):
    title = fields.String(missing=None)
    technical_level = fields.String(
        validate=validate.OneOf(['beginner', 'intermediate', 'advanced']),
        load_default='intermediate' # Changed from missing
    )
    target_length = fields.Integer(
        validate=validate.Range(min=5, max=60),
        load_default=15 # Changed from missing
    )
    use_preferences = fields.Boolean(load_default=True) # Changed from missing
    paper_ids = fields.List(fields.String(), load_default=[]) # Changed from missing

podcast_create_schema = PodcastCreateSchema()

@podcasts_bp.route('', methods=['POST'])
@jwt_required()
def create_podcast():
    """Create a new podcast generation task."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response(404, "User not found")
        
        # Validate request data
        try:
            data = podcast_create_schema.load(request.json or {}) # Ensure empty dict if no json
        except ValidationError as err:
            return error_response(400, err.messages)
        
        # Validate user has preferences if use_preferences is True
        if data['use_preferences']:
            if not user.preferences:
                return error_response(400, "No research preferences found. Please set them first.")
            # ADDED THIS NEW CHECK:
            if not (user.preferences.topics or \
                    user.preferences.categories or \
                    user.preferences.authors):
                return error_response(400, "User preferences are empty (no topics, categories, or authors defined). Please set them first.")
        elif not data['paper_ids']: # If not using preferences, paper_ids must be provided
             return error_response(400, "If not using preferences, paper_ids must be provided.")


        # Create podcast record
        podcast = Podcast(
            user_id=user.id,
            title=data['title'] or f"Podcast {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            technical_level=data['technical_level'],
            target_length=data['target_length'],
            status=Podcast.STATUS_PENDING
        )
        db.session.add(podcast)
        db.session.commit()
        
        # Create generation task
        task_id = str(uuid.uuid4())
        task = GenerationTask(
            user_id=user.id,
            podcast_id=podcast.id,
            task_id=task_id,
            task_type=GenerationTask.TYPE_SCRIPT_GENERATION,
            status=GenerationTask.STATUS_QUEUED # Initially queued
        )
        db.session.add(task)
        db.session.commit()
        
        # Queue the task
        celery_task_object = generate_podcast_script.delay(
            task_id=task_id,
            podcast_id=podcast.id,
            use_preferences=data['use_preferences'],
            paper_ids=data['paper_ids']
        )
        
        # Update task with celery task id
        # Re-fetch the task to ensure it's the committed one, especially with eager tasks
        # that might have already modified it.
        db.session.refresh(task) # Refresh the task object from the DB
        task.metadata = {'celery_task_id': celery_task_object.id}
        if current_app.config.get("CELERY_TASK_ALWAYS_EAGER"):
            # If tasks are eager, the script task might have already completed.
            # Reflect its potentially updated status from the DB.
            db.session.refresh(task) 
        db.session.commit()
        
        return jsonify({
            'podcast_id': podcast.id,
            'task_id': task_id,
            'status': task.status, # This will be the status after eager execution if applicable
            'created_at': task.created_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error creating podcast: {str(e)}", exc_info=True)
        db.session.rollback()
        return error_response(500, "Failed to create podcast")

@podcasts_bp.route('/<int:podcast_id>', methods=['GET'])
@jwt_required()
def get_podcast(podcast_id):
    """Get podcast details."""
    try:
        user_id = get_jwt_identity()
        
        podcast = Podcast.query.filter_by(id=podcast_id, user_id=user_id).first()
        if not podcast:
            return error_response(404, "Podcast not found")
        
        return jsonify(podcast.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error retrieving podcast {podcast_id}: {str(e)}")
        return error_response(500, "Failed to retrieve podcast")

@podcasts_bp.route('', methods=['GET'])
@jwt_required()
def list_podcasts():
    """List user's podcasts."""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Build query
        query = Podcast.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        pagination = query.order_by(Podcast.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        return jsonify({
            'podcasts': [podcast.to_dict() for podcast in pagination.items],
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        })
    except Exception as e:
        current_app.logger.error(f"Error listing podcasts: {str(e)}")
        return error_response(500, "Failed to list podcasts")

@podcasts_bp.route('/<int:podcast_id>/audio', methods=['GET'])
@jwt_required()
def get_podcast_audio(podcast_id):
    """Stream or download podcast audio."""
    try:
        user_id = get_jwt_identity()
        
        podcast = Podcast.query.filter_by(id=podcast_id, user_id=user_id).first()
        if not podcast or not podcast.audio:
            return error_response(404, "Podcast audio not found")
        
        stream = request.args.get('stream', False, type=bool)
        
        storage_service = StorageService()
        file_path = storage_service.download_audio(podcast.audio.file_url)
        
        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=not stream,
            download_name=f"{podcast.title}.mp3"
        )
    except Exception as e:
        current_app.logger.error(f"Error retrieving audio: {str(e)}", exc_info=True)
        return error_response(500, "Failed to retrieve audio")

@podcasts_bp.route('/<int:podcast_id>/regenerate-audio', methods=['POST'])
@jwt_required()
def regenerate_audio(podcast_id):
    """Regenerate audio for a podcast."""
    try:
        user_id = get_jwt_identity()
        
        podcast = Podcast.query.filter_by(id=podcast_id, user_id=user_id).first()
        if not podcast:
            return error_response(404, "Podcast not found")
        
        if not podcast.script:
            return error_response(400, "No script found for this podcast. Cannot regenerate audio.")
        
        podcast.status = Podcast.STATUS_PROCESSING # Update status before task
        db.session.commit()

        task_id = str(uuid.uuid4())
        task = GenerationTask(
            user_id=user_id,
            podcast_id=podcast.id,
            task_id=task_id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION,
            status=GenerationTask.STATUS_QUEUED
        )
        db.session.add(task)
        db.session.commit()
        
        celery_task_object = generate_podcast_audio.delay(
            task_id=task_id,
            podcast_id=podcast_id
        )
        
        db.session.refresh(task)
        task.metadata = {'celery_task_id': celery_task_object.id}
        if current_app.config.get("CELERY_TASK_ALWAYS_EAGER"):
             db.session.refresh(task) # audio task also runs eagerly
        db.session.commit()
        
        return jsonify({
            'task_id': task_id,
            'status': task.status,
            'created_at': task.created_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error regenerating audio: {str(e)}", exc_info=True)
        db.session.rollback()
        # Attempt to set podcast status back to failed if it was processing
        if podcast and podcast.status == Podcast.STATUS_PROCESSING:
            podcast.status = Podcast.STATUS_FAILED
            podcast.error_message = "Audio regeneration failed."
            db.session.commit()
        return error_response(500, "Failed to regenerate audio")