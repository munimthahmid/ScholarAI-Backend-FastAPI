"""
AI-powered text structuring service for academic papers

This service uses Gemini 2.0 Flash to transform raw extracted text into structured,
queryable data including sections, facts, and metadata.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check for AI availability
try:
    import google.generativeai as genai

    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    AI_IMPORT_ERROR = str(e)
    logger.warning(
        f"Gemini AI not available: {AI_IMPORT_ERROR}. Text structuring disabled."
    )


@dataclass
class StructuredText:
    """
    Structured representation of an academic paper
    """

    # Raw sections with boundaries
    sections: List[Dict[str, Any]]

    # Structured facts (machine-readable)
    structured_facts: Dict[str, Any]

    # Human-friendly summary with proper fields
    human_summary: Dict[str, Any]

    # Processing metadata
    metadata: Dict[str, Any]


class TextStructuringService:
    """
    Service for AI-powered academic paper text structuring using Google's Gemini.

    Transforms raw extracted text into structured data including:
    - Section boundaries and content
    - Machine-readable structured facts
    - Human-friendly summaries
    - Metadata extraction
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self.is_initialized = False
        self.is_available = AI_AVAILABLE

        if not AI_AVAILABLE:
            logger.warning("Text structuring service initialized but AI not available")

    async def initialize(self) -> bool:
        """
        Initialize the Gemini AI client.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.is_available:
            logger.info("🤖 AI not available, text structuring disabled")
            return False

        try:
            logger.info("🤖 Initializing Gemini for text structuring...")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            self.is_initialized = True
            logger.info("✅ Gemini initialized successfully for text structuring")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.client = None
            self.is_initialized = False
            self.is_available = False
            return False

    async def structure_paper_text(
        self, raw_text: str, paper_metadata: Dict[str, Any]
    ) -> Optional[StructuredText]:
        """
        Structure raw paper text into organized, queryable format.

        Args:
            raw_text: Raw extracted text from PDF
            paper_metadata: Paper metadata (title, authors, etc.)

        Returns:
            StructuredText object with sections, facts, and summaries
        """
        if not self.is_available or not self.is_initialized:
            logger.debug("AI structuring not available")
            return None

        if not raw_text or len(raw_text.strip()) < 100:
            logger.debug("Text too short for structuring")
            return None

        try:
            logger.info("🤖 Structuring paper text with Gemini...")

            # Generate sections
            sections = await self._extract_sections(raw_text, paper_metadata)

            # Generate structured facts
            structured_facts = await self._extract_structured_facts(
                raw_text, paper_metadata
            )

            # Generate human summary
            human_summary = await self._generate_human_summary(raw_text, paper_metadata)

            # Extract metadata
            metadata = await self._extract_metadata(raw_text, paper_metadata)

            result = StructuredText(
                sections=sections,
                structured_facts=structured_facts,
                human_summary=human_summary,
                metadata=metadata,
            )

            logger.info("✅ Text structuring completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error structuring text: {str(e)}")
            return None

    async def _extract_sections(
        self, raw_text: str, paper_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract section boundaries and organize content by sections"""

        prompt = f"""
You are an expert at analyzing academic paper structure. 

Paper Title: {paper_metadata.get('title', 'Unknown')}
Authors: {paper_metadata.get('authors', 'Unknown')}

Please analyze this academic paper text and identify the main sections with their content.

Text:
{raw_text[:8000]}

Return a JSON array of sections with this exact format:
[
  {{
    "heading": "Abstract",
    "content": "actual section content here",
    "start_position": 0,
    "end_position": 200,
    "word_count": 45
  }},
  {{
    "heading": "Introduction", 
    "content": "actual section content here",
    "start_position": 201,
    "end_position": 800,
    "word_count": 120
  }}
]

Common academic sections include: Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion, References.
Return ONLY the JSON array, no other text, not even a single space or new line or anything else.
"""

        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            logger.debug(f"🤖 Gemini response object: {response}")
            
            if response and response.text:
                response_text = response.text.strip()
                logger.debug(f"🤖 Gemini response text: '{response_text[:500]}...'")
                
                # Strip markdown code block markers if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
                
                # Clean problematic characters for JSON parsing
                response_text = self._clean_json_text(response_text)
                
                # Parse JSON response
                sections_data = json.loads(response_text)
                return sections_data if isinstance(sections_data, list) else []
            else:
                logger.error(f"❌ Empty or invalid Gemini response: response={response}, text={getattr(response, 'text', 'N/A')}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in sections: {str(e)}. Response text: '{getattr(response, 'text', 'N/A')}'")
        except Exception as e:
            logger.error(f"❌ Error extracting sections: {str(e)}")

        return []

    async def _extract_structured_facts(
        self, raw_text: str, paper_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract machine-readable structured facts"""

        prompt = f"""
You are an expert at extracting structured data from academic papers.

Paper Title: {paper_metadata.get('title', 'Unknown')}
Authors: {paper_metadata.get('authors', 'Unknown')}

Extract structured facts from this academic paper:

Text:
{raw_text[:10000]}

Return a JSON object with this exact structure - fill in ALL fields accurately:
{{
  "abstract": "extracted or refined abstract text",
  "authors": [
    {{
      "name": "Author Name",
      "affiliation": "University/Organization",
      "email": "email if found"
    }}
  ],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "research_area": "Computer Science/Machine Learning/Physics/Biology/etc",
  "methodology": {{
    "approach": "detailed description of the method/algorithm",
    "datasets": ["dataset1", "dataset2"],
    "evaluation_metrics": ["accuracy", "precision", "recall", "F1"],
    "tools_technologies": ["tool1", "framework1", "language1"],
    "experimental_setup": "brief description of how experiments were conducted"
  }},
  "key_findings": [
    "finding 1: specific result with numbers if available",
    "finding 2: specific result with numbers if available",
    "finding 3: specific result with numbers if available"
  ],
  "main_contributions": [
    "contribution 1: what was novel/new",
    "contribution 2: what was novel/new",
    "contribution 3: what was novel/new"
  ],
  "results_performance": {{
    "main_metrics": {{
      "metric1": "value1",
      "metric2": "value2"
    }},
    "baseline_comparison": "how it compares to existing methods",
    "significance": "statistical significance or improvement percentage"
  }},
  "limitations": [
    "limitation 1: specific constraint or weakness",
    "limitation 2: specific constraint or weakness"
  ],
  "future_work": "detailed description of suggested future research directions",
  "technical_details": {{
    "model_architecture": "description if applicable",
    "computational_complexity": "time/space complexity if mentioned",
    "implementation_details": "important implementation notes"
  }},
  "citations_references": {{
    "total_references": 0,
    "key_citations": ["Author et al. 2023", "Smith et al. 2022"],
    "related_work_summary": "brief summary of how this relates to existing work"
  }}
}}

Extract ALL information accurately from the paper. If information is not available for a field, use appropriate empty values (empty string, empty array, etc.) but try to extract as much as possible.

Return ONLY the JSON object, no other text, not even a single space or new line or anything else.
"""

        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            logger.debug(f"🤖 Gemini facts response object: {response}")
            
            if response and response.text:
                response_text = response.text.strip()
                logger.debug(f"🤖 Gemini facts response text: '{response_text[:500]}...'")
                
                # Strip markdown code block markers if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
                
                # Clean problematic characters for JSON parsing
                response_text = self._clean_json_text(response_text)
                
                # Parse JSON response
                facts_data = json.loads(response_text)
                return facts_data if isinstance(facts_data, dict) else {}
            else:
                logger.error(f"❌ Empty or invalid Gemini facts response: response={response}, text={getattr(response, 'text', 'N/A')}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in structured facts: {str(e)}. Response text: '{getattr(response, 'text', 'N/A')}'")
        except Exception as e:
            logger.error(f"❌ Error extracting structured facts: {str(e)}")

        return {}

    async def _generate_human_summary(
        self, raw_text: str, paper_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate human-friendly structured summary"""

        prompt = f"""
You are an expert research analyst. Create a structured summary of this academic paper.

Paper Title: {paper_metadata.get('title', 'Unknown')}
Authors: {paper_metadata.get('authors', 'Unknown')}

Text:
{raw_text[:10000]}

Create a JSON summary with this exact structure:
{{
  "problem_motivation": "1-2 sentence description of the problem and why it matters",
  "key_contributions": [
    "bullet point contribution 1",
    "bullet point contribution 2"
  ],
  "method_overview": "short paragraph describing the approach or methodology",
  "data_experimental_setup": "description of datasets, baselines, experimental protocol",
  "headline_results": [
    {{
      "metric": "accuracy",
      "baseline": "85%", 
      "proposed": "92%",
      "improvement": "7%"
    }}
  ],
  "limitations_failure_modes": [
    "limitation 1",
    "limitation 2"
  ],
  "practical_implications_next_steps": "how to use these results and future research directions"
}}

Return ONLY the JSON object, no other text.
"""

        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            logger.debug(f"🤖 Gemini summary response object: {response}")
            
            if response and response.text:
                response_text = response.text.strip()
                logger.debug(f"🤖 Gemini summary response text: '{response_text[:500]}...'")
                
                # Strip markdown code block markers if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
                
                # Clean problematic characters for JSON parsing
                response_text = self._clean_json_text(response_text)
                
                # Parse JSON response
                summary_data = json.loads(response_text)
                return summary_data if isinstance(summary_data, dict) else {}
            else:
                logger.error(f"❌ Empty or invalid Gemini summary response: response={response}, text={getattr(response, 'text', 'N/A')}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in human summary: {str(e)}. Response text: '{getattr(response, 'text', 'N/A')}'")
        except Exception as e:
            logger.error(f"❌ Error generating human summary: {str(e)}")

        return {}

    async def _extract_metadata(
        self, raw_text: str, paper_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract additional metadata from the paper"""

        # Calculate basic text statistics
        word_count = len(raw_text.split())
        char_count = len(raw_text)

        # Estimate reading time (average 200 words per minute)
        estimated_reading_time = max(1, word_count // 200)

        return {
            "text_statistics": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_reading_time_minutes": estimated_reading_time,
            },
            "processing_info": {
                "structuring_model": self.model_name,
                "structure_version": "1.0",
            },
            "quality_indicators": {
                "has_abstract": "abstract" in raw_text.lower(),
                "has_references": "references" in raw_text.lower()
                or "bibliography" in raw_text.lower(),
                "has_methodology": any(
                    term in raw_text.lower()
                    for term in ["method", "approach", "algorithm", "experiment"]
                ),
                "has_results": any(
                    term in raw_text.lower()
                    for term in ["result", "finding", "evaluation", "performance"]
                ),
            },
        }

    def is_ready(self) -> bool:
        """Check if the AI service is ready to use"""
        return self.is_available and self.is_initialized

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "ai_available": self.is_available,
            "initialized": self.is_initialized,
            "model_name": self.model_name,
            "ready": self.is_ready(),
        }

    def _clean_json_text(self, text: str) -> str:
        """
        Clean text to make it valid JSON by handling problematic characters.
        
        Args:
            text: Raw text that may contain problematic characters
            
        Returns:
            Cleaned text safe for JSON parsing
        """
        import re
        
        # Replace problematic Unicode characters with ASCII equivalents
        replacements = {
            'ﬁ': 'fi',  # Unicode ligature
            'ﬂ': 'fl',  # Unicode ligature
            '`': "'",   # Backtick to apostrophe
            '"': '"',   # Smart quote to regular quote
            '"': '"',   # Smart quote to regular quote
            ''': "'",   # Smart apostrophe to regular apostrophe
            ''': "'",   # Smart apostrophe to regular apostrophe
            '–': '-',   # En dash to hyphen
            '—': '-',   # Em dash to hyphen
            '…': '...',  # Ellipsis to three dots
        }
        
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
        
        # Remove or replace other control characters (except allowed ones like \n, \t)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text

    async def close(self):
        """Clean up resources"""
        self.client = None
        self.is_initialized = False
        logger.info("🔒 Text structuring service closed")
