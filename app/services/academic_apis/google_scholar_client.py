"""
Google Scholar client for comprehensive academic search and citation analysis.
Uses the scholarly library to access Google Scholar data with rate limiting
and error handling.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from scholarly import scholarly, ProxyGenerator
from .base_client import BaseAcademicClient

logger = logging.getLogger(__name__)


class GoogleScholarClient(BaseAcademicClient):
    """
    Google Scholar client providing:
    - Comprehensive academic search
    - Citation and reference networks
    - Author profiles and metrics
    - Real-time citation counts
    - Access to diverse publication types
    """

    def __init__(self, use_proxy: bool = False):
        super().__init__(
            base_url="https://scholar.google.com",
            rate_limit_calls=10,  # Conservative rate limiting for Google Scholar
            rate_limit_period=60,
            timeout=30,
        )

        # Setup proxy if requested (helps avoid rate limiting)
        if use_proxy:
            try:
                pg = ProxyGenerator()
                pg.FreeProxies()
                scholarly.use_proxy(pg)
                logger.info("Google Scholar proxy configured")
            except Exception as e:
                logger.warning(f"Failed to setup proxy for Google Scholar: {str(e)}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Google Scholar doesn't use API authentication"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Google Scholar

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (not directly supported by scholarly)
            filters: Additional filters (year range, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        try:
            # Build search parameters
            search_params = {"query": query}

            if filters:
                if "year_low" in filters:
                    search_params["year_low"] = filters["year_low"]
                if "year_high" in filters:
                    search_params["year_high"] = filters["year_high"]
                if "patents" in filters:
                    search_params["patents"] = filters["patents"]
                if "citations" in filters:
                    search_params["citations"] = filters["citations"]

            # Perform search in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, self._perform_search, search_params, limit
            )

            logger.info(
                f"Found {len(search_results)} papers from Google Scholar for query: {query}"
            )

            # Normalize papers to standard format
            normalized_papers = []
            for paper in search_results:
                normalized = self._normalize_paper(paper)
                if normalized:
                    normalized_papers.append(normalized)

            return normalized_papers

        except Exception as e:
            logger.error(f"Error searching Google Scholar: {str(e)}")
            return []

    def _perform_search(
        self, search_params: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """
        Perform the actual search using scholarly library

        Args:
            search_params: Search parameters
            limit: Maximum number of results

        Returns:
            List of raw paper dictionaries from scholarly
        """
        try:
            search_query = scholarly.search_pubs(**search_params)
            results = []

            for i, paper in enumerate(search_query):
                if i >= limit:
                    break

                # Try to fill in additional details
                try:
                    filled_paper = scholarly.fill(paper)
                    results.append(filled_paper)
                except Exception as e:
                    logger.warning(f"Could not fill details for paper {i}: {str(e)}")
                    results.append(paper)

                # Add delay to avoid rate limiting
                import time

                time.sleep(1)

            return results

        except Exception as e:
            logger.error(f"Error in Google Scholar search execution: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper
        Note: Google Scholar doesn't have stable paper IDs, so this is limited

        Args:
            paper_id: Paper identifier (could be title or partial info)

        Returns:
            Normalized paper dictionary or None if not found
        """
        try:
            # Search for the specific paper
            papers = await self.search_papers(paper_id, limit=1)
            return papers[0] if papers else None

        except Exception as e:
            logger.error(f"Error getting Google Scholar paper details: {str(e)}")
            return None

    async def get_citations(
        self, paper_title: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_title: Title of the paper to find citations for
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        try:
            # First find the paper
            papers = await self.search_papers(paper_title, limit=1)
            if not papers:
                return []

            # Get the first paper's citation info
            paper = papers[0]
            if not paper.get("citedby_url"):
                return []

            # Perform citation search in executor
            loop = asyncio.get_event_loop()
            citations = await loop.run_in_executor(
                None, self._get_citations_sync, paper, limit
            )

            logger.info(f"Found {len(citations)} citations for paper: {paper_title}")

            # Normalize citations
            normalized_citations = []
            for citation in citations:
                normalized = self._normalize_paper(citation)
                if normalized:
                    normalized_citations.append(normalized)

            return normalized_citations

        except Exception as e:
            logger.error(f"Error getting citations from Google Scholar: {str(e)}")
            return []

    def _get_citations_sync(
        self, paper: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """
        Synchronous method to get citations using scholarly

        Args:
            paper: Paper dictionary with citation info
            limit: Maximum number of citations

        Returns:
            List of citing papers
        """
        try:
            citations = []
            if "citedby_url" in paper:
                # This would require implementing citation following
                # For now, return empty list as it's complex with scholarly
                pass

            return citations

        except Exception as e:
            logger.error(f"Error in synchronous citation retrieval: {str(e)}")
            return []

    async def get_references(
        self, paper_title: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Google Scholar doesn't provide direct reference data
        """
        logger.info("Google Scholar doesn't provide reference data directly")
        return []

    async def get_author_profile(self, author_name: str) -> Optional[Dict[str, Any]]:
        """
        Get author profile information from Google Scholar

        Args:
            author_name: Name of the author

        Returns:
            Author profile dictionary or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(
                None, self._get_author_profile_sync, author_name
            )

            return profile

        except Exception as e:
            logger.error(f"Error getting author profile from Google Scholar: {str(e)}")
            return None

    def _get_author_profile_sync(self, author_name: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous method to get author profile

        Args:
            author_name: Name of the author

        Returns:
            Author profile dictionary
        """
        try:
            search_query = scholarly.search_author(author_name)
            author = next(search_query, None)

            if author:
                filled_author = scholarly.fill(author)

                return {
                    "name": filled_author.get("name"),
                    "scholar_id": filled_author.get("scholar_id"),
                    "affiliation": filled_author.get("affiliation"),
                    "email": filled_author.get("email"),
                    "interests": filled_author.get("interests", []),
                    "citedby": filled_author.get("citedby"),
                    "citedby5y": filled_author.get("citedby5y"),
                    "hindex": filled_author.get("hindex"),
                    "hindex5y": filled_author.get("hindex5y"),
                    "i10index": filled_author.get("i10index"),
                    "i10index5y": filled_author.get("i10index5y"),
                    "url_picture": filled_author.get("url_picture"),
                    "homepage": filled_author.get("homepage"),
                }

            return None

        except Exception as e:
            logger.error(f"Error in synchronous author profile retrieval: {str(e)}")
            return None

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Google Scholar paper data to standard format

        Args:
            raw_paper: Raw paper data from scholarly

        Returns:
            Normalized paper dictionary
        """
        if not raw_paper or not raw_paper.get("title"):
            return {}

        # Extract basic information
        title = raw_paper.get("title", "")
        abstract = raw_paper.get("abstract", "")

        # Extract authors
        authors = []
        author_list = raw_paper.get("author", [])
        if isinstance(author_list, list):
            for author in author_list:
                if isinstance(author, str):
                    authors.append(
                        {
                            "name": author,
                            "orcid": None,
                            "gsProfileUrl": None,
                            "affiliation": None,
                        }
                    )
                elif isinstance(author, dict):
                    authors.append(
                        {
                            "name": author.get("name", ""),
                            "orcid": None,
                            "gsProfileUrl": author.get("scholar_id"),
                            "affiliation": author.get("affiliation"),
                        }
                    )

        # Extract publication info
        venue_name = raw_paper.get("venue", "")
        pub_year = raw_paper.get("pub_year")
        pub_date = f"{pub_year}-01-01" if pub_year else None

        # Extract citation count
        citation_count = 0
        if "num_citations" in raw_paper:
            citation_count = raw_paper["num_citations"]
        elif "citedby" in raw_paper:
            citation_count = raw_paper["citedby"]

        # Extract URLs
        paper_url = raw_paper.get("pub_url") or raw_paper.get("eprint")
        pdf_url = (
            raw_paper.get("eprint")
            if raw_paper.get("eprint", "").endswith(".pdf")
            else None
        )

        # Extract additional metadata
        publisher = raw_paper.get("publisher", "")

        normalized = {
            "title": title,
            "doi": None,  # Google Scholar doesn't always provide DOIs
            "publicationDate": pub_date,
            "venueName": venue_name,
            "publisher": publisher,
            "peerReviewed": True,  # Assume peer-reviewed unless specified otherwise
            "authors": authors,
            "citationCount": citation_count,
            "abstract": abstract,
            "paperUrl": paper_url,
            "pdfUrl": pdf_url,
            "pdfContent": None,
            "googleScholarId": raw_paper.get("scholar_id"),
            "citedbyUrl": raw_paper.get("citedby_url"),
            "relatedUrl": raw_paper.get("related_url"),
            "source": "google_scholar",
        }

        return normalized
