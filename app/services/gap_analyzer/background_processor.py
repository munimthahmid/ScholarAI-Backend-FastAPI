"""
Background processor for gap analysis jobs.
Handles async processing and job status tracking.
"""

import asyncio
import logging
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4, UUID
from pathlib import Path
from enum import Enum

from .orchestrator import GapAnalysisOrchestrator
from .models import GapAnalysisRequest
from ...db.database import SessionLocal, GapAnalysisJob, GapAnalysisResult

logger = logging.getLogger(__name__)


def clean_json_data(data):
    """Recursively clean JSON data to ensure all datetime objects are serialized"""
    if isinstance(data, dict):
        return {key: clean_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

class JobInfo:
    def __init__(self, job_id: str, request: GapAnalysisRequest):
        self.job_id = job_id
        self.request = request
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.progress_message: str = "Job queued for processing"
        self.result_file: Optional[str] = None

class GapAnalysisBackgroundProcessor:
    """
    Background processor for gap analysis jobs with database persistence.
    """
    
    def __init__(self):
        self.orchestrator = GapAnalysisOrchestrator()
        # Only keep running jobs in memory - everything else is in database
        self.running_jobs_tracker: Dict[str, JobInfo] = {}
        
        logger.info(f"📂 Using PostgreSQL database for gap analysis persistence")
        
        # Track running jobs to prevent overload
        self.max_concurrent_jobs = 2
        self.running_jobs = 0
        
    async def initialize(self):
        """Initialize the orchestrator and B2 client."""
        try:
            await self.orchestrator.initialize()
            logger.info("Gap analysis background processor initialized successfully - jobs will be read from disk on demand")
        except Exception as e:
            logger.error(f"Failed to initialize gap analysis background processor: {str(e)}")
            raise

    async def force_reload_jobs(self):
        """DEBUG: Show statistics about jobs on disk (no longer needed for functionality)."""
        try:
            logger.info(f"🔧 [RELOAD] Starting force reload jobs")
            logger.info(f"💾 [RELOAD] Using database storage for jobs")
            logger.info(f"💾 [RELOAD] Using database storage for jobs and results")
            logger.info(f"💾 [RELOAD] Database connection available")
            
            # Use os.listdir for more reliable file listing
            try:
                # Get job count from database instead of files
                db = SessionLocal()
                try:
                    job_count = db.query(GapAnalysisJob).count()
                    logger.info(f"📊 [RELOAD] Total jobs in database: {job_count}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ [RELOAD] Cannot access database: {str(e)}")
            
            try:
                # Get result count from database instead of files
                db = SessionLocal()
                try:
                    result_count = db.query(GapAnalysisResult).count()
                    logger.info(f"📊 [RELOAD] Total results in database: {result_count}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ [RELOAD] Cannot access database for results: {str(e)}")
            
            logger.info(f"🔧 [RELOAD] Database storage active for jobs and results")
            
            # List some file names for debugging
            if job_files:
                logger.info(f"📄 [RELOAD] Sample job files: {[f.name for f in job_files[:3]]}")
            if result_files:
                logger.info(f"📄 [RELOAD] Sample result files: {[f.name for f in result_files[:3]]}")
            
            # Count jobs by status
            status_counts = {}
            for job_file in job_files:
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                    status = job_data.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                except:
                    status_counts["corrupted"] = status_counts.get("corrupted", 0) + 1
            
            logger.info(f"📊 [RELOAD] Status breakdown: {status_counts}")
            
            return {
                "status": "completed",
                "total_job_files": len(job_files),
                "total_result_files": len(result_files),
                "status_breakdown": status_counts,
                "message": "Jobs are now read directly from disk - no memory loading needed"
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk statistics: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _save_job_status_direct(self, job: JobInfo):
        """Save job status directly to database."""
        try:
            logger.info(f"💾 [SAVE] Attempting to save job {job.job_id} to database")
            
            job_data = {
                "job_id": job.job_id,
                "request": {
                    "url": job.request.url,
                    "max_papers": job.request.max_papers,
                    "validation_threshold": job.request.validation_threshold,
                    "analysis_mode": job.request.analysis_mode
                },
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "progress_message": job.progress_message,
                "result_file": job.result_file
            }
            
            if job.started_at:
                job_data["started_at"] = job.started_at.isoformat()
            if job.completed_at:
                job_data["completed_at"] = job.completed_at.isoformat()
            if job.error_message:
                job_data["error_message"] = job.error_message
            
            db = SessionLocal()
            try:
                job_uuid = UUID(job.job_id)
                
                # Check if job already exists
                existing_job = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_uuid).first()
                
                if existing_job:
                    # Update existing job
                    existing_job.status = job.status.value
                    existing_job.job_data = job_data
                    existing_job.analysis_mode = job.request.analysis_mode
                    logger.info(f"🔄 [SAVE] Updated existing job {job.job_id}")
                else:
                    # Create new job
                    new_job = GapAnalysisJob(
                        id=job_uuid,
                        status=job.status.value,
                        job_data=job_data,
                        analysis_mode=job.request.analysis_mode
                    )
                    db.add(new_job)
                    logger.info(f"➕ [SAVE] Created new job {job.job_id}")
                
                db.commit()
                logger.info(f"✅ [SAVE] Job {job.job_id} saved successfully to database")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ [SAVE] Failed to save job status for {job.job_id}: {str(e)}")
            logger.error(f"❌ [SAVE] Exception type: {type(e).__name__}")
            raise

    def _save_job_status(self, job_id: str):
        """Save job status to database (for running jobs)."""
        try:
            if job_id in self.running_jobs_tracker:
                job = self.running_jobs_tracker[job_id]
                self._save_job_status_direct(job)
            else:
                logger.warning(f"Attempted to save status for non-running job {job_id}")
                
        except Exception as e:
            logger.error(f"Failed to save job status for {job_id}: {str(e)}")

    def _delete_job_status(self, job_id: str):
        """Delete job status from persistent storage."""
        try:
            # Job deletion now handled by database - no file operations needed
            db = SessionLocal()
            try:
                job_uuid = UUID(job_id)
                job = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_uuid).first()
                if job:
                    db.delete(job)
                    db.commit()
                    logger.info(f"Deleted job from database: {job_id}")
                else:
                    logger.warning(f"Job {job_id} not found in database for deletion")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to delete job status for {job_id}: {str(e)}")
        
    async def submit_job(self, request: GapAnalysisRequest) -> str:
        """
        Submit a new gap analysis job for background processing.
        
        Args:
            request: Gap analysis request
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid4())
        job_info = JobInfo(job_id, request)
        
        logger.info(f"🚀 [SUBMIT] Starting job submission for {job_id}")
        logger.info(f"📄 [SUBMIT] URL: {request.url}")
        logger.info(f"💾 [SUBMIT] Using database storage for jobs")
        logger.info(f"💾 [SUBMIT] Using database storage for results")
        
        # Save job to disk immediately
        try:
            self._save_job_status_direct(job_info)
            logger.info(f"✅ [SUBMIT] Job {job_id} saved to disk successfully")
        except Exception as e:
            logger.error(f"❌ [SUBMIT] Failed to save job {job_id} to disk: {str(e)}")
            raise
        
        logger.info(f"🚀 Gap analysis job {job_id} submitted for URL: {request.url}")
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job from database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information or None if not found
        """
        try:
            db = SessionLocal()
            try:
                # Convert string to UUID
                job_uuid = UUID(job_id)
                job = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_uuid).first()
                
                if not job:
                    logger.warning(f"❌ [GET_STATUS] Job not found in database: {job_id}")
                    return None
                
                logger.info(f"✅ [GET_STATUS] Job loaded from database: {job_id}")
                logger.info(f"📄 [GET_STATUS] Job status: {job.status}")
                
                job_data = job.job_data
                
                # Handle backwards compatibility for missing analysis_mode
                if "request" in job_data and "analysis_mode" not in job_data["request"]:
                    job_data["request"]["analysis_mode"] = "deep"
                
                # Return the status info
                status_info = {
                    "job_id": str(job.id),
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "progress_message": job_data.get("progress_message", "Job queued"),
                    "url": job_data["request"]["url"]
                }
                
                if job_data.get("started_at"):
                    status_info["started_at"] = job_data["started_at"]
                    
                if job_data.get("completed_at"):
                    status_info["completed_at"] = job_data["completed_at"]
                    # Calculate processing time
                    if job_data.get("started_at"):
                        started = datetime.fromisoformat(job_data["started_at"])
                        completed = datetime.fromisoformat(job_data["completed_at"])
                        status_info["processing_time_seconds"] = (completed - started).total_seconds()
                    
                if job_data.get("error_message"):
                    status_info["error"] = job_data["error_message"]
                    
                if job_data.get("result_file"):
                    status_info["result_file"] = job_data["result_file"]
                    
                return status_info
                
            finally:
                db.close()
                
        except ValueError:
            logger.error(f"Invalid job ID format: {job_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get job status from database for {job_id}: {str(e)}")
            return None
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete analysis result for a completed job from database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Complete analysis result or None if not available
        """
        try:
            db = SessionLocal()
            try:
                # Convert string to UUID
                job_uuid = UUID(job_id)
                
                # First check if job exists and is completed
                job = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_uuid).first()
                if not job:
                    return None
                
                if job.status != "completed":
                    return None
                
                # Get the result from database
                result = db.query(GapAnalysisResult).filter(GapAnalysisResult.job_id == job_uuid).first()
                if result:
                    return result.result_data
                else:
                    logger.warning(f"No result found in database for job {job_id}")
                    return None
                    
            finally:
                db.close()
                
        except ValueError:
            logger.error(f"Invalid job ID format: {job_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load result from database for job {job_id}: {str(e)}")
            return None
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent jobs with their status from database.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job status information
        """
        try:
            logger.info(f"📋 [LIST_JOBS] Starting to list jobs from database")
            
            db = SessionLocal()
            try:
                # Get jobs ordered by creation time, most recent first
                jobs = db.query(GapAnalysisJob).order_by(GapAnalysisJob.created_at.desc()).limit(limit).all()
                
                logger.info(f"📄 [LIST_JOBS] Found {len(jobs)} jobs in database")
                
                result = []
                for job in jobs:
                    job_data = job.job_data
                    
                    # Handle backwards compatibility for missing analysis_mode
                    if "request" in job_data and "analysis_mode" not in job_data["request"]:
                        job_data["request"]["analysis_mode"] = "deep"
                        logger.info(f"🔄 Added default analysis_mode to job {job.id} for backwards compatibility")
                    
                    # Create status info
                    status_info = {
                        "job_id": str(job.id),
                        "status": job.status,
                        "created_at": job.created_at.isoformat(),
                        "progress_message": job_data.get("progress_message", "Job queued"),
                        "url": job_data["request"]["url"]
                    }
                    
                    if job_data.get("started_at"):
                        status_info["started_at"] = job_data["started_at"]
                        
                    if job_data.get("completed_at"):
                        status_info["completed_at"] = job_data["completed_at"]
                        # Calculate processing time
                        if job_data.get("started_at"):
                            started = datetime.fromisoformat(job_data["started_at"])
                            completed = datetime.fromisoformat(job_data["completed_at"])
                            status_info["processing_time_seconds"] = (completed - started).total_seconds()
                        
                    if job_data.get("error_message"):
                        status_info["error"] = job_data["error_message"]
                        
                    if job_data.get("result_file"):
                        status_info["result_file"] = job_data["result_file"]
                        
                    result.append(status_info)
                
                logger.info(f"📊 Listed {len(result)} jobs from database")
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to list jobs from database: {str(e)}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to list jobs from disk: {str(e)}")
            return []
    
    async def _process_job(self, job_id: str):
        """
        Process a gap analysis job in the background.
        
        Args:
            job_id: Job identifier
        """
        # Load job from database
        job_status = self.get_job_status(job_id)
        if not job_status:
            logger.error(f"Job {job_id} not found in database")
            return
            
        # Load full request from database
        try:
            db = SessionLocal()
            try:
                job_uuid = UUID(job_id)
                job_record = db.query(GapAnalysisJob).filter(GapAnalysisJob.id == job_uuid).first()
                if not job_record:
                    logger.error(f"Job {job_id} not found in database")
                    return
                
                from .models import GapAnalysisRequest
                request = GapAnalysisRequest(**job_record.job_data["request"])
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to load job request from database: {str(e)}")
            return
            
        job = JobInfo(job_id, request)
        job.created_at = datetime.fromisoformat(job_status["created_at"])
        
        # Add to running jobs tracker
        self.running_jobs_tracker[job_id] = job
        
        try:
            # Wait if too many jobs are running
            while self.running_jobs >= self.max_concurrent_jobs:
                await asyncio.sleep(5)
            
            # Start processing
            self.running_jobs += 1
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.progress_message = "Analyzing seed paper and extracting initial gaps..."
            
            # Save status to persistent storage
            self._save_job_status(job_id)
            
            logger.info(f"🔥 Starting gap analysis job {job_id}")
            
            # Phase 1: Paper analysis
            job.progress_message = "Phase 1: Analyzing seed paper structure and content..."
            self._save_job_status(job_id)
            await asyncio.sleep(0.1)  # Allow status updates
            
            # Phase 2: Gap discovery and validation
            job.progress_message = "Phase 2: Discovering research gaps and expanding frontier..."
            self._save_job_status(job_id)
            
            # CRITICAL FIX: Ensure orchestrator state is reset for each new analysis
            # This prevents accumulation of gaps from previous analyses
            logger.info("🔄 Resetting orchestrator state before starting new analysis")
            await self.orchestrator.initialize()
            
            # Run the actual analysis
            result = await self.orchestrator.analyze_research_gaps(job.request)
            
            # Phase 3: Save results
            job.progress_message = "Phase 3: Finalizing analysis and generating comprehensive report..."
            self._save_job_status(job_id)
            
            # Save result to database
            result_dict = result.model_dump()
            
            # Clean the result data to handle datetime objects
            cleaned_result_dict = clean_json_data(result_dict)
            
            # Save result to database
            db = SessionLocal()
            try:
                job_uuid = UUID(job_id)
                
                # Check if result already exists
                existing_result = db.query(GapAnalysisResult).filter(GapAnalysisResult.job_id == job_uuid).first()
                
                if existing_result:
                    # Update existing result
                    existing_result.result_data = cleaned_result_dict
                    logger.info(f"🔄 Updated existing result for job {job_id}")
                else:
                    # Create new result
                    new_result = GapAnalysisResult(
                        job_id=job_uuid,
                        result_data=cleaned_result_dict
                    )
                    db.add(new_result)
                    logger.info(f"💾 Saved new result for job {job_id} to database")
                
                db.commit()
                
            finally:
                db.close()
            
            # Update job completion
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result_file = f"gap_analysis_{job_id}_{int(time.time())}.json"  # Keep for backwards compatibility
            gap_count = len(result.validated_gaps) if result.validated_gaps else 0
            job.progress_message = f"Analysis completed! Found {gap_count} validated research gaps."
            
            # Save final status to persistent storage
            self._save_job_status(job_id)
            
            logger.info(f"✅ Gap analysis job {job_id} completed successfully")
            
        except Exception as e:
            # Handle job failure
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            job.progress_message = f"Analysis failed: {str(e)}"
            
            # Save failure status to persistent storage
            self._save_job_status(job_id)
            
            logger.error(f"❌ Gap analysis job {job_id} failed: {str(e)}")
            
        finally:
            # Remove from running jobs tracker
            if job_id in self.running_jobs_tracker:
                del self.running_jobs_tracker[job_id]
            self.running_jobs -= 1

# Global instance for the FastAPI app
background_processor = GapAnalysisBackgroundProcessor()