# app/api/health.py

from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from datetime import datetime
import redis
from google.cloud import storage

from .. import db
from .errors import error_response

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Check database connection
        try:
            db.session.execute(text('SELECT 1'))
            health_status['services']['database'] = {
                'status': 'connected',
                'type': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').split('://')[0]
            }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['services']['database'] = {
                'status': 'disconnected',
                'error': str(e)
            }
        
        # Check Redis connection
        try:
            redis_url = current_app.config.get('CELERY_BROKER_URL')
            if redis_url:
                r = redis.Redis.from_url(redis_url)
                r.ping()
                health_status['services']['redis'] = {
                    'status': 'connected'
                }
            else:
                health_status['services']['redis'] = {
                    'status': 'not_configured'
                }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['services']['redis'] = {
                'status': 'disconnected',
                'error': str(e)
            }
        
        # Check Google Cloud Storage
        try:
            storage_client = storage.Client()
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                bucket = storage_client.bucket(bucket_name)
                bucket.exists()
                health_status['services']['storage'] = {
                    'status': 'connected',
                    'bucket': bucket_name
                }
            else:
                health_status['services']['storage'] = {
                    'status': 'not_configured'
                }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['services']['storage'] = {
                'status': 'disconnected',
                'error': str(e)
            }
        
        # Check Celery worker status
        try:
            from .. import celery
            
            # Inspect worker stats
            inspect = celery.control.inspect()
            stats = inspect.stats()
            
            if stats:
                health_status['services']['celery'] = {
                    'status': 'running',
                    'workers': len(stats)
                }
            else:
                health_status['status'] = 'degraded'
                health_status['services']['celery'] = {
                    'status': 'no_workers'
                }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['services']['celery'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return jsonify(health_status)
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {str(e)}")
        return error_response(500, "Health check failed")

@health_bp.route('/liveness', methods=['GET'])
def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    })

@health_bp.route('/readiness', methods=['GET'])
def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception:
        return error_response(503, "Service not ready")