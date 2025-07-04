"""
Extraction Message Handler for ScholarAI
Handles text extraction requests via RabbitMQ messaging.
"""

import json
import logging
from typing import Dict, Any

from aio_pika import IncomingMessage

from ..base_handler import BaseMessageHandler
from ...extractor.text_extractor import (
    TextExtractorAgent,
    ExtractionRequest,
    ExtractionStatus,
)
from ...b2_storage import B2StorageService

logger = logging.getLogger(__name__)


class ExtractionMessageHandler(BaseMessageHandler):
    """
    Handler for text extraction request messages.

    Processes PDF text extraction requests using the TextExtractorAgent.
    """

    def __init__(
        self,
        extractor_agent: TextExtractorAgent = None,
        b2_client: B2StorageService = None,
    ):
        super().__init__()
        self.b2_client = b2_client or B2StorageService()
        self.extractor_agent = extractor_agent or TextExtractorAgent(self.b2_client)

    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text extraction request message.

        Args:
            body: Request body containing extraction parameters

        Returns:
            Extraction results with text content and metadata
        """
        # Debug: Log the incoming message body
        logger.info(f"🔍 Received message body: {body}")
        
        # Validate required fields
        self._validate_extraction_request(body)

        # Create extraction request
        extraction_request = ExtractionRequest(
            correlation_id=body.get("correlationId", ""),
            paper_id=body["paperId"],
            pdf_url=body["pdfUrl"],
            requested_by=body.get("requestedBy", "system"),
        )

        # Process the extraction request
        result = await self.extractor_agent.process_extraction_request(
            extraction_request
        )

        # Convert result to dictionary for messaging
        result_dict = {
            "correlationId": result.correlation_id,
            "paperId": str(result.paper_id),  # Ensure UUID is sent as string
            "extractedText": result.extracted_text,
            "status": result.status.value,
            "errorMessage": result.error_message,
            "extractionMethod": result.extraction_method,
            "textLength": result.text_length,
            "handler": self.handler_name,
            "processing_time": self._get_processing_time(),
        }

        return result_dict

    def _validate_extraction_request(self, body: Dict[str, Any]):
        """
        Validate extraction request body.

        Args:
            body: Request body to validate

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ["paperId", "pdfUrl"]

        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")

        # Validate paperId is a string
        if not isinstance(body["paperId"], str) or not body["paperId"].strip():
            raise ValueError("paperId must be a non-empty string")

        # Validate pdfUrl is a string
        if not isinstance(body["pdfUrl"], str) or not body["pdfUrl"].strip():
            raise ValueError("pdfUrl must be a non-empty string")

        # Validate optional correlationId
        if "correlationId" in body and not isinstance(body["correlationId"], str):
            raise ValueError("correlationId must be a string")

    def _get_processing_time(self) -> str:
        """Get current timestamp for processing time tracking"""
        from datetime import datetime

        return datetime.now().isoformat()

    async def close(self):
        """Clean up handler resources"""
        if hasattr(self.extractor_agent, "close"):
            await self.extractor_agent.close()
        if hasattr(self.b2_client, "close"):
            await self.b2_client.close()
