"""
Semantic Scholar API client for comprehensive paper discovery and citation analysis.
Semantic Scholar provides one of the most comprehensive academic databases with
rich citation networks and metadata.
"""

import logging
from typing import Dict, Any, List, Optional
from .base_client import BaseAcademicClient

logger = logging.getLogger(__name__)


class SemanticScholarClient(BaseAcademicClient):
    """
    Semantic Scholar API client providing:
    - Comprehensive paper search
    - Citation and reference networks
    - Author information and metrics
    - Venue and publication details
    - PDF availability detection
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://api.semanticscholar.org/graph/v1",
            rate_limit_calls=100,  # 100 requests per 5 minutes for free tier
            rate_limit_period=300,
            api_key=api_key,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Semantic Scholar API authentication headers"""
        if self.api_key:
            return {"x-api-key": self.api_key}
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Semantic Scholar's search API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (year, venue, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "query": query,
            "limit": min(limit, 100),  # API limit
            "offset": offset,
            "fields": "paperId,externalIds,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,publicationTypes,publicationDate,journal",
        }

        # Add filters if provided
        if filters:
            if "year" in filters:
                params["year"] = filters["year"]
            if "venue" in filters:
                params["venue"] = filters["venue"]
            if "fieldsOfStudy" in filters:
                params["fieldsOfStudy"] = filters["fieldsOfStudy"]

        try:
            response = await self._make_request("GET", "/paper/search", params=params)
            papers = response.get("data", [])

            logger.info(
                f"Found {len(papers)} papers from Semantic Scholar for query: {query}"
            )

            # Normalize papers to standard format
            normalized_papers = []
            for paper in papers:
                normalized = self._normalize_paper(paper)
                if normalized:
                    normalized_papers.append(normalized)

            return normalized_papers

        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")
            return []

    async def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI

        Returns:
            Normalized paper dictionary or None if not found
        """
        fields = "paperId,externalIds,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,publicationTypes,publicationDate,journal,references,citations"

        try:
            response = await self._make_request(
                "GET", f"/paper/{paper_id}", params={"fields": fields}
            )

            if response:
                return self._normalize_paper(response)
            return None

        except Exception as e:
            logger.error(f"Error getting paper details from Semantic Scholar: {str(e)}")
            return None

    async def get_citations(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = "paperId,externalIds,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,publicationTypes,publicationDate,journal"

        try:
            response = await self._make_request(
                "GET",
                f"/paper/{paper_id}/citations",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            citations = response.get("data", [])
            logger.info(f"Found {len(citations)} citations for paper {paper_id}")

            normalized_citations = []
            for citation in citations:
                citing_paper = citation.get("citingPaper", {})
                normalized = self._normalize_paper(citing_paper)
                if normalized:
                    normalized_citations.append(normalized)

            return normalized_citations

        except Exception as e:
            logger.error(f"Error getting citations from Semantic Scholar: {str(e)}")
            return []

    async def get_references(
        self, paper_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given paper

        Args:
            paper_id: Semantic Scholar paper ID or DOI
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = "paperId,externalIds,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,publicationTypes,publicationDate,journal"

        try:
            response = await self._make_request(
                "GET",
                f"/paper/{paper_id}/references",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            references = response.get("data", [])
            logger.info(f"Found {len(references)} references for paper {paper_id}")

            normalized_references = []
            for reference in references:
                cited_paper = reference.get("citedPaper", {})
                normalized = self._normalize_paper(cited_paper)
                if normalized:
                    normalized_references.append(normalized)

            return normalized_references

        except Exception as e:
            logger.error(f"Error getting references from Semantic Scholar: {str(e)}")
            return []

    async def get_author_papers(
        self, author_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get papers by a specific author

        Args:
            author_id: Semantic Scholar author ID
            limit: Maximum number of papers to return

        Returns:
            List of normalized paper dictionaries
        """
        fields = "paperId,externalIds,title,abstract,venue,year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,publicationTypes,publicationDate,journal"

        try:
            response = await self._make_request(
                "GET",
                f"/author/{author_id}/papers",
                params={"fields": fields, "limit": min(limit, 1000)},
            )

            papers = response.get("data", [])
            logger.info(f"Found {len(papers)} papers for author {author_id}")

            normalized_papers = []
            for paper in papers:
                normalized = self._normalize_paper(paper)
                if normalized:
                    normalized_papers.append(normalized)

            return normalized_papers

        except Exception as e:
            logger.error(f"Error getting author papers from Semantic Scholar: {str(e)}")
            return []

    def _normalize_paper(self, raw_paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Semantic Scholar paper data to standard format

        Args:
            raw_paper: Raw paper data from Semantic Scholar API

        Returns:
            Normalized paper dictionary
        """
        if not raw_paper or not raw_paper.get("title"):
            return {}

        # Extract DOI
        doi = None
        external_ids = raw_paper.get("externalIds", {})
        if external_ids and "DOI" in external_ids:
            doi = external_ids["DOI"]

        # Extract authors
        authors = []
        for author in raw_paper.get("authors", []):
            author_info = {
                "name": author.get("name", ""),
                "authorId": author.get("authorId"),
                "orcid": None,
                "gsProfileUrl": None,
                "affiliation": None,
            }

            # Try to extract additional author info if available
            if "externalIds" in author and author["externalIds"]:
                if "ORCID" in author["externalIds"]:
                    author_info["orcid"] = author["externalIds"]["ORCID"]

            authors.append(author_info)

        # Extract venue information
        venue_name = raw_paper.get("venue") or ""
        journal = raw_paper.get("journal", {})
        if journal and not venue_name:
            venue_name = journal.get("name", "")

        # Extract publication date
        pub_date = raw_paper.get("publicationDate") or raw_paper.get("year")
        if isinstance(pub_date, int):
            pub_date = f"{pub_date}-01-01"

        # Check for PDF availability
        pdf_url = None
        pdf_content = None
        open_access_pdf = raw_paper.get("openAccessPdf")
        if open_access_pdf and open_access_pdf.get("url"):
            pdf_url = open_access_pdf["url"]

        # Extract paper URL
        paper_url = None
        if external_ids:
            if "ArXiv" in external_ids:
                paper_url = f"https://arxiv.org/abs/{external_ids['ArXiv']}"
            elif "DOI" in external_ids:
                paper_url = f"https://doi.org/{external_ids['DOI']}"

        normalized = {
            "title": raw_paper.get("title", ""),
            "doi": doi,
            "publicationDate": pub_date,
            "venueName": venue_name,
            "publisher": journal.get("publisher") if journal else None,
            "peerReviewed": True,  # Assume peer-reviewed unless specified otherwise
            "authors": authors,
            "citationCount": raw_paper.get("citationCount", 0),
            "referenceCount": raw_paper.get("referenceCount", 0),
            "influentialCitationCount": raw_paper.get("influentialCitationCount", 0),
            "isOpenAccess": raw_paper.get("isOpenAccess", False),
            "abstract": raw_paper.get("abstract"),
            "paperUrl": paper_url,
            "pdfUrl": pdf_url,
            "pdfContent": pdf_content,
            "semanticScholarId": raw_paper.get("paperId"),
            "externalIds": external_ids,
            "publicationTypes": raw_paper.get("publicationTypes", []),
            "fieldsOfStudy": raw_paper.get("fieldsOfStudy", []),
            "source": "semantic_scholar",
        }

        return normalized
