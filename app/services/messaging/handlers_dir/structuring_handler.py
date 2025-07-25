"""
Message handler for text structuring requests
"""

import logging
from typing import Dict, Any, Optional
from ..base_handler import BaseMessageHandler
from ...structurer.text_structurer import TextStructuringService
from ...websearch.config import AppConfig

logger = logging.getLogger(__name__)


class StructuringMessageHandler(BaseMessageHandler):
    """
    Handles text structuring messages from RabbitMQ.
    
    Receives raw extracted text and transforms it into structured,
    queryable data using AI-powered analysis.
    """
    
    def __init__(self, structuring_service: Optional[TextStructuringService] = None):
        super().__init__()
        self.handler_name = "text_structuring"
        
        # Initialize structuring service
        if structuring_service:
            self.structuring_service = structuring_service
        else:
            config = AppConfig.from_env()
            self.structuring_service = TextStructuringService(
                api_key=config.ai.api_key,
                model_name="gemini-2.0-flash"
            )
    
    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text structuring request message.
        
        Expected message format:
        {
            "correlationId": "uuid-string",
            "paperId": "uuid-string", 
            "extractedText": "raw text content",
            "paperMetadata": {
                "title": "paper title",
                "authors": "author info",
                "source": "source name"
            },
            "requestedBy": "user-email"
        }
        
        Returns structured response with sections, facts, and summaries.
        """
        logger.info(f"🔍 Processing text structuring request: {body.get('correlationId', 'unknown')}")
        
        try:
            # Validate request
            self._validate_structuring_request(body)
            
            # Extract message fields
            correlation_id = body["correlationId"]
            paper_id = body["paperId"]
            extracted_text = body["extractedText"]
            paper_metadata = body.get("paperMetadata", {})
            requested_by = body.get("requestedBy", "system")
            
            # Check if structuring service is ready
            if not self.structuring_service.is_ready():
                # Initialize if not ready
                await self.structuring_service.initialize()
                
                if not self.structuring_service.is_ready():
                    return self._create_error_response(
                        correlation_id, paper_id,
                        "AI service not available for text structuring"
                    )
            
            # Structure the text using AI
            logger.info(f"🤖 Structuring text for paper {paper_id} (length: {len(extracted_text)} chars)")
            
            structured_result = await self.structuring_service.structure_paper_text(
                raw_text=extracted_text,
                paper_metadata=paper_metadata
            )
            
            if not structured_result:
                return self._create_error_response(
                    correlation_id, paper_id,
                    "Failed to structure text - AI service returned no results"
                )
            
            # Create successful response
            response = {
                "status": "COMPLETED",
                "correlationId": correlation_id,
                "paperId": paper_id,
                "sections": structured_result.sections,
                "structuredFacts": structured_result.structured_facts,
                "humanSummary": structured_result.human_summary,
                "metadata": structured_result.metadata,
                "handler": self.handler_name,
                "requestedBy": requested_by,
                "textLength": len(extracted_text),
                "sectionsCount": len(structured_result.sections),
                "processingModel": self.structuring_service.model_name
            }
            
            logger.info(f"✅ Text structuring completed for paper {paper_id} - {len(structured_result.sections)} sections identified")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Text structuring failed: {str(e)}")
            return self._create_error_response(
                body.get("correlationId", "unknown"),
                body.get("paperId", "unknown"),
                str(e)
            )
    
    def _validate_structuring_request(self, body: Dict[str, Any]) -> None:
        """Validate the structuring request message"""
        required_fields = ["correlationId", "paperId", "extractedText"]
        
        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate extracted text is not empty
        extracted_text = body["extractedText"]
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise ValueError("Extracted text is too short for structuring (minimum 50 characters)")
        
        # Validate paper metadata has at least title
        paper_metadata = body.get("paperMetadata", {})
        if not paper_metadata.get("title"):
            logger.warning("Paper metadata missing title - this may affect structuring quality")
    
    def _create_error_response(
        self, 
        correlation_id: str, 
        paper_id: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "status": "FAILED",
            "correlationId": correlation_id,
            "paperId": paper_id,
            "errorMessage": error_message,
            "handler": self.handler_name,
            "sections": [],
            "structuredFacts": {},
            "humanSummary": {},
            "metadata": {}
        }