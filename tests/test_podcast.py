# tests/test_podcast.py

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from app.models import Podcast, PodcastScript, PodcastAudio, GenerationTask, UserPreference, User
from app import db as flask_db # Import the main db instance from your app
from datetime import datetime, timezone


class TestPodcastAPI:
    """Test podcast API endpoints."""

    def test_create_podcast_with_user_preferences(self, client, auth_headers, test_user, db_session,
                                                  mock_arxiv_service, mock_gemini_service,
                                                  mock_tts_service, mock_storage_service):
        """Test creating a new podcast using user preferences."""
        assert test_user.preferences is not None
        assert test_user.preferences.topics == ['machine learning']
        test_user.preferences.sort_by = "relevance"
        db_session.commit()


        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast API Create via Prefs',
                'technical_level': 'intermediate',
                'target_length': 15,
                'use_preferences': True
            }
        )
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error') if data else 'No JSON response'}"
        assert 'podcast_id' in data
        assert 'task_id' in data
        # With Celery eager mode and tasks not re-raising exceptions that halt the API response:
        # The initial task status from API might be QUEUED or PROCESSING if not fully propagated.
        # The final status check will be in the DB.
        # For this specific test where everything is mocked to succeed, eager execution should complete all.
        assert data['status'] == GenerationTask.STATUS_COMPLETED

        mock_arxiv_service.search_papers.assert_called_once()
        called_kwargs = mock_arxiv_service.search_papers.call_args.kwargs
        assert called_kwargs.get('topics') == test_user.preferences.topics
        assert called_kwargs.get('categories') == test_user.preferences.categories
        assert called_kwargs.get('authors') == test_user.preferences.authors
        assert called_kwargs.get('sort_by_preference') == test_user.preferences.sort_by


    def test_create_podcast_with_specific_paper_ids(self, client, auth_headers, test_user, db_session,
                                                    mock_arxiv_service, mock_gemini_service,
                                                    mock_tts_service, mock_storage_service):
        """Test creating a new podcast using specific paper_ids."""
        paper_ids_to_use = ["paper_id_A", "paper_id_B"]

        def side_effect_get_paper_by_id(paper_id, _retry_count=0):
            if paper_id == "paper_id_A":
                return {'id': 'paper_id_A', 'title': 'Paper A Title', 'abstract': 'Abstract A', 'authors': ['Author A']}
            if paper_id == "paper_id_B":
                return {'id': 'paper_id_B', 'title': 'Paper B Title', 'abstract': 'Abstract B', 'authors': ['Author B']}
            return None
        mock_arxiv_service.get_paper_by_id_side_effect = side_effect_get_paper_by_id
        mock_arxiv_service.get_paper_by_id.side_effect = side_effect_get_paper_by_id


        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast API Create via PaperIDs',
                'technical_level': 'beginner',
                'target_length': 10,
                'use_preferences': False,
                'paper_ids': paper_ids_to_use
            }
        )
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error') if data else 'No JSON response'}"
        assert 'podcast_id' in data
        podcast_id = data['podcast_id']

        assert mock_arxiv_service.get_paper_by_id.call_count == len(paper_ids_to_use)
        mock_arxiv_service.get_paper_by_id.assert_any_call("paper_id_A")
        mock_arxiv_service.get_paper_by_id.assert_any_call("paper_id_B")

        mock_gemini_service.generate_script.assert_called_once()
        gemini_call_kwargs = mock_gemini_service.generate_script.call_args.kwargs
        assert len(gemini_call_kwargs.get('papers')) == len(paper_ids_to_use)
        assert gemini_call_kwargs.get('papers')[0]['id'] == 'paper_id_A'
        assert gemini_call_kwargs.get('papers')[1]['id'] == 'paper_id_B'

        podcast_obj = db_session.get(Podcast, podcast_id)
        assert podcast_obj is not None
        assert podcast_obj.status == Podcast.STATUS_COMPLETED
        assert podcast_obj.script is not None
        assert sorted(podcast_obj.script.paper_ids) == sorted(paper_ids_to_use)


    def test_create_podcast_audio_generation_fails(self, client, auth_headers, test_user, db_session,
                                                  mock_arxiv_service, mock_gemini_service,
                                                  mock_tts_service, mock_storage_service):
        """Test podcast creation when (mocked) audio generation fails."""
        mock_tts_service.generate_audio_side_effect = Exception("Mock TTS Failure")

        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast Audio Failure',
                'use_preferences': True
            }
        )
        data = response.get_json()
        # After modifying tasks to not re-raise, API should return 200 for task submission
        assert response.status_code == 200
        podcast_id = data['podcast_id']
        initial_script_task_id = data['task_id']


        db_session.expire_all()
        podcast_obj = db_session.get(Podcast, podcast_id)
        assert podcast_obj is not None
        assert podcast_obj.status == Podcast.STATUS_FAILED
        assert "Mock TTS Failure" in podcast_obj.error_message # Or a more specific message from the task

        script_task = db_session.query(GenerationTask).filter_by(task_id=initial_script_task_id).one()
        assert script_task.status == GenerationTask.STATUS_COMPLETED

        audio_task = db_session.query(GenerationTask).filter_by(podcast_id=podcast_id, task_type=GenerationTask.TYPE_AUDIO_GENERATION).one_or_none()
        assert audio_task is not None
        assert audio_task.status == GenerationTask.STATUS_FAILED
        assert "Mock TTS Failure" in audio_task.error_message


    def test_create_podcast_invalid_input_empty_paper_ids(self, client, auth_headers):
        """Test podcast creation with use_preferences: False and empty paper_ids."""
        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Empty Paper IDs',
                'use_preferences': False,
                'paper_ids': []
            }
        )
        data = response.get_json()
        assert response.status_code == 400
        assert "paper_ids must be provided" in data.get("message", "").lower()

    def test_create_podcast_script_generation_fails(self, client, auth_headers, test_user, db_session,
                                                  mock_arxiv_service, mock_gemini_service,
                                                  mock_tts_service, mock_storage_service):
        """Test podcast creation when (mocked) script generation fails."""
        mock_gemini_service.generate_script_side_effect = Exception("Mock Gemini Script Failure")

        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast Script Failure',
                'use_preferences': True
            }
        )
        data = response.get_json()
        # API should return 200 after task modification
        assert response.status_code == 200
        podcast_id = data['podcast_id']
        initial_script_task_id = data['task_id']


        db_session.expire_all()
        podcast_obj = db_session.get(Podcast, podcast_id)
        assert podcast_obj is not None
        assert podcast_obj.status == Podcast.STATUS_FAILED
        assert "Mock Gemini Script Failure" in podcast_obj.error_message

        script_task = db_session.query(GenerationTask).filter_by(task_id=initial_script_task_id).one()
        assert script_task.status == GenerationTask.STATUS_FAILED
        assert "Mock Gemini Script Failure" in script_task.error_message

        audio_task = db_session.query(GenerationTask).filter_by(podcast_id=podcast_id, task_type=GenerationTask.TYPE_AUDIO_GENERATION).first()
        assert audio_task is None # Audio task should not be created if script gen fails early
        mock_tts_service.generate_audio.assert_not_called()


    def test_get_podcast(self, client, auth_headers, test_user, db_session):
        """Test retrieving a podcast."""
        podcast = Podcast(
            user_id=test_user.id, title='Test Podcast for Get',
            status='completed', technical_level='intermediate'
        )
        db_session.add(podcast)
        db_session.commit()
        response = client.get(f'/api/v1/podcasts/{podcast.id}', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Test Podcast for Get'

    def test_list_podcasts(self, client, auth_headers, test_user, db_session):
        """Test listing user podcasts."""
        for i in range(3):
            db_session.add(Podcast(user_id=test_user.id, title=f'List Podcast {i}', status='completed'))
        db_session.commit()
        response = client.get('/api/v1/podcasts', headers=auth_headers, query_string={'page': 1, 'limit': 10})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['podcasts']) == 3
        assert data['total'] == 3

    def test_create_podcast_without_user_preferences_topics(self, client, auth_headers, test_user, db_session,
                                                             mock_arxiv_service, mock_gemini_service, mock_tts_service, mock_storage_service):
        """Test creating podcast with use_preferences=True when user has no preference topics."""
        if test_user.preferences:
            test_user.preferences.topics = []
            test_user.preferences.categories = []
            test_user.preferences.authors = []
            db_session.commit()
            db_session.refresh(test_user.preferences)
            current_user_prefs = db_session.get(UserPreference, test_user.preferences.id)
            assert not current_user_prefs.topics

        response = client.post(
            '/api/v1/podcasts', headers=auth_headers,
            json={
                'title': 'Test No Prefs Topics Podcast',
                'technical_level': 'beginner',
                'target_length': 10,
                'use_preferences': True
            }
        )
        data = response.get_json()
        assert response.status_code == 400, f"API Error: {data.get('message', 'Expected 400 if preferences are effectively empty')}. Check API validation."
        assert "preferences are empty" in data.get("message", "").lower() or \
               "no research preferences found" in data.get("message", "").lower() or \
               "topics must be provided" in data.get("message", "").lower()

    def test_e2e_podcast_creation_workflow_with_mocks(
        self, client, auth_headers, test_user, db_session,
        mock_arxiv_service, mock_gemini_service,
        mock_tts_service, mock_storage_service
    ):
        if not test_user.preferences:
            pref = UserPreference(user_id=test_user.id, topics=['E2E mock service test'])
            db_session.add(pref)
            test_user.preferences = pref
        else:
            test_user.preferences.topics = ['E2E mock service test topic']
            test_user.preferences.categories = ['cs.LG']
            test_user.preferences.authors = []
            test_user.preferences.max_results = 2
            test_user.preferences.days_back = 10
            test_user.preferences.sort_by = "relevance"
        db_session.commit()
        db_session.refresh(test_user)
        if test_user.preferences:
            db_session.refresh(test_user.preferences)


        api_response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'E2E Workflow Test Podcast Title',
                'technical_level': 'intermediate',
                'target_length': 7,
                'use_preferences': True
            }
        )
        api_data = api_response.get_json()

        assert api_response.status_code == 200
        assert 'podcast_id' in api_data
        assert 'task_id' in api_data

        podcast_id = api_data['podcast_id']
        initial_script_task_id_str = api_data['task_id']
        assert api_data['status'] == GenerationTask.STATUS_COMPLETED


        current_db_session = flask_db.session

        podcast_obj = current_db_session.get(Podcast, podcast_id)
        assert podcast_obj is not None
        assert podcast_obj.status == Podcast.STATUS_COMPLETED

        script_obj = current_db_session.query(PodcastScript).filter_by(podcast_id=podcast_id).first()
        assert script_obj is not None
        assert 'title' in script_obj.script_content
        assert 'sections' in script_obj.script_content
        assert len(script_obj.paper_ids) > 0
        assert script_obj.paper_ids[0] == 'test-paper-1'

        audio_obj = current_db_session.query(PodcastAudio).filter_by(podcast_id=podcast_id).first()
        assert audio_obj is not None
        assert audio_obj.file_url == 'https://fake.storage.com/podcast_e2e_test.mp3'
        assert audio_obj.duration == 180

        script_gen_task = current_db_session.query(GenerationTask).filter_by(task_id=initial_script_task_id_str).first()
        assert script_gen_task is not None
        assert script_gen_task.task_type == GenerationTask.TYPE_SCRIPT_GENERATION
        assert script_gen_task.status == GenerationTask.STATUS_COMPLETED
        assert script_gen_task.progress == 100

        audio_gen_task = current_db_session.query(GenerationTask).filter_by(
            podcast_id=podcast_id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION
        ).first()
        assert audio_gen_task is not None
        assert audio_gen_task.status == GenerationTask.STATUS_COMPLETED
        assert audio_gen_task.progress == 100

        mock_arxiv_service.search_papers.assert_called_once()
        arxiv_call_kwargs = mock_arxiv_service.search_papers.call_args.kwargs
        assert arxiv_call_kwargs.get('topics') == ['E2E mock service test topic']
        assert arxiv_call_kwargs.get('categories') == ['cs.LG']
        assert arxiv_call_kwargs.get('sort_by_preference') == "relevance"

        mock_gemini_service.generate_script.assert_called_once()
        gemini_call_kwargs = mock_gemini_service.generate_script.call_args.kwargs
        assert len(gemini_call_kwargs.get('papers')) == 1
        assert gemini_call_kwargs.get('papers')[0]['id'] == 'test-paper-1'
        assert gemini_call_kwargs.get('technical_level') == 'intermediate'
        assert gemini_call_kwargs.get('target_length') == 7

        mock_tts_service.generate_audio.assert_called_once()
        tts_call_kwargs = mock_tts_service.generate_audio.call_args.kwargs
        assert 'title' in tts_call_kwargs.get('script_content')
        assert tts_call_kwargs.get('voice_preference') == 'mixed'

        mock_storage_service.upload_audio.assert_called_once()
        storage_call_args_tuple = mock_storage_service.upload_audio.call_args.args
        storage_call_kwargs_dict = mock_storage_service.upload_audio.call_args.kwargs

        assert len(storage_call_args_tuple) == 1
        assert isinstance(storage_call_args_tuple[0], bytes)
        assert 'filename' in storage_call_kwargs_dict
        assert storage_call_kwargs_dict['filename'].startswith(f"podcast_{podcast_id}_")


class TestAuthAPI:
    """Test authentication endpoints."""

    def test_login_redirect(self, client):
        response = client.get('/api/v1/auth/login')
        assert response.status_code == 302
        assert 'accounts.google.com' in response.location

    def test_refresh_token_with_refresh_token(self, client, refresh_auth_headers):
        response = client.post('/api/v1/auth/refresh', headers=refresh_auth_headers)
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error')}"
        assert 'access_token' in data

    def test_refresh_token_with_access_token_fails(self, client, auth_headers):
        response = client.post('/api/v1/auth/refresh', headers=auth_headers)
        assert response.status_code == 422


class TestArxivAPI:
    """Test ArXiv API endpoints."""

    def test_search_papers(self, client, auth_headers, mock_arxiv_service):
        query_params = [
            ('topics', 'machine learning'),
            ('topics', 'AI'),
            ('categories', 'cs.AI'),
            ('max_results', '5')
        ]
        response = client.get('/api/v1/arxiv/search', headers=auth_headers, query_string=query_params)
        data = response.get_json()
        assert response.status_code == 200
        assert 'papers' in data
        assert len(data['papers']) == 1
        assert data['papers'][0]['id'] == 'test-paper-1'

    def test_get_categories(self, client, auth_headers):
        response = client.get('/api/v1/arxiv/categories', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'categories' in data
        assert any(cat['id'] == 'cs.AI' for cat in data['categories'])

class TestPodcastTasks:
    def test_generate_script_task_uses_user_sort_preference(
        self, app, test_user, db_session,
        mock_arxiv_service, mock_gemini_service,
        mock_tts_service, mock_storage_service
    ):
        if not test_user.preferences:
            test_user.preferences = UserPreference(user_id=test_user.id)
            db_session.add(test_user.preferences)

        test_user.preferences.topics = ["cosmology", "dark matter"]
        test_user.preferences.categories = ["astro-ph.CO"]
        test_user.preferences.authors = ["Some Author"]
        test_user.preferences.max_results = 10
        test_user.preferences.days_back = 90
        test_user.preferences.sort_by = "lastUpdatedDate"
        db_session.commit()

        podcast = Podcast(
            user_id=test_user.id, title="Cosmology Sort Test Task",
            technical_level="intermediate", target_length=15, status=Podcast.STATUS_PENDING
        )
        db_session.add(podcast)
        db_session.commit()

        script_task_id_str = str(uuid.uuid4())
        script_task_record = GenerationTask(
            user_id=test_user.id, podcast_id=podcast.id, task_id=script_task_id_str,
            task_type=GenerationTask.TYPE_SCRIPT_GENERATION, status=GenerationTask.STATUS_QUEUED
        )
        db_session.add(script_task_record)
        db_session.commit()

        from app.tasks.podcast_tasks import generate_podcast_script

        with app.app_context():
            with patch('app.tasks.podcast_tasks.generate_podcast_audio.delay') as mock_generate_audio_delay_in_test:
                mock_celery_async_result_in_test = MagicMock()
                mock_celery_async_result_in_test.id = str(uuid.uuid4())
                mock_generate_audio_delay_in_test.return_value = mock_celery_async_result_in_test

                result = generate_podcast_script.apply_async(
                    args=[script_task_id_str, podcast.id],
                    kwargs={'use_preferences': True, 'paper_ids': None}
                )


        assert result.successful(), f"Celery task 'generate_podcast_script' failed: {result.info}"

        mock_arxiv_service.search_papers.assert_called_once()
        called_kwargs = mock_arxiv_service.search_papers.call_args.kwargs

        assert called_kwargs.get('topics') == ["cosmology", "dark matter"]
        assert called_kwargs.get('categories') == ["astro-ph.CO"]
        assert called_kwargs.get('authors') == ["Some Author"]
        assert called_kwargs.get('sort_by_preference') == "lastUpdatedDate"

        db_session.expire_all()
        updated_script_task = db_session.get(GenerationTask, script_task_record.id)
        assert updated_script_task.status == GenerationTask.STATUS_COMPLETED

        audio_task_record = db_session.query(GenerationTask).filter_by(
            podcast_id=podcast.id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION
        ).first()
        assert audio_task_record is not None
        # Since generate_podcast_audio.delay is mocked, the audio task will remain in its initial QUEUED state.
        # It won't proceed to COMPLETED unless the mock itself simulates that behavior.
        assert audio_task_record.status == GenerationTask.STATUS_QUEUED
        mock_generate_audio_delay_in_test.assert_called_once()