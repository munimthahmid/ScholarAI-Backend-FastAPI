"""
🚀 MULTI-SOURCE ACADEMIC PAPER FETCHING AGENT 🚀
Designed to fetch as many relevant papers as possible from multiple academic sources.

Core Purpose:
- Fetch papers from ALL available academic APIs (Semantic Scholar, arXiv, Crossref, PubMed, Google Scholar)
- Smart deduplication across sources
- Optional AI-powered search refinement for additional rounds
- Stack up papers from multiple search iterations

Features:
- Multi-API orchestration for maximum paper coverage
- Intelligent deduplication using multiple identifiers
- Optional Gemini AI analysis for search query refinement
- Iterative search rounds for comprehensive coverage
- Simple, focused approach prioritizing quantity and relevance
"""

import asyncio
import logging
import hashlib
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

try:
    import google.generativeai as genai

    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    import_error = str(e)

from .academic_apis import (
    SemanticScholarClient,
    ArxivClient,
    CrossrefClient,
    PubMedClient,
    GoogleScholarClient,
)

logger = logging.getLogger(__name__)

if not AI_AVAILABLE:
    logger.warning(
        f"Gemini AI not available: {import_error}. Search refinement disabled."
    )


class MultiSourcePaperFetcher:
    """
    🎯 Multi-source academic paper fetching agent.

    Focuses on fetching as many relevant papers as possible from multiple academic sources,
    with optional AI-powered search refinement for additional rounds.
    """

    def __init__(self):
        # Initialize all academic API clients
        self.semantic_scholar = SemanticScholarClient()
        self.arxiv = ArxivClient()
        self.crossref = CrossrefClient()
        self.pubmed = PubMedClient()
        self.google_scholar = GoogleScholarClient()

        # Initialize Gemini AI for search refinement
        self.gemini_client = None
        self.gemini_api_key = "AIzaSyAX4osMXYhYTMUYuDPBGEWAEwbX7VslByg"
        self.gemini_model_name = "gemini-2.0-flash-lite"

        # Paper tracking for deduplication
        self.seen_papers: Set[str] = set()
        self.all_papers: List[Dict[str, Any]] = []

        # Configuration
        self.papers_per_source = 2  # Fetch up to 2 papers per source
        self.max_search_rounds = 2  # Maximum search iterations
        self.enable_ai_refinement = AI_AVAILABLE

    async def initialize_ai(self):
        """Initialize Gemini AI for search refinement"""
        if not AI_AVAILABLE:
            logger.info("🤖 AI not available, search refinement disabled")
            return

        try:
            if self.gemini_client is None:
                logger.info("🤖 Initializing Gemini for search refinement...")
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel(self.gemini_model_name)
                logger.info("✅ Gemini initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.gemini_client = None
            self.enable_ai_refinement = False

    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Main entry point for multi-source paper fetching
        """
        project_id = request_data.get("projectId")
        query_terms = request_data.get("queryTerms", [])
        domain = request_data.get("domain", "Computer Science")
        batch_size = request_data.get("batchSize", 10)
        correlation_id = request_data.get("correlationId")

        logger.info(f"🚀 Starting multi-source paper fetching for project {project_id}")
        logger.info(f"🔍 Query terms: {query_terms}")
        logger.info(f"🏛️ Domain: {domain}")
        logger.info(f"📊 Target batch size: {batch_size}")

        # Initialize AI if available
        await self.initialize_ai()

        # Clear previous search state
        self.seen_papers.clear()
        self.all_papers.clear()

        # Execute multi-round paper fetching
        papers = await self.fetch_papers_multi_round(query_terms, domain, batch_size)

        # Return result
        result = {
            "projectId": project_id,
            "correlationId": correlation_id,
            "papers": papers,
            "batchSize": len(papers),
            "queryTerms": query_terms,
            "domain": domain,
            "status": "COMPLETED",
            "searchStrategy": "multi_source_fetching",
            "totalSourcesUsed": 4,  # 4 academic sources (Google Scholar disabled)
            "aiEnhanced": self.enable_ai_refinement,
            "searchRounds": min(self.max_search_rounds, 2),
        }

        logger.info(f"🎉 Fetched {len(papers)} papers from multiple sources")
        return result

    async def fetch_papers_multi_round(
        self, query_terms: List[str], domain: str, target_size: int
    ) -> List[Dict[str, Any]]:
        """
        🔄 Execute multiple rounds of paper fetching with optional AI refinement
        """
        search_queries = [" ".join(query_terms)]  # Start with original query

        for round_num in range(self.max_search_rounds):
            logger.info(f"📡 Round {round_num + 1}: Fetching papers from all sources")

            # Fetch papers from all sources for current queries
            for query in search_queries:
                round_papers = await self.fetch_from_all_sources(query, domain)
                self.add_papers_with_deduplication(round_papers)

                logger.info(
                    f"Round {round_num + 1}, Query '{query}': Added {len(round_papers)} new papers"
                )

            # Check if we have enough papers
            if len(self.all_papers) >= target_size:
                logger.info(f"✅ Target size reached: {len(self.all_papers)} papers")
                break

            # Generate refined queries for next round using AI (if available and not last round)
            if (
                round_num < self.max_search_rounds - 1
                and self.enable_ai_refinement
                and len(self.all_papers) > 0
            ):

                logger.info("🤖 Generating refined search queries using AI...")
                refined_queries = await self.generate_refined_queries(
                    query_terms, domain, self.all_papers[:10]  # Analyze top 10 papers
                )

                if refined_queries:
                    search_queries = refined_queries
                    logger.info(
                        f"🔍 Generated {len(refined_queries)} refined queries for next round"
                    )
                else:
                    logger.info("No refined queries generated, stopping search")
                    break
            else:
                break

        # Return top papers up to target size
        return self.all_papers[:target_size]

    async def fetch_from_all_sources(
        self, query: str, domain: str
    ) -> List[Dict[str, Any]]:
        """
        📡 Fetch papers from all academic sources in parallel
        """
        logger.info(f"🔍 Fetching papers for query: '{query}'")

        # Define search tasks for all sources
        search_tasks = [
            self.safe_search(
                self.semantic_scholar.search_papers, query, "Semantic Scholar"
            ),
            self.safe_search(self.arxiv.search_papers, query, "arXiv"),
            self.safe_search(self.crossref.search_papers, query, "Crossref"),
            self.safe_search(self.pubmed.search_papers, query, "PubMed"),
            # Note: Google Scholar disabled due to CAPTCHA issues that cause hanging
            # self.safe_search(
            #     self.google_scholar.search_papers, query, "Google Scholar"
            # ),
        ]

        # Execute all searches in parallel
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Combine results from all sources
        all_papers = []
        source_names = [
            "Semantic Scholar",
            "arXiv",
            "Crossref",
            "PubMed",
            # "Google Scholar",  # Disabled due to CAPTCHA issues
        ]

        for i, result in enumerate(results):
            source_name = source_names[i]
            if isinstance(result, Exception):
                logger.warning(f"❌ {source_name} search failed: {str(result)}")
                continue

            if isinstance(result, list) and result:
                logger.info(f"✅ {source_name}: Found {len(result)} papers")
                # Add source information to each paper
                for paper in result:
                    paper["source"] = source_name
                all_papers.extend(result)
            else:
                logger.info(f"ℹ️ {source_name}: No papers found")

        logger.info(f"📊 Total papers fetched from all sources: {len(all_papers)}")
        return all_papers

    async def safe_search(
        self, search_func, query: str, source_name: str
    ) -> List[Dict[str, Any]]:
        """
        🛡️ Safely execute search with error handling
        """
        try:
            # Use domain-specific filters if applicable
            filters = self.get_domain_filters(source_name, query)

            papers = await search_func(
                query=query, limit=self.papers_per_source, filters=filters
            )
            return papers or []
        except Exception as e:
            logger.error(f"Error searching {source_name}: {str(e)}")
            return []

    def get_domain_filters(self, source_name: str, query: str) -> Dict[str, Any]:
        """
        🎯 Get domain-specific filters for better results
        """
        filters = {}

        # Add recent year filter to get more current papers
        current_year = datetime.now().year

        # Different sources need different date formats
        if source_name == "Crossref":
            # Crossref needs separate from/until parameters
            filters["from-pub-date"] = f"{current_year-5}"
            filters["until-pub-date"] = f"{current_year}"
        elif source_name == "PubMed":
            # PubMed uses date_range
            filters["date_range"] = [f"{current_year-5}", f"{current_year}"]
        else:
            # Semantic Scholar, arXiv, Google Scholar use year
            filters["year"] = f"{current_year-5}-{current_year}"

        return filters

    def add_papers_with_deduplication(self, new_papers: List[Dict[str, Any]]):
        """
        🔄 Add papers with smart deduplication
        """
        added_count = 0

        for paper in new_papers:
            # Generate unique identifiers for the paper
            identifiers = self.generate_paper_identifiers(paper)

            # Check if we've seen this paper before
            is_duplicate = False
            for identifier in identifiers:
                if identifier in self.seen_papers:
                    is_duplicate = True
                    break

            if not is_duplicate:
                # Add all identifiers to seen set
                for identifier in identifiers:
                    self.seen_papers.add(identifier)

                # Add paper to collection
                self.all_papers.append(paper)
                added_count += 1

        logger.info(f"➕ Added {added_count} new papers (deduplicated)")

    def generate_paper_identifiers(self, paper: Dict[str, Any]) -> List[str]:
        """
        🔑 Generate multiple identifiers for deduplication
        """
        identifiers = []

        # DOI (most reliable)
        doi = paper.get("doi") or paper.get("DOI")
        if doi:
            identifiers.append(f"doi:{doi.lower().strip()}")

        # Title hash (for papers without DOI)
        title = paper.get("title", "").strip()
        if title:
            title_hash = hashlib.md5(title.lower().encode()).hexdigest()
            identifiers.append(f"title:{title_hash}")

        # arXiv ID
        arxiv_id = paper.get("arxiv_id") or paper.get("arXivId")
        if arxiv_id:
            identifiers.append(f"arxiv:{arxiv_id}")

        # PubMed ID
        pubmed_id = paper.get("pubmed_id") or paper.get("pmid")
        if pubmed_id:
            identifiers.append(f"pubmed:{pubmed_id}")

        # Semantic Scholar ID
        ss_id = paper.get("paperId") or paper.get("semanticScholarId")
        if ss_id:
            identifiers.append(f"ss:{ss_id}")

        return identifiers

    async def generate_refined_queries(
        self,
        original_terms: List[str],
        domain: str,
        sample_papers: List[Dict[str, Any]],
    ) -> List[str]:
        """
        🤖 Use AI to generate refined search queries based on found papers
        """
        if not self.gemini_client:
            return []

        try:
            # Prepare context from sample papers
            paper_context = ""
            for i, paper in enumerate(sample_papers[:5]):  # Use top 5 papers
                title = paper.get("title", "")
                abstract = paper.get("abstract", "")[:200]  # First 200 chars
                paper_context += f"{i+1}. {title}\nAbstract: {abstract}...\n\n"

            # Create prompt for query refinement
            prompt = f"""
Based on the original search terms: {', '.join(original_terms)}
Domain: {domain}

Here are some relevant papers found:
{paper_context}

Generate 2-3 refined search queries that could help find MORE relevant papers in this domain.
The queries should:
1. Use different terminology/synonyms
2. Focus on specific aspects or subtopics
3. Be concise (3-6 words each)

Return only the queries, one per line, without numbering or explanation.
"""

            response = await asyncio.to_thread(
                self.gemini_client.generate_content, prompt
            )

            if response and response.text:
                refined_queries = [
                    line.strip()
                    for line in response.text.strip().split("\n")
                    if line.strip()
                    and not line.strip().startswith(("1.", "2.", "3.", "-", "*"))
                ]
                return refined_queries[:3]  # Max 3 refined queries

        except Exception as e:
            logger.error(f"Error generating refined queries: {str(e)}")

        return []

    async def close(self):
        """🔒 Clean up resources"""
        try:
            await self.semantic_scholar.close()
            await self.arxiv.close()
            await self.crossref.close()
            await self.pubmed.close()
            await self.google_scholar.close()
        except Exception as e:
            logger.error(f"Error closing clients: {str(e)}")


# Alias for backward compatibility
class WebSearchAgent(MultiSourcePaperFetcher):
    """
    🔄 Backward compatibility alias
    """

    pass


# Create global instance
websearch_agent = WebSearchAgent()
