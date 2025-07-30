#!/usr/bin/env python3
"""
Test script to run a full gap analysis and identify where fallback messages appear.
"""

import asyncio
import json
import time
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator
from app.services.gap_analyzer.models import GapAnalysisRequest
from app.core.config import settings

async def test_full_gap_analysis():
    """Test a full gap analysis to identify where fallback messages come from."""
    
    print("🧪 TESTING FULL GAP ANALYSIS")
    print("=" * 50)
    
    # Check API key status
    print(f"\n🔑 API Key Status:")
    print(f"   API Key exists: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"   API Key preview: {settings.GEMINI_API_KEY[:10]}..." if settings.GEMINI_API_KEY else "None")
    
    # Create orchestrator
    print("\n🎯 Creating Gap Analysis Orchestrator...")
    orchestrator = GapAnalysisOrchestrator()
    
    # Initialize orchestrator
    print("\n🔄 Initializing orchestrator...")
    try:
        await orchestrator.initialize()
        print("   ✅ Orchestrator initialized successfully")
    except Exception as e:
        print(f"   ❌ Orchestrator initialization failed: {str(e)}")
        return
    
    # Create a test request
    print("\n📋 Creating test request...")
    request = GapAnalysisRequest(
        url="https://f003.backblazeb2.com/b2api/v3/b2_download_file_by_id?fileId=4_z64a715e19e4932e197750a19_f1150354a5122dcca_d20250729_m123552_c003_v0312024_t0024_u01753792552180",
        max_papers=6,
        validation_threshold=1,
        analysis_mode="light"
    )
    
    # Using actual paper URL from the request
    
    print("\n🚀 Starting full gap analysis...")
    start_time = time.time()
    
    try:
        # Run the full gap analysis using the actual request
        response = await orchestrator.analyze_research_gaps(request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Analysis completed in {duration:.2f} seconds")
        
        if response:
            print("   ✅ Gap analysis completed successfully")
            print(f"   Validated gaps count: {len(response.validated_gaps)}")
            print(f"   AI models used: {response.ai_models_used}")
            
            # Check for fallback messages in the response
            response_text = json.dumps(response.model_dump(), indent=2, default=str)
            
            if "GEMINI API KEY EXHAUSTED" in response_text:
                print("   ⚠️ Response contains 'GEMINI API KEY EXHAUSTED' messages")
                print("   This indicates API failures during the analysis")
                
                # Count occurrences
                exhaustion_count = response_text.count("GEMINI API KEY EXHAUSTED")
                print(f"   Number of exhaustion messages: {exhaustion_count}")
                
                # Show where they appear
                lines = response_text.split('\n')
                for i, line in enumerate(lines):
                    if "GEMINI API KEY EXHAUSTED" in line:
                        print(f"   Line {i+1}: {line.strip()}")
            else:
                print("   ✅ No fallback messages found - API worked throughout")
            
            # Show sample gaps
            if response.validated_gaps:
                print(f"\n📊 Sample validated gaps:")
                for i, gap in enumerate(response.validated_gaps[:2]):
                    print(f"   Gap {i+1}: {gap.gap_title}")
                    print(f"   Description: {gap.description[:100]}...")
                    print(f"   Confidence: {gap.confidence_score}")
                    print()
        else:
            print("   ❌ Gap analysis failed")
            
    except Exception as e:
        print(f"   ❌ Gap analysis error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Full gap analysis test completed!")

if __name__ == "__main__":
    asyncio.run(test_full_gap_analysis()) 