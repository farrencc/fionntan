# app/tasks/podcast_tasks.py

from datetime import datetime, timezone # Added timezone
import logging
import uuid

from flask import current_app # Import current_app for config access

from .. import celery, db
from ..models import User, Podcast, PodcastScript, PodcastAudio, GenerationTask
from ..services.arxiv_service import ArxivService
from ..services.gemini_service import GeminiService
from ..services.tts_service import TTSService
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def generate_podcast_script(self, task_id, podcast_id, use_preferences=True, paper_ids=None):
    task = None
    podcast_obj = None
    try:
        task = GenerationTask.query.filter_by(task_id=task_id).first()
        if not task:
            raise Exception(f"Script generation task not found: {task_id}")

        task.status = GenerationTask.STATUS_PROCESSING
        task.started_at = datetime.now(timezone.utc) # Use timezone-aware UTC
        db.session.commit()

        podcast_obj = Podcast.query.get(podcast_id)
        user = User.query.get(task.user_id)

        if not podcast_obj or not user:
            raise Exception("Podcast or user not found for script generation.")

        podcast_obj.status = Podcast.STATUS_PROCESSING
        db.session.commit()

        if hasattr(self, 'update_state'): # Check if self is a Celery task instance
            self.update_state(state='PROGRESS', meta={'progress': 10})

        arxiv_service = ArxivService()
        fetched_papers_data = None

        if use_preferences and user.preferences:
            fetched_papers_data = arxiv_service.search_papers(
                topics=user.preferences.topics,
                categories=user.preferences.categories,
                authors=user.preferences.authors,
                max_results=min(user.preferences.max_results, 5),
                days_back=user.preferences.days_back,
                sort_by_preference=user.preferences.sort_by
            )
        elif paper_ids:
           temp_papers_list = []
           for paper_id_val in paper_ids:
                paper = arxiv_service.get_paper_by_id(paper_id_val)
                if paper:
                    temp_papers_list.append(paper)

        # elif paper_ids:
        #     temp_papers_list = []
        #     for paper_id_val in paper_ids:
        #     # TEMPORARY MOCK DATA FOR POC TESTING
        #         mock_paper = {
        #         'id': paper_id_val,
        #         'title': f'Advances in Machine Learning: {paper_id_val}',
        #         'abstract': f'This paper presents novel approaches to machine learning and artificial intelligence. We introduce new methods for {paper_id_val} that achieve state-of-the-art performance on benchmark datasets. Our approach demonstrates significant improvements in both accuracy and computational efficiency compared to existing methods.',
        #         'authors': ['Dr. Sarah Chen', 'Prof. Michael Rodriguez'],
        #         'categories': ['cs.AI', 'cs.LG'],
        #         'published': '2024-01-15',
        #         'updated': '2024-01-20',
        #         'url': f'https://arxiv.org/abs/{paper_id_val}',
        #         'comment': 'Submitted to ICML 2024',
        #         'primary_category': 'cs.AI'
        #         }
        #         temp_papers_list.append(mock_paper)
                if temp_papers_list:
                    fetched_papers_data = (temp_papers_list, len(temp_papers_list))
        else:
            raise Exception("No paper source defined: use_preferences or paper_ids required.")

        papers = fetched_papers_data[0] if fetched_papers_data and fetched_papers_data[0] else []

        if not papers:
            raise Exception("No papers found based on the provided criteria.")

        if hasattr(self, 'update_state'):
            self.update_state(state='PROGRESS', meta={'progress': 30})

        gemini_service = GeminiService()
        script_content = gemini_service.generate_script(
            papers=papers,
            technical_level=podcast_obj.technical_level,
            target_length=podcast_obj.target_length,
            episode_title=podcast_obj.title
        )

        if hasattr(self, 'update_state'):
            self.update_state(state='PROGRESS', meta={'progress': 70})

        script = PodcastScript(
            podcast_id=podcast_obj.id,
            script_content=script_content,
            paper_ids=[paper['id'] for paper in papers]
        )
        db.session.add(script)

        task.status = GenerationTask.STATUS_COMPLETED
        task.progress = 100
        task.completed_at = datetime.now(timezone.utc) # Use timezone-aware UTC

        audio_task_id = str(uuid.uuid4())
        audio_task_record = GenerationTask(
            user_id=user.id,
            podcast_id=podcast_obj.id,
            task_id=audio_task_id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION,
            status=GenerationTask.STATUS_QUEUED
        )
        db.session.add(audio_task_record)
        db.session.commit()

        celery_audio_task = generate_podcast_audio.delay(
            task_id=audio_task_id,
            podcast_id=podcast_obj.id
        )
        
        committed_audio_task_record = GenerationTask.query.filter_by(task_id=audio_task_id).first()
        if committed_audio_task_record:
            committed_audio_task_record.metadata = {'celery_task_id': celery_audio_task.id}
            db.session.commit()
        else:
            logger.error(f"Failed to find committed audio task record for ID {audio_task_id} to update with Celery ID.")

        return {'status': 'script_completed', 'audio_task_id': audio_task_id, 'progress': 100}

    except Exception as e:
        logger.error(f"Error generating script for podcast_id {podcast_id}: {str(e)}", exc_info=True)
        if task:
            task.status = GenerationTask.STATUS_FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
        if podcast_obj:
            podcast_obj.status = Podcast.STATUS_FAILED
            podcast_obj.error_message = str(e)
        db.session.commit()
        # Do not re-raise if CELERY_TASK_EAGER_PROPAGATES is True,
        # to allow API to return 200 and test failure handling via DB state.
        if not current_app.config.get("CELERY_TASK_EAGER_PROPAGATES", False):
            raise


@celery.task(bind=True)
def generate_podcast_audio(self, task_id, podcast_id):
    task = None
    podcast_obj = None
    try:
        task = GenerationTask.query.filter_by(task_id=task_id).first()
        if not task:
            logger.error(f"Audio generation task record not found in DB for task_id: {task_id}")
            raise Exception(f"Audio generation task not found: {task_id}")

        task.status = GenerationTask.STATUS_PROCESSING
        task.started_at = datetime.now(timezone.utc)
        db.session.commit()

        podcast_obj = Podcast.query.get(podcast_id)
        if not podcast_obj or not podcast_obj.script:
            raise Exception(f"Podcast (ID: {podcast_id}) or its script not found for audio generation.")

        if hasattr(self, 'update_state'):
            self.update_state(state='PROGRESS', meta={'progress': 10})

        tts_service = TTSService()
        audio_file_bytes = tts_service.generate_audio(
            script_content=podcast_obj.script.script_content,
            voice_preference='mixed'
        )

        if hasattr(self, 'update_state'):
            self.update_state(state='PROGRESS', meta={'progress': 60})

        storage_service = StorageService()
        file_url = storage_service.upload_audio(
            audio_file_bytes,
            filename=f"podcast_{podcast_obj.id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.mp3"
        )

        if hasattr(self, 'update_state'):
            self.update_state(state='PROGRESS', meta={'progress': 80})

        file_size = len(audio_file_bytes)
        duration = tts_service.get_audio_duration(audio_file_bytes)

        audio_record = PodcastAudio(
            podcast_id=podcast_obj.id,
            file_url=file_url,
            file_size=file_size,
            duration=duration,
            audio_format='mp3'
        )
        db.session.add(audio_record)

        podcast_obj.status = Podcast.STATUS_COMPLETED
        podcast_obj.completed_at = datetime.now(timezone.utc)
        podcast_obj.error_message = None

        task.status = GenerationTask.STATUS_COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.progress = 100
        db.session.commit()

        return {'status': 'audio_completed', 'file_url': file_url, 'progress': 100}

    except Exception as e:
        logger.error(f"Error generating audio for podcast_id {podcast_id}: {str(e)}", exc_info=True)
        if task:
            task.status = GenerationTask.STATUS_FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
        if podcast_obj:
            podcast_obj.status = Podcast.STATUS_FAILED
            podcast_obj.error_message = f"Audio generation failed: {str(e)}"
        db.session.commit()
        # Do not re-raise if CELERY_TASK_EAGER_PROPAGATES is True
        if not current_app.config.get("CELERY_TASK_EAGER_PROPAGATES", False):
            raise
