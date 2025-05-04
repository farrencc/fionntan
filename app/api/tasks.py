# app/api/tasks.py

from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import GenerationTask
from ..api.errors import error_response
from .. import celery

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Get task status and details."""
    try:
        user_id = get_jwt_identity()
        
        task = GenerationTask.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not task:
            return error_response(404, "Task not found")
        
        # Check Celery task status if task is still processing
        if task.status in [GenerationTask.STATUS_QUEUED, GenerationTask.STATUS_PROCESSING]:
            if task.metadata and 'celery_task_id' in task.metadata:
                celery_task = celery.AsyncResult(task.metadata['celery_task_id'])
                
                # Update task status based on Celery status
                if celery_task.state == 'PENDING':
                    task.status = GenerationTask.STATUS_QUEUED
                elif celery_task.state == 'STARTED':
                    task.status = GenerationTask.STATUS_PROCESSING
                elif celery_task.state == 'SUCCESS':
                    task.status = GenerationTask.STATUS_COMPLETED
                elif celery_task.state == 'FAILURE':
                    task.status = GenerationTask.STATUS_FAILED
                    task.error_message = str(celery_task.result)
                
                # Update progress if available
                if hasattr(celery_task, 'info') and isinstance(celery_task.info, dict):
                    task.progress = celery_task.info.get('progress', task.progress)
        
        return jsonify(task.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error retrieving task {task_id}: {str(e)}")
        return error_response(500, "Failed to retrieve task")

@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """Cancel a running task."""
    try:
        user_id = get_jwt_identity()
        
        task = GenerationTask.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not task:
            return error_response(404, "Task not found")
        
        # Can only cancel queued or processing tasks
        if task.status not in [GenerationTask.STATUS_QUEUED, GenerationTask.STATUS_PROCESSING]:
            return error_response(400, "Task cannot be cancelled")
        
        # Cancel Celery task
        if task.metadata and 'celery_task_id' in task.metadata:
            celery_task = celery.AsyncResult(task.metadata['celery_task_id'])
            celery_task.revoke(terminate=True)
        
        # Update task status
        task.status = GenerationTask.STATUS_CANCELLED
        task.completed_at = datetime.utcnow()
        
        # Update associated podcast status
        if task.podcast:
            task.podcast.status = 'cancelled'
            task.podcast.error_message = "Task cancelled by user"
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task cancelled successfully',
            'task_id': task_id
        })
    except Exception as e:
        current_app.logger.error(f"Error cancelling task {task_id}: {str(e)}")
        db.session.rollback()
        return error_response(500, "Failed to cancel task")