# app/services/arxiv_service.py

import arxiv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ArxivService:
    """Service for interacting with ArXiv API."""
    
    def __init__(self):
        """Initialize ArXiv service."""
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=1,
            num_retries=3
        )
    
    def search_papers(
        self,
        topics: List[str] = None,
        categories: List[str] = None,
        authors: List[str] = None,
        max_results: int = 10,
        page: int = 1,
        days_back: int = 30
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search ArXiv papers with filters."""
        try:
            # Build query
            query_parts = []
            
            # Topics search
            if topics:
                topic_query = " OR ".join([f"all:{topic}" for topic in topics])
                query_parts.append(f"({topic_query})")
            
            # Categories filter
            if categories:
                category_query = " OR ".join([f"cat:{cat}" for cat in categories])
                query_parts.append(f"({category_query})")
            
            # Authors filter
            if authors:
                author_query = " OR ".join([f"au:\"{author}\"" for author in authors])
                query_parts.append(f"({author_query})")
            
            # Date filter
            if days_back > 0:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                date_str = cutoff_date.strftime("%Y%m%d")
                query_parts.append(f"submittedDate:[{date_str}000000 TO 99991231235959]")
            
            # Combine query parts
            query = " AND ".join(query_parts) if query_parts else "all:*"
            
            # Calculate offset based on page
            offset = (page - 1) * max_results
            
            # Perform search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Get results
            results = list(self.client.results(search))
            
            # Convert to dictionary format
            papers = []
            for result in results:
                papers.append(self._process_paper(result))
            
            # Get total count (approximate)
            total = len(results)
            
            return papers, total
            
        except Exception as e:
            logger.error(f"Error searching ArXiv: {str(e)}")
            raise
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get specific paper by ID."""
        try:
            search = arxiv.Search(id_list=[paper_id])
            results = list(self.client.results(search))
            
            if results:
                return self._process_paper(results[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {str(e)}")
            raise
    
    def _process_paper(self, paper) -> Dict[str, Any]:
        """Process ArXiv paper result into dictionary."""
        try:
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
                "comment": paper.comment,
                "primary_category": paper.primary_category
            }
        except Exception as e:
            logger.error(f"Error processing paper: {str(e)}")
            raise