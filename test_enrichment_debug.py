#!/usr/bin/env python3
"""
Test script to debug why enrich_validated_gap method is not using the API properly.
"""

import asyncio
import json
from app.services.gap_analyzer.gap_validator import GapValidator
from app.services.gap_analyzer.models import ResearchGap
from app.core.config import settings

async def test_enrichment_debug():
    """Test the enrichment process to identify why it's not using the API."""
    
    print("🧪 TESTING ENRICHMENT DEBUG")
    print("=" * 50)
    
    # Check API key status
    print(f"\n🔑 API Key Status:")
    print(f"   API Key exists: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"   API Key preview: {settings.GEMINI_API_KEY[:10]}..." if settings.GEMINI_API_KEY else "None")
    
    # Create gap validator
    print("\n🔍 Creating Gap Validator...")
    gap_validator = GapValidator()
    print(f"   Model available: {'Yes' if gap_validator.model else 'No'}")
    print(f"   Model type: {type(gap_validator.model).__name__ if gap_validator.model else 'None'}")
    
    # Create a test gap
    test_gap = ResearchGap(
        gap_id="test_gap_1",
        description="Identifying relatively 'more correct' or reliable trees within potentially large sets of equally optimal trees in a terrace is a significant challenge for existing tree search algorithms.",
        source_paper="test_paper_url",
        source_paper_title="Test Paper on Species Tree Terraces",
        validation_strikes=2
    )
    
    print(f"\n📋 Test Gap:")
    print(f"   ID: {test_gap.gap_id}")
    print(f"   Description: {test_gap.description[:100]}...")
    print(f"   Source Paper: {test_gap.source_paper_title}")
    print(f"   Validation Strikes: {test_gap.validation_strikes}")
    
    # Test enrichment
    print("\n🚀 Testing Gap Enrichment...")
    try:
        enriched_gap = await gap_validator.enrich_validated_gap(test_gap)
        
        if enriched_gap:
            print("   ✅ Enrichment successful")
            print(f"   Gap Title: {enriched_gap.gap_title}")
            print(f"   Validation Evidence: {enriched_gap.validation_evidence}")
            print(f"   Potential Impact: {enriched_gap.potential_impact}")
            print(f"   Category: {enriched_gap.category}")
            print(f"   Confidence Score: {enriched_gap.confidence_score}")
            print(f"   Suggested Approaches: {enriched_gap.suggested_approaches}")
            
            # Check if content is generic or detailed
            is_generic = any(
                generic_text in enriched_gap.validation_evidence.lower() 
                for generic_text in [
                    "validated through systematic analysis",
                    "significant research opportunity identified",
                    "detailed analysis required"
                ]
            )
            
            if is_generic:
                print("   ⚠️ Content appears to be generic/fallback")
            else:
                print("   ✅ Content appears to be detailed and API-generated")
                
        else:
            print("   ❌ Enrichment returned None")
            
    except Exception as e:
        print(f"   ❌ Enrichment error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    # Test API call directly
    print("\n🤖 Testing Direct API Call...")
    if gap_validator.model:
        try:
            test_prompt = "Hello, this is a test. Please respond with 'API working' if you can see this message."
            response = await asyncio.to_thread(
                gap_validator.model.generate_content,
                test_prompt
            )
            
            if response and response.text:
                print(f"   ✅ Direct API call successful")
                print(f"   Response: {response.text.strip()[:100]}...")
            else:
                print(f"   ❌ Direct API call returned empty response")
                
        except Exception as e:
            print(f"   ❌ Direct API call failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
    else:
        print("   ❌ No model available for direct API test")
    
    print("\n" + "=" * 50)
    print("🏁 Enrichment debug test completed!")

if __name__ == "__main__":
    asyncio.run(test_enrichment_debug()) 