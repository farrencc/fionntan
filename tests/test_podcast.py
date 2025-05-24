# tests/test_podcast.py

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from app.models import Podcast, PodcastScript, PodcastAudio, GenerationTask, UserPreference, User
from app import db as flask_db # Import the main db instance from your app

class TestPodcastAPI:
    """Test podcast API endpoints."""

    def test_create_podcast(self, client, auth_headers, test_user,
                            mock_arxiv_service, mock_gemini_service, mock_tts_service, mock_storage_service):
        """Test creating a new podcast."""
        assert test_user.preferences is not None
        assert test_user.preferences.topics == ['machine learning']

        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast API Create',
                'technical_level': 'intermediate',
                'target_length': 15,
                'use_preferences': True
            }
        )
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error') if data else 'No JSON response'}"
        assert 'podcast_id' in data
        assert 'task_id' in data
        assert data['status'] == GenerationTask.STATUS_COMPLETED

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
        """
        Test the full end-to-end podcast creation workflow using mocked external services.
        """
        # --- 1. Setup: Ensure User Preferences are Set for the Test ---
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

        # --- 2. Action: Make the API Call to Create a Podcast ---
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

        # --- 3. Verification: Initial API Response ---
        assert api_response.status_code == 200, \
            f"API call to create podcast failed: {api_data.get('message', 'Unknown error') if api_data else 'No JSON response'}"
        assert 'podcast_id' in api_data, "Response missing 'podcast_id'"
        assert 'task_id' in api_data, "Response missing 'task_id'"

        podcast_id = api_data['podcast_id']
        initial_script_task_id_str = api_data['task_id']
        assert api_data['status'] == GenerationTask.STATUS_COMPLETED, \
            f"Initial script task status in API response was {api_data['status']}, expected {GenerationTask.STATUS_COMPLETED}"

        # --- 4. Verification: Database State After Eager Celery Task Execution ---
        current_db_session = flask_db.session

        podcast_obj = current_db_session.get(Podcast, podcast_id)
        assert podcast_obj is not None, f"Podcast with ID {podcast_id} not found in DB."
        assert podcast_obj.status == Podcast.STATUS_COMPLETED, \
            f"Final Podcast status is '{podcast_obj.status}', expected '{Podcast.STATUS_COMPLETED}'. Error: {podcast_obj.error_message or 'None'}"

        script_obj = current_db_session.query(PodcastScript).filter_by(podcast_id=podcast_id).first()
        assert script_obj is not None, "PodcastScript not created for the podcast."
        assert 'title' in script_obj.script_content, "Generated script content missing 'title'."
        assert 'sections' in script_obj.script_content, "Generated script content missing 'sections'."
        assert len(script_obj.paper_ids) > 0, "PodcastScript should have associated paper_ids."
        assert script_obj.paper_ids[0] == 'test-paper-1', "Paper ID in script does not match mock."

        audio_obj = current_db_session.query(PodcastAudio).filter_by(podcast_id=podcast_id).first()
        assert audio_obj is not None, "PodcastAudio not created for the podcast."
        assert audio_obj.file_url == 'https://fake.storage.com/podcast_e2e_test.mp3', "Audio file URL mismatch."
        assert audio_obj.duration == 180, "Audio duration mismatch."

        script_gen_task = current_db_session.query(GenerationTask).filter_by(task_id=initial_script_task_id_str).first()
        assert script_gen_task is not None, f"Script generation task with ID {initial_script_task_id_str} not found."
        assert script_gen_task.task_type == GenerationTask.TYPE_SCRIPT_GENERATION
        assert script_gen_task.status == GenerationTask.STATUS_COMPLETED, "Script generation task did not complete."
        assert script_gen_task.progress == 100, "Script generation task progress is not 100."

        audio_gen_task = current_db_session.query(GenerationTask).filter_by(
            podcast_id=podcast_id,
            task_type=GenerationTask.TYPE_AUDIO_GENERATION
        ).first()
        assert audio_gen_task is not None, "Audio generation task record not created."
        assert audio_gen_task.status == GenerationTask.STATUS_COMPLETED, "Audio generation task did not complete."
        assert audio_gen_task.progress == 100, "Audio generation task progress is not 100."

        # --- 5. Verification: Mock Service Calls ---
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
        # Correctly access .args for positional and .kwargs for keyword
        storage_call_args_tuple = mock_storage_service.upload_audio.call_args.args
        storage_call_kwargs_dict = mock_storage_service.upload_audio.call_args.kwargs
        
        assert len(storage_call_args_tuple) == 1, "Expected 1 positional argument for upload_audio"
        assert isinstance(storage_call_args_tuple[0], bytes) # The audio_data
        assert 'filename' in storage_call_kwargs_dict, "filename keyword argument missing"
        assert storage_call_kwargs_dict['filename'].startswith(f"podcast_{podcast_id}_")


class TestAuthAPI:
    """Test authentication endpoints."""

    def test_login_redirect(self, client):
        """Test OAuth login redirect."""
        response = client.get('/api/v1/auth/login')
        assert response.status_code == 302
        assert 'accounts.google.com' in response.location

    def test_refresh_token_with_refresh_token(self, client, refresh_auth_headers):
        """Test JWT token refresh with a refresh token."""
        response = client.post('/api/v1/auth/refresh', headers=refresh_auth_headers)
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error')}"
        assert 'access_token' in data

    def test_refresh_token_with_access_token_fails(self, client, auth_headers):
        """Test JWT token refresh fails with an access token."""
        response = client.post('/api/v1/auth/refresh', headers=auth_headers)
        assert response.status_code == 422


class TestArxivAPI:
    """Test ArXiv API endpoints."""

    def test_search_papers(self, client, auth_headers, mock_arxiv_service):
        """Test searching ArXiv papers."""
        query_params = [
            ('topics', 'machine learning'),
            ('topics', 'AI'),
            ('categories', 'cs.AI'),
            ('max_results', '5')
        ]
        response = client.get('/api/v1/arxiv/search', headers=auth_headers, query_string=query_params)
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error') if data else 'No JSON response'}"
        assert 'papers' in data
        assert len(data['papers']) == 1
        assert data['papers'][0]['id'] == 'test-paper-1'

    def test_get_categories(self, client, auth_headers):
        """Test getting ArXiv categories."""
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
        """
        Tests if the generate_podcast_script Celery task correctly uses the
        user's sort_by preference when fetching papers from ArxivService.
        """
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

        with patch('app.tasks.podcast_tasks.generate_podcast_audio.delay') as mock_generate_audio_delay_in_test:
            mock_celery_async_result_in_test = MagicMock()
            mock_celery_async_result_in_test.id = str(uuid.uuid4())
            mock_generate_audio_delay_in_test.return_value = mock_celery_async_result_in_test

            result = generate_podcast_script.apply_async(
                args=[script_task_id_str, podcast.id],
                kwargs={'use_preferences':True, 'paper_ids':None}
            )

            assert result.successful(), f"Celery task 'generate_podcast_script' failed: {result.info}"

            mock_arxiv_service.search_papers.assert_called_once()
            called_kwargs = mock_arxiv_service.search_papers.call_args.kwargs

            assert called_kwargs.get('topics') == ["cosmology", "dark matter"]
            assert called_kwargs.get('sort_by_preference') == "lastUpdatedDate"

            db_session.expire_all()
            updated_script_task = db_session.get(GenerationTask, script_task_record.id)
            assert updated_script_task.status == GenerationTask.STATUS_COMPLETED

            audio_task_record = db_session.query(GenerationTask).filter_by(
                podcast_id=podcast.id,
                task_type=GenerationTask.TYPE_AUDIO_GENERATION
            ).first()
            assert audio_task_record is not None
            mock_generate_audio_delay_in_test.assert_called_once()