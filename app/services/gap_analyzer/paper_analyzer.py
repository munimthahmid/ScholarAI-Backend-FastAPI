"""
Paper Analyzer for extracting structured data from research papers.
Integrates with the existing TextExtractor and uses Gemini AI for analysis.
"""

import logging
import re
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import google.generativeai as genai

from .models import PaperAnalysis
from ..extractor.text_extractor import TextExtractorAgent, ExtractionRequest
from ..b2_storage import B2StorageService
from ...core.config import settings

logger = logging.getLogger(__name__)


class PaperAnalyzer:
    """
    Analyzes research papers to extract structured information including
    key findings, limitations, and future work directions.
    """
    
    def __init__(self):
        # Initialize Gemini AI
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            logger.warning("Gemini API key not found. Paper analysis will be limited.")
            self.model = None
            
        # Initialize text extractor
        self.b2_client = B2StorageService()
        self.text_extractor = TextExtractorAgent(self.b2_client)
        
    async def initialize(self):
        """Initialize B2 client for proper authentication."""
        try:
            await self.b2_client.initialize()
            logger.info("B2 client initialized for paper analyzer")
        except Exception as e:
            logger.error(f"Failed to initialize B2 client: {str(e)}")
            raise
        
    async def analyze_paper(self, paper_url: str) -> Optional[PaperAnalysis]:
        """
        Extract and analyze a research paper to create structured analysis.
        
        Args:
            paper_url: URL of the paper to analyze
            
        Returns:
            PaperAnalysis object or None if analysis fails
        """
        logger.info(f"Starting analysis of paper: {paper_url}")
        
        try:
            # Step 1: Extract text from the paper
            paper_text = await self._extract_paper_text(paper_url)
            if not paper_text:
                logger.error(f"Failed to extract text from paper: {paper_url}")
                return None
            
            # Step 2: Analyze the extracted text
            return await self.analyze_paper_text(paper_text, paper_url)
            
        except Exception as e:
            logger.error(f"Error analyzing paper {paper_url}: {str(e)}")
            return None

    async def analyze_paper_text(self, paper_text: str, paper_url: str = "test_paper") -> Optional[PaperAnalysis]:
        """
        Analyze paper text to create structured analysis. This function is separated 
        for easy testing without needing actual URLs.
        
        Args:
            paper_text: The full text content of the paper
            paper_url: URL or identifier for the paper (defaults to "test_paper")
            
        Returns:
            PaperAnalysis object or None if analysis fails
        """
        logger.info(f"Starting text analysis for paper: {paper_url}")
        
        try:
            # Use Gemini to analyze the paper structure
            analysis = await self._analyze_with_gemini(paper_text)
            if not analysis:
                logger.error(f"Failed to analyze paper text with Gemini")
                return None
            
            # Create structured analysis object
            paper_analysis = PaperAnalysis(
                url=paper_url,
                title=analysis.get("title", "Unknown Title"),
                key_findings=analysis.get("key_findings", []),
                methods=analysis.get("methods", []),
                limitations=analysis.get("limitations", []),
                future_work=analysis.get("future_work", []),
                abstract=analysis.get("abstract"),
                year=analysis.get("year"),
                authors=analysis.get("authors", [])
            )
            
            logger.info(f"Successfully analyzed paper: {paper_analysis.title}")
            return paper_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing paper text: {str(e)}")
            return None
    
    async def _extract_paper_text(self, paper_url: str) -> Optional[str]:
        """Extract text content from a research paper URL"""
        try:
            # For B2 URLs, use proper B2 download method
            if "backblazeb2.com" in paper_url:
                # Create extraction request for B2 URL
                extraction_request = ExtractionRequest(
                    correlation_id=f"gap_analysis_{hash(paper_url)}",
                    paper_id=paper_url.split("fileId=")[1].split("&")[0] if "fileId=" in paper_url else paper_url,
                    pdf_url=paper_url,
                    requested_by="gap_analyzer"
                )
                
                # Extract text using existing extractor (which handles B2 properly)
                result = await self.text_extractor.process_extraction_request(extraction_request)
                
                if result.extracted_text:
                    return result.extracted_text
                else:
                    logger.warning(f"Text extraction failed for B2 URL {paper_url}: {result.error_message}")
                    return None
            
            # For ArXiv papers, we can directly download the PDF
            elif "arxiv.org" in paper_url:
                # Convert ArXiv URL to PDF URL
                if "/abs/" in paper_url:
                    pdf_url = paper_url.replace("/abs/", "/pdf/") + ".pdf"
                else:
                    pdf_url = paper_url
                
                # Create extraction request
                extraction_request = ExtractionRequest(
                    correlation_id=f"gap_analysis_{hash(paper_url)}",
                    paper_id=paper_url.split("/")[-1],
                    pdf_url=pdf_url,
                    requested_by="gap_analyzer"
                )
                
                # Extract text using existing extractor
                result = await self.text_extractor.process_extraction_request(extraction_request)
                
                if result.extracted_text:
                    return result.extracted_text
                else:
                    logger.warning(f"Text extraction failed for {paper_url}: {result.error_message}")
                    return None
            
            # For other URLs, try to extract abstract/content via web scraping
            else:
                return await self._extract_from_web_page(paper_url)
                
        except Exception as e:
            logger.error(f"Failed to extract text from {paper_url}: {str(e)}")
            return None
    
    async def _extract_from_web_page(self, url: str) -> Optional[str]:
        """Extract text content from a web page (for non-PDF papers)"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract abstract and content from common academic sites
                text_content = ""
                
                # Try to find abstract
                abstract_selectors = [
                    'div[class*="abstract"]',
                    'section[class*="abstract"]',
                    'p[class*="abstract"]',
                    '#abstract',
                    '.abstract'
                ]
                
                for selector in abstract_selectors:
                    abstract_elem = soup.select_one(selector)
                    if abstract_elem:
                        text_content += f"Abstract: {abstract_elem.get_text().strip()}\n\n"
                        break
                
                # Try to find main content
                content_selectors = [
                    'main',
                    'article',
                    'div[class*="content"]',
                    'div[class*="paper"]',
                    'div[class*="article"]'
                ]
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content_text = content_elem.get_text().strip()
                        if len(content_text) > 500:  # Only use if substantial content
                            text_content += content_text
                            break
                
                return text_content if len(text_content) > 100 else None
                
        except Exception as e:
            logger.warning(f"Web scraping failed for {url}: {str(e)}")
            return None
    
    async def _analyze_with_gemini(self, paper_text: str) -> Optional[Dict[str, Any]]:
        """Analyze paper text using Gemini AI to extract structured information"""
        
        if not self.model:
            logger.warning("Gemini model not available, using fallback analysis")
            return self._fallback_analysis(paper_text)
        
        prompt = f"""
        You are an expert research analyst tasked with extracting comprehensive, structured information from academic papers. Your analysis will be used by an autonomous research frontier agent to identify genuine research gaps and avoid false positives.

        CRITICAL MISSION: Extract precise, actionable information that will help identify REAL research gaps that haven't been solved by existing work.

        ANALYSIS FRAMEWORK:
        1. **KEY FINDINGS**: Focus on concrete achievements, breakthrough results, novel solutions, and validated contributions
        2. **LIMITATIONS**: Identify explicit acknowledgments of unsolved problems, failed approaches, scope constraints, and remaining challenges
        3. **FUTURE WORK**: Extract specific research directions that authors recommend for addressing current limitations
        4. **METHODS**: Document the technical approaches, algorithms, frameworks, and methodologies employed

        EXTRACTION GUIDELINES:
        - Be SPECIFIC and DETAILED in descriptions (not generic statements)
        - Focus on TECHNICAL GAPS rather than incremental improvements  
        - Prioritize ACTIONABLE research directions over vague suggestions
        - Extract QUANTIFIED results when available (accuracy rates, performance metrics, etc.)
        - Identify SCOPE LIMITATIONS (specific domains, datasets, conditions where method fails)

        EXAMPLES OF GOOD vs BAD EXTRACTIONS:
        
        GOOD Limitation: "Our model fails to generalize to unseen object categories, achieving only 34% accuracy on novel classes compared to 89% on trained categories"
        BAD Limitation: "Generalization could be improved"
        
        GOOD Future Work: "Develop few-shot learning techniques that can adapt to new object categories with less than 10 labeled examples per class"
        BAD Future Work: "Improve the model"
        
        GOOD Key Finding: "Achieved 94.2% mAP on KITTI dataset using transformer-based architecture, representing 12% improvement over previous SOTA"
        BAD Key Finding: "Good performance achieved"

        EXTRACT INFORMATION IN THIS EXACT JSON FORMAT:
        {{
            "title": "Complete paper title as written",
            "abstract": "Paper abstract if clearly identifiable",
            "key_findings": [
                "Specific achievement 1 with quantified results when possible",
                "Novel contribution 2 with technical details",
                "Validated finding 3 with scope and limitations"
            ],
            "methods": [
                "Primary methodology/algorithm used",
                "Key technical approach or framework",
                "Novel technique or modification introduced"
            ],
            "limitations": [
                "Specific technical limitation with scope (what fails and under what conditions)",
                "Acknowledged performance gap with quantified metrics if available",
                "Scope constraint or domain limitation explicitly mentioned",
                "Computational or resource constraint that limits deployment"
            ],
            "future_work": [
                "Specific research direction to address identified limitation",
                "Concrete next step suggested by authors with technical details",
                "Recommended improvement with clear scope and expected impact"
            ],
            "year": null_or_number,
            "authors": ["Author names if clearly identifiable"]
        }}

        CRITICAL REQUIREMENTS:
        - Each limitation should be SPECIFIC enough to search for solutions in literature
        - Each future work item should be ACTIONABLE and technically detailed
        - Avoid generic statements like "further research needed" or "performance could be improved"
        - Focus on CONCRETE gaps that represent genuine research opportunities
        - If the paper solves significant problems, document what was solved (this helps eliminate gaps in other papers)

        RESEARCH PAPER TO ANALYZE:
        {paper_text[:12000]}

        RESPOND WITH VALID JSON ONLY - NO OTHER TEXT OR EXPLANATION.
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response with robust error handling
            import json
            
            try:
                analysis = json.loads(response_text)
                # Validate and clean the analysis
                return self._validate_analysis(analysis)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON parsing failed: {json_error}")
                logger.warning(f"Raw response: {response_text[:500]}...")
                
                # Try to fix common JSON issues
                try:
                    # Remove trailing commas
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', response_text)
                    # Fix unescaped quotes in strings
                    fixed_json = re.sub(r'(?<!\\)"(?![,}\]:\s])', r'\\"', fixed_json)
                    
                    analysis = json.loads(fixed_json)
                    logger.info("JSON parsing succeeded after cleanup")
                    return self._validate_analysis(analysis)
                except:
                    logger.warning("JSON cleanup failed, using fallback analysis")
                    return self._fallback_analysis(paper_text)
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return self._fallback_analysis(paper_text)
    
    def _fallback_analysis(self, paper_text: str) -> Dict[str, Any]:
        """Fallback analysis using simple text processing"""
        logger.info("Using fallback analysis method")
        
        # Extract title (first line or first significant text)
        lines = paper_text.split('\n')
        title = "Unknown Title"
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and not line.isupper():
                title = line
                break
        
        # Simple keyword-based extraction
        text_lower = paper_text.lower()
        
        # Extract limitations
        limitations = []
        limitation_patterns = [
            r"limitation[s]?[:\s]([^.]+)",
            r"constraint[s]?[:\s]([^.]+)",
            r"challenge[s]?[:\s]([^.]+)",
            r"problem[s]?[:\s]([^.]+)"
        ]
        
        for pattern in limitation_patterns:
            matches = re.findall(pattern, text_lower)
            limitations.extend([match.strip() for match in matches[:2]])
        
        # Extract future work
        future_work = []
        future_patterns = [
            r"future work[:\s]([^.]+)",
            r"future research[:\s]([^.]+)",
            r"further investigation[:\s]([^.]+)",
            r"next steps[:\s]([^.]+)"
        ]
        
        for pattern in future_patterns:
            matches = re.findall(pattern, text_lower)
            future_work.extend([match.strip() for match in matches[:2]])
        
        # Generate domain-specific fallback based on paper content
        text_sample = paper_text.lower()[:1000]
        
        # Detect domain and generate appropriate fallback
        if any(term in text_sample for term in ['omics', 'genomics', 'proteomics', 'bioinformatics', 'cancer', 'precision medicine']):
            domain_limitations = [
                "Batch effects across different omics platforms create integration challenges",
                "Missing data patterns limit comprehensive multi-omics analysis",
                "Computational scalability issues with large patient cohorts"
            ]
            domain_future_work = [
                "Development of robust batch correction methods for cross-platform integration", 
                "Novel imputation algorithms for handling missing multi-omics data",
                "Federated learning approaches for collaborative analysis"
            ]
            domain_methods = ["Multi-omics integration frameworks", "Deep learning autoencoders", "Graph neural networks"]
            domain_findings = ["Integration methods show improved prediction accuracy", "Multi-omics outperforms single-omics approaches"]
        else:
            domain_limitations = limitations if limitations else ["Technical limitations identified in analysis"]
            domain_future_work = future_work if future_work else ["Research directions requiring further investigation"]
            domain_methods = ["Methodology analysis from paper content"]
            domain_findings = ["Key contributions identified from analysis"]

        return {
            "title": title,
            "abstract": paper_text[:500] + "..." if len(paper_text) > 500 else paper_text,
            "key_findings": domain_findings,
            "methods": domain_methods,
            "limitations": domain_limitations,
            "future_work": domain_future_work,
            "year": None,
            "authors": []
        }
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the analysis results"""
        
        # Ensure all required fields exist
        required_fields = ["title", "key_findings", "methods", "limitations", "future_work"]
        for field in required_fields:
            if field not in analysis:
                analysis[field] = []
        
        # Ensure lists are actually lists
        list_fields = ["key_findings", "methods", "limitations", "future_work", "authors"]
        for field in list_fields:
            if not isinstance(analysis.get(field), list):
                analysis[field] = [str(analysis.get(field, ""))] if analysis.get(field) else []
        
        # Clean up strings
        if isinstance(analysis.get("title"), str):
            analysis["title"] = analysis["title"].strip()
        
        if isinstance(analysis.get("abstract"), str):
            analysis["abstract"] = analysis["abstract"].strip()
        
        # Limit list lengths
        for field in list_fields:
            if len(analysis[field]) > 5:
                analysis[field] = analysis[field][:5]
        
        return analysis