#!/usr/bin/env python3
"""
Test script to verify API key behavior and identify why fallback messages appear incorrectly.
"""

import asyncio
import json
import os
from app.services.gap_analyzer.paper_analyzer import PaperAnalyzer
from app.services.gap_analyzer.gap_validator import GapValidator
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator
from app.core.config import settings

async def test_api_key_behavior():
    """Test the current API key behavior to identify issues."""
    
    print("🧪 TESTING API KEY BEHAVIOR")
    print("=" * 50)
    
    # Check current API key status
    print(f"\n🔑 Current API Key Status:")
    print(f"   API Key exists: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"   API Key length: {len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0}")
    print(f"   API Key preview: {settings.GEMINI_API_KEY[:10]}..." if settings.GEMINI_API_KEY else "None")
    
    # Test 1: Paper Analyzer Initialization
    print("\n📄 Test 1: Paper Analyzer Initialization")
    paper_analyzer = PaperAnalyzer()
    print(f"   Model available: {'Yes' if paper_analyzer.model else 'No'}")
    print(f"   Model type: {type(paper_analyzer.model).__name__ if paper_analyzer.model else 'None'}")
    
    # Test 2: Gap Validator Initialization
    print("\n🔍 Test 2: Gap Validator Initialization")
    gap_validator = GapValidator()
    print(f"   Model available: {'Yes' if gap_validator.model else 'No'}")
    print(f"   Model type: {type(gap_validator.model).__name__ if gap_validator.model else 'None'}")
    
    # Test 3: Orchestrator Initialization
    print("\n🎯 Test 3: Orchestrator Initialization")
    orchestrator = GapAnalysisOrchestrator()
    print(f"   Model available: {'Yes' if orchestrator.model else 'No'}")
    print(f"   Model type: {type(orchestrator.model).__name__ if orchestrator.model else 'None'}")
    
    # Test 4: Simulate API Call (if model is available)
    if paper_analyzer.model:
        print("\n🤖 Test 4: Simulate API Call")
        try:
            # Test with a simple prompt
            test_prompt = "Hello, this is a test. Please respond with 'API working' if you can see this message."
            response = await asyncio.to_thread(
                paper_analyzer.model.generate_content,
                test_prompt
            )
            
            if response and response.text:
                print(f"   ✅ API call successful")
                print(f"   Response: {response.text.strip()[:100]}...")
            else:
                print(f"   ❌ API call returned empty response")
                
        except Exception as e:
            print(f"   ❌ API call failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
    else:
        print("\n🤖 Test 4: Skipped (no model available)")
    
    # Test 5: Check what happens when model is None
    print("\n🔧 Test 5: Behavior when model is None")
    
    # Temporarily set model to None
    original_model = paper_analyzer.model
    paper_analyzer.model = None
    
    try:
        # This should trigger the fallback analysis
        fallback_analysis = await paper_analyzer._analyze_with_gemini("test paper content")
        
        if fallback_analysis:
            print("   ✅ Fallback analysis triggered when model is None")
            print(f"   Title: {fallback_analysis.get('title', 'N/A')}")
            print(f"   Abstract: {fallback_analysis.get('abstract', 'N/A')}")
            
            # Check if it shows exhaustion message
            if "GEMINI API KEY EXHAUSTED" in str(fallback_analysis):
                print("   ⚠️ Shows 'GEMINI API KEY EXHAUSTED' message")
            else:
                print("   ✅ Shows appropriate fallback message")
        else:
            print("   ❌ Fallback analysis failed")
            
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")
    finally:
        # Restore original model
        paper_analyzer.model = original_model
    
    print("\n" + "=" * 50)
    print("🏁 API key behavior test completed!")

if __name__ == "__main__":
    asyncio.run(test_api_key_behavior()) 