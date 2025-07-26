"""
PaperCall API endpoints for conference calls and journal special issues
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.services.papercall.papercall_service import papercall_service

logger = logging.getLogger(__name__)

router = APIRouter()


class PaperCallResponse(BaseModel):
    """Response model for paper call data"""
    title: str = Field(..., description="Title of the conference/journal special issue")
    link: str = Field(..., description="Link to the call for papers")
    type: str = Field(..., description="Type: 'conference' or 'journal'")
    source: str = Field(..., description="Source: WikiCFP, MDPI, Taylor & Francis, Springer")
    when: Optional[str] = Field(None, description="When the conference is held (for conferences)")
    where: Optional[str] = Field(None, description="Where the conference is held (for conferences)")
    deadline: Optional[str] = Field(None, description="Submission deadline (for conferences)")
    description: Optional[str] = Field(None, description="Description (for journal special issues)")


class StatisticsResponse(BaseModel):
    """Response model for paper call statistics"""
    domain: str = Field(..., description="Research domain searched")
    total_calls: int = Field(..., description="Total number of paper calls found")
    conferences: int = Field(..., description="Number of conference calls")
    journals: int = Field(..., description="Number of journal special issues")
    sources: Dict[str, int] = Field(..., description="Count by source")
    timestamp: str = Field(..., description="Timestamp of the search")


@router.get("/calls", response_model=List[PaperCallResponse], summary="Get All Paper Calls")
async def get_paper_calls(
    domain: str = Query(..., description="Research domain to search for", example="machine learning")
):
    """
    Get all paper calls (conferences and journal special issues) for a given domain.
    
    This endpoint aggregates results from multiple sources:
    - WikiCFP (conferences)
    - MDPI (journal special issues)
    - Taylor & Francis (journal special issues)
    - Springer (journal special issues)
    """
    try:
        logger.info(f"📋 API request: Get all paper calls for domain '{domain}'")
        
        calls = papercall_service.get_paper_calls(domain)
        
        logger.info(f"✅ Found {len(calls)} paper calls for domain '{domain}'")
        return calls
        
    except Exception as e:
        logger.error(f"Error in get_paper_calls API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch paper calls: {str(e)}")


@router.get("/conferences", response_model=List[PaperCallResponse], summary="Get Conference Calls")
async def get_conferences(
    domain: str = Query(..., description="Research domain to search for", example="machine learning")
):
    """
    Get conference calls for papers for a given domain.
    
    Fetches conference information from WikiCFP including:
    - Conference name and link
    - When and where the conference is held
    - Submission deadline
    """
    try:
        logger.info(f"🏛️ API request: Get conferences for domain '{domain}'")
        
        conferences = papercall_service.get_conferences(domain)
        
        logger.info(f"✅ Found {len(conferences)} conferences for domain '{domain}'")
        return conferences
        
    except Exception as e:
        logger.error(f"Error in get_conferences API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conferences: {str(e)}")


@router.get("/journals", response_model=List[PaperCallResponse], summary="Get Journal Special Issues")
async def get_journals(
    domain: str = Query(..., description="Research domain to search for", example="machine learning")
):
    """
    Get journal special issues for a given domain.
    
    Fetches special issue information from:
    - MDPI journals
    - Taylor & Francis journals
    - Springer journals
    """
    try:
        logger.info(f"📚 API request: Get journal special issues for domain '{domain}'")
        
        journals = papercall_service.get_journals(domain)
        
        logger.info(f"✅ Found {len(journals)} journal special issues for domain '{domain}'")
        return journals
        
    except Exception as e:
        logger.error(f"Error in get_journals API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch journals: {str(e)}")


@router.get("/source/{source}", response_model=List[PaperCallResponse], summary="Get Paper Calls by Source")
async def get_paper_calls_by_source(
    source: str = Path(..., description="Source name", example="MDPI"),
    domain: str = Query(..., description="Research domain to search for", example="machine learning")
):
    """
    Get paper calls from a specific source for a given domain.
    
    Available sources:
    - WikiCFP (conferences)
    - MDPI (journal special issues)
    - Taylor & Francis (journal special issues)
    - Springer (journal special issues)
    """
    try:
        logger.info(f"📡 API request: Get paper calls from {source} for domain '{domain}'")
        
        # Validate source
        valid_sources = ["WikiCFP", "MDPI", "Taylor & Francis", "Springer"]
        if source not in valid_sources:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}"
            )
        
        calls = papercall_service.get_paper_calls_by_source(domain, source)
        
        logger.info(f"✅ Found {len(calls)} paper calls from {source} for domain '{domain}'")
        return calls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_paper_calls_by_source API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch from {source}: {str(e)}")


@router.get("/health", summary="PaperCall Service Health Check")
async def health_check():
    """Health check endpoint for PaperCall service"""
    try:
        return {
            "status": "healthy",
            "service": "PaperCall",
            "version": "1.0.0",
            "sources": ["WikiCFP", "MDPI", "Taylor & Francis", "Springer"],
            "endpoints": [
                "/calls",
                "/conferences", 
                "/journals",
                "/statistics"
            ]
        }
    except Exception as e:
        logger.error(f"PaperCall health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "PaperCall",
            "error": str(e)
        } 