# tests/conftest.py

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch # Ensure MagicMock and patch are imported
import sys
import os

# Add the project root directory (parent of 'tests') to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import app and db instance AFTER potentially modifying sys.path
from app import create_app, db as flask_db_instance, celery as celery_app
from app.models import User, UserPreference, Podcast, GenerationTask, PodcastScript, PodcastAudio
from flask_jwt_extended import create_access_token, create_refresh_token
# Import actual service classes for spec if desired (optional, but good practice)
# from app.services.arxiv_service import ArxivService
# from app.services.gemini_service import GeminiService
# from app.services.tts_service import TTSService
# from app.services.storage_service import StorageService


# --- App and DB Fixtures (Keep as they are) ---
@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    app_instance = create_app('testing')
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": os.environ.get('TEST_DATABASE_URL', "sqlite:///:memory:"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-super-secret-key-for-testing",
        "SERVER_NAME": "localhost.test",
        "CELERY_TASK_ALWAYS_EAGER": True,
        "CELERY_TASK_EAGER_PROPAGATES": True,
        "CELERY_BROKER_URL": "memory://",
        "CELERY_RESULT_BACKEND": "cache+memory://",
        "BROKER_URL": "memory://",
        "RATELIMIT_STORAGE_URL": "memory://",
        "RATELIMIT_ENABLED": False,
        "SESSION_COOKIE_SECURE": False,
        "DEBUG": False,
    }
    app_instance.config.update(test_config)
    celery_app.conf.update(
        broker_url=app_instance.config['CELERY_BROKER_URL'],
        result_backend=app_instance.config['CELERY_RESULT_BACKEND'],
        task_always_eager=app_instance.config['CELERY_TASK_ALWAYS_EAGER'],
        task_eager_propagates=app_instance.config['CELERY_TASK_EAGER_PROPAGATES']
    )
    return app_instance

@pytest.fixture(scope='function')
def db(app):
    """Set up database tables for each test function using the app context."""
    with app.app_context():
        flask_db_instance.create_all()
        yield flask_db_instance
        flask_db_instance.session.remove()
        flask_db_instance.drop_all()

@pytest.fixture(scope='function')
def db_session(app, db):
    """Provides a SQLAlchemy session scoped to a test function, managing a transaction."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db.Session(bind=connection)
        yield session
        session.close()
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
def test_user(db, db_session):
    """Create and save a test user for each test. Ensures user_id is populated."""
    unique_google_id = f"test-google-id-{uuid.uuid4()}"
    user = User(
        email=f'{unique_google_id}@example.com',
        name='Test User',
        google_id=unique_google_id,
        last_login=datetime.now(timezone.utc)
    )
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
    db_session.commit()
    return db_session.get(User, user.id)

@pytest.fixture
def auth_headers(app, test_user):
    """Create authentication headers for the test_user."""
    with app.app_context():
        if test_user is None or test_user.id is None:
             pytest.fail("test_user fixture did not provide a committed user with an ID.")
        access_token = create_access_token(identity=test_user.id)
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def refresh_auth_headers(app, test_user):
    with app.app_context():
        if test_user is None or test_user.id is None:
            pytest.fail("test_user fixture did not provide a committed user with an ID.")
        refresh_token = create_refresh_token(identity=test_user.id)
    return {'Authorization': f'Bearer {refresh_token}'}


# --- Corrected Mock Service Fixtures ---
@pytest.fixture
def mock_arxiv_service(monkeypatch):
    mock_instance = MagicMock() # Use spec=ArxivService if ArxivService is imported
    
    # Configure the 'search_papers' method
    mock_search_return = ([{
        'id': 'test-paper-1', 'title': 'Test Paper from Mock', 
        'authors': ['Mock Author'], 'abstract': 'Mock abstract content.',
        'categories': ['cs.AI'], 'published': '2024-01-01',
        'updated': '2024-01-01', 'url': 'http://example.com/test-paper-1',
        'comment': 'A mock comment', 'primary_category': 'cs.AI'
    }], 1) # Returns 1 paper, total_count 1
    mock_instance.search_papers = MagicMock(return_value=mock_search_return)

    # Configure the 'get_paper_by_id' method
    mock_instance.get_paper_by_id = MagicMock(return_value={
        'id': 'test-paper-id-get', 'title': 'Specific Mock Paper by ID', 
        'authors': ['Mock Author Get'], 'abstract': 'Abstract for specific mock paper.',
        'categories': ['cs.LG'], 'published': '2024-01-02', 
        'updated': '2024-01-02', 'url': 'http://example.com/test-paper-id-get',
        'comment': 'Comment for specific paper get', 'primary_category': 'cs.LG'
    })

    def mock_constructor(*args, **kwargs):
        return mock_instance

    # Primary patch: Patch the ArxivService class in the module where it's defined.
    # This is usually the most effective way.
    monkeypatch.setattr('app.services.arxiv_service.ArxivService', mock_constructor)
    
    # Also patch it where it might be directly imported in specific modules under test, if necessary.
    # This handles cases where modules might have `from app.services import ArxivService` and use it.
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'ArxivService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'ArxivService', mock_constructor)
    if 'app.api.arxiv' in sys.modules and hasattr(sys.modules['app.api.arxiv'], 'ArxivService'):
        monkeypatch.setattr(sys.modules['app.api.arxiv'], 'ArxivService', mock_constructor)
        
    return mock_instance

@pytest.fixture
def mock_gemini_service(monkeypatch):
    mock_instance = MagicMock() # Use spec=GeminiService if GeminiService is imported
    mock_instance.generate_script = MagicMock(return_value={
        'title': 'Mock Script from E2E Gemini', 
        'sections': [{'title': 'E2E_INTRODUCTION', 'segments': [{'speaker': 'alex', 'text': 'E2E Mock intro from Gemini'}]}]
    })
    
    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.gemini_service.GeminiService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'GeminiService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'GeminiService', mock_constructor)
         
    return mock_instance

@pytest.fixture
def mock_tts_service(monkeypatch):
    mock_instance = MagicMock() # Use spec=TTSService if TTSService is imported
    mock_instance.generate_audio = MagicMock(return_value=b'mock e2e tts audio data')
    mock_instance.get_audio_duration = MagicMock(return_value=180)

    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.tts_service.TTSService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'TTSService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'TTSService', mock_constructor)
        
    return mock_instance

@pytest.fixture
def mock_storage_service(monkeypatch):
    mock_instance = MagicMock() # Use spec=StorageService if StorageService is imported
    mock_instance.upload_audio = MagicMock(return_value='https://fake.storage.com/podcast_e2e_test.mp3')
    mock_instance.download_audio = MagicMock(return_value='/tmp/mock_e2e_downloaded_audio.mp3')

    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.storage_service.StorageService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'StorageService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'StorageService', mock_constructor)
        
    return mock_instance