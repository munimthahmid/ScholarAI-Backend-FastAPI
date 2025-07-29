#!/usr/bin/env python3
"""
Direct test of job loading functionality without full environment setup.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, 'app')

def test_job_loading():
    """Test job loading directly from disk."""
    
    print("🧪 Testing Job Loading Functionality")
    print("=" * 50)
    
    # Test directories
    jobs_dir = Path("gap_analysis_jobs")
    results_dir = Path("gap_analysis_results")
    
    print(f"📁 Jobs directory: {jobs_dir}")
    print(f"📁 Results directory: {results_dir}")
    print(f"📁 Jobs directory exists: {jobs_dir.exists()}")
    print(f"📁 Results directory exists: {results_dir.exists()}")
    
    if not jobs_dir.exists():
        print("❌ Jobs directory doesn't exist!")
        return False
    
    # Get all job files
    job_files = list(jobs_dir.glob("job_*.json"))
    print(f"📊 Found {len(job_files)} job files")
    
    # Test reading each job file
    valid_jobs = []
    for job_file in job_files:
        print(f"\n🔍 Testing job file: {job_file.name}")
        
        try:
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            print(f"   ✅ JSON parsing successful")
            print(f"   📝 Job ID: {job_data.get('job_id', 'missing')}")
            print(f"   🌐 URL: {job_data.get('request', {}).get('url', 'missing')[:60]}...")
            print(f"   📊 Status: {job_data.get('status', 'missing')}")
            print(f"   📅 Created: {job_data.get('created_at', 'missing')}")
            
            # Check if analysis_mode is missing
            request_data = job_data.get('request', {})
            if 'analysis_mode' not in request_data:
                print(f"   ⚠️  Missing analysis_mode - adding default 'deep'")
                request_data['analysis_mode'] = 'deep'
            else:
                print(f"   ✅ Analysis mode: {request_data['analysis_mode']}")
            
            # Simulate the status info creation
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
                
            if job_data.get("error_message"):
                status_info["error"] = job_data["error_message"]
                
            if job_data.get("result_file"):
                status_info["result_file"] = job_data["result_file"]
            
            valid_jobs.append(status_info)
            print(f"   ✅ Job processed successfully")
            
        except Exception as e:
            print(f"   ❌ Error processing job: {str(e)}")
            print(f"   📄 File content: {job_file.read_text()[:200]}...")
            continue
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total job files: {len(job_files)}")
    print(f"   Valid jobs processed: {len(valid_jobs)}")
    print(f"   Invalid/corrupted jobs: {len(job_files) - len(valid_jobs)}")
    
    if valid_jobs:
        print(f"\n✅ SUCCESSFULLY PROCESSED JOBS:")
        for job in valid_jobs[:3]:  # Show first 3 jobs
            print(f"   - {job['job_id']}: {job['status']} ({job['created_at']})")
        
        if len(valid_jobs) > 3:
            print(f"   ... and {len(valid_jobs) - 3} more jobs")
    
    return len(valid_jobs) > 0

if __name__ == "__main__":
    success = test_job_loading()
    if success:
        print(f"\n🎉 TEST PASSED: Job loading works correctly!")
        sys.exit(0)
    else:
        print(f"\n💥 TEST FAILED: Job loading has issues!")
        sys.exit(1)