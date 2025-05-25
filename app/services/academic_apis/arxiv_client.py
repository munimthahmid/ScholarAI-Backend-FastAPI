"""
arXiv API client for accessing preprints and early research papers.
arXiv is a crucial source for the latest research, especially in physics,
mathematics, computer science, and related fields.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from urllib.parse import quote
import feedparser
from .base_client import BaseAcademicClient

logger = logging.getLogger(__name__)


class ArxivClient(BaseAcademicClient):
    """
    arXiv API client providing:
    - Search for preprints and papers
    - Access to full-text PDFs
    - Author and category information
    - Version history tracking
    - Subject classification
    """

    def __init__(self):
        super().__init__(
            base_url="http://export.arxiv.org/api",
            rate_limit_calls=300,  # arXiv allows 3 requests per second
            rate_limit_period=60,
            timeout=30,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """arXiv doesn't require authentication"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using arXiv's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (category, date range, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # Build search query
        search_query = self._build_search_query(query, filters)

        params = {
            "search_query": search_query,
            "start": offset,
            "max_results": min(limit, 2000),  # arXiv API limit
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            response = await self._make_request("GET", "/query", params=params)

            # Parse the Atom feed response
            if isinstance(response, dict) and "content" in response:
                feed_content = response["content"]
            else:
                feed_content = str(response)

            # Use feedparser to parse the Atom feed
            feed = feedparser.parse(feed_content)
            papers = feed.entries

            logger.info(f"Found {len(papers)} papers from arXiv for query: {query}")

            # Normalize papers to standard format
            normalized_papers = []
            for paper in papers:
                normalized = self._normalize_paper(paper)
                if normalized:
                    normalized_papers.append(normalized)

            return normalized_papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific arXiv paper

        Args:
            paper_id: arXiv ID (e.g., "2301.12345" or "cs.AI/0601001")

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Clean the arXiv ID
        arxiv_id = paper_id.replace("arXiv:", "").replace("https://arxiv.org/abs/", "")

        params = {"id_list": arxiv_id, "max_results": 1}

        try:
            response = await self._make_request("GET", "/query", params=params)

            # Parse the Atom feed response
            if isinstance(response, dict) and "content" in response:
                feed_content = response["content"]
            else:
                feed_content = str(response)

            feed = feedparser.parse(feed_content)

            if feed.entries:
                return self._normalize_paper(feed.entries[0])
            return None

        except Exception as e:
            logger.error(f"Error getting arXiv paper details: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        arXiv doesn't provide direct citation data, so we return empty list
        This could be enhanced by integrating with other services
        """
        logger.info("arXiv doesn't provide citation data directly")
        return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        arXiv doesn't provide direct reference data, so we return empty list
        This could be enhanced by parsing PDF content for references
        """
        logger.info("arXiv doesn't provide reference data directly")
        return []

    def _build_search_query(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build arXiv search query with filters

        Args:
            query: Base search query
            filters: Additional filters

        Returns:
            Formatted search query string
        """
        search_parts = []

        # Add main query to title and abstract
        if query:
            search_parts.append(f"all:{quote(query)}")

        # Add filters if provided
        if filters:
            if "category" in filters:
                search_parts.append(f"cat:{filters['category']}")

            if "author" in filters:
                search_parts.append(f"au:{quote(filters['author'])}")

            if "title" in filters:
                search_parts.append(f"ti:{quote(filters['title'])}")

            if "abstract" in filters:
                search_parts.append(f"abs:{quote(filters['abstract'])}")

        return " AND ".join(search_parts) if search_parts else "all:*"

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize arXiv paper data to standard format

        Args:
            raw_paper: Raw paper data from arXiv API (feedparser entry)

        Returns:
            Normalized paper dictionary
        """
        if not raw_paper or not raw_paper.get("title"):
            return {}

        # Extract arXiv ID
        arxiv_id = None
        paper_url = None
        pdf_url = None

        if "id" in raw_paper:
            arxiv_id = raw_paper["id"].split("/")[-1]  # Extract ID from URL
            paper_url = raw_paper["id"]
            pdf_url = raw_paper["id"].replace("/abs/", "/pdf/") + ".pdf"

        # Extract DOI if available
        doi = None
        if "arxiv_doi" in raw_paper:
            doi = raw_paper["arxiv_doi"]

        # Extract authors
        authors = []
        if "authors" in raw_paper:
            for author in raw_paper["authors"]:
                author_name = (
                    author.get("name", "") if isinstance(author, dict) else str(author)
                )
                authors.append(
                    {
                        "name": author_name,
                        "orcid": None,
                        "gsProfileUrl": None,
                        "affiliation": None,
                    }
                )

        # Extract categories/subjects
        categories = []
        if "tags" in raw_paper:
            for tag in raw_paper["tags"]:
                if isinstance(tag, dict) and "term" in tag:
                    categories.append(tag["term"])

        # Extract publication date
        pub_date = None
        if "published" in raw_paper:
            try:
                from dateutil.parser import parse

                parsed_date = parse(raw_paper["published"])
                pub_date = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Extract updated date
        updated_date = None
        if "updated" in raw_paper:
            try:
                from dateutil.parser import parse

                parsed_date = parse(raw_paper["updated"])
                updated_date = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Extract abstract
        abstract = raw_paper.get("summary", "").strip()

        # Extract version information
        version = None
        if "arxiv_comment" in raw_paper:
            comment = raw_paper["arxiv_comment"]
            if "v" in comment:
                version = comment

        normalized = {
            "title": raw_paper.get("title", "").strip(),
            "doi": doi,
            "publicationDate": pub_date,
            "updatedDate": updated_date,
            "venueName": "arXiv",
            "publisher": "arXiv",
            "peerReviewed": False,  # arXiv papers are preprints
            "authors": authors,
            "citationCount": 0,  # arXiv doesn't provide citation counts
            "abstract": abstract,
            "paperUrl": paper_url,
            "pdfUrl": pdf_url,
            "pdfContent": None,  # Could be downloaded separately
            "arxivId": arxiv_id,
            "categories": categories,
            "version": version,
            "comment": raw_paper.get("arxiv_comment"),
            "journalRef": raw_paper.get("arxiv_journal_ref"),
            "source": "arxiv",
            "isPreprint": True,
        }

        return normalized

    async def download_pdf(self, arxiv_id: str) -> Optional[bytes]:
        """
        Download PDF content for an arXiv paper

        Args:
            arxiv_id: arXiv ID

        Returns:
            PDF content as bytes or None if download fails
        """
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        try:
            response = await self.client.get(pdf_url)
            response.raise_for_status()

            logger.info(f"Downloaded PDF for arXiv:{arxiv_id}")
            return response.content

        except Exception as e:
            logger.error(f"Error downloading PDF for arXiv:{arxiv_id}: {str(e)}")
            return None

    async def get_paper_versions(self, arxiv_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of an arXiv paper

        Args:
            arxiv_id: arXiv ID

        Returns:
            List of paper versions with metadata
        """
        try:
            # Get paper details which includes version info
            paper = await self.get_paper_details(arxiv_id)
            if paper:
                # For now, return the current version
                # This could be enhanced to fetch all versions
                return [paper]
            return []

        except Exception as e:
            logger.error(f"Error getting paper versions for arXiv:{arxiv_id}: {str(e)}")
            return []
