"""
Simplified search agent for discovering related academic papers.
Uses existing ArXiv and Semantic Scholar clients for focused paper discovery.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse

from ..academic_apis.clients.arxiv_client import ArxivClient
from ..academic_apis.clients.semantic_scholar_client import SemanticScholarClient

logger = logging.getLogger(__name__)


class SimpleSearchAgent:
    """
    Simplified academic search agent that leverages existing API clients
    for focused paper discovery without complex orchestration.
    """
    
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.semantic_client = SemanticScholarClient()
        self.max_results_per_query = 5  # Keep focused
        
    async def search_papers(self, queries: List[str], limit_per_query: int = 5) -> List[str]:
        """
        Search for papers using multiple queries across ArXiv and Semantic Scholar.
        
        Args:
            queries: List of search query strings
            limit_per_query: Maximum papers to return per query
            
        Returns:
            List of unique paper URLs
        """
        all_paper_urls = set()
        
        logger.info(f"Executing {len(queries)} search queries")
        
        for query in queries:
            try:
                # Search ArXiv for recent preprints (focusing on ArXiv only for faster testing)
                arxiv_papers = await self._search_arxiv(query, limit_per_query)
                logger.info(f"🔍 PROCESSING: Got {len(arxiv_papers)} papers from ArXiv for query '{query}'")
                arxiv_urls = self._extract_urls_from_papers(arxiv_papers)
                logger.info(f"🔍 URL EXTRACTION: Extracted {len(arxiv_urls)} URLs from {len(arxiv_papers)} papers")
                if arxiv_urls:
                    logger.info(f"🔍 URL SAMPLE: First URL: {arxiv_urls[0]}")
                all_paper_urls.update(arxiv_urls)
                
                # DISABLED: Semantic Scholar to avoid rate limiting during testing
                # semantic_papers = await self._search_semantic_scholar(query, limit_per_query)
                # semantic_urls = self._extract_urls_from_papers(semantic_papers)
                # all_paper_urls.update(semantic_urls)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {str(e)}")
                continue
        
        paper_urls = list(all_paper_urls)
        logger.info(f"Found {len(paper_urls)} unique papers from {len(queries)} queries")
        
        return paper_urls[:limit_per_query * len(queries)]  # Limit total results
    
    async def search_for_gap_validation(self, gap_description: str) -> List[str]:
        """
        Execute targeted searches to find papers that might invalidate a research gap.
        
        Args:
            gap_description: Description of the research gap to validate
            
        Returns:
            List of paper URLs that might address the gap
        """
        # Extract key terms from gap description for better search
        key_terms = self._extract_search_terms(gap_description)
        
        # Generate validation-focused queries using key terms
        validation_queries = [
            " ".join(key_terms[:3]),  # Top 3 key terms
            f"{key_terms[0]} {key_terms[1] if len(key_terms) > 1 else 'solution'}",  # Top 2 terms
            f"shadow removal {key_terms[0]}" if "shadow" in gap_description.lower() else f"{key_terms[0]} method",  # Domain specific
        ]
        
        logger.info(f"Searching for papers that might address gap: {gap_description[:100]}...")
        logger.info(f"🔍 SEARCH QUERIES: {validation_queries}")
        
        return await self.search_papers(validation_queries, limit_per_query=3)
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract key search terms from gap description"""
        import re
        
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
            'by', 'from', 'as', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'that', 'which', 'who', 'where', 'when', 'why', 'how', 'this', 'these', 'those',
            'often', 'always', 'never', 'sometimes', 'usually', 'frequently'
        }
        
        # Extract words, remove punctuation, convert to lowercase
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words and get meaningful terms
        key_terms = [word for word in words if word not in stop_words]
        
        # Return top 5 most relevant terms
        return key_terms[:5] if key_terms else ["research", "method"]
    
    async def _search_arxiv(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search ArXiv for papers"""
        try:
            logger.info(f"🔍 ARXIV SEARCH: Searching ArXiv for '{query}' (limit={limit})")
            papers = await self.arxiv_client.search_papers(
                query=query,
                limit=limit,
                filters={"category": "cs"} if "computer" in query.lower() else None
            )
            logger.info(f"🔍 ARXIV RESULTS: Found {len(papers)} papers for '{query}'")
            if papers:
                logger.info(f"🔍 ARXIV SAMPLE: First paper title: {papers[0].get('title', 'No title')}")
            return papers
        except Exception as e:
            logger.error(f"ArXiv search failed for '{query}': {str(e)}")
            import traceback
            logger.error(f"ArXiv search traceback: {traceback.format_exc()}")
            
            # Try fallback direct ArXiv API search
            logger.info("🔄 Trying fallback direct ArXiv search...")
            return await self._fallback_arxiv_search(query, limit)
    
    async def _fallback_arxiv_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback direct ArXiv search using HTTP API"""
        try:
            import httpx
            import xml.etree.ElementTree as ET
            
            # ArXiv API endpoint
            api_url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                papers = []
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns)
                    summary = entry.find('atom:summary', ns)
                    id_elem = entry.find('atom:id', ns)
                    
                    if title is not None and id_elem is not None:
                        arxiv_id = id_elem.text.split('/')[-1]
                        papers.append({
                            "title": title.text.strip(),
                            "abstract": summary.text.strip() if summary is not None else "",
                            "id": arxiv_id,
                            "url": f"https://arxiv.org/abs/{arxiv_id}",
                            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                        })
                
                logger.info(f"🔄 FALLBACK ARXIV: Found {len(papers)} papers for '{query}'")
                return papers
                
        except Exception as e:
            logger.error(f"Fallback ArXiv search also failed: {str(e)}")
            return []
    
    async def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for papers"""
        try:
            papers = await self.semantic_client.search_papers(
                query=query,
                limit=limit
            )
            return papers
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed for '{query}': {str(e)}")
            return []
    
    def _extract_urls_from_papers(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Extract paper URLs from API response"""
        urls = []
        
        for paper in papers:
            # Try to get URL from various possible fields
            url = None
            
            logger.info(f"🔍 PAPER DEBUG: Paper keys = {list(paper.keys())}")
            
            # Check for ArXiv client format (normalized by PaperNormalizer)
            if "paperUrl" in paper:
                url = paper["paperUrl"]
                logger.info(f"🔍 URL FOUND: paperUrl = {url}")
            elif "pdfUrl" in paper:
                url = paper["pdfUrl"]
                logger.info(f"🔍 URL FOUND: pdfUrl = {url}")
            # Check for direct URL formats
            elif "url" in paper:
                url = paper["url"]
                logger.info(f"🔍 URL FOUND: url = {url}")
            elif "pdf_url" in paper:
                url = paper["pdf_url"]
                logger.info(f"🔍 URL FOUND: pdf_url = {url}")
            elif "link" in paper:
                url = paper["link"]
                logger.info(f"🔍 URL FOUND: link = {url}")
            elif "external_ids" in paper and paper["external_ids"]:
                # For Semantic Scholar papers
                external_ids = paper["external_ids"]
                if "ArXiv" in external_ids:
                    url = f"https://arxiv.org/abs/{external_ids['ArXiv']}"
                    logger.info(f"🔍 URL CONSTRUCTED: ArXiv external_id = {url}")
                elif "DOI" in external_ids:
                    url = f"https://doi.org/{external_ids['DOI']}"
                    logger.info(f"🔍 URL CONSTRUCTED: DOI external_id = {url}")
            elif "id" in paper:
                # Construct URL based on source
                paper_id = paper["id"]
                if "arxiv" in str(paper_id).lower():
                    url = f"https://arxiv.org/abs/{paper_id}"
                    logger.info(f"🔍 URL CONSTRUCTED: ArXiv id = {url}")
                else:
                    # Assume it's a DOI or similar
                    url = f"https://doi.org/{paper_id}"
                    logger.info(f"🔍 URL CONSTRUCTED: DOI id = {url}")
            
            if url and self._is_valid_paper_url(url):
                urls.append(url)
                logger.info(f"✅ VALID URL ADDED: {url}")
            elif url:
                logger.warning(f"❌ INVALID URL REJECTED: {url}")
            else:
                logger.warning(f"❌ NO URL FOUND IN PAPER: {paper.get('title', 'No title')}")
        
        logger.info(f"🔍 TOTAL URLS EXTRACTED: {len(urls)} from {len(papers)} papers")
        return urls
    
    def _is_valid_paper_url(self, url: str) -> bool:
        """Check if URL is a valid paper URL"""
        try:
            parsed = urlparse(url)
            
            # Check for common academic domains
            valid_domains = [
                "arxiv.org",
                "doi.org", 
                "semanticscholar.org",
                "pubmed.ncbi.nlm.nih.gov",
                "acm.org",
                "ieee.org",
                "springer.com",
                "elsevier.com",
                "nature.com",
                "science.org"
            ]
            
            domain = parsed.netloc.lower()
            return any(valid_domain in domain for valid_domain in valid_domains)
            
        except Exception:
            return False
    
    async def get_paper_details(self, paper_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.
        
        Args:
            paper_url: URL of the paper
            
        Returns:
            Paper details dictionary or None if not found
        """
        try:
            # Determine source and extract ID
            if "arxiv.org" in paper_url:
                paper_id = paper_url.split("/")[-1]
                return await self.arxiv_client.get_paper_details(paper_id)
            elif "semanticscholar.org" in paper_url:
                paper_id = paper_url.split("/")[-1]
                return await self.semantic_client.get_paper_details(paper_id)
            else:
                # Try Semantic Scholar with the full URL
                return await self.semantic_client.get_paper_details(paper_url)
                
        except Exception as e:
            logger.warning(f"Failed to get details for paper {paper_url}: {str(e)}")
            return None