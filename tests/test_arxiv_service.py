# tests/test_arxiv_service.py
import pytest
from unittest.mock import patch, MagicMock, call
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
    with patch('arxiv.Client', spec=OriginalArxivClient) as mock_client_constructor:
        mock_instance = MagicMock(spec=OriginalArxivClient)
        mock_instance.results.return_value = iter([])
        mock_client_constructor.return_value = mock_instance
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

# --- Tests for _build_search_query ---
def test_build_search_query_only_topics():
    service = ArxivService()
    query = service._build_search_query(topics=["topic1", "topic2"], days_back=0) # Explicitly set days_back=0
    assert "(all:topic1 OR all:topic2)" == query # Corrected: should be the exact query
    assert "cat:" not in query
    assert "au:" not in query
    assert "submittedDate:" not in query


def test_build_search_query_only_categories():
    service = ArxivService()
    query = service._build_search_query(categories=["cs.AI", "cs.LG"], days_back=0)
    assert "(cat:cs.AI OR cat:cs.LG)" == query # Corrected
    assert "all:" not in query
    assert "au:" not in query
    assert "submittedDate:" not in query


def test_build_search_query_only_authors():
    service = ArxivService()
    query = service._build_search_query(authors=["Author One", "Author Two"], days_back=0)
    assert '(au:"Author One" OR au:"Author Two")' == query # Corrected
    assert "all:" not in query
    assert "cat:" not in query
    assert "submittedDate:" not in query


def test_build_search_query_with_days_back():
    service = ArxivService()
    days_back = 15
    query = service._build_search_query(topics=["test"], days_back=days_back)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    date_str = cutoff_date.strftime("%Y%m%d")
    expected_query = f"(all:test) AND submittedDate:[{date_str}000000 TO 99991231235959]"
    assert expected_query == query

def test_build_search_query_all_parameters():
    service = ArxivService()
    days_back = 10
    query = service._build_search_query(
        topics=["topic1"],
        categories=["cat1"],
        authors=["author1"],
        days_back=days_back
    )
    cutoff_date = datetime.now() - timedelta(days=days_back)
    date_str = cutoff_date.strftime("%Y%m%d")
    expected_query = f"(all:topic1) AND (cat:cat1) AND (au:\"author1\") AND submittedDate:[{date_str}000000 TO 99991231235959]"
    assert query == expected_query


def test_build_search_query_empty_lists_or_none():
    service = ArxivService()
    query_empty_topics_no_date = service._build_search_query(topics=[], days_back=0)
    assert "all:*" == query_empty_topics_no_date

    query_none_params_with_date = service._build_search_query() # days_back defaults to 30
    cutoff_date = datetime.now() - timedelta(days=30)
    date_str = cutoff_date.strftime("%Y%m%d")
    expected_date_query = f"submittedDate:[{date_str}000000 TO 99991231235959]"
    # As per corrected logic, if only date filter is active, it becomes the primary query
    assert expected_date_query == query_none_params_with_date


    query_with_empty_strings = service._build_search_query(topics=["  ", "topic1"], categories=["", "cat1"], days_back=0)
    assert "(all:topic1) AND (cat:cat1)" == query_with_empty_strings

def test_build_search_query_no_days_back():
    service = ArxivService()
    query = service._build_search_query(topics=["test"], days_back=0)
    assert "submittedDate:" not in query
    assert query == "(all:test)"

    query_negative_days = service._build_search_query(topics=["test"], days_back=-5) # days_back <=0 means no date filter
    assert "submittedDate:" not in query_negative_days
    assert query_negative_days == "(all:test)"

def test_build_search_query_only_days_back():
    service = ArxivService()
    days_back = 5
    query = service._build_search_query(days_back=days_back)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    date_str = cutoff_date.strftime("%Y%m%d")
    expected_query = f"submittedDate:[{date_str}000000 TO 99991231235959]"
    assert query == expected_query # It should be just the date query
    assert "all:" not in query
    assert "AND" not in query


# --- Tests for _handle_rate_limit_internally ---
@patch('time.sleep') # Mock time.sleep to avoid actual delays
def test_handle_rate_limit_internally_success_after_retries(mock_sleep, mock_arxiv_client):
    service = ArxivService()
    service.rate_limit_max_retries_internal = 2 # loop for i=0, 1
    mock_arxiv_client.results.side_effect = [
        urllib.error.HTTPError('url', 429, 'msg', {}, None), # Fails for ping attempt when i=0
        iter([MockArxivResult(entry_id_url="http://arxiv.org/abs/id_test", title="t", summary="s")]) # Succeeds for ping attempt when i=1
    ]
    service.client = mock_arxiv_client

    service._handle_rate_limit_internally() 

    assert mock_sleep.call_count == service.rate_limit_max_retries_internal # Sleep is called for each retry attempt
    assert mock_arxiv_client.results.call_count == 2 # First failing ping, second successful ping


@patch('time.sleep')
def test_handle_rate_limit_internally_fails_after_max_retries(mock_sleep, mock_arxiv_client):
    service = ArxivService()
    service.rate_limit_max_retries_internal = 2
    mock_arxiv_client.results.side_effect = urllib.error.HTTPError('url', 429, 'msg for test', {}, None)
    service.client = mock_arxiv_client

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        service._handle_rate_limit_internally()

    assert excinfo.value.code == 429
    assert "Failed to recover from rate limiting after internal retries." in str(excinfo.value.reason)
    assert mock_sleep.call_count == service.rate_limit_max_retries_internal
    assert mock_arxiv_client.results.call_count == service.rate_limit_max_retries_internal

@patch('time.sleep')
def test_handle_rate_limit_internally_non_429_error(mock_sleep, mock_arxiv_client):
    service = ArxivService()
    mock_arxiv_client.results.side_effect = urllib.error.HTTPError('url', 500, 'Internal Server Error', {}, None)
    service.client = mock_arxiv_client

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        service._handle_rate_limit_internally()

    assert excinfo.value.code == 500
    assert mock_sleep.call_count == 1 # Sleep occurs once before the first ping
    assert mock_arxiv_client.results.call_count == 1

@patch('time.sleep')
def test_search_papers_invokes_internal_rate_handler(mock_sleep, mock_arxiv_client):
    service = ArxivService()
    http_error_429 = urllib.error.HTTPError('http://example.com/api', 429, 'Rate limit exceeded', {}, None)
    mock_paper = MockArxivResult(entry_id_url="http://arxiv.org/abs/success/123", title="Success Paper", summary="Content")
    service.rate_limit_max_retries_internal = 1

    mock_arxiv_client.results.side_effect = [
        http_error_429,
        iter([mock_paper]),
        iter([mock_paper])
    ]
    service.client = mock_arxiv_client

    papers, total = service.search_papers(topics=["test"])
    assert len(papers) == 1
    assert papers[0]['title'] == "Success Paper"
    assert mock_sleep.call_count == 1
    assert mock_arxiv_client.results.call_count == 3


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

def test_process_paper():
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
    assert processed["title"] == "Test Title"
    assert processed["primary_category"] == "cs.AI"


def test_search_papers_sort_by_preference(mock_arxiv_client):
    """Test that search_papers uses the sort_by_preference."""
    service = ArxivService()
    mock_arxiv_client.results.return_value = iter([
        MockArxivResult(entry_id_url="http://arxiv.org/abs/2301.00001v1", title="Test Paper 1", summary="Abstract 1")
    ])

    service.search_papers(topics=["AI"], sort_by_preference="relevance")
    args, kwargs = mock_arxiv_client.results.call_args
    search_instance_relevance = args[0]
    assert search_instance_relevance.sort_by == arxiv.SortCriterion.Relevance

    service.search_papers(topics=["AI"], sort_by_preference="lastUpdatedDate")
    args, kwargs = mock_arxiv_client.results.call_args
    search_instance_last_updated = args[0]
    assert search_instance_last_updated.sort_by == arxiv.SortCriterion.LastUpdatedDate

    service.search_papers(topics=["AI"], sort_by_preference="submittedDate")
    args, kwargs = mock_arxiv_client.results.call_args
    search_instance_submitted_date = args[0]
    assert search_instance_submitted_date.sort_by == arxiv.SortCriterion.SubmittedDate

    service.search_papers(topics=["AI"]) # Default
    args, kwargs = mock_arxiv_client.results.call_args
    search_instance_default = args[0]
    assert search_instance_default.sort_by == arxiv.SortCriterion.Relevance