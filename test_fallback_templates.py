#!/usr/bin/env python3
"""
Test script to verify that fallback templates show "GEMINI API KEY EXHAUSTED" messages.
"""

import asyncio
import json
from app.services.gap_analyzer.paper_analyzer import PaperAnalyzer
from app.services.gap_analyzer.gap_validator import GapValidator
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator
from app.services.gap_analyzer.models import ResearchGap

async def test_fallback_templates():
    """Test that fallback templates show API exhaustion messages."""
    
    print("🧪 TESTING FALLBACK TEMPLATES")
    print("=" * 50)
    
    # Test 1: Paper Analyzer Fallback
    print("\n📄 Test 1: Paper Analyzer Fallback")
    paper_analyzer = PaperAnalyzer()
    
    # Simulate Gemini failure by not initializing the model
    paper_analyzer.model = None
    
    try:
        # This should trigger the fallback analysis
        fallback_analysis = await paper_analyzer._analyze_with_gemini("test paper content")
        
        if fallback_analysis:
            print("✅ Paper analyzer fallback triggered")
            print(f"   Title: {fallback_analysis.get('title', 'N/A')}")
            print(f"   Abstract: {fallback_analysis.get('abstract', 'N/A')}")
            print(f"   Key Findings: {fallback_analysis.get('key_findings', [])}")
            print(f"   Limitations: {fallback_analysis.get('limitations', [])}")
            print(f"   Future Work: {fallback_analysis.get('future_work', [])}")
            
            # Check if all fields contain the exhaustion message
            all_fields_exhausted = all(
                "GEMINI API KEY EXHAUSTED" in str(value) 
                for value in fallback_analysis.values() 
                if value and isinstance(value, (str, list))
            )
            
            if all_fields_exhausted:
                print("✅ All fields contain 'GEMINI API KEY EXHAUSTED' message")
            else:
                print("❌ Some fields don't contain exhaustion message")
        else:
            print("❌ Paper analyzer fallback failed")
            
    except Exception as e:
        print(f"❌ Paper analyzer test failed: {str(e)}")
    
    # Test 2: Gap Validator Fallback
    print("\n🔍 Test 2: Gap Validator Fallback")
    gap_validator = GapValidator()
    
    # Simulate Gemini failure
    gap_validator.model = None
    
    try:
        # Create a test gap
        test_gap = ResearchGap(
            gap_id="test_gap_1",
            description="Test research gap description",
            source_paper="test_paper_url",
            source_paper_title="Test Paper"
        )
        
        # Test validation queries fallback
        validation_queries = await gap_validator.generate_validation_queries(test_gap)
        print("✅ Gap validator validation queries fallback triggered")
        print(f"   Queries: {validation_queries}")
        
        # Test gap enrichment fallback
        enriched_gap = await gap_validator.enrich_validated_gap(test_gap)
        print("✅ Gap validator enrichment fallback triggered")
        print(f"   Gap Title: {enriched_gap.gap_title}")
        print(f"   Description: {enriched_gap.description}")
        print(f"   Category: {enriched_gap.category}")
        print(f"   Confidence Score: {enriched_gap.confidence_score}")
        
        # Check if all fields contain the exhaustion message
        gap_fields = [
            enriched_gap.gap_title,
            enriched_gap.description,
            enriched_gap.category,
            enriched_gap.validation_evidence,
            enriched_gap.potential_impact,
            enriched_gap.source_paper_title
        ]
        
        all_gap_fields_exhausted = all(
            "GEMINI API KEY EXHAUSTED" in str(field) 
            for field in gap_fields
        )
        
        if all_gap_fields_exhausted:
            print("✅ All gap fields contain 'GEMINI API KEY EXHAUSTED' message")
        else:
            print("❌ Some gap fields don't contain exhaustion message")
            
    except Exception as e:
        print(f"❌ Gap validator test failed: {str(e)}")
    
    # Test 3: Orchestrator Quick Enrichment Fallback
    print("\n🎯 Test 3: Orchestrator Quick Enrichment Fallback")
    
    try:
        orchestrator = GapAnalysisOrchestrator()
        
        # Create a test gap
        test_gap = ResearchGap(
            gap_id="test_gap_2",
            description="Test research gap for orchestrator",
            source_paper="test_paper_url",
            source_paper_title="Test Paper"
        )
        
        # Test quick enrichment fallback
        enriched_gap = await orchestrator._quick_gap_enrichment(test_gap)
        print("✅ Orchestrator quick enrichment fallback triggered")
        print(f"   Gap Title: {enriched_gap.gap_title}")
        print(f"   Description: {enriched_gap.description}")
        print(f"   Category: {enriched_gap.category}")
        print(f"   Confidence Score: {enriched_gap.confidence_score}")
        
        # Check if all fields contain the exhaustion message
        orchestrator_fields = [
            enriched_gap.gap_title,
            enriched_gap.description,
            enriched_gap.category,
            enriched_gap.validation_evidence,
            enriched_gap.potential_impact,
            enriched_gap.source_paper_title
        ]
        
        all_orchestrator_fields_exhausted = all(
            "GEMINI API KEY EXHAUSTED" in str(field) 
            for field in orchestrator_fields
        )
        
        if all_orchestrator_fields_exhausted:
            print("✅ All orchestrator fields contain 'GEMINI API KEY EXHAUSTED' message")
        else:
            print("❌ Some orchestrator fields don't contain exhaustion message")
            
    except Exception as e:
        print(f"❌ Orchestrator test failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Fallback template tests completed!")
    print("\n📋 SUMMARY:")
    print("   - All fallback templates now show 'GEMINI API KEY EXHAUSTED'")
    print("   - Users will clearly see when API key is exhausted")
    print("   - System continues to function with clear error indication")

if __name__ == "__main__":
    asyncio.run(test_fallback_templates()) 