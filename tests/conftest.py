# tests/conftest.py

import pytest
import os
from datetime import datetime

from app import create_app, db
from app.models import User, UserPreference

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    return app

@pytest.fixture(scope='session')
def _db(app):
    """Create database for testing."""
    db.create_all()
    yield db
    db.drop_all()

@pytest.fixture(scope='function')
def db_session(_db):
    """Create a database session for testing."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    # Configure session
    session = _db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    
    # Make session available
    _db.session = session
    
    yield session
    
    # Cleanup
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers(client, test_user):
    """Create authentication headers."""
    # Login user
    response = client.post('/api/v1/auth/login', json={
        'email': test_user.email,
        'password': 'password'
    })
    
    data = response.get_json()
    access_token = data['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}'
    }

@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email='test@example.com',
        name='Test User',
        google_id='test-google-id',
        last_login=datetime.utcnow()
    )
    
    # Create preferences
    preferences = UserPreference(
        topics=['machine learning'],
        categories=['cs.AI'],
        authors=['Test Author'],
        max_results=10,
        days_back=30
    )
    
    user.preferences = preferences
    
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def mock_arxiv_service(monkeypatch):
    """Mock ArXiv service."""
    class MockArxivService:
        def search_papers(self, **kwargs):
            return [{
                'id': 'test-paper-1',
                'title': 'Test Paper',
                'authors': ['Test Author'],
                'abstract': 'Test abstract',
                'categories': ['cs.AI'],
                'published': '2024-01-01'
            }], 1
        
        def get_paper_by_id(self, paper_id):
            return {
                'id': paper_id,
                'title': 'Test Paper',
                'authors': ['Test Author'],
                'abstract': 'Test abstract'
            }
    
    monkeypatch.setattr('app.services.arxiv_service.ArxivService', MockArxivService)

@pytest.fixture
def mock_gemini_service(monkeypatch):
    """Mock Gemini service."""
    class MockGeminiService:
        def generate_script(self, **kwargs):
            return {
                'title': 'Test Podcast',
                'sections': [
                    {
                        'title': 'INTRODUCTION',
                        'segments': [
                            {'speaker': 'alex', 'text': 'Welcome to the podcast!'},
                            {'speaker': 'jordan', 'text': 'Thanks for listening!'}
                        ]
                    }
                ]
            }
    
    monkeypatch.setattr('app.services.gemini_service.GeminiService', MockGeminiService)

@pytest.fixture
def mock_tts_service(monkeypatch):
    """Mock TTS service."""
    class MockTTSService:
        def generate_audio(self, **kwargs):
            return b'mock audio content'
        
        def get_audio_duration(self, audio_data):
            return 300  # 5 minutes
    
    monkeypatch.setattr('app.services.tts_service.TTSService', MockTTSService)

@pytest.fixture
def mock_storage_service(monkeypatch):
    """Mock storage service."""
    class MockStorageService:
        def upload_audio(self, audio_data, filename):
            return f'https://storage.googleapis.com/test-bucket/{filename}'
        
        def download_audio(self, file_url):
            return '/tmp/test-audio.mp3'
    
    monkeypatch.setattr('app.services.storage_service.StorageService', MockStorageService)