#!/usr/bin/env python3
"""
Test script to verify that the /jobs endpoint returns all jobs from persistent storage.
"""

import asyncio
import httpx
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1/gap-analysis"

async def test_jobs_endpoint():
    """
    Test that the /jobs endpoint returns all jobs from persistent storage.
    """
    
    print("🧪 TESTING /JOBS ENDPOINT WITH PERSISTENT STORAGE")
    print("=" * 60)
    
    # First, let's check what job files we have
    jobs_dir = Path("gap_analysis_jobs")
    job_files = list(jobs_dir.glob("job_*.json"))
    
    print(f"📁 Found {len(job_files)} job status files in persistent storage:")
    for job_file in job_files:
        print(f"   - {job_file.name}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test the /jobs endpoint
        print("📊 Testing /jobs endpoint...")
        
        try:
            jobs_response = await client.get(f"{BASE_URL}/jobs?limit=50")
            
            if jobs_response.status_code == 200:
                jobs = jobs_response.json()
                print(f"✅ /jobs endpoint returned {len(jobs)} jobs")
                print()
                
                # Display job details
                for i, job in enumerate(jobs, 1):
                    print(f"Job {i}:")
                    print(f"   ID: {job['job_id']}")
                    print(f"   Status: {job['status']}")
                    print(f"   Created: {job['created_at']}")
                    print(f"   Progress: {job['progress_message']}")
                    print(f"   URL: {job['url'][:80]}...")
                    if job.get('result_file'):
                        print(f"   Result: {job['result_file']}")
                    print()
                
                # Verify that all our job files are represented
                job_ids_from_api = {job['job_id'] for job in jobs}
                job_ids_from_files = {job_file.stem.replace('job_', '') for job_file in job_files}
                
                print("🔍 Verifying job coverage:")
                print(f"   Jobs from API: {len(job_ids_from_api)}")
                print(f"   Jobs from files: {len(job_ids_from_files)}")
                
                missing_in_api = job_ids_from_files - job_ids_from_api
                if missing_in_api:
                    print(f"   ❌ Missing in API: {missing_in_api}")
                else:
                    print(f"   ✅ All job files are represented in API response")
                
                extra_in_api = job_ids_from_api - job_ids_from_files
                if extra_in_api:
                    print(f"   ⚠️  Extra in API (from memory): {extra_in_api}")
                
            else:
                print(f"❌ /jobs endpoint failed: {jobs_response.status_code}")
                print(f"   Error: {jobs_response.text}")
                
        except Exception as e:
            print(f"❌ Error testing /jobs endpoint: {str(e)}")
        
        # Test the health endpoint
        print(f"\n🏥 Testing health endpoint...")
        
        try:
            health_response = await client.get(f"{BASE_URL}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check successful:")
                print(f"   Status: {health_data['status']}")
                print(f"   Total jobs: {health_data['total_jobs']}")
                print(f"   Running jobs: {health_data['running_jobs']}")
                print(f"   Results directory: {health_data['results_directory']}")
                print(f"   Jobs directory: {health_data['jobs_directory']}")
                
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking health: {str(e)}")
        
        print(f"\n🎯 TEST COMPLETED")
        print(f"📊 The /api/v1/gap-analysis/jobs endpoint should now show all {len(job_files)} jobs!")

if __name__ == "__main__":
    asyncio.run(test_jobs_endpoint()) 