#!/usr/bin/env python3
"""
Test script for the new Gap Analysis API endpoints.
Demonstrates the async workflow that frontend should follow.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# API base URL (adjust if needed)
BASE_URL = "http://localhost:8000/api/v1/gap-analysis"

async def test_gap_analysis_workflow():
    """
    Test the complete gap analysis workflow:
    1. Submit job
    2. Poll status  
    3. Retrieve results
    """
    
    print("🧪 TESTING GAP ANALYSIS API ENDPOINTS")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        # Step 1: Submit a job
        print("\n📤 Step 1: Submitting gap analysis job...")
        
        submission_data = {
            "url": "https://arxiv.org/pdf/2506.15524",  # Example URL
            "max_papers": 5,  # Small for testing
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
                print(f"   Estimated time: {submission_result['estimated_time_minutes']} minutes")
                print(f"   Message: {submission_result['message']}")
                
            else:
                print(f"❌ Job submission failed: {submit_response.status_code}")
                print(f"   Error: {submit_response.text}")
                return
                
        except Exception as e:
            print(f"❌ Job submission error: {str(e)}")
            return
        
        # Step 2: Poll job status
        print(f"\n🔄 Step 2: Polling job status...")
        
        max_polls = 60  # Poll for up to 10 minutes
        poll_interval = 10  # seconds
        
        for poll_count in range(max_polls):
            try:
                status_response = await client.get(f"{BASE_URL}/status/{job_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]
                    progress = status_data["progress_message"]
                    
                    print(f"   Poll {poll_count + 1}: Status = {status}")
                    print(f"   Progress: {progress}")
                    
                    if status == "completed":
                        print("✅ Job completed successfully!")
                        if "processing_time_seconds" in status_data:
                            print(f"   Processing time: {status_data['processing_time_seconds']:.1f} seconds")
                        break
                        
                    elif status == "failed":
                        print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
                        return
                        
                    elif status in ["pending", "running"]:
                        print(f"   Waiting {poll_interval} seconds before next poll...")
                        await asyncio.sleep(poll_interval)
                        continue
                        
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return
                    
            except Exception as e:
                print(f"❌ Status polling error: {str(e)}")
                await asyncio.sleep(poll_interval)
                continue
        
        else:
            print("⏰ Timeout: Job did not complete within expected time")
            return
        
        # Step 3: Retrieve results
        print(f"\n📊 Step 3: Retrieving results...")
        
        try:
            result_response = await client.get(f"{BASE_URL}/result/{job_id}")
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                
                print("✅ Results retrieved successfully!")
                print("\n📋 ANALYSIS SUMMARY:")
                print(f"   Request ID: {result_data.get('request_id', 'N/A')}")
                print(f"   Validated Gaps: {len(result_data.get('validated_gaps', []))}")
                print(f"   Papers Analyzed: {result_data.get('process_metadata', {}).get('total_papers_analyzed', 'N/A')}")
                print(f"   Gaps Eliminated: {result_data.get('process_metadata', {}).get('gaps_eliminated', 'N/A')}")
                
                # Show first gap as example
                gaps = result_data.get('validated_gaps', [])
                if gaps:
                    first_gap = gaps[0]
                    print(f"\n🎯 EXAMPLE GAP:")
                    print(f"   Title: {first_gap.get('gap_title', 'N/A')}")
                    print(f"   Category: {first_gap.get('category', 'N/A')}")
                    print(f"   Description: {first_gap.get('description', 'N/A')[:100]}...")
                
                # Save full result to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file = f"test_result_{timestamp}.json"
                with open(result_file, 'w') as f:
                    json.dump(result_data, f, indent=2, default=str)
                print(f"\n💾 Full results saved to: {result_file}")
                
            else:
                print(f"❌ Result retrieval failed: {result_response.status_code}")
                print(f"   Error: {result_response.text}")
                
        except Exception as e:
            print(f"❌ Result retrieval error: {str(e)}")

async def test_health_and_info():
    """Test the health and info endpoints"""
    
    print("\n🏥 TESTING HEALTH AND INFO ENDPOINTS")
    print("=" * 40)
    
    async with httpx.AsyncClient() as client:
        
        # Test health endpoint
        try:
            health_response = await client.get(f"{BASE_URL}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print("✅ Health check passed!")
                print(f"   Service: {health_data.get('service', 'N/A')}")
                print(f"   Version: {health_data.get('version', 'N/A')}")
                print(f"   Running jobs: {health_data.get('running_jobs', 'N/A')}")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
        
        # Test info endpoint
        try:
            info_response = await client.get(f"{BASE_URL}/info")
            if info_response.status_code == 200:
                info_data = info_response.json()
                print("\n📖 Service Info:")
                print(f"   Name: {info_data.get('service_name', 'N/A')}")
                print(f"   Description: {info_data.get('description', 'N/A')}")
                print(f"   New Features: {len(info_data.get('new_features', []))} features")
                print(f"   Supported Domains: {len(info_data.get('supported_domains', []))} domains")
            else:
                print(f"❌ Info endpoint failed: {info_response.status_code}")
        except Exception as e:
            print(f"❌ Info endpoint error: {str(e)}")

async def main():
    """Main test function"""
    start_time = time.time()
    
    print(f"🚀 Starting API endpoint tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📝 Make sure the FastAPI server is running on localhost:8000")
    
    # Test health and info first
    await test_health_and_info()
    
    # Then test the full workflow
    await test_gap_analysis_workflow()
    
    total_time = time.time() - start_time
    print(f"\n🏁 All tests completed in {total_time:.1f} seconds")
    print("\n📋 FRONTEND INTEGRATION NOTES:")
    print("   1. POST /submit to start analysis (returns job_id)")
    print("   2. Poll GET /status/{job_id} every 5-10 seconds")
    print("   3. GET /result/{job_id} when status = 'completed'")
    print("   4. Handle errors gracefully with status codes")

if __name__ == "__main__":
    asyncio.run(main())