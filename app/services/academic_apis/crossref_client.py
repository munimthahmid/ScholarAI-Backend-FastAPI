"""
Crossref API client for comprehensive bibliographic metadata and DOI resolution.
Crossref is the official DOI registration agency and provides extensive
metadata for scholarly publications.
"""

import logging
from typing import Dict, Any, List, Optional
from .base_client import BaseAcademicClient

logger = logging.getLogger(__name__)


class CrossrefClient(BaseAcademicClient):
    """
    Crossref API client providing:
    - DOI resolution and metadata
    - Comprehensive bibliographic data
    - Publisher and journal information
    - Citation and reference data
    - Funding information
    - License and access information
    """

    def __init__(
        self, api_key: Optional[str] = None, mailto: str = "contact@scholarai.dev"
    ):
        super().__init__(
            base_url="https://api.crossref.org",
            rate_limit_calls=50,  # Polite pool: 50 requests per second
            rate_limit_period=1,
            api_key=api_key,
        )
        self.mailto = mailto
        # Update headers for Crossref polite pool
        self.headers.update(
            {"User-Agent": f"ScholarAI/1.0 (https://scholarai.dev; mailto:{mailto})"}
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Crossref uses Plus service for authenticated requests"""
        if self.api_key:
            return {"Crossref-Plus-API-Token": f"Bearer {self.api_key}"}
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Crossref's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (type, publisher, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "query": query,
            "rows": min(limit, 1000),  # Crossref API limit
            "offset": offset,
            "sort": "relevance",
            "order": "desc",
        }

        # Add filters if provided
        if filters:
            filter_parts = []

            if "type" in filters:
                filter_parts.append(f"type:{filters['type']}")

            if "publisher" in filters:
                filter_parts.append(f"publisher-name:{filters['publisher']}")

            if "year" in filters:
                if isinstance(filters["year"], list) and len(filters["year"]) == 2:
                    filter_parts.append(f"from-pub-date:{filters['year'][0]}")
                    filter_parts.append(f"until-pub-date:{filters['year'][1]}")
                else:
                    filter_parts.append(f"from-pub-date:{filters['year']}")
                    filter_parts.append(f"until-pub-date:{filters['year']}")

            if "journal" in filters:
                filter_parts.append(f"container-title:{filters['journal']}")

            if "has_full_text" in filters and filters["has_full_text"]:
                filter_parts.append("has-full-text:true")

            if "has_license" in filters and filters["has_license"]:
                filter_parts.append("has-license:true")

            if filter_parts:
                params["filter"] = ",".join(filter_parts)

        try:
            response = await self._make_request("GET", "/works", params=params)

            message = response.get("message", {})
            items = message.get("items", [])

            logger.info(f"Found {len(items)} papers from Crossref for query: {query}")

            # Normalize papers to standard format
            normalized_papers = []
            for paper in items:
                normalized = self._normalize_paper(paper)
                if normalized:
                    normalized_papers.append(normalized)

            return normalized_papers

        except Exception as e:
            logger.error(f"Error searching Crossref: {str(e)}")
            return []

    async def get_paper_details(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper by DOI

        Args:
            doi: DOI of the paper

        Returns:
            Normalized paper dictionary or None if not found
        """
        # Clean the DOI
        clean_doi = doi.replace("https://doi.org/", "").replace(
            "http://dx.doi.org/", ""
        )

        try:
            response = await self._make_request("GET", f"/works/{clean_doi}")

            message = response.get("message", {})
            if message:
                return self._normalize_paper(message)
            return None

        except Exception as e:
            logger.error(f"Error getting Crossref paper details: {str(e)}")
            return None

    async def get_citations(self, doi: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given DOI
        Note: Crossref doesn't provide direct citation data in their free API
        This would require integration with other services or Crossref Plus
        """
        logger.info("Crossref free API doesn't provide citation data directly")
        return []

    async def get_references(self, doi: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given DOI

        Args:
            doi: DOI of the paper
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        clean_doi = doi.replace("https://doi.org/", "").replace(
            "http://dx.doi.org/", ""
        )

        try:
            # Get the paper details first
            paper = await self.get_paper_details(clean_doi)
            if not paper:
                return []

            # Extract references from the paper metadata
            # Note: Not all papers have reference DOIs in Crossref
            references = []
            # This would need to be implemented based on Crossref's reference format

            return references

        except Exception as e:
            logger.error(f"Error getting references from Crossref: {str(e)}")
            return []

    async def resolve_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DOI to get basic metadata

        Args:
            doi: DOI to resolve

        Returns:
            Basic paper metadata or None if not found
        """
        return await self.get_paper_details(doi)

    async def get_journal_info(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a journal by ISSN

        Args:
            issn: ISSN of the journal

        Returns:
            Journal metadata or None if not found
        """
        try:
            response = await self._make_request("GET", f"/journals/{issn}")

            message = response.get("message", {})
            if message:
                return {
                    "title": message.get("title"),
                    "issn": message.get("ISSN", []),
                    "publisher": message.get("publisher"),
                    "subject": message.get("subject", []),
                    "language": message.get("language"),
                    "url": message.get("URL"),
                }
            return None

        except Exception as e:
            logger.error(f"Error getting journal info from Crossref: {str(e)}")
            return None

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Crossref paper data to standard format

        Args:
            raw_paper: Raw paper data from Crossref API

        Returns:
            Normalized paper dictionary
        """
        if not raw_paper or not raw_paper.get("title"):
            return {}

        # Extract title (Crossref titles are arrays)
        title = ""
        if "title" in raw_paper and raw_paper["title"]:
            title = (
                raw_paper["title"][0]
                if isinstance(raw_paper["title"], list)
                else str(raw_paper["title"])
            )

        # Extract DOI
        doi = raw_paper.get("DOI")

        # Extract authors
        authors = []
        for author in raw_paper.get("author", []):
            author_info = {
                "name": f"{author.get('given', '')} {author.get('family', '')}".strip(),
                "orcid": author.get("ORCID"),
                "gsProfileUrl": None,
                "affiliation": None,
            }

            # Extract affiliation if available
            if "affiliation" in author and author["affiliation"]:
                affiliations = [aff.get("name", "") for aff in author["affiliation"]]
                author_info["affiliation"] = "; ".join(affiliations)

            authors.append(author_info)

        # Extract publication date
        pub_date = None
        if "published-print" in raw_paper:
            date_parts = raw_paper["published-print"].get("date-parts", [[]])[0]
        elif "published-online" in raw_paper:
            date_parts = raw_paper["published-online"].get("date-parts", [[]])[0]
        else:
            date_parts = []

        if date_parts:
            year = date_parts[0] if len(date_parts) > 0 else None
            month = date_parts[1] if len(date_parts) > 1 else 1
            day = date_parts[2] if len(date_parts) > 2 else 1
            if year:
                pub_date = f"{year:04d}-{month:02d}-{day:02d}"

        # Extract venue information
        venue_name = ""
        publisher = ""

        if "container-title" in raw_paper and raw_paper["container-title"]:
            venue_name = (
                raw_paper["container-title"][0]
                if isinstance(raw_paper["container-title"], list)
                else str(raw_paper["container-title"])
            )

        if "publisher" in raw_paper:
            publisher = raw_paper["publisher"]

        # Extract URLs
        paper_url = raw_paper.get("URL")
        if not paper_url and doi:
            paper_url = f"https://doi.org/{doi}"

        # Check for open access
        is_open_access = False
        license_info = raw_paper.get("license", [])
        if license_info:
            is_open_access = True

        # Extract abstract (not always available in Crossref)
        abstract = raw_paper.get("abstract")

        # Extract citation count (not available in free Crossref API)
        citation_count = raw_paper.get("is-referenced-by-count", 0)

        # Extract reference count
        reference_count = raw_paper.get("references-count", 0)

        # Extract type
        paper_type = raw_paper.get("type", "journal-article")

        # Extract ISSN
        issn = raw_paper.get("ISSN", [])

        # Extract funding information
        funding = []
        for funder in raw_paper.get("funder", []):
            funding.append(
                {
                    "name": funder.get("name"),
                    "doi": funder.get("DOI"),
                    "award": funder.get("award", []),
                }
            )

        normalized = {
            "title": title,
            "doi": doi,
            "publicationDate": pub_date,
            "venueName": venue_name,
            "publisher": publisher,
            "peerReviewed": paper_type in ["journal-article", "proceedings-article"],
            "authors": authors,
            "citationCount": citation_count,
            "referenceCount": reference_count,
            "isOpenAccess": is_open_access,
            "abstract": abstract,
            "paperUrl": paper_url,
            "pdfUrl": None,  # Crossref doesn't provide direct PDF links
            "pdfContent": None,
            "crossrefType": paper_type,
            "issn": issn,
            "license": license_info,
            "funding": funding,
            "volume": raw_paper.get("volume"),
            "issue": raw_paper.get("issue"),
            "page": raw_paper.get("page"),
            "source": "crossref",
        }

        return normalized
