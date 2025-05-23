# tests/test_podcast.py

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from app.models import Podcast, GenerationTask, UserPreference, User 

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
        assert data['status'] == GenerationTask.STATUS_QUEUED 
    
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
            db_session.refresh(test_user.preferences) # Ensure changes are loaded
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
        # This test's expectation (400 vs 200 then task failure) depends on your API logic
        # in app/api/podcasts.py. If it doesn't validate that preferences.topics is non-empty
        # when use_preferences is True, it will queue the task, which will then fail.
        # For a 400, the API must perform this check.
        # Example API check:
        # if data.get('use_preferences'):
        #     if not user.preferences:
        #         return error_response(400, "User preferences not set.")
        #     if not (user.preferences.topics or user.preferences.categories or user.preferences.authors):
        #         return error_response(400, "User preferences are empty (no topics, categories, or authors defined).")
        assert response.status_code == 400, f"API Error: {data.get('message', 'Expected 400 if preferences are effectively empty')}. Check API validation."
        assert "preferences are empty" in data.get("message", "").lower() or \
               "no research preferences found" in data.get("message", "").lower() or \
               "topics must be provided" in data.get("message", "").lower()


class TestAuthAPI:
    """Test authentication endpoints."""
    
    def test_login_redirect(self, client):
        """Test OAuth login redirect."""
        response = client.get('/api/v1/auth/login')
        assert response.status_code == 302
        assert 'accounts.google.com' in response.location
    
    def test_refresh_token_with_refresh_token(self, client, refresh_auth_headers): # Uses new fixture
        """Test JWT token refresh with a refresh token."""
        response = client.post('/api/v1/auth/refresh', headers=refresh_auth_headers)
        data = response.get_json()
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error')}"
        assert 'access_token' in data

    def test_refresh_token_with_access_token_fails(self, client, auth_headers):
        """Test JWT token refresh fails with an access token."""
        response = client.post('/api/v1/auth/refresh', headers=auth_headers) # Sends ACCESS token
        assert response.status_code == 422 # flask-jwt-extended: "Only refresh tokens are allowed"

class TestArxivAPI:
    """Test ArXiv API endpoints."""
    
    def test_search_papers(self, client, auth_headers, mock_arxiv_service):
        """Test searching ArXiv papers."""
        query_params = [
            ('topics', 'machine learning'),
            ('topics', 'AI'),
            ('categories', 'cs.AI'),
            ('max_results', '5') # Values in query_string are typically strings
        ]
        response = client.get('/api/v1/arxiv/search', headers=auth_headers, query_string=query_params)
        data = response.get_json()
        # If this fails with 500 and "Not a valid list", the issue is in app/api/arxiv.py schema loading
        assert response.status_code == 200, f"API Error: {data.get('message', 'Unknown error')}"
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
    # Removed @pytest.mark.usefixtures("app_context")
    def test_generate_script_task_uses_user_sort_preference(
        self, app, test_user, db_session, # client fixture removed, app fixture added
        mock_arxiv_service, mock_gemini_service, 
        mock_tts_service, mock_storage_service # Ensure all mocks used by the task chain are here
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
        
        # Use a local patch for ArxivService to precisely inspect the instance used by the task
        with patch('app.tasks.podcast_tasks.ArxivService') as MockArxivServiceCls_in_test:
            mock_arxiv_instance_in_test = MockArxivServiceCls_in_test.return_value
            mock_arxiv_paper = {
                'id': '2301.00001v1', 'title': 'Mock Paper', 'authors': ['A. Uthor'], 
                'abstract': 'text', 'pdf_url': '', 'categories': [], 
                'published': '2024-01-01', 'updated': '2024-01-01', 
                'url': '', 'comment': '', 'primary_category': ''
            } # Completed mock_arxiv_paper
            mock_arxiv_instance_in_test.search_papers.return_value = ([mock_arxiv_paper], 1)

            with patch('app.tasks.podcast_tasks.generate_podcast_audio.delay') as mock_generate_audio_delay_in_test:
                mock_celery_async_result_in_test = MagicMock()
                mock_celery_async_result_in_test.id = str(uuid.uuid4())
                mock_generate_audio_delay_in_test.return_value = mock_celery_async_result_in_test
                
                # Call task using apply_async for eager execution
                result = generate_podcast_script.apply_async(
                    args=[script_task_id_str, podcast.id],
                    kwargs={'use_preferences':True, 'paper_ids':None}
                )
                
                assert result.successful(), f"Celery task 'generate_podcast_script' failed: {result.info}"

                mock_arxiv_instance_in_test.search_papers.assert_called_once()
                called_kwargs = mock_arxiv_instance_in_test.search_papers.call_args.kwargs
                
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
                assert audio_task_record.status == GenerationTask.STATUS_QUEUED
                mock_generate_audio_delay_in_test.assert_called_once()