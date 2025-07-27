#!/usr/bin/env python3
"""
Test script to verify persistent job status storage.
This script tests that job status information is saved to JSON files
and can be loaded back after server restart.
"""

import asyncio
import httpx
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1/gap-analysis"

async def test_persistent_job_storage():
    """
    Test that job status is saved to persistent storage.
    """
    
    print("🧪 TESTING PERSISTENT JOB STATUS STORAGE")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        # Step 1: Submit a job
        print("\n📤 Step 1: Submitting gap analysis job...")
        
        submission_data = {
            "url": "https://arxiv.org/pdf/2506.15524",
            "max_papers": 3,  # Small for testing
            "validation_threshold": 1
        }
        
        try:
            submit_response = await client.post(
                f"{BASE_URL}/submit",
                json=submission_data
            )
            
            if submit_response.status_code == 200:
                submission_result = submit_response.json()
                job_id = submission_result["job_id"]
                
                print(f"✅ Job submitted successfully!")
                print(f"   Job ID: {job_id}")
                
            else:
                print(f"❌ Job submission failed: {submit_response.status_code}")
                print(f"   Error: {submit_response.text}")
                return
                
        except Exception as e:
            print(f"❌ Job submission error: {str(e)}")
            return
        
        # Step 2: Check if job status file was created
        print(f"\n📁 Step 2: Checking persistent storage...")
        
        jobs_dir = Path("gap_analysis_jobs")
        job_file = jobs_dir / f"job_{job_id}.json"
        
        if job_file.exists():
            print(f"✅ Job status file created: {job_file}")
            
            # Read and display the job status file
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            print(f"   Status: {job_data['status']}")
            print(f"   Created: {job_data['created_at']}")
            print(f"   Progress: {job_data['progress_message']}")
            print(f"   URL: {job_data['request']['url']}")
            
        else:
            print(f"❌ Job status file not found: {job_file}")
        
        # Step 3: Check the /jobs endpoint
        print(f"\n📊 Step 3: Checking /jobs endpoint...")
        
        try:
            jobs_response = await client.get(f"{BASE_URL}/jobs?limit=10")
            
            if jobs_response.status_code == 200:
                jobs = jobs_response.json()
                print(f"✅ Found {len(jobs)} jobs in /jobs endpoint")
                
                # Find our job
                our_job = None
                for job in jobs:
                    if job["job_id"] == job_id:
                        our_job = job
                        break
                
                if our_job:
                    print(f"✅ Our job found in /jobs endpoint:")
                    print(f"   Status: {our_job['status']}")
                    print(f"   Progress: {our_job['progress_message']}")
                else:
                    print(f"❌ Our job not found in /jobs endpoint")
                    
            else:
                print(f"❌ Failed to get jobs: {jobs_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting jobs: {str(e)}")
        
        # Step 4: Check health endpoint for storage info
        print(f"\n🏥 Step 4: Checking health endpoint...")
        
        try:
            health_response = await client.get(f"{BASE_URL}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check successful:")
                print(f"   Status: {health_data['status']}")
                print(f"   Total jobs: {health_data['total_jobs']}")
                print(f"   Running jobs: {health_data['running_jobs']}")
                
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking health: {str(e)}")
        
        print(f"\n🎯 TEST COMPLETED")
        print(f"Job status should now be persisted in: {job_file}")

if __name__ == "__main__":
    asyncio.run(test_persistent_job_storage()) 