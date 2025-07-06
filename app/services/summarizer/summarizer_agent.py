"""
Summarizer Agent for ScholarAI
Uses Gemini 2.0 Flash to create structured paper analysis from extracted text.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

import google.generativeai as genai
from google.generativeai import GenerativeModel


logger = logging.getLogger(__name__)


class SummarizationStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class SummarizationRequest:
    correlation_id: str
    paper_id: str
    extracted_text: str
    paper_metadata: Dict[str, Any]
    requested_by: str = "system"


@dataclass
class StructuredSummary:
    correlation_id: str
    paper_id: str
    author_info: Dict[str, Any]
    abstract: str
    key_insights: List[str]
    methodology: str
    results: str
    conclusions: str
    references: List[str]
    keywords: List[str]
    research_area: str
    limitations: str
    future_work: str
    status: SummarizationStatus
    error_message: Optional[str] = None
    processing_time: Optional[str] = None


class SummarizerAgent:
    """
    Summarizer Agent that uses Gemini 2.0 Flash to analyze and structure academic papers.
    """
    
    def __init__(self, gemini_api_key: str):
        """
        Initialize the Summarizer Agent with Gemini API key.
        
        Args:
            gemini_api_key: API key for Google Gemini
        """
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini 2.0 Flash model
        self.model = GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("🤖 SummarizerAgent initialized with Gemini 2.0 Flash")

    async def summarize_paper(self, paper_content: str, paper_metadata: Dict[str, Any]) -> StructuredSummary:
        """
        Analyze and summarize paper content using Gemini 2.0 Flash.
        
        Args:
            paper_content: Full extracted text from the paper
            paper_metadata: Paper metadata (title, authors, etc.)
            
        Returns:
            StructuredSummary with analyzed content
        """
        try:
            logger.info(f"🔍 Starting summarization for paper: {paper_metadata.get('title', 'Unknown')}")
            
            # Build the analysis prompt
            prompt = self._build_summarization_prompt(paper_content, paper_metadata)
            
            # Call Gemini 2.0 Flash
            logger.info("📡 Calling Gemini 2.0 Flash for analysis...")
            response = await self._call_gemini(prompt)
            
            # Parse and validate the response
            structured_data = self._parse_gemini_response(response)
            
            logger.info("✅ Successfully analyzed paper with Gemini 2.0 Flash")
            return structured_data
            
        except Exception as e:
            logger.error(f"❌ Failed to summarize paper: {str(e)}")
            raise

    async def process_summarization_request(self, request: SummarizationRequest) -> StructuredSummary:
        """
        Process a summarization request.
        
        Args:
            request: SummarizationRequest with paper content and metadata
            
        Returns:
            StructuredSummary with processing results
        """
        logger.info(f"Processing summarization request for paper {request.paper_id}")
        
        try:
            # Perform the summarization
            summary = await self.summarize_paper(request.extracted_text, request.paper_metadata)
            
            # Update the summary with request details
            summary.correlation_id = request.correlation_id
            summary.paper_id = request.paper_id
            summary.status = SummarizationStatus.COMPLETED
            
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed for paper {request.paper_id}: {str(e)}")
            return StructuredSummary(
                correlation_id=request.correlation_id,
                paper_id=request.paper_id,
                author_info={},
                abstract="",
                key_insights=[],
                methodology="",
                results="",
                conclusions="",
                references=[],
                keywords=[],
                research_area="",
                limitations="",
                future_work="",
                status=SummarizationStatus.FAILED,
                error_message=str(e)
            )

    def _build_summarization_prompt(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Build a structured prompt for Gemini 2.0 Flash analysis.
        
        Args:
            content: Full paper text
            metadata: Paper metadata
            
        Returns:
            Formatted prompt string
        """
        return f"""
You are an expert research analyst. Analyze this academic paper and provide a comprehensive structured summary.

Paper Title: {metadata.get('title', 'N/A')}
Authors: {metadata.get('authors', 'N/A')}
DOI: {metadata.get('doi', 'N/A')}
Publication Date: {metadata.get('publication_date', 'N/A')}

Full Paper Content:
{content}

Please analyze this paper thoroughly and provide a JSON response with the following structure:

{{
    "authorInfo": {{
        "primaryAuthors": ["First Author", "Second Author"],
        "affiliations": ["University A", "Institute B"],
        "correspondingAuthor": "email@university.edu"
    }},
    "abstract": "Comprehensive summary of the paper's main contribution",
    "keyInsights": [
        "Key finding 1",
        "Key finding 2", 
        "Key finding 3"
    ],
    "methodology": "Detailed description of the research methodology used",
    "results": "Summary of the main results and findings",
    "conclusions": "Key conclusions and implications",
    "references": [
        "Important reference 1",
        "Important reference 2"
    ],
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "researchArea": "Primary research domain (e.g., Computer Science, Medicine, etc.)",
    "limitations": "Study limitations and constraints",
    "futureWork": "Suggested future research directions"
}}

Requirements:
1. Extract information ONLY from the provided paper content
2. Be comprehensive and accurate
3. Use clear, concise language
4. Include 3-5 key insights that represent the most important findings
5. Identify 5-10 relevant keywords
6. If information is not available in the paper, use empty strings or arrays
7. Ensure all JSON fields are properly formatted

Provide ONLY the JSON response, no additional text.
"""

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini 2.0 Flash with the analysis prompt.
        
        Args:
            prompt: The analysis prompt
            
        Returns:
            Raw response from Gemini
        """
        try:
            # Generate content using Gemini 2.0 Flash
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to call Gemini API: {str(e)}")
            raise

    def _parse_gemini_response(self, response: str) -> StructuredSummary:
        """
        Parse and validate Gemini's JSON response.
        
        Args:
            response: Raw JSON response from Gemini
            
        Returns:
            StructuredSummary object
        """
        try:
            # Clean the response (remove any markdown formatting)
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            data = json.loads(response)
            
            # Create StructuredSummary object
            return StructuredSummary(
                correlation_id="",  # Will be set by the caller
                paper_id="",        # Will be set by the caller
                author_info=data.get("authorInfo", {}),
                abstract=data.get("abstract", ""),
                key_insights=data.get("keyInsights", []),
                methodology=data.get("methodology", ""),
                results=data.get("results", ""),
                conclusions=data.get("conclusions", ""),
                references=data.get("references", []),
                keywords=data.get("keywords", []),
                research_area=data.get("researchArea", ""),
                limitations=data.get("limitations", ""),
                future_work=data.get("futureWork", ""),
                status=SummarizationStatus.COMPLETED
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process Gemini response: {str(e)}")
            raise

    async def get_summarization_status(self, paper_id: str) -> SummarizationStatus:
        """Get the current summarization status for a paper."""
        # This would typically query a database or cache
        # For now, return a default status
        return SummarizationStatus.PENDING