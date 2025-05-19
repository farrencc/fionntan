# app/services/arxiv_service.py

import arxiv
import logging
import time # Required for time.sleep
import random # Required for jitter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import urllib.error # For specifically catching HTTPError

logger = logging.getLogger(__name__)

class ArxivService:
    """Service for interacting with ArXiv API."""

    def __init__(self):
        """Initialize ArXiv service."""
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=1,
            # Set num_retries to 0 so our custom logic is fully tested by test_handle_rate_limit
            num_retries=0
        )
        self.rate_limit_max_retries_internal = 2 # Number of retries within _handle_rate_limit_internally
        self.rate_limit_base_delay = 1  # seconds for custom backoff

    def _build_search_query(
        self,
        topics: List[str] = None,
        categories: List[str] = None,
        authors: List[str] = None,
        days_back: int = 30
    ) -> str:
        """Build a search query string."""
        query_parts = []
        if topics:
            topic_query = " OR ".join([f"all:{topic.strip()}" for topic in topics if topic.strip()])
            if topic_query: query_parts.append(f"({topic_query})")
        if categories:
            category_query = " OR ".join([f"cat:{cat.strip()}" for cat in categories if cat.strip()])
            if category_query: query_parts.append(f"({category_query})")
        if authors:
            author_query = " OR ".join([f"au:\"{author.strip()}\"" for author in authors if author.strip()])
            if author_query: query_parts.append(f"({author_query})")
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            date_str = cutoff_date.strftime("%Y%m%d")
            query_parts.append(f"submittedDate:[{date_str}000000 TO 99991231235959]")

        query = " AND ".join(query_parts) if query_parts else "all:*"
        logger.info(f"Constructed arXiv query: {query}")
        return query

    def _handle_rate_limit_internally(self) -> None:
        """
        Internal handler for rate limiting with exponential backoff and test pings.
        This is called when a 429 is detected by search_papers or get_paper_by_id.
        """
        for i in range(self.rate_limit_max_retries_internal):
            delay = (self.rate_limit_base_delay * (2**i)) + \
                    random.uniform(0, 0.1 * (self.rate_limit_base_delay * (2**i)))
            logger.warning(
                f"Rate limit: backing off for {delay:.2f} seconds "
                f"(internal attempt {i+1}/{self.rate_limit_max_retries_internal})."
            )
            time.sleep(delay) # This will be mocked in the test for test_handle_rate_limit
            try:
                test_search = arxiv.Search(query="all:test", max_results=1)
                # The test_handle_rate_limit's side_effect on mock_arxiv_client.results
                # will control the outcome of this self.client.results call.
                next(self.client.results(test_search)) # Consume generator to trigger API call
                logger.info("Rate limit appears to be lifted after internal test ping.")
                return  # Exit if the test ping was successful
            except urllib.error.HTTPError as e_test:
                if e_test.code == 429:
                    logger.warning(f"Still rate-limited during internal ping (attempt {i+1}).")
                    if i == self.rate_limit_max_retries_internal - 1:
                        logger.error("Max retries for internal rate limit handling reached.")
                        raise # Re-raise the last 429 error, to be caught by the original caller
                else:
                    logger.error(f"Non-429 HTTPError during rate limit test ping: {e_test}")
                    raise # Re-raise other HTTP errors
            except Exception as e_exc:
                logger.error(f"Unexpected error during rate limit test ping: {e_exc}")
                raise
        # If loop finishes, it means all retries failed (should be caught by the raise in the loop)
        # For safety, raise if somehow loop completes without returning or raising.
        raise urllib.error.HTTPError(
            'http://example.com/api', 429,
            'Failed to recover from rate limiting after internal retries.', {}, None
        )

    def search_papers(
        self,
        topics: List[str] = None,
        categories: List[str] = None,
        authors: List[str] = None,
        max_results: int = 10,
        page: int = 1, # Note: `page` is not directly used by arxiv.Search, iteration handles pages.
        days_back: int = 30,
        _retry_count: int = 0 # Internal counter for retries of the main search
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search ArXiv papers with filters and rate limit handling."""
        query = self._build_search_query(topics, categories, authors, days_back)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate, # Defaulting as per test expectation
            sort_order=arxiv.SortOrder.Descending
        )

        try:
            results_iterable = self.client.results(search)
            results_list = list(results_iterable)
            papers = [self._process_paper(result) for result in results_list]
            total = len(papers)
            return papers, total
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error during search_papers. URL: {getattr(e, 'url', 'N/A')}, Code: {e.code}, Message: {e.msg}")
            if e.code == 429:
                if _retry_count >= self.rate_limit_max_retries:
                    logger.error("Max retries for search_papers reached after rate limiting. Raising.")
                    raise
                logger.warning("Rate limit (429) on search_papers. Attempting to handle and retry.")
                try:
                    self._handle_rate_limit_internally()
                    logger.info("Retrying search_papers call after successful rate limit handling.")
                    return self.search_papers(
                        topics=topics, categories=categories, authors=authors,
                        max_results=max_results, page=page, days_back=days_back,
                        _retry_count=_retry_count + 1
                    )
                except urllib.error.HTTPError as e_handle: # Catch if _handle_rate_limit_internally re-raises 429
                     logger.error(f"Failed to handle rate limit; _handle_rate_limit_internally also failed: {e_handle}")
                     raise e_handle # Re-raise the error from the handler
            else:
                raise
        except Exception as e:
            logger.error(f"Unexpected error in search_papers: {str(e)}")
            raise

    def get_paper_by_id(self, paper_id: str, _retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """Get specific paper by ID with rate limit handling."""
        try:
            search = arxiv.Search(id_list=[paper_id])
            results_iterable = self.client.results(search)
            results_list = list(results_iterable)
            if results_list:
                return self._process_paper(results_list[0])
            return None
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error in get_paper_by_id({paper_id}). Code: {e.code}, Message: {e.msg}")
            if e.code == 429:
                if _retry_count >= self.rate_limit_max_retries:
                    logger.error(f"Max retries for get_paper_by_id({paper_id}) reached. Raising.")
                    raise
                logger.warning(f"Rate limit (429) for get_paper_by_id({paper_id}). Handling and retrying.")
                try:
                    self._handle_rate_limit_internally()
                    logger.info(f"Retrying get_paper_by_id({paper_id}) call after successful rate limit handling.")
                    return self.get_paper_by_id(paper_id, _retry_count=_retry_count + 1)
                except urllib.error.HTTPError as e_handle:
                     logger.error(f"Failed to handle rate limit for get_paper_by_id; _handle_rate_limit_internally also failed: {e_handle}")
                     raise e_handle
            else:
                raise
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {str(e)}")
            raise

    def _process_paper(self, paper) -> Dict[str, Any]:
        """Process ArXiv paper result into dictionary."""
        # Add debug prints here if test_process_paper still fails on authors
        # print(f"DEBUG: _process_paper received paper object: {type(paper)}")
        # if hasattr(paper, 'authors'):
        #     print(f"DEBUG: paper.authors type: {type(paper.authors)}")
        #     if paper.authors:
        #         print(f"DEBUG: first author type: {type(paper.authors[0])}")
        #         print(f"DEBUG: first author.name type: {type(paper.authors[0].name)}")
        #         print(f"DEBUG: first author.name value: {paper.authors[0].name}")
        # authors_list = [author.name for author in paper.authors]
        # print(f"DEBUG: Extracted authors_list: {authors_list}")

        try:
            return {
                "id": paper.get_short_id(),
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary,
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
                "published": paper.published.strftime("%Y-%m-%d"),
                "updated": paper.updated.strftime("%Y-%m-%d"),
                "url": paper.entry_id,
                "comment": paper.comment,
                "primary_category": paper.primary_category
            }
        except Exception as e:
            logger.error(f"Error processing paper {getattr(paper, 'entry_id', 'UNKNOWN_ID')}: {str(e)}")
            raise