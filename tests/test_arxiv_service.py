# tests/test_arxiv_service.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import arxiv # For arxiv.HTTPError if needed by the library's exceptions
import urllib.error # For instantiating HTTPError

# Assuming ArxivService is in app/services/arxiv_service.py
from app.services.arxiv_service import ArxivService
# If your ArxivService class is actually in app/arxiv_scraper.py, change the import:
# from app.arxiv_scraper import ArxivService

# --- Helper Mock Class ---
class MockArxivResult:
    def __init__(self, entry_id_url, title, summary, authors_mocks=None, categories=None, pdf_url=None, published=None, updated=None, comment=None, primary_category=None):
        self.entry_id = entry_id_url # This is the full URL like "http://arxiv.org/abs/2301.00001v1"
        self.title = title
        self.summary = summary
        # Authors should be a list of objects that have a .name attribute
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
            # Handles cases like 'http://arxiv.org/abs/cs/0102003v1' -> 'cs/0102003v1'
            # or 'http://arxiv.org/abs/2301.00001v1' -> '2301.00001v1'
            return self.entry_id.split('/abs/')[1]
        # Fallback for other URL structures, though arxiv.Result typically uses /abs/
        return self.entry_id.split('/')[-1]

# --- Pytest Fixture ---
@pytest.fixture
def mock_arxiv_client():
    """Fixture to mock the arxiv.Client for ArxivService."""
    # The 'arxiv.Client' string tells patch where to find the class to mock.
    # It should match how ArxivService imports and uses it (e.g., from the arxiv module).
    with patch('arxiv.Client') as mock_client_constructor:
        mock_client_instance = MagicMock()
        # Default mock_client_instance.results to return an empty iterator.
        # Individual tests can override this with .return_value or .side_effect.
        mock_client_instance.results.return_value = iter([])
        mock_client_constructor.return_value = mock_client_instance
        yield mock_client_instance

# --- Test Functions ---

def test_arxiv_service_initialization(mock_arxiv_client):
    """Test that ArxivService initializes the arxiv.Client correctly."""
    service = ArxivService()
    # ArxivService.__init__ should call arxiv.Client()
    # The mock_arxiv_client fixture patches arxiv.Client
    # So, service.client should be the instance our mock_client_constructor returned.
    assert service.client is mock_arxiv_client

def test_search_papers_basic(mock_arxiv_client):
    """Test basic paper search functionality."""
    mock_paper_1_id_url = "http://arxiv.org/abs/2301.00001v1"
    mock_paper_2_id_url = "http://arxiv.org/abs/2301.00002v1"
    mock_results_data = [
        MockArxivResult(entry_id_url=mock_paper_1_id_url, title="Test Paper 1", summary="Abstract 1"),
        MockArxivResult(entry_id_url=mock_paper_2_id_url, title="Test Paper 2", summary="Abstract 2"),
    ]
    # Configure the mock client's results method for this specific test
    mock_arxiv_client.results.return_value = iter(mock_results_data)

    service = ArxivService()
    papers, total = service.search_papers(topics=["AI"], max_results=2)

    assert len(papers) == 2
    assert total == 2 # Based on current ArxivService implementation for total
    assert papers[0]["title"] == "Test Paper 1"
    assert papers[0]["id"] == "2301.00001v1" # Assuming ArxivService._process_paper uses get_short_id()
    assert papers[1]["abstract"] == "Abstract 2"
    mock_arxiv_client.results.assert_called_once()

def test_search_papers_query_construction(mock_arxiv_client):
    """Test the query construction logic."""
    service = ArxivService()

    # Test with topics and categories
    # No need to re-patch service.client.results if the default (empty iter) is fine
    # We are interested in the arguments passed to arxiv.Search, which is then passed to client.results
    service.search_papers(topics=["machine learning", "NLP"], categories=["cs.CL"], days_back=7)
    # Get the arxiv.Search object passed to client.results
    # The mock_arxiv_client's 'results' method was called.
    # The first argument to 'results' is the arxiv.Search instance.
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    query = search_instance_arg.query

    assert "(all:machine learning OR all:NLP)" in query
    assert "(cat:cs.CL)" in query
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)
    date_str = seven_days_ago.strftime("%Y%m%d")
    assert f"submittedDate:[{date_str}000000 TO 99991231235959]" in query

    # Reset mock for next call or use a new mock if state matters significantly
    mock_arxiv_client.reset_mock()
    mock_arxiv_client.results.return_value = iter([]) # Ensure it's set for the next call

    # Test with authors
    service.search_papers(authors=["John Doe", "Jane Smith"])
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    query = search_instance_arg.query
    assert '(au:"John Doe" OR au:"Jane Smith")' in query

def test_get_paper_by_id_found(mock_arxiv_client):
    """Test retrieving a paper by its ID when found."""
    paper_id_short_form = "2305.00001v1"
    mock_paper_url = f"http://arxiv.org/abs/{paper_id_short_form}"
    mock_paper = MockArxivResult(entry_id_url=mock_paper_url, title="Specific Paper", summary="Specific abstract.")
    mock_arxiv_client.results.return_value = iter([mock_paper])

    service = ArxivService()
    paper = service.get_paper_by_id(paper_id_short_form)

    assert paper is not None
    assert paper["id"] == paper_id_short_form
    assert paper["title"] == "Specific Paper"
    mock_arxiv_client.results.assert_called_once()
    # Check that the arxiv.Search object was constructed with the id_list
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    assert search_instance_arg.id_list == [paper_id_short_form]

def test_get_paper_by_id_not_found(mock_arxiv_client):
    """Test retrieving a paper by ID when not found."""
    mock_arxiv_client.results.return_value = iter([]) # Simulate no results

    service = ArxivService()
    paper = service.get_paper_by_id("nonexistent.id")

    assert paper is None
    mock_arxiv_client.results.assert_called_once()

def test_process_paper():
    """Test the _process_paper method directly. Assumes ArxivService uses get_short_id()."""
    service = ArxivService()
    now = datetime.now()

    author_mock1 = MagicMock()
    author_mock1.name = "Author One"
    author_mock2 = MagicMock()
    author_mock2.name = "Author Two"

    mock_api_result = MockArxivResult(
        entry_id_url="http://arxiv.org/abs/cs/0102003v1",
        title="Test Title",
        summary="This is a test abstract.",
        authors_mocks=[author_mock1, author_mock2],
        categories=["cs.AI", "cs.LG"],
        pdf_url="http://arxiv.org/pdf/cs/0102003v1.pdf",
        published=now - timedelta(days=5),
        updated=now - timedelta(days=2),
        comment="A test comment.",
        primary_category="cs.AI"
    )

    processed = service._process_paper(mock_api_result)

    assert processed["id"] == "cs/0102003v1"
    assert processed["title"] == "Test Title"
    assert processed["authors"] == ["Author One", "Author Two"]
    assert processed["abstract"] == "This is a test abstract."
    assert processed["pdf_url"] == "http://arxiv.org/pdf/cs/0102003v1.pdf"
    assert processed["categories"] == ["cs.AI", "cs.LG"]
    assert processed["published"] == (now - timedelta(days=5)).strftime("%Y-%m-%d")
    assert processed["updated"] == (now - timedelta(days=2)).strftime("%Y-%m-%d")
    assert processed["url"] == "http://arxiv.org/abs/cs/0102003v1"
    assert processed["comment"] == "A test comment."
    assert processed["primary_category"] == "cs.AI"

@patch('time.sleep')
def test_handle_rate_limit(mock_sleep, mock_arxiv_client):
    """Test the rate limit handling mechanism."""
    service = ArxivService()
    # arxiv.HTTPError is an alias for urllib.error.HTTPError.
    # Constructor: HTTPError(url, code, msg, hdrs, fp)
    http_error_429 = urllib.error.HTTPError('http://example.com/api', 429, 'Rate limit exceeded', {}, None)

    mock_arxiv_client.results.side_effect = [
        http_error_429,
        http_error_429,
        iter([MockArxivResult(entry_id_url="http://arxiv.org/abs/id_test_success", title="t_test", summary="s_test")]),
        iter([MockArxivResult(entry_id_url="http://arxiv.org/abs/id_final", title="t_final", summary="s_final")])
    ]

    # This call will trigger the rate limit handling
    papers, total = service.search_papers(topics=["test"])

    assert len(papers) == 1
    assert papers[0]["title"] == "t_final"
    assert mock_sleep.call_count >= 1 # Ensure sleep was called at least once
    # The number of calls to results depends on the retry logic within _handle_rate_limit
    # 1. Initial call (fails)
    # 2. First test call in _handle_rate_limit (fails)
    # 3. Second test call in _handle_rate_limit (succeeds)
    # 4. The retried call by search_papers (succeeds)
    assert mock_arxiv_client.results.call_count == 4