# tests/test_arxiv_service.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import arxiv # For the original arxiv.Client and arxiv.HTTPError
import urllib.error # For instantiating HTTPError correctly

from app.services.arxiv_service import ArxivService

# Store a reference to the original arxiv.Client BEFORE any patching
OriginalArxivClient = arxiv.Client

# --- Helper Mock Class ---
class MockArxivResult:
    def __init__(self, entry_id_url, title, summary, authors_mocks=None, categories=None, pdf_url=None, published=None, updated=None, comment=None, primary_category=None):
        self.entry_id = entry_id_url
        self.title = title
        self.summary = summary
        if authors_mocks is None:
            author_default_mock = MagicMock()
            author_default_mock.name = "Author Default"
            self.authors = [author_default_mock]
        else:
            self.authors = authors_mocks
        self.categories = categories or ["cs.AI"]
        self.pdf_url = pdf_url or f"http://arxiv.org/pdf/{entry_id_url.split('/')[-1]}.pdf"
        self.published = published or datetime(2023, 1, 1)
        self.updated = updated or datetime(2023, 1, 2)
        self.comment = comment or "No comments"
        self.primary_category = primary_category or "cs.AI"

    def get_short_id(self):
        if '/abs/' in self.entry_id:
            return self.entry_id.split('/abs/')[1]
        return self.entry_id.split('/')[-1]

# --- Pytest Fixture ---
@pytest.fixture
def mock_arxiv_client():
    """Fixture to mock the arxiv.Client for ArxivService."""
    # Patch 'arxiv.Client' at the source where it's imported by the arxiv library,
    # or where ArxivService would find it if it does 'import arxiv'.
    # If ArxivService does 'from arxiv import Client', you'd patch 'app.services.arxiv_service.Client'.
    # Assuming 'import arxiv' then 'arxiv.Client()' in ArxivService:
    with patch('arxiv.Client', spec=OriginalArxivClient) as mock_client_constructor:
        # mock_client_constructor is the mock for the arxiv.Client class.
        # We want ArxivService() to get an *instance* of this mock class.
        mock_instance = MagicMock(spec=OriginalArxivClient) # This instance will be returned by mock_client_constructor()
        mock_instance.results.return_value = iter([]) # Default: client.results() returns an empty iterator
        mock_client_constructor.return_value = mock_instance # When ArxivService calls arxiv.Client(), it gets mock_instance
        yield mock_instance

# --- Test Functions ---

def test_arxiv_service_initialization(mock_arxiv_client):
    service = ArxivService()
    assert service.client is mock_arxiv_client

def test_search_papers_basic(mock_arxiv_client):
    mock_paper_1_id_url = "http://arxiv.org/abs/2301.00001v1"
    mock_paper_2_id_url = "http://arxiv.org/abs/2301.00002v1"
    mock_results_data = [
        MockArxivResult(entry_id_url=mock_paper_1_id_url, title="Test Paper 1", summary="Abstract 1"),
        MockArxivResult(entry_id_url=mock_paper_2_id_url, title="Test Paper 2", summary="Abstract 2"),
    ]
    mock_arxiv_client.results.return_value = iter(mock_results_data)

    service = ArxivService()
    papers, total = service.search_papers(topics=["AI"], max_results=2)

    assert len(papers) == 2
    assert total == 2
    assert papers[0]["title"] == "Test Paper 1"
    assert papers[0]["id"] == "2301.00001v1"
    mock_arxiv_client.results.assert_called_once()

def test_search_papers_query_construction(mock_arxiv_client):
    service = ArxivService()
    service.search_papers(topics=["machine learning", "NLP"], categories=["cs.CL"], days_back=7)
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    query = search_instance_arg.query
    assert "(all:machine learning OR all:NLP)" in query
    assert "(cat:cs.CL)" in query
    # ... (date assertion as before)

    mock_arxiv_client.reset_mock() # Reset call count for the next part of this test
    mock_arxiv_client.results.return_value = iter([]) # Re-set default behavior

    service.search_papers(authors=["John Doe", "Jane Smith"])
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    query = search_instance_arg.query
    assert '(au:"John Doe" OR au:"Jane Smith")' in query

def test_get_paper_by_id_found(mock_arxiv_client):
    paper_id_short_form = "2305.00001v1"
    mock_paper_url = f"http://arxiv.org/abs/{paper_id_short_form}"
    mock_paper = MockArxivResult(entry_id_url=mock_paper_url, title="Specific Paper", summary="Specific abstract.")
    mock_arxiv_client.results.return_value = iter([mock_paper])
    service = ArxivService()
    paper = service.get_paper_by_id(paper_id_short_form)
    assert paper is not None
    assert paper["id"] == paper_id_short_form
    search_instance_arg = mock_arxiv_client.results.call_args[0][0]
    assert search_instance_arg.id_list == [paper_id_short_form]

def test_get_paper_by_id_not_found(mock_arxiv_client):
    mock_arxiv_client.results.return_value = iter([])
    service = ArxivService()
    paper = service.get_paper_by_id("nonexistent.id")
    assert paper is None

def test_process_paper(): # This test does not need mock_arxiv_client
    service = ArxivService()
    now = datetime.now()
    author_mock1 = MagicMock()
    author_mock1.name = "Author One"
    author_mock2 = MagicMock()
    author_mock2.name = "Author Two"
    mock_api_result = MockArxivResult(
        entry_id_url="http://arxiv.org/abs/cs/0102003v1", title="Test Title",
        summary="This is a test abstract.", authors_mocks=[author_mock1, author_mock2],
        categories=["cs.AI", "cs.LG"], pdf_url="http://arxiv.org/pdf/cs/0102003v1.pdf",
        published=now - timedelta(days=5), updated=now - timedelta(days=2),
        comment="A test comment.", primary_category="cs.AI"
    )
    processed = service._process_paper(mock_api_result)
    assert processed["id"] == "cs/0102003v1"
    assert processed["authors"] == ["Author One", "Author Two"]
    # Add other assertions for test_process_paper as needed

# Use a consistent name for the rate limit test, e.g., test_handle_rate_limit
@patch('time.sleep')
def test_handle_rate_limit(mock_sleep, mock_arxiv_client):
    """Test the rate limit handling and retry mechanism."""
    service = ArxivService()
    # Use urllib.error.HTTPError for instantiation
    http_error_429 = urllib.error.HTTPError('http://example.com/api', 429, 'Rate limit exceeded', {}, None)

    mock_arxiv_client.results.side_effect = [
        http_error_429,
        http_error_429,
        iter([MockArxivResult(entry_id_url="http://arxiv.org/abs/id_test_success", title="t_test", summary="s_test")]),
        iter([MockArxivResult(entry_id_url="http://arxiv.org/abs/id_final", title="t_final", summary="s_final")])
    ]

    papers, total = service.search_papers(topics=["test"])

    assert len(papers) == 1
    assert papers[0]["title"] == "t_final"
    assert mock_sleep.call_count >= 1
    assert mock_arxiv_client.results.call_count == 4