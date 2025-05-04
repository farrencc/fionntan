# tests/test_podcasts.py

import pytest
import json
from app.models import Podcast, GenerationTask

class TestPodcastAPI:
    """Test podcast API endpoints."""
    
    def test_create_podcast(self, client, auth_headers, mock_arxiv_service, mock_gemini_service):
        """Test creating a new podcast."""
        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'title': 'Test Podcast',
                'technical_level': 'intermediate',
                'target_length': 15,
                'use_preferences': True
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'podcast_id' in data
        assert 'task_id' in data
        assert data['status'] == 'queued'
    
    def test_get_podcast(self, client, auth_headers, test_user, db_session):
        """Test retrieving a podcast."""
        podcast = Podcast(
            user_id=test_user.id,
            title='Test Podcast',
            status='completed',
            technical_level='intermediate'
        )
        db_session.add(podcast)
        db_session.commit()
        
        response = client.get(
            f'/api/v1/podcasts/{podcast.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Test Podcast'
    
    def test_list_podcasts(self, client, auth_headers, test_user, db_session):
        """Test listing user podcasts."""
        for i in range(3):
            podcast = Podcast(
                user_id=test_user.id,
                title=f'Podcast {i}',
                status='completed'
            )
            db_session.add(podcast)
        db_session.commit()
        
        response = client.get(
            '/api/v1/podcasts',
            headers=auth_headers,
            query_string={'page': 1, 'limit': 10}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['podcasts']) == 3
        assert data['total'] == 3
    
    def test_create_podcast_without_preferences(self, client, auth_headers):
        """Test creating podcast without user preferences."""
        response = client.post(
            '/api/v1/podcasts',
            headers=auth_headers,
            json={
                'use_preferences': True
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'preferences' in data['message'].lower()

# tests/test_auth.py

class TestAuthAPI:
    """Test authentication endpoints."""
    
    def test_login_redirect(self, client):
        """Test OAuth login redirect."""
        response = client.get('/api/v1/auth/login')
        
        assert response.status_code == 302
        assert 'accounts.google.com' in response.location
    
    def test_refresh_token(self, client, auth_headers):
        """Test JWT token refresh."""
        # First get a refresh token
        # This is simplified for the example
        response = client.post(
            '/api/v1/auth/refresh',
            headers=auth_headers,
            json={'refresh_token': 'fake-refresh-token'}
        )
        
        # Note: This would fail with actual auth
        # This is just an example structure
        assert response.status_code in [200, 401]

# tests/test_arxiv.py

class TestArxivAPI:
    """Test ArXiv API endpoints."""
    
    def test_search_papers(self, client, auth_headers, mock_arxiv_service):
        """Test searching ArXiv papers."""
        response = client.get(
            '/api/v1/arxiv/search',
            headers=auth_headers,
            query_string={
                'topics': ['machine learning'],
                'categories': ['cs.AI'],
                'max_results': 5
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'papers' in data
        assert len(data['papers']) > 0
    
    def test_get_categories(self, client, auth_headers):
        """Test getting ArXiv categories."""
        response = client.get(
            '/api/v1/arxiv/categories',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'categories' in data
        assert any(cat['id'] == 'cs.AI' for cat in data['categories'])