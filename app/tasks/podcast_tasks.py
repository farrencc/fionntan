# app/tasks/podcast_tasks.py

from datetime import datetime
import logging
import uuid

from .. import celery, db
from ..models import User, Podcast, PodcastScript, PodcastAudio, GenerationTask
from ..services.arxiv_service import ArxivService
from ..services.gemini_service import GeminiService
from ..services.tts_service import TTSService
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def generate_podcast_script(self, task_id, podcast_id, use_preferences=True, paper_ids=None):
    """Task to generate podcast script."""
    try:
        # Update task status
        task = GenerationTask.query.filter_by(task_id=task_id).first()
        if not task:
            raise Exception("Task not found")
        
        task.status = GenerationTask.STATUS_PROCESSING
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # Get podcast and user
        podcast = Podcast.query.get(podcast_id)
        user = User.query.get(task.user_id)
        
        if not podcast or not user:
            raise Exception("Podcast or user not found")
        
        # Update podcast status
        podcast.status = Podcast.STATUS_PROCESSING
        db.session.commit()
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 10})
        
        # Get papers from ArXiv
        arxiv_service = ArxivService()
        
        if use_preferences and user.preferences:
            papers = arxiv_service.search_papers(
                topics=user.preferences.topics,
                categories=user.preferences.categories,
                authors=user.preferences.authors,
                max_results=min(user.preferences.max_results, 5),
                days_back=user.preferences.days_back
            )
        elif paper_ids:
            papers = []
            for paper_id in paper_ids:
                paper = arxiv_service.get_paper_by_id(paper_id)
                if paper:
                    papers.append(paper)
        else:
            raise Exception("No papers to generate script from")
        
        if not papers:
            raise Exception("No papers found")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 30})
        
        # Generate script using Gemini
        gemini_service = GeminiService()
        script_content = gemini_service.generate_script(
            papers=papers,
            technical_level=podcast.technical_level,
            target_length=podcast.target_length,
            episode_title=podcast.title
        )
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 70})
        
        # Save script to database
        script = PodcastScript(
            podcast_id=podcast.id,
            script_content=script_content,
            paper_ids=[paper['id'] for paper in papers]
        )
        db.session.add(script)
        
        # Update podcast status
        podcast.status = Podcast.STATUS_COMPLETED
        podcast.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Update task status
        task.status = GenerationTask.STATUS_COMPLETED
        task.completed_at = datetime.utcnow()
        task.progress = 100
        db.session.commit()
        
        # Queue audio generation task
        audio_task_id = str(uuid.uuid4())
        audio_task = GenerationTask(
            user_id=user.id,
            podcast_id=podcast.id,
            task_id=audio_task_id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION,
            status=GenerationTask.STATUS_QUEUED
        )
        db.session.add(audio_task)
        db.session.commit()
        
        # Start audio generation
        celery_task = generate_podcast_audio.delay(
            task_id=audio_task_id,
            podcast_id=podcast_id
        )
        
        audio_task.metadata = {'celery_task_id': celery_task.id}
        db.session.commit()
        
        return {'status': 'completed', 'progress': 100}
        
    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        
        # Update task status
        if task:
            task.status = GenerationTask.STATUS_FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.session.commit()
        
        # Update podcast status
        if podcast:
            podcast.status = Podcast.STATUS_FAILED
            podcast.error_message = str(e)
            db.session.commit()
        
        raise

@celery.task(bind=True)
def generate_podcast_audio(self, task_id, podcast_id):
    """Task to generate podcast audio."""
    try:
        # Update task status
        task = GenerationTask.query.filter_by(task_id=task_id).first()
        if not task:
            raise Exception("Task not found")
        
        task.status = GenerationTask.STATUS_PROCESSING
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # Get podcast and script
        podcast = Podcast.query.get(podcast_id)
        if not podcast or not podcast.script:
            raise Exception("Podcast or script not found")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 10})
        
        # Generate audio using TTS
        tts_service = TTSService()
        audio_file = tts_service.generate_audio(
            script_content=podcast.script.script_content,
            voice_preference='mixed'  # Could be made configurable per user
        )
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 60})
        
        # Upload audio to storage
        storage_service = StorageService()
        file_url = storage_service.upload_audio(
            audio_file,
            filename=f"podcast_{podcast_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp3"
        )
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 80})
        
        # Get audio file info
        file_size = len(audio_file)
        duration = tts_service.get_audio_duration(audio_file)
        
        # Save audio info to database
        audio = PodcastAudio(
            podcast_id=podcast.id,
            file_url=file_url,
            file_size=file_size,
            duration=duration,
            audio_format='mp3'
        )
        db.session.add(audio)
        
        # Update task status
        task.status = GenerationTask.STATUS_COMPLETED
        task.completed_at = datetime.utcnow()
        task.progress = 100
        db.session.commit()
        
        return {'status': 'completed', 'progress': 100}
        
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        
        # Update task status
        if task:
            task.status = GenerationTask.STATUS_FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.session.commit()
        
        raise