"""
Summarization Message Handler for ScholarAI
Handles RabbitMQ messages for paper summarization requests.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from app.services.messaging.base_handler import BaseMessageHandler
from app.services.summarizer.summarizer_agent import (
    SummarizerAgent, 
    SummarizationRequest,
    SummarizationStatus
)
from app.config import get_settings


logger = logging.getLogger(__name__)


class SummarizationMessageHandler(BaseMessageHandler):
    """
    Handler for summarization request messages.

    Processes paper summarization requests using the SummarizerAgent.
    """

    def __init__(
        self,
        summarizer_agent: SummarizerAgent = None,
    ):
        super().__init__()
        settings = get_settings()
        self.summarizer_agent = summarizer_agent or SummarizerAgent(
            gemini_api_key=settings.gemini_api_key
        )

    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process summarization request message.

        Args:
            body: Request body containing summarization parameters

        Returns:
            Summarization results with structured content
        """
        # Debug: Log the incoming message body
        logger.info(f"🔍 Received summarization message body: {body}")
        
        # Validate required fields
        self._validate_summarization_request(body)

        # Create summarization request
        summarization_request = SummarizationRequest(
            correlation_id=body.get("correlationId", ""),
            paper_id=body["paperId"],
            extracted_text=body["extractedText"],
            paper_metadata=body.get("paperMetadata", {}),
            requested_by=body.get("requestedBy", "system"),
        )

        # Process the summarization request
        result = await self.summarizer_agent.process_summarization_request(
            summarization_request
        )

        # Print summarization success details
        if result.status == SummarizationStatus.COMPLETED:
            print(f"\n🎉 SUMMARIZATION SUCCESS for paper {result.paper_id}")
            print(f"📄 Research Area: {result.research_area}")
            print(f"🔍 Key Insights: {len(result.key_insights)} insights extracted")
            print(f"📝 Abstract Length: {len(result.abstract)} characters")
            print(f"🏷️ Keywords: {', '.join(result.keywords[:5])}{'...' if len(result.keywords) > 5 else ''}")
            print(f"{'='*80}\n")

        # Convert result to dictionary for messaging
        result_dict = {
            "correlationId": result.correlation_id,
            "paperId": str(result.paper_id),  # Ensure UUID is sent as string
            "authorInfo": result.author_info,
            "abstract": result.abstract,
            "keyInsights": result.key_insights,
            "methodology": result.methodology,
            "results": result.results,
            "conclusions": result.conclusions,
            "references": result.references,
            "keywords": result.keywords,
            "researchArea": result.research_area,
            "limitations": result.limitations,
            "futureWork": result.future_work,
            "status": result.status.value,
            "errorMessage": result.error_message,
            "handler": self.handler_name,
            "processing_time": self._get_processing_time(),
        }

        return result_dict

    def _validate_summarization_request(self, body: Dict[str, Any]):
        """
        Validate summarization request body.

        Args:
            body: Request body to validate

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ["paperId", "extractedText"]

        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")

        # Validate extracted text is not empty
        if not body["extractedText"] or not body["extractedText"].strip():
            raise ValueError("extractedText cannot be empty")

        # Validate paper ID format
        paper_id = body["paperId"]
        if not isinstance(paper_id, str) or len(paper_id.strip()) == 0:
            raise ValueError("paperId must be a non-empty string")

    def _get_processing_time(self) -> str:
        """Get current processing timestamp."""
        return datetime.now().isoformat()

    @property
    def handler_name(self) -> str:
        """Return the handler name for logging."""
        return "SummarizationMessageHandler"