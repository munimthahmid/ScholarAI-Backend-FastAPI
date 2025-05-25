"""
PubMed API client for biomedical and life sciences literature.
PubMed is the premier database for biomedical literature maintained by NCBI.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from .base_client import BaseAcademicClient

logger = logging.getLogger(__name__)


class PubMedClient(BaseAcademicClient):
    """
    PubMed API client providing:
    - Biomedical literature search
    - MeSH term integration
    - Author and affiliation data
    - Journal and publication metadata
    - Abstract and full-text access
    """

    def __init__(
        self, api_key: Optional[str] = None, email: str = "contact@scholarai.dev"
    ):
        super().__init__(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            rate_limit_calls=10,  # 10 requests per second with API key, 3 without
            rate_limit_period=1,
            api_key=api_key,
        )
        self.email = email
        self.tool = "ScholarAI"

    def _get_auth_headers(self) -> Dict[str, str]:
        """PubMed doesn't use headers for auth, uses query parameters"""
        return {}

    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using PubMed's ESearch API

        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            filters: Additional filters (date range, publication type, etc.)

        Returns:
            List of normalized paper dictionaries
        """
        # Build search query with filters
        search_query = self._build_search_query(query, filters)

        # First, search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": min(limit, 10000),  # PubMed limit
            "retstart": offset,
            "sort": "relevance",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            # Search for PMIDs
            search_response = await self._make_request(
                "GET", "/esearch.fcgi", params=search_params
            )

            # Parse XML response
            if isinstance(search_response, dict) and "content" in search_response:
                xml_content = search_response["content"]
            else:
                xml_content = str(search_response)

            root = ET.fromstring(xml_content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]

            if not pmids:
                logger.info(f"No papers found in PubMed for query: {query}")
                return []

            logger.info(f"Found {len(pmids)} PMIDs from PubMed for query: {query}")

            # Fetch detailed information for the PMIDs
            papers = await self._fetch_paper_details(pmids)
            return papers

        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            return []

    async def get_paper_details(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific PubMed paper

        Args:
            pmid: PubMed ID

        Returns:
            Normalized paper dictionary or None if not found
        """
        papers = await self._fetch_paper_details([pmid])
        return papers[0] if papers else None

    async def get_citations(self, pmid: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers that cite the given PMID using PubMed's link database

        Args:
            pmid: PubMed ID
            limit: Maximum number of citations to return

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_citedin",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self._make_request("GET", "/elink.fcgi", params=params)

            # Parse XML response
            if isinstance(response, dict) and "content" in response:
                xml_content = response["content"]
            else:
                xml_content = str(response)

            root = ET.fromstring(xml_content)
            citing_pmids = [id_elem.text for id_elem in root.findall(".//Link/Id")]

            # Limit results
            citing_pmids = citing_pmids[:limit]

            if citing_pmids:
                logger.info(f"Found {len(citing_pmids)} citations for PMID {pmid}")
                return await self._fetch_paper_details(citing_pmids)

            return []

        except Exception as e:
            logger.error(f"Error getting citations from PubMed: {str(e)}")
            return []

    async def get_references(self, pmid: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get papers referenced by the given PMID

        Args:
            pmid: PubMed ID
            limit: Maximum number of references to return

        Returns:
            List of normalized paper dictionaries
        """
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "linkname": "pubmed_pubmed_refs",
            "tool": self.tool,
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self._make_request("GET", "/elink.fcgi", params=params)

            # Parse XML response
            if isinstance(response, dict) and "content" in response:
                xml_content = response["content"]
            else:
                xml_content = str(response)

            root = ET.fromstring(xml_content)
            ref_pmids = [id_elem.text for id_elem in root.findall(".//Link/Id")]

            # Limit results
            ref_pmids = ref_pmids[:limit]

            if ref_pmids:
                logger.info(f"Found {len(ref_pmids)} references for PMID {pmid}")
                return await self._fetch_paper_details(ref_pmids)

            return []

        except Exception as e:
            logger.error(f"Error getting references from PubMed: {str(e)}")
            return []

    async def _fetch_paper_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed paper information for a list of PMIDs

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of normalized paper dictionaries
        """
        if not pmids:
            return []

        # Batch fetch details (PubMed allows up to 200 IDs per request)
        batch_size = 200
        all_papers = []

        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]

            params = {
                "db": "pubmed",
                "id": ",".join(batch_pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "tool": self.tool,
                "email": self.email,
            }

            if self.api_key:
                params["api_key"] = self.api_key

            try:
                response = await self._make_request(
                    "GET", "/efetch.fcgi", params=params
                )

                # Parse XML response
                if isinstance(response, dict) and "content" in response:
                    xml_content = response["content"]
                else:
                    xml_content = str(response)

                root = ET.fromstring(xml_content)

                # Parse each article
                for article in root.findall(".//PubmedArticle"):
                    normalized = self._normalize_paper(article)
                    if normalized:
                        all_papers.append(normalized)

            except Exception as e:
                logger.error(f"Error fetching PubMed details for batch: {str(e)}")
                continue

        return all_papers

    def _build_search_query(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build PubMed search query with filters

        Args:
            query: Base search query
            filters: Additional filters

        Returns:
            Formatted search query string
        """
        search_parts = [query] if query else []

        if filters:
            if "date_range" in filters:
                date_range = filters["date_range"]
                if isinstance(date_range, list) and len(date_range) == 2:
                    search_parts.append(
                        f'("{date_range[0]}"[Date - Publication] : "{date_range[1]}"[Date - Publication])'
                    )

            if "publication_type" in filters:
                search_parts.append(
                    f"\"{filters['publication_type']}\"[Publication Type]"
                )

            if "journal" in filters:
                search_parts.append(f"\"{filters['journal']}\"[Journal]")

            if "author" in filters:
                search_parts.append(f"\"{filters['author']}\"[Author]")

            if "mesh_terms" in filters:
                for mesh_term in filters["mesh_terms"]:
                    search_parts.append(f'"{mesh_term}"[MeSH Terms]')

        return " AND ".join(search_parts)

    def _normalize_paper(self, article_xml: ET.Element) -> Dict[str, Any]:
        """
        Normalize PubMed paper data to standard format

        Args:
            article_xml: XML element containing article data

        Returns:
            Normalized paper dictionary
        """
        try:
            # Extract PMID
            pmid_elem = article_xml.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Extract title
            title_elem = article_xml.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Extract abstract
            abstract_parts = []
            for abstract_elem in article_xml.findall(".//AbstractText"):
                label = abstract_elem.get("Label", "")
                text = abstract_elem.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # Extract authors
            authors = []
            for author_elem in article_xml.findall(".//Author"):
                last_name = author_elem.find("LastName")
                first_name = author_elem.find("ForeName")
                initials = author_elem.find("Initials")

                name_parts = []
                if first_name is not None:
                    name_parts.append(first_name.text)
                elif initials is not None:
                    name_parts.append(initials.text)

                if last_name is not None:
                    name_parts.append(last_name.text)

                name = " ".join(name_parts)

                # Extract affiliation
                affiliation_elem = author_elem.find(".//Affiliation")
                affiliation = (
                    affiliation_elem.text if affiliation_elem is not None else None
                )

                authors.append(
                    {
                        "name": name,
                        "orcid": None,
                        "gsProfileUrl": None,
                        "affiliation": affiliation,
                    }
                )

            # Extract journal information
            journal_elem = article_xml.find(".//Journal")
            venue_name = ""
            issn = None

            if journal_elem is not None:
                title_elem = journal_elem.find("Title")
                if title_elem is not None:
                    venue_name = title_elem.text

                issn_elem = journal_elem.find("ISSN")
                if issn_elem is not None:
                    issn = issn_elem.text

            # Extract publication date
            pub_date = None
            pub_date_elem = article_xml.find(".//PubDate")
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find("Year")
                month_elem = pub_date_elem.find("Month")
                day_elem = pub_date_elem.find("Day")

                if year_elem is not None:
                    year = year_elem.text
                    month = month_elem.text if month_elem is not None else "01"
                    day = day_elem.text if day_elem is not None else "01"

                    # Convert month name to number if necessary
                    month_map = {
                        "Jan": "01",
                        "Feb": "02",
                        "Mar": "03",
                        "Apr": "04",
                        "May": "05",
                        "Jun": "06",
                        "Jul": "07",
                        "Aug": "08",
                        "Sep": "09",
                        "Oct": "10",
                        "Nov": "11",
                        "Dec": "12",
                    }
                    if month in month_map:
                        month = month_map[month]

                    try:
                        pub_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except:
                        pub_date = f"{year}-01-01"

            # Extract DOI
            doi = None
            for article_id in article_xml.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

            # Extract MeSH terms
            mesh_terms = []
            for mesh_elem in article_xml.findall(".//MeshHeading/DescriptorName"):
                mesh_terms.append(mesh_elem.text)

            # Extract publication types
            pub_types = []
            for pub_type_elem in article_xml.findall(".//PublicationType"):
                pub_types.append(pub_type_elem.text)

            # Build paper URL
            paper_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

            normalized = {
                "title": title,
                "doi": doi,
                "publicationDate": pub_date,
                "venueName": venue_name,
                "publisher": None,
                "peerReviewed": True,  # PubMed papers are generally peer-reviewed
                "authors": authors,
                "citationCount": 0,  # PubMed doesn't provide citation counts directly
                "abstract": abstract,
                "paperUrl": paper_url,
                "pdfUrl": None,  # PubMed doesn't provide direct PDF links
                "pdfContent": None,
                "pmid": pmid,
                "issn": issn,
                "meshTerms": mesh_terms,
                "publicationTypes": pub_types,
                "source": "pubmed",
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing PubMed paper: {str(e)}")
            return {}
