"""
Question-Answering API endpoints for academic papers
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ....services.qa.paper_qa_service import PaperQAService
from ....services.websearch.config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for paper chat"""
    query: str = Field(..., description="User's question about the paper")
    paper_content: str = Field(..., description="Full extracted text of the paper")
    paper_metadata: Dict[str, Any] = Field(default_factory=dict, description="Paper metadata")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Previous conversation messages")


class ChatResponse(BaseModel):
    """Response model for paper chat"""
    response: str = Field(..., description="AI-generated answer")
    success: bool = Field(default=True, description="Whether the request was successful")
    error: str = Field(default="", description="Error message if any")


# Global QA service instance
_qa_service: PaperQAService = None


async def get_qa_service() -> PaperQAService:
    """Dependency to get QA service instance"""
    global _qa_service
    
    if _qa_service is None:
        config = AppConfig.from_env()
        _qa_service = PaperQAService(
            api_key=config.ai.api_key,
            model_name="gemini-2.0-flash"
        )
        await _qa_service.initialize()
    
    return _qa_service


@router.post("/papers/{paper_id}/chat", response_model=ChatResponse)
async def chat_with_paper(
    paper_id: UUID,
    request: ChatRequest,
    qa_service: PaperQAService = Depends(get_qa_service)
):
    """
    Chat with a paper using its extracted content.
    
    This endpoint is called by SpringBoot's PaperQAService to get
    AI-powered answers to questions about academic papers.
    """
    try:
        logger.info(f"QA request received for paper {paper_id}: '{request.query[:50]}...'")
        
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if not request.paper_content.strip():
            raise HTTPException(status_code=400, detail="Paper content cannot be empty")
        
        # Check if QA service is ready
        if not qa_service.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="AI service is not available. Please try again later."
            )
        
        # Get answer from AI service
        answer = await qa_service.answer_question(
            query=request.query,
            paper_content=request.paper_content,
            paper_metadata=request.paper_metadata,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"✅ QA response generated for paper {paper_id}")
        
        return ChatResponse(
            response=answer,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in QA endpoint for paper {paper_id}: {str(e)}")
        return ChatResponse(
            response="I apologize, but I encountered an error while processing your question. Please try again.",
            success=False,
            error=str(e)
        )


@router.get("/qa/health")
async def qa_health_check():
    """Health check endpoint for QA service"""
    try:
        qa_service = await get_qa_service()
        status = qa_service.get_status()
        
        return {
            "status": "healthy" if status["ready"] else "degraded",
            "service": "paper_qa",
            "details": status
        }
    except Exception as e:
        logger.error(f"QA health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "paper_qa",
            "error": str(e)
        }


@router.get("/qa/status")
async def qa_status():
    """Get detailed QA service status"""
    try:
        qa_service = await get_qa_service()
        return qa_service.get_status()
    except Exception as e:
        logger.error(f"Failed to get QA status: {str(e)}")
        return {
            "ai_available": False,
            "initialized": False,
            "ready": False,
            "error": str(e)
        }