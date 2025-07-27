"""
API routes for Gap Analysis service.
Provides endpoints for submitting, tracking, and retrieving gap analysis results.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import logging

from ...services.gap_analyzer.models import GapAnalysisRequest
from ...services.gap_analyzer.background_processor import background_processor, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gap-analysis", tags=["Gap Analysis"])

class GapAnalysisSubmissionRequest(BaseModel):
    """Request model for submitting gap analysis"""
    url: HttpUrl
    max_papers: Optional[int] = 10
    validation_threshold: Optional[int] = 2

class GapAnalysisSubmissionResponse(BaseModel):
    """Response when submitting gap analysis"""
    job_id: str
    status: str
    message: str
    estimated_time_minutes: int

class JobStatusResponse(BaseModel):
    """Response for job status queries"""
    job_id: str
    status: str
    created_at: str
    progress_message: str
    url: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    error: Optional[str] = None
    result_file: Optional[str] = None

@router.post("/submit", response_model=GapAnalysisSubmissionResponse)
async def submit_gap_analysis(request: GapAnalysisSubmissionRequest):
    """
    Submit a new gap analysis job for background processing.
    
    The analysis will run asynchronously and you can check progress using the job_id.
    
    Args:
        request: Gap analysis parameters including paper URL
        
    Returns:
        Job submission confirmation with tracking ID
    """
    try:
        # Convert to internal request model
        gap_request = GapAnalysisRequest(
            url=str(request.url),
            max_papers=request.max_papers or 10,
            validation_threshold=request.validation_threshold or 2
        )
        
        # Submit job for background processing
        job_id = await background_processor.submit_job(gap_request)
        
        # Estimate processing time based on parameters
        estimated_minutes = max(3, (gap_request.max_papers * 0.8) + 2)
        
        logger.info(f"🎯 Gap analysis job {job_id} submitted for {request.url}")
        
        return GapAnalysisSubmissionResponse(
            job_id=job_id,
            status="submitted",
            message="Gap analysis job submitted successfully. Use the job_id to track progress.",
            estimated_time_minutes=int(estimated_minutes)
        )
        
    except Exception as e:
        logger.error(f"Failed to submit gap analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit gap analysis: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a gap analysis job.
    
    Args:
        job_id: The job identifier returned from submit endpoint
        
    Returns:
        Current job status and progress information
    """
    try:
        status_info = background_processor.get_job_status(job_id)
        
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        return JobStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    """
    Get the complete analysis result for a completed job.
    
    Args:
        job_id: The job identifier returned from submit endpoint
        
    Returns:
        Complete gap analysis result with all research intelligence
    """
    try:
        # First check if job exists and is completed
        status_info = background_processor.get_job_status(job_id)
        
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        if status_info["status"] == JobStatus.PENDING.value:
            raise HTTPException(
                status_code=202,  # Accepted but not ready
                detail="Job is still pending. Please check back later."
            )
        
        if status_info["status"] == JobStatus.RUNNING.value:
            raise HTTPException(
                status_code=202,  # Accepted but not ready
                detail=f"Job is still running. Progress: {status_info['progress_message']}"
            )
        
        if status_info["status"] == JobStatus.FAILED.value:
            raise HTTPException(
                status_code=500,
                detail=f"Job failed: {status_info.get('error', 'Unknown error')}"
            )
        
        # Get the actual result
        result = background_processor.get_job_result(job_id)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Job completed but result file not found"
            )
        
        logger.info(f"📊 Gap analysis result retrieved for job {job_id}")
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job result: {str(e)}"
        )

@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_recent_jobs(limit: int = 20):
    """
    List recent gap analysis jobs with their status.
    
    Args:
        limit: Maximum number of jobs to return (default: 20, max: 100)
        
    Returns:
        List of recent jobs with status information
    """
    try:
        # Limit the number of jobs returned
        limit = min(limit, 100)
        
        jobs = background_processor.list_jobs(limit)
        
        return [JobStatusResponse(**job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )

@router.get("/health")
async def gap_analysis_health():
    """
    Health check endpoint for gap analysis service.
    
    Returns:
        Service health information
    """
    try:
        return {
            "status": "healthy",
            "service": "gap_analysis",
            "running_jobs": background_processor.running_jobs,
            "max_concurrent_jobs": background_processor.max_concurrent_jobs,
            "total_jobs": len(background_processor.jobs),
            "results_directory": str(background_processor.results_dir),
            "jobs_directory": str(background_processor.jobs_dir)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running or pending gap analysis job.
    
    Args:
        job_id: The job identifier to cancel
        
    Returns:
        Cancellation confirmation
    """
    try:
        status_info = background_processor.get_job_status(job_id)
        
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        if status_info["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job that is already {status_info['status']}"
            )
        
        # Mark job as failed to effectively cancel it
        if job_id in background_processor.jobs:
            job = background_processor.jobs[job_id]
            job.status = JobStatus.FAILED
            job.error_message = "Job cancelled by user"
            job.progress_message = "Job cancelled"
            # Save cancelled status to persistent storage
            background_processor._save_job_status(job_id)
        
        logger.info(f"🚫 Gap analysis job {job_id} cancelled")
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )