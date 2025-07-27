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
        self.jobs: Dict[str, JobInfo] = {}
        self.results_dir = Path("gap_analysis_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Track running jobs to prevent overload
        self.max_concurrent_jobs = 2
        self.running_jobs = 0
        
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
        self.jobs[job_id] = job_info
        
        logger.info(f"🚀 Gap analysis job {job_id} submitted for URL: {request.url}")
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information or None if not found
        """
        if job_id not in self.jobs:
            return None
            
        job = self.jobs[job_id]
        
        status_info = {
            "job_id": job_id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "progress_message": job.progress_message,
            "url": job.request.url
        }
        
        if job.started_at:
            status_info["started_at"] = job.started_at.isoformat()
            
        if job.completed_at:
            status_info["completed_at"] = job.completed_at.isoformat()
            status_info["processing_time_seconds"] = (job.completed_at - job.started_at).total_seconds()
            
        if job.error_message:
            status_info["error"] = job.error_message
            
        if job.result_file:
            status_info["result_file"] = job.result_file
            
        return status_info
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the complete analysis result for a completed job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Complete analysis result or None if not available
        """
        if job_id not in self.jobs:
            return None
            
        job = self.jobs[job_id]
        
        if job.status != JobStatus.COMPLETED or not job.result_file:
            return None
            
        try:
            result_path = self.results_dir / job.result_file
            if result_path.exists():
                with open(result_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load result for job {job_id}: {str(e)}")
            
        return None
    
    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent jobs with their status.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job status information
        """
        # Sort by creation time, most recent first
        sorted_jobs = sorted(
            self.jobs.items(), 
            key=lambda x: x[1].created_at, 
            reverse=True
        )
        
        return [
            self.get_job_status(job_id) 
            for job_id, _ in sorted_jobs[:limit]
        ]
    
    async def _process_job(self, job_id: str):
        """
        Process a gap analysis job in the background.
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs[job_id]
        
        try:
            # Wait if too many jobs are running
            while self.running_jobs >= self.max_concurrent_jobs:
                await asyncio.sleep(5)
            
            # Start processing
            self.running_jobs += 1
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.progress_message = "Analyzing seed paper and extracting initial gaps..."
            
            logger.info(f"🔥 Starting gap analysis job {job_id}")
            
            # Phase 1: Paper analysis
            job.progress_message = "Phase 1: Analyzing seed paper structure and content..."
            await asyncio.sleep(0.1)  # Allow status updates
            
            # Phase 2: Gap discovery and validation
            job.progress_message = "Phase 2: Discovering research gaps and expanding frontier..."
            
            # Run the actual analysis
            result = await self.orchestrator.analyze_research_gaps(job.request)
            
            # Phase 3: Save results
            job.progress_message = "Phase 3: Finalizing analysis and generating comprehensive report..."
            
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
            job.progress_message = f"Analysis completed! Found {len(result.validated_gaps)} validated research gaps."
            
            logger.info(f"✅ Gap analysis job {job_id} completed successfully")
            
        except Exception as e:
            # Handle job failure
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            job.progress_message = f"Analysis failed: {str(e)}"
            
            logger.error(f"❌ Gap analysis job {job_id} failed: {str(e)}")
            
        finally:
            self.running_jobs -= 1

# Global instance for the FastAPI app
background_processor = GapAnalysisBackgroundProcessor()