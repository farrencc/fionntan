"""
arXiv Paper Scraper

This module provides functionality to search and retrieve papers from arXiv
based on user preferences including topics, categories, and researchers.

Features:
- Search papers by topics, categories, and authors
- Filter results by recency and relevance
- Download and structure paper metadata
- Handle API rate limits with exponential backoff
- Error handling and logging
"""

import arxiv
import time
import logging
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.error import HTTPError
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("arxiv_scraper")

@dataclass
class UserPreferences:
    """Store user preferences for paper searches."""
    topics: List[str]
    categories: List[str] = None
    authors: List[str] = None
    max_results: int = 50
    days_back: int = 30
    sort_by: str = "relevance"  # 'relevance' or 'lastUpdatedDate'


class ArXivScraper:
    """
    ArXiv paper scraper that fetches papers based on user preferences.
    Handles rate limiting and error recovery.
    """
    
    # arXiv API base URL
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # arXiv API rate limits
    # See: https://arxiv.org/help/api/user-manual#dos
    MAX_REQUESTS_PER_SECOND = 1
    
    def __init__(self, user_prefs: UserPreferences):
        """
        Initialize the ArXiv scraper with user preferences.
        
        Args:
            user_prefs: UserPreferences object containing search parameters
        """
        self.user_prefs = user_prefs
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=1,  # Respect arXiv's rate limits
            num_retries=3
        )
        
    def _build_search_query(self) -> str:
        """
        Build a search query string from user preferences.
        
        Returns:
            str: arXiv API compatible search query
        """
        # Build topic query
        topic_query = " OR ".join([f"all:{topic}" for topic in self.user_prefs.topics])
        
        # Add categories if specified
        category_filter = ""
        if self.user_prefs.categories:
            category_filter = " AND (" + " OR ".join([f"cat:{cat}" for cat in self.user_prefs.categories]) + ")"
        
        # Add authors if specified
        author_filter = ""
        if self.user_prefs.authors:
            author_filter = " AND (" + " OR ".join([f"au:\"{author}\"" for author in self.user_prefs.authors]) + ")"
        
        # Add date filter
        date_filter = ""
        if self.user_prefs.days_back > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.user_prefs.days_back)
            date_str = cutoff_date.strftime("%Y%m%d")
            date_filter = f" AND submittedDate:[{date_str}000000 TO 99991231235959]"
        
        # Combine all parts
        query = f"({topic_query}){category_filter}{author_filter}{date_filter}"
        logger.info(f"Search query: {query}")
        return query

    def search_papers(self) -> List[Dict[str, Any]]:
        """
        Search for papers based on user preferences.
        
        Returns:
            List[Dict]: List of paper metadata dictionaries
        """
        query = self._build_search_query()
        
        try:
            # Create search parameters
            search = arxiv.Search(
                query=query,
                max_results=self.user_prefs.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate if self.user_prefs.sort_by == "lastUpdatedDate" 
                      else arxiv.SortCriterion.Relevance
            )
            
            # Execute search with rate limiting
            papers = []
            for result in self.client.results(search):
                papers.append(self._process_paper(result))
                
            logger.info(f"Found {len(papers)} papers matching the criteria")
            return papers
            
        except HTTPError as e:
            logger.error(f"HTTP error during search: {e}")
            if e.code == 429:  # Too Many Requests
                logger.warning("Rate limit hit, implementing exponential backoff")
                self._handle_rate_limit()
                return self.search_papers()  # Retry after backoff
            raise
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def _process_paper(self, paper) -> Dict[str, Any]:
        """
        Process a paper result into a structured dictionary.
        
        Args:
            paper: arXiv result object
            
        Returns:
            Dict: Structured paper metadata
        """
        return {
            "id": paper.entry_id.split("/")[-1],
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "abstract": paper.summary,
            "pdf_url": paper.pdf_url,
            "categories": paper.categories,
            "published": paper.published.strftime("%Y-%m-%d"),
            "updated": paper.updated.strftime("%Y-%m-%d"),
            "url": paper.entry_id,
            "comment": paper.comment
        }
    
    def _handle_rate_limit(self) -> None:
        """Handle rate limiting with exponential backoff."""
        # Start with a 1-second delay, then increase exponentially
        base_delay = 1
        max_delay = 60  # Maximum 1 minute delay
        retries = 0
        max_retries = 5
        
        while retries < max_retries:
            retries += 1
            # Calculate delay with jitter
            delay = min(max_delay, base_delay * (2 ** retries))
            jitter = random.uniform(0, 0.1 * delay)
            total_delay = delay + jitter
            
            logger.warning(f"Rate limit backoff: waiting {total_delay:.2f} seconds (retry {retries}/{max_retries})")
            time.sleep(total_delay)
            
            # Try a simple request to see if we're still rate limited
            try:
                # Make a minimal test request
                test_search = arxiv.Search(query="test", max_results=1)
                next(self.client.results(test_search))
                logger.info("Rate limit backoff successful")
                return  # We're good to go
            except HTTPError as e:
                if e.code != 429:  # If it's not a rate limit issue, raise
                    raise
                # Otherwise continue with backoff
        
        # If we've exhausted retries
        logger.error("Rate limit backoff failed after maximum retries")
        raise Exception("Rate limiting could not be resolved after multiple retries")

    def download_batch(self, topics: List[str], categories: Optional[List[str]] = None, 
                       authors: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Convenience method to download a batch of papers with updated preferences.
        
        Args:
            topics: List of topics to search for
            categories: Optional list of arXiv categories
            authors: Optional list of authors to filter by
            
        Returns:
            List[Dict]: List of paper metadata dictionaries
        """
        # Update preferences
        self.user_prefs.topics = topics
        if categories:
            self.user_prefs.categories = categories
        if authors:
            self.user_prefs.authors = authors
            
        return self.search_papers()


def main():
    """Example usage of the ArXivScraper class."""
    # Example user preferences
    user_prefs = UserPreferences(
        topics=["transformer", "attention mechanism"],
        categories=["cs.CL", "cs.AI"],
        authors=["Yoshua Bengio", "Geoffrey Hinton"],
        max_results=10,
        days_back=90,
        sort_by="relevance"
    )
    
    # Create scraper
    scraper = ArXivScraper(user_prefs)
    
    # Search for papers
    try:
        papers = scraper.search_papers()
        print(f"Found {len(papers)} papers")
        
        # Print first paper details
        if papers:
            paper = papers[0]
            print(f"Sample paper: {paper['title']}")
            print(f"Authors: {', '.join(paper['authors'])}")
            print(f"Abstract: {paper['abstract'][:150]}...")
            print(f"URL: {paper['url']}")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()