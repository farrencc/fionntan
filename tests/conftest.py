# tests/conftest.py

import sys
import os
import pytest
import uuid
from datetime import datetime, timezone # Import timezone for UTC awareness

# Add the project root directory (parent of 'tests') to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import app and db instance AFTER potentially modifying sys.path
from app import create_app, db as flask_db_instance, celery as celery_app
from app.models import User, UserPreference, Podcast, GenerationTask, PodcastScript, PodcastAudio
from flask_jwt_extended import create_access_token, create_refresh_token

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    app_instance = create_app('testing') # Your app factory from app/__init__.py
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.environ.get('TEST_DATABASE_URL', "sqlite:///:memory:"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-super-secret-key-for-testing", # Consistent secret for tests
        "SERVER_NAME": "localhost.test", # Helps with url_for in tests if needed
        
        # Celery configuration for testing:
        "CELERY_TASK_ALWAYS_EAGER": True,  # Tasks execute locally, synchronously
        "CELERY_TASK_EAGER_PROPAGATES": True, # Exceptions in eager tasks are re-raised
        "CELERY_BROKER_URL": "memory://",       # Use in-memory broker
        "CELERY_RESULT_BACKEND": "cache+memory://", # Use in-memory result backend
        "BROKER_URL": "memory://", # For older celery versions/compatibility

        # Flask-Limiter configuration for testing:
        "RATELIMIT_STORAGE_URL": "memory://", # Use in-memory for tests
        "RATELIMIT_ENABLED": False, # Often good to disable rate limiting for tests
                                    # unless specifically testing limiter behavior.
        "SESSION_COOKIE_SECURE": False, # Allow session cookies over HTTP for testing
        "DEBUG": False, # Usually False for testing to catch errors as they'd appear in prod
    }
    app_instance.config.update(test_config)

    # Directly update the Celery app instance's config
    # This is important because Celery might have already been configured
    # when the app was created by create_app.
    celery_app.conf.update(
        broker_url=app_instance.config['CELERY_BROKER_URL'],
        result_backend=app_instance.config['CELERY_RESULT_BACKEND'],
        task_always_eager=app_instance.config['CELERY_TASK_ALWAYS_EAGER'],
        task_eager_propagates=app_instance.config['CELERY_TASK_EAGER_PROPAGATES']
    )
    
    return app_instance

@pytest.fixture(scope='function')
def db(app):
    """
    Set up database tables for each test function using the app context.
    Yields the SQLAlchemy extension instance.
    """
    with app.app_context():
        flask_db_instance.create_all()
        yield flask_db_instance # Provide the db extension instance
        flask_db_instance.session.remove() # Clean up the session
        flask_db_instance.drop_all()

@pytest.fixture(scope='function')
def db_session(app, db): # db fixture ensures tables are created and app context is active
    """
    Provides a SQLAlchemy session scoped to a test function, managing a transaction.
    """
    with app.app_context(): # Ensure app context is active for session creation
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Use the session factory from the SQLAlchemy instance, bound to the connection
        session = db.Session(bind=connection)

        yield session

        session.close() # Important to close the session
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def test_user(db, db_session): # Uses function-scoped db & db_session
    """Create and save a test user for each test. Ensures user_id is populated."""
    # Create user with a unique google_id for each invocation
    unique_google_id = f"test-google-id-{uuid.uuid4()}"
    user = User(
        email=f'{unique_google_id}@example.com', # Ensure email is also unique
        name='Test User',
        google_id=unique_google_id,
        last_login=datetime.now(timezone.utc) # Use timezone-aware UTC
    )
    
    # Create and associate preferences
    user_preferences = UserPreference(
        topics=['machine learning'],
        categories=['cs.AI'],
        authors=['Test Author'],
        max_results=10,
        days_back=30,
        sort_by='relevance'
    )
    user.preferences = user_preferences

    db_session.add(user)
    db_session.commit() # Commit to populate user.id and persist user/preferences
    
    # Re-fetch to ensure the instance is bound to the current session and all attributes are loaded
    return db_session.get(User, user.id) 

@pytest.fixture
def auth_headers(app, test_user): # test_user now guarantees an ID
    """Create authentication headers for the test_user."""
    with app.app_context():
        if test_user is None or test_user.id is None:
             pytest.fail("test_user fixture did not provide a committed user with an ID.")
        access_token = create_access_token(identity=test_user.id)
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def refresh_auth_headers(app, test_user): # New fixture for refresh tokens
    with app.app_context():
        if test_user is None or test_user.id is None:
            pytest.fail("test_user fixture did not provide a committed user with an ID.")
        refresh_token = create_refresh_token(identity=test_user.id)
    return {'Authorization': f'Bearer {refresh_token}'}


# --- Mock Service Fixtures ---
@pytest.fixture
def mock_arxiv_service(monkeypatch):
    class MockArxivService:
        def search_papers(self, topics=None, categories=None, authors=None, max_results=10, page=1, days_back=30, sort_by_preference="relevance"):
            return ([{'id': 'test-paper-1', 'title': 'Test Paper', 'authors': ['Test Author'],'abstract': 'Test abstract', 'categories': ['cs.AI'], 'published': '2024-01-01','updated': '2024-01-01', 'url': 'http://example.com/test-paper-1','comment': 'A test comment', 'primary_category': 'cs.AI'}], 1)
        def get_paper_by_id(self, paper_id): return {'id': paper_id, 'title': 'Mock Paper by ID', 'authors': ['Test Author'],'abstract': 'Test abstract by ID', 'categories': ['cs.AI'], 'published': '2024-01-01','updated': '2024-01-01', 'url': f'http://example.com/{paper_id}','comment': 'A test comment by ID', 'primary_category': 'cs.AI'}
    
    # Patch where ArxivService is imported by the modules using it
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules.get('app.tasks.podcast_tasks'), 'ArxivService'):
        monkeypatch.setattr('app.tasks.podcast_tasks.ArxivService', MockArxivService)
    if 'app.api.arxiv' in sys.modules and hasattr(sys.modules.get('app.api.arxiv'), 'ArxivService'):
        monkeypatch.setattr('app.api.arxiv.ArxivService', MockArxivService)
    monkeypatch.setattr('app.services.arxiv_service.ArxivService', MockArxivService, raising=False) 
    return MockArxivService()

@pytest.fixture
def mock_gemini_service(monkeypatch):
    class MockGeminiService:
        def __init__(self, *args, **kwargs): pass # Mock __init__
        def generate_script(self, papers, technical_level, target_length, episode_title=None):
            return {'title': episode_title or 'Mock Script from Gemini', 'sections': [{'title': 'INTRODUCTION', 'segments': [{'speaker': 'alex', 'text': 'Mock intro from Gemini'}]}]}
    
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules.get('app.tasks.podcast_tasks'), 'GeminiService'):
        monkeypatch.setattr('app.tasks.podcast_tasks.GeminiService', MockGeminiService)
    monkeypatch.setattr('app.services.gemini_service.GeminiService', MockGeminiService, raising=False)
    return MockGeminiService()

@pytest.fixture
def mock_tts_service(monkeypatch):
    class MockTTSService:
        def __init__(self, *args, **kwargs): pass # Mock __init__
        def generate_audio(self, script_content, voice_preference='mixed'): return b'mock tts audio'
        def get_audio_duration(self, audio_data): return 180
    
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules.get('app.tasks.podcast_tasks'), 'TTSService'):
        monkeypatch.setattr('app.tasks.podcast_tasks.TTSService', MockTTSService)
    monkeypatch.setattr('app.services.tts_service.TTSService', MockTTSService, raising=False)
    return MockTTSService()

@pytest.fixture
def mock_storage_service(monkeypatch):
    class MockStorageService:
        def __init__(self, *args, **kwargs): pass # Mock __init__
        def upload_audio(self, audio_data, filename): return f'https://fake.storage.com/{filename}'
        def download_audio(self, file_url): return '/tmp/fakedownload.mp3'
        
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules.get('app.tasks.podcast_tasks'), 'StorageService'):
        monkeypatch.setattr('app.tasks.podcast_tasks.StorageService', MockStorageService)
    monkeypatch.setattr('app.services.storage_service.StorageService', MockStorageService, raising=False)
    return MockStorageService()