"""
Background processor for gap analysis jobs.
Handles async processing and job status tracking.
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from pathlib import Path
from enum import Enum

from .orchestrator import GapAnalysisOrchestrator
from .models import GapAnalysisRequest

logger = logging.getLogger(__name__)

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
    Background processor for gap analysis jobs with status tracking.
    """
    
    def __init__(self):
        self.orchestrator = GapAnalysisOrchestrator()
        # Only keep running jobs in memory - everything else is read from disk
        self.running_jobs_tracker: Dict[str, JobInfo] = {}
        
        # Create directories for persistent storage
        self.results_dir = Path("gap_analysis_results")
        self.jobs_dir = Path("gap_analysis_jobs")
        self.results_dir.mkdir(exist_ok=True)
        self.jobs_dir.mkdir(exist_ok=True)
        
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
            job_files = list(self.jobs_dir.glob("job_*.json"))
            result_files = list(self.results_dir.glob("gap_analysis_*.json"))
            
            logger.info(f"🔧 Disk statistics: {len(job_files)} job files, {len(result_files)} result files")
            
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
        """Save job status directly to persistent storage."""
        try:
            job_file = self.jobs_dir / f"job_{job.job_id}.json"
            
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
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save job status for {job.job_id}: {str(e)}")

    def _save_job_status(self, job_id: str):
        """Save job status to persistent storage (for running jobs)."""
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
            job_file = self.jobs_dir / f"job_{job_id}.json"
            if job_file.exists():
                job_file.unlink()
                logger.info(f"Deleted job status file for {job_id}")
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
        
        # Save job to disk immediately
        self._save_job_status_direct(job_info)
        
        logger.info(f"🚀 Gap analysis job {job_id} submitted for URL: {request.url}")
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job by reading directly from disk.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information or None if not found
        """
        try:
            job_file = self.jobs_dir / f"job_{job_id}.json"
            if not job_file.exists():
                return None
                
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            # CRITICAL FIX: Handle backwards compatibility for missing analysis_mode
            if "request" in job_data and "analysis_mode" not in job_data["request"]:
                job_data["request"]["analysis_mode"] = "deep"  # Default for older jobs
            
            # Return the status info directly from file
            status_info = {
                "job_id": job_data["job_id"],
                "status": job_data.get("status", "pending"),
                "created_at": job_data["created_at"],
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
            
        except Exception as e:
            logger.error(f"Failed to read job status from disk for {job_id}: {str(e)}")
            return None
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete analysis result for a completed job by reading from disk.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Complete analysis result or None if not available
        """
        try:
            # First check if job exists and get its status from disk
            job_status = self.get_job_status(job_id)
            if not job_status:
                return None
            
            # Only return results for completed jobs
            if job_status.get("status") != "completed":
                return None
                
            result_file = job_status.get("result_file")
            if not result_file:
                return None
                
            # Load result from disk
            result_path = self.results_dir / result_file
            if result_path.exists():
                with open(result_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Result file {result_file} not found for job {job_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load result for job {job_id}: {str(e)}")
            return None
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent jobs with their status by reading directly from disk.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job status information
        """
        try:
            # Get all job files from disk
            job_files = list(self.jobs_dir.glob("job_*.json"))
            
            # Read job data and sort by creation time
            jobs_data = []
            for job_file in job_files:
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                    
                    # CRITICAL FIX: Handle backwards compatibility for missing analysis_mode
                    if "request" in job_data and "analysis_mode" not in job_data["request"]:
                        job_data["request"]["analysis_mode"] = "deep"  # Default for older jobs
                        logger.info(f"🔄 Added default analysis_mode to job {job_data.get('job_id', 'unknown')} for backwards compatibility")
                    
                    # Add created_at as datetime for sorting
                    job_data['created_at_dt'] = datetime.fromisoformat(job_data['created_at'])
                    jobs_data.append(job_data)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to read job file {job_file}: {str(e)}")
                    logger.error(f"   Job file content: {job_file.read_text()[:500]}...")
                    continue
            
            # Sort by creation time, most recent first
            jobs_data.sort(key=lambda x: x['created_at_dt'], reverse=True)
            
            # Convert to status info format and limit results
            result = []
            for job_data in jobs_data[:limit]:
                job_id = job_data['job_id']
                status_info = self.get_job_status(job_id)
                if status_info:
                    result.append(status_info)
            
            logger.info(f"📊 Listed {len(result)} jobs from disk (out of {len(job_files)} total)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list jobs from disk: {str(e)}")
            return []
    
    async def _process_job(self, job_id: str):
        """
        Process a gap analysis job in the background.
        
        Args:
            job_id: Job identifier
        """
        # Load job from disk
        job_status = self.get_job_status(job_id)
        if not job_status:
            logger.error(f"Job {job_id} not found on disk")
            return
            
        # Create JobInfo for tracking running job
        from .models import GapAnalysisRequest
        request = GapAnalysisRequest(
            url=job_status["url"],
            max_papers=10,  # Will be loaded from request in job file
            validation_threshold=2,
            analysis_mode="deep"
        )
        
        # Load full request from disk
        try:
            job_file = self.jobs_dir / f"job_{job_id}.json"
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            request = GapAnalysisRequest(**job_data["request"])
        except Exception as e:
            logger.error(f"Failed to load job request from disk: {str(e)}")
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
            
            # Save result to file
            result_filename = f"gap_analysis_{job_id}_{int(time.time())}.json"
            result_path = self.results_dir / result_filename
            
            # Convert Pydantic model to dict for JSON serialization
            result_dict = result.model_dump()
            
            with open(result_path, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            # Update job completion
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result_file = result_filename
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