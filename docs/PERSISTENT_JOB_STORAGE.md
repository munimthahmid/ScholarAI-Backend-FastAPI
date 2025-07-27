# Persistent Job Status Storage

## Overview

The gap analysis service now includes persistent storage for job status information. This ensures that job status is preserved across server restarts and provides better reliability for long-running analysis jobs.

## Storage Structure

### Directories

- **`gap_analysis_results/`** - Stores the actual analysis results (JSON files)
- **`gap_analysis_jobs/`** - Stores job status information (JSON files)

### File Naming Convention

- **Results**: `gap_analysis_{job_id}_{timestamp}.json`
- **Job Status**: `job_{job_id}.json`

## Job Status File Structure

Each job status file contains:

```json
{
  "job_id": "uuid-string",
  "request": {
    "url": "https://arxiv.org/pdf/...",
    "max_papers": 10,
    "validation_threshold": 2
  },
  "status": "pending|running|completed|failed",
  "created_at": "2024-01-01T12:00:00",
  "progress_message": "Job queued for processing",
  "result_file": "gap_analysis_uuid_timestamp.json",
  "started_at": "2024-01-01T12:01:00",
  "completed_at": "2024-01-01T12:05:00",
  "error_message": "Error details if failed"
}
```

## Implementation Details

### Background Processor Changes

The `GapAnalysisBackgroundProcessor` class has been enhanced with:

1. **Persistent Storage Initialization**:
   ```python
   self.jobs_dir = Path("gap_analysis_jobs")
   self.jobs_dir.mkdir(exist_ok=True)
   ```

2. **Job Status Loading on Startup**:
   ```python
   async def _load_existing_jobs(self):
       # Loads all existing job status files on server startup
   ```

3. **Automatic Status Saving**:
   ```python
   def _save_job_status(self, job_id: str):
       # Saves job status to JSON file whenever it changes
   ```

### Key Methods

- **`_save_job_status(job_id)`** - Saves current job state to persistent storage
- **`_load_existing_jobs()`** - Loads all existing jobs on startup
- **`_delete_job_status(job_id)`** - Removes job status file (for cleanup)

### Status Persistence Points

Job status is automatically saved at these key points:

1. **Job Submission** - When a new job is created
2. **Job Start** - When processing begins
3. **Phase Updates** - During each processing phase
4. **Job Completion** - When analysis finishes successfully
5. **Job Failure** - When analysis encounters an error
6. **Job Cancellation** - When user cancels a job

## API Endpoints

### Health Check

The health endpoint now includes information about both storage directories:

```json
{
  "status": "healthy",
  "service": "Autonomous Research Frontier Agent",
  "version": "2.0.0",
  "running_jobs": 1,
  "max_concurrent_jobs": 2,
  "total_jobs": 5,
  "results_directory": "gap_analysis_results",
  "jobs_directory": "gap_analysis_jobs",
  "features": [
    "Async background processing",
    "Job status tracking", 
    "Result persistence",
    "Persistent job status storage",
    "Multi-omics gap analysis",
    "Bioinformatics support"
  ]
}
```

### Jobs List

The `/api/v1/gap-analysis/jobs` endpoint now returns data from persistent storage, ensuring jobs are available even after server restarts.

## Benefits

1. **Reliability** - Job status survives server restarts
2. **Debugging** - Complete job history available for troubleshooting
3. **Monitoring** - Persistent job tracking for operational insights
4. **Recovery** - Ability to resume interrupted jobs
5. **Audit Trail** - Complete record of all analysis attempts

## File Management

### Automatic Cleanup

Currently, job status files are not automatically cleaned up. Consider implementing:

1. **Age-based cleanup** - Remove files older than X days
2. **Size-based cleanup** - Limit total storage usage
3. **Status-based cleanup** - Remove completed/failed jobs after X days

### Manual Cleanup

To manually clean up old job files:

```bash
# Remove job status files older than 30 days
find gap_analysis_jobs -name "job_*.json" -mtime +30 -delete

# Remove result files older than 30 days  
find gap_analysis_results -name "gap_analysis_*.json" -mtime +30 -delete
```

## Testing

Use the provided test script to verify persistent storage:

```bash
python test_persistent_jobs.py
```

This script will:
1. Submit a test job
2. Verify job status file creation
3. Check the `/jobs` endpoint
4. Display health information

## Migration Notes

- Existing jobs in memory will be lost on first restart after this update
- New jobs will be automatically persisted
- No manual migration required for new jobs 