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
    analysis_mode: Optional[str] = "deep"  # "light" or "deep"

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
        # Enhanced input validation
        if not request.url:
            raise HTTPException(
                status_code=400,
                detail="URL is required for gap analysis"
            )
        
        # Validate analysis_mode parameter
        if request.analysis_mode and request.analysis_mode not in ["light", "deep"]:
            raise HTTPException(
                status_code=400,
                detail="analysis_mode must be either 'light' or 'deep'"
            )
        
        # Validate parameter ranges
        if request.max_papers and (request.max_papers < 5 or request.max_papers > 20):
            raise HTTPException(
                status_code=400,
                detail="max_papers must be between 5 and 20"
            )
        
        if request.validation_threshold and (request.validation_threshold < 1 or request.validation_threshold > 5):
            raise HTTPException(
                status_code=400,
                detail="validation_threshold must be between 1 and 5"
            )
        
        # Convert to internal request model
        gap_request = GapAnalysisRequest(
            url=str(request.url),
            max_papers=request.max_papers or 10,
            validation_threshold=request.validation_threshold or 2,
            analysis_mode=request.analysis_mode or "deep"
        )
        
        # Submit job for background processing
        job_id = await background_processor.submit_job(gap_request)
        
        # Estimate processing time based on parameters and analysis mode
        if gap_request.analysis_mode == "light":
            estimated_minutes = 2  # Hard 2-minute limit for light mode
        else:
            estimated_minutes = max(5, (gap_request.max_papers * 0.8) + 3)  # Deep mode estimation
        
        logger.info(f"🎯 Gap analysis job {job_id} submitted for {request.url} (mode: {gap_request.analysis_mode}, papers: {gap_request.max_papers})")
        
        return GapAnalysisSubmissionResponse(
            job_id=job_id,
            status="submitted",
            message="Gap analysis job submitted successfully. Use the job_id to track progress.",
            estimated_time_minutes=int(estimated_minutes)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error submitting gap analysis for {request.url}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: Failed to submit gap analysis job. Please try again or contact support if the problem persists."
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
        # Validate job_id format
        if not job_id or not job_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Job ID is required and cannot be empty"
            )
        
        status_info = background_processor.get_job_status(job_id.strip())
        
        if not status_info:
            logger.warning(f"Job status requested for non-existent job: {job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Gap analysis job '{job_id}' not found. Job may have expired or never existed."
            )
        
        logger.debug(f"Retrieved status for job {job_id}: {status_info['status']}")
        return JobStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting job status for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error: Failed to retrieve job status. Please try again."
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
        # Validate job_id format
        if not job_id or not job_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Job ID is required and cannot be empty"
            )
        
        job_id = job_id.strip()
        
        # First check if job exists and is completed
        status_info = background_processor.get_job_status(job_id)
        
        if not status_info:
            logger.warning(f"Job result requested for non-existent job: {job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Gap analysis job '{job_id}' not found. Job may have expired or never existed."
            )
        
        current_status = status_info["status"]
        
        if current_status == JobStatus.PENDING.value:
            raise HTTPException(
                status_code=202,  # Accepted but not ready
                detail="Gap analysis is still queued for processing. Please check back in a few minutes."
            )
        
        if current_status == JobStatus.RUNNING.value:
            progress = status_info.get('progress_message', 'Processing...')
            raise HTTPException(
                status_code=202,  # Accepted but not ready
                detail=f"Gap analysis is still running. Current phase: {progress}"
            )
        
        if current_status == JobStatus.FAILED.value:
            error_msg = status_info.get('error', 'Unknown error occurred during analysis')
            logger.error(f"Job {job_id} failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Gap analysis failed: {error_msg}"
            )
        
        # Get the actual result
        result = background_processor.get_job_result(job_id)
        
        if not result:
            logger.error(f"Job {job_id} completed but result file not found")
            raise HTTPException(
                status_code=500,
                detail="Gap analysis completed but results are missing. Please try re-running the analysis."
            )
        
        # Validate result structure
        if not isinstance(result, dict) or 'validated_gaps' not in result:
            logger.error(f"Job {job_id} returned invalid result structure")
            raise HTTPException(
                status_code=500,
                detail="Gap analysis completed but returned invalid results. Please try re-running the analysis."
            )
        
        logger.info(f"📊 Gap analysis result retrieved for job {job_id} - {len(result.get('validated_gaps', []))} gaps found")
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting job result for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error: Failed to retrieve gap analysis results. Please try again."
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
        # Count jobs on disk
        job_files = list(background_processor.jobs_dir.glob("job_*.json"))
        
        return {
            "status": "healthy",
            "service": "gap_analysis",
            "running_jobs": background_processor.running_jobs,
            "max_concurrent_jobs": background_processor.max_concurrent_jobs,
            "total_jobs_on_disk": len(job_files),
            "results_directory": str(background_processor.results_dir),
            "jobs_directory": str(background_processor.jobs_dir),
            "architecture": "disk-based (no memory loading needed)"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/debug/reload-jobs")
async def force_reload_jobs():
    """
    DEBUG ENDPOINT: Force reload all jobs from disk.
    
    This endpoint is useful for debugging job persistence issues.
    Use when jobs are missing from memory but exist on disk.
    
    Returns:
        Reload status and statistics
    """
    try:
        result = await background_processor.force_reload_jobs()
        logger.info(f"🔧 Jobs force reloaded via API: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to force reload jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload jobs: {str(e)}"
        )

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
        if job_id in background_processor.running_jobs_tracker:
            job = background_processor.running_jobs_tracker[job_id]
            job.status = JobStatus.FAILED
            job.error_message = "Job cancelled by user"
            job.progress_message = "Job cancelled"
            # Save cancelled status to persistent storage
            background_processor._save_job_status(job_id)
        else:
            # Job is not running, just update the file directly
            job_file = background_processor.jobs_dir / f"job_{job_id}.json"
            if job_file.exists():
                import json
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                job_data['status'] = 'failed'
                job_data['error_message'] = 'Job cancelled by user'
                job_data['progress_message'] = 'Job cancelled'
                with open(job_file, 'w') as f:
                    json.dump(job_data, f, indent=2)
        
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