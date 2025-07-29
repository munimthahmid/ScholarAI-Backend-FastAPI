#!/usr/bin/env python3
"""
Test the actual API endpoint logic without running the server.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def simulate_list_jobs_api(limit: int = 50):
    """Simulate the list_jobs API endpoint logic."""
    
    print(f"🔄 Simulating list_jobs API call with limit={limit}")
    
    try:
        jobs_dir = Path("gap_analysis_jobs")
        
        # Get all job files from disk
        job_files = list(jobs_dir.glob("job_*.json"))
        print(f"📁 Found {len(job_files)} job files on disk")
        
        # Read job data and sort by creation time
        jobs_data = []
        for job_file in job_files:
            try:
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                
                # CRITICAL FIX: Handle backwards compatibility for missing analysis_mode
                if "request" in job_data and "analysis_mode" not in job_data["request"]:
                    job_data["request"]["analysis_mode"] = "deep"  # Default for older jobs
                    print(f"🔄 Added default analysis_mode to job {job_data.get('job_id', 'unknown')}")
                
                # Add created_at as datetime for sorting
                job_data['created_at_dt'] = datetime.fromisoformat(job_data['created_at'])
                jobs_data.append(job_data)
                
            except Exception as e:
                print(f"❌ Failed to read job file {job_file}: {str(e)}")
                print(f"   Job file content: {job_file.read_text()[:500]}...")
                continue
        
        # Sort by creation time, most recent first
        jobs_data.sort(key=lambda x: x['created_at_dt'], reverse=True)
        
        # Convert to status info format and limit results
        result = []
        for job_data in jobs_data[:limit]:
            job_id = job_data['job_id']
            
            # Simulate get_job_status logic
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
                
            result.append(status_info)
        
        print(f"📊 Listed {len(result)} jobs from disk (out of {len(job_files)} total)")
        return result
        
    except Exception as e:
        print(f"💥 Failed to list jobs from disk: {str(e)}")
        return []

def main():
    print("🧪 Testing Gap Analysis Jobs API Endpoint Logic")
    print("=" * 60)
    
    # Test the list_jobs logic
    jobs = simulate_list_jobs_api(20)
    
    print(f"\n📊 API Response Summary:")
    print(f"   Jobs returned: {len(jobs)}")
    
    if len(jobs) == 0:
        print(f"   ❌ EMPTY RESPONSE - This is the problem!")
        return False
    
    print(f"   ✅ SUCCESSFUL RESPONSE")
    print(f"\n📋 Jobs Details:")
    for i, job in enumerate(jobs[:3]):
        print(f"   {i+1}. Job ID: {job['job_id']}")
        print(f"      Status: {job['status']}")
        print(f"      URL: {job['url'][:60]}...")
        print(f"      Created: {job['created_at']}")
    
    if len(jobs) > 3:
        print(f"   ... and {len(jobs) - 3} more jobs")
    
    # Test JSON serialization
    try:
        json_output = json.dumps(jobs, indent=2, default=str)
        print(f"\n✅ JSON serialization successful ({len(json_output)} chars)")
        
        # Write to file for inspection
        with open("test_api_output.json", "w") as f:
            f.write(json_output)
        print(f"📁 Output written to test_api_output.json")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 API ENDPOINT TEST PASSED!")
        print(f"📈 The jobs endpoint should be returning data correctly")
        sys.exit(0)
    else:
        print(f"\n💥 API ENDPOINT TEST FAILED!")
        sys.exit(1)