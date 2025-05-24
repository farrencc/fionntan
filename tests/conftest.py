# tests/conftest.py

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import sys
import os
import urllib.error # Added for HTTPError instantiation

# Add the project root directory (parent of 'tests') to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import app and db instance AFTER potentially modifying sys.path
from app import create_app, db as flask_db_instance, celery as celery_app
from app.models import User, UserPreference, Podcast, GenerationTask, PodcastScript, PodcastAudio
from flask_jwt_extended import create_access_token, create_refresh_token

# --- App and DB Fixtures ---
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
        "CELERY_BROKER_URL": "memory://", # Use in-memory broker for tests
        "CELERY_RESULT_BACKEND": "cache+memory://", # Use in-memory backend for tests
        "BROKER_URL": "memory://", # Also for Flask app config if used directly
        "RATELIMIT_STORAGE_URL": "memory://",
        "RATELIMIT_ENABLED": False,
        "SESSION_COOKIE_SECURE": False,
        "DEBUG": False, # Usually False for testing to mimic production more closely
        "PROPAGATE_EXCEPTIONS": True, # Helps in debugging test failures
    }
    app_instance.config.update(test_config)

    # Ensure Celery app is configured with test settings
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
        # Use a session that is bound to this connection and transaction
        session = db.Session(bind=connection)
        yield session
        session.close()
        transaction.rollback() # Ensure tests are isolated
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
def test_user(db, db_session): # Changed scope to function for better isolation
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
    db_session.commit() # Commit to get an ID
    # It's crucial that the user object returned has its ID populated.
    # db_session.refresh(user) # Ensure all attributes are up-to-date from DB
    return db_session.get(User, user.id) # Return the user attached to the current session


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


# --- Mock Service Fixtures with Failure Simulation Capability ---

@pytest.fixture
def mock_arxiv_service(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.search_papers_return_value = ([{
        'id': 'test-paper-1', 'title': 'Test Paper from Mock',
        'authors': ['Mock Author'], 'abstract': 'Mock abstract content.',
        'categories': ['cs.AI'], 'published': '2024-01-01',
        'updated': '2024-01-01', 'url': 'http://example.com/test-paper-1',
        'comment': 'A mock comment', 'primary_category': 'cs.AI'
    }], 1)
    mock_instance.get_paper_by_id_return_value = {
        'id': 'test-paper-id-get', 'title': 'Specific Mock Paper by ID',
        'authors': ['Mock Author Get'], 'abstract': 'Abstract for specific mock paper.',
        'categories': ['cs.LG'], 'published': '2024-01-02',
        'updated': '2024-01-02', 'url': 'http://example.com/test-paper-id-get',
        'comment': 'Comment for specific paper get', 'primary_category': 'cs.LG'
    }
    mock_instance.search_papers_side_effect = None
    mock_instance.get_paper_by_id_side_effect = None

    def mock_search_papers(*args, **kwargs):
        if mock_instance.search_papers_side_effect:
            effect = mock_instance.search_papers_side_effect
            if callable(effect): # If it's a function, call it
                 return effect(*args, **kwargs)
            raise effect # Otherwise, raise it (it's an exception instance)
        return mock_instance.search_papers_return_value

    def mock_get_paper_by_id(*args, **kwargs):
        if mock_instance.get_paper_by_id_side_effect:
            effect = mock_instance.get_paper_by_id_side_effect
            if callable(effect):
                return effect(*args, **kwargs)
            raise effect
        # Simulate not found if a specific ID is requested to fail
        if hasattr(mock_instance, 'fail_on_paper_id') and args[0] == mock_instance.fail_on_paper_id:
            return None
        return mock_instance.get_paper_by_id_return_value

    mock_instance.search_papers = MagicMock(side_effect=mock_search_papers)
    mock_instance.get_paper_by_id = MagicMock(side_effect=mock_get_paper_by_id)


    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.arxiv_service.ArxivService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'ArxivService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'ArxivService', mock_constructor)
    if 'app.api.arxiv' in sys.modules and hasattr(sys.modules['app.api.arxiv'], 'ArxivService'):
        monkeypatch.setattr(sys.modules['app.api.arxiv'], 'ArxivService', mock_constructor)

    return mock_instance

@pytest.fixture
def mock_gemini_service(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.generate_script_return_value = {
        'title': 'Mock Script from E2E Gemini',
        'sections': [{'title': 'E2E_INTRODUCTION', 'segments': [{'speaker': 'alex', 'text': 'E2E Mock intro from Gemini'}]}]
    }
    mock_instance.generate_script_side_effect = None

    def mock_generate_script(*args, **kwargs):
        if mock_instance.generate_script_side_effect:
            effect = mock_instance.generate_script_side_effect
            if callable(effect):
                return effect(*args, **kwargs)
            raise effect
        return mock_instance.generate_script_return_value

    mock_instance.generate_script = MagicMock(side_effect=mock_generate_script)

    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.gemini_service.GeminiService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'GeminiService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'GeminiService', mock_constructor)

    return mock_instance

@pytest.fixture
def mock_tts_service(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.generate_audio_return_value = b'mock e2e tts audio data'
    mock_instance.get_audio_duration_return_value = 180
    mock_instance.generate_audio_side_effect = None # To allow simulating errors

    def mock_generate_audio(*args, **kwargs):
        if mock_instance.generate_audio_side_effect:
            effect = mock_instance.generate_audio_side_effect
            if callable(effect): # If it's a function, call it
                 return effect(*args, **kwargs)
            raise effect # Otherwise, raise it (it's an exception instance)
        return mock_instance.generate_audio_return_value

    mock_instance.generate_audio = MagicMock(side_effect=mock_generate_audio)
    mock_instance.get_audio_duration = MagicMock(return_value=mock_instance.get_audio_duration_return_value)


    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.tts_service.TTSService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'TTSService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'TTSService', mock_constructor)

    return mock_instance

@pytest.fixture
def mock_storage_service(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.upload_audio_return_value = 'https://fake.storage.com/podcast_e2e_test.mp3'
    mock_instance.download_audio_return_value = '/tmp/mock_e2e_downloaded_audio.mp3'
    mock_instance.upload_audio_side_effect = None # To allow simulating errors


    def mock_upload_audio(*args, **kwargs):
        if mock_instance.upload_audio_side_effect:
            effect = mock_instance.upload_audio_side_effect
            if callable(effect):
                 return effect(*args, **kwargs)
            raise effect
        return mock_instance.upload_audio_return_value

    mock_instance.upload_audio = MagicMock(side_effect=mock_upload_audio)
    mock_instance.download_audio = MagicMock(return_value=mock_instance.download_audio_return_value)


    def mock_constructor(*args, **kwargs):
        return mock_instance

    monkeypatch.setattr('app.services.storage_service.StorageService', mock_constructor)
    if 'app.tasks.podcast_tasks' in sys.modules and hasattr(sys.modules['app.tasks.podcast_tasks'], 'StorageService'):
        monkeypatch.setattr(sys.modules['app.tasks.podcast_tasks'], 'StorageService', mock_constructor)

    return mock_instance