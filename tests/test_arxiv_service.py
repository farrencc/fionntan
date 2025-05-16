# tests/test_arxiv_service.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import arxiv # Ensure this is here
import urllib.error # Add this

# Adjust the import path based on your project structure
# If ArxivService is in app/services/arxiv_service.py:
from app.services.arxiv_service import ArxivService
# If it's in app/arxiv_scraper.py as ArxivService:
# from app.arxiv_scraper import ArxivService

# If UserPreferences is a dataclass defined in the same file:
# from app.services.arxiv_service import UserPreferences
# Or if it's a model (which is more likely given your models.py)
# you might not need to import it here directly for these specific unit tests
# as we'll be mocking its attributes.

# ... (MockArxivResult and other fixtures) ...

# --- For test_process_paper ---
class MockArxivResult:
    def __init__(self, entry_id_url, title, summary, authors_mocks=None, categories=None, pdf_url=None, published=None, updated=None, comment=None, primary_category=None):
        self.entry_id = entry_id_url
        self.title = title
        self.summary = summary
        if authors_mocks is None:
            author_default_mock = MagicMock()
            author_default_mock.name = "Author Default" # Configure the .name attribute
            self.authors = [author_default_mock]
        else:
            self.authors = authors_mocks # Expect a list of pre-configured mocks
        self.categories = categories or ["cs.AI"]
        self.pdf_url = pdf_url or f"http://arxiv.org/pdf/{entry_id_url.split('/')[-1]}.pdf"
        self.published = published or datetime(2023, 1, 1)
        self.updated = updated or datetime(2023, 1, 2)
        self.comment = comment or "No comments"
        self.primary_category = primary_category or "cs.AI"

    def get_short_id(self):
        # Mimic the behavior of arxiv.Result.get_short_id()
        if '/abs/' in self.entry_id:
            return self.entry_id.split('/abs/')[1]
        return self.entry_id.split('/')[-1]

def test_process_paper():
    service = ArxivService()
    now = datetime.now()

    author1_mock = MagicMock()
    author1_mock.name = "Author One" # Set the .name attribute
    author2_mock = MagicMock()
    author2_mock.name = "Author Two" # Set the .name attribute

    mock_api_result = MockArxivResult(
        entry_id_url="http://arxiv.org/abs/cs/0102003v1",
        title="Test Title",
        summary="This is a test abstract.",
        authors_mocks=[author1_mock, author2_mock], # Pass the list of mocks
        categories=["cs.AI", "cs.LG"],
        pdf_url="http://arxiv.org/pdf/cs/0102003v1.pdf",
        published=now - timedelta(days=5),
        updated=now - timedelta(days=2),
        comment="A test comment.",
        primary_category="cs.AI"
    )

    processed = service._process_paper(mock_api_result)

    assert processed["id"] == "cs/0102003v1" # Assuming your ArxivService uses get_short_id()
    assert processed["title"] == "Test Title"
    assert processed["authors"] == ["Author One", "Author Two"] # This should now pass
    assert processed["abstract"] == "This is a test abstract."
    assert processed["pdf_url"] == "http://arxiv.org/pdf/cs/0102003v1.pdf"
    assert processed["categories"] == ["cs.AI", "cs.LG"]
    assert processed["published"] == (now - timedelta(days=5)).strftime("%Y-%m-%d")
    assert processed["updated"] == (now - timedelta(days=2)).strftime("%Y-%m-%d")
    assert processed["url"] == "http://arxiv.org/abs/cs/0102003v1"
    assert processed["comment"] == "A test comment."
    assert processed["primary_category"] == "cs.AI"

# --- For test_handle_rate_limit ---
@patch('time.sleep')
def test_handle_rate_limit(mock_sleep, mock_arxiv_client):
    service = ArxivService()
    # arxiv.HTTPError is an alias for urllib.error.HTTPError.
    # Constructor: HTTPError(url, code, msg, hdrs, fp)
    http_error_429 = urllib.error.HTTPError('http://example.com/api', 429, 'Rate limit exceeded', {}, None)

    mock_arxiv_client.results.side_effect = [
        http_error_429,
        http_error_429,
        iter([MockArxivResult(entry_id_url="id_test_success", title="t_test", summary="s_test")]),
        iter([MockArxivResult(entry_id_url="id_final", title="t_final", summary="s_final")])
    ]

    papers, total = service.search_papers(topics=["test"])

    assert len(papers) == 1
    assert papers[0]["title"] == "t_final"
    assert mock_sleep.call_count > 0
    assert mock_arxiv_client.results.call_count == 4