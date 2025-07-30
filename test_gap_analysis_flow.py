#!/usr/bin/env python3
"""
Test script to simulate the actual gap analysis flow and identify where fallback messages come from.
"""

import asyncio
import json
import time
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator
from app.services.gap_analyzer.models import GapAnalysisRequest
from app.core.config import settings

async def test_gap_analysis_flow():
    """Test the actual gap analysis flow to identify issues."""
    
    print("🧪 TESTING GAP ANALYSIS FLOW")
    print("=" * 50)
    
    # Check API key status
    print(f"\n🔑 API Key Status:")
    print(f"   API Key exists: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"   API Key preview: {settings.GEMINI_API_KEY[:10]}..." if settings.GEMINI_API_KEY else "None")
    
    # Create orchestrator
    print("\n🎯 Creating Gap Analysis Orchestrator...")
    orchestrator = GapAnalysisOrchestrator()
    print(f"   Orchestrator model available: {'Yes' if orchestrator.model else 'No'}")
    print(f"   Paper analyzer model available: {'Yes' if orchestrator.paper_analyzer.model else 'No'}")
    print(f"   Gap validator model available: {'Yes' if orchestrator.gap_validator.model else 'No'}")
    
    # Initialize orchestrator
    print("\n🔄 Initializing orchestrator...")
    try:
        await orchestrator.initialize()
        print("   ✅ Orchestrator initialized successfully")
    except Exception as e:
        print(f"   ❌ Orchestrator initialization failed: {str(e)}")
        return
    
    # Test with a simple paper text
    print("\n📄 Testing with sample paper text...")
    sample_paper_text = """
    Title: A Novel Approach to Machine Learning
    
    Abstract: This paper presents a new methodology for improving machine learning performance.
    
    Introduction: Machine learning has become increasingly important in various domains.
    
    Methods: We propose a novel algorithm that combines deep learning with traditional statistical methods.
    
    Results: Our approach achieves 85% accuracy on benchmark datasets, representing a 10% improvement over existing methods.
    
    Discussion: While our results are promising, there are several limitations to consider. First, our experiments were limited to specific datasets and may not generalize to other domains. Second, the computational requirements are high, making deployment on resource-constrained devices challenging. Third, the model requires significant amounts of training data, which may not be available in all applications.
    
    Future Work: Several directions for future research include: (1) developing more efficient training algorithms to reduce computational requirements, (2) investigating transfer learning approaches to reduce data requirements, and (3) exploring the application of our methodology to other domains beyond the current scope.
    
    Conclusion: We have presented a novel approach that shows promise for improving machine learning performance.
    """
    
    try:
        # Test paper analysis directly
        print("\n🔍 Testing paper analysis...")
        paper_analysis = await orchestrator.paper_analyzer.analyze_paper_text(
            sample_paper_text, 
            "test_paper_url"
        )
        
        if paper_analysis:
            print("   ✅ Paper analysis successful")
            print(f"   Title: {paper_analysis.title}")
            print(f"   Key findings count: {len(paper_analysis.key_findings)}")
            print(f"   Limitations count: {len(paper_analysis.limitations)}")
            print(f"   Future work count: {len(paper_analysis.future_work)}")
            
            # Check for fallback messages
            all_text = str(paper_analysis)
            if "GEMINI API KEY EXHAUSTED" in all_text:
                print("   ⚠️ Contains 'GEMINI API KEY EXHAUSTED' messages")
                print("   This indicates the API is failing or quota is exhausted")
            else:
                print("   ✅ No fallback messages found - API is working correctly")
                
            # Show some content
            print(f"   Sample key findings: {paper_analysis.key_findings[:2]}")
            print(f"   Sample limitations: {paper_analysis.limitations[:2]}")
            print(f"   Sample future work: {paper_analysis.future_work[:2]}")
        else:
            print("   ❌ Paper analysis failed")
            
    except Exception as e:
        print(f"   ❌ Paper analysis error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
    
    # Test gap validation
    print("\n🔍 Testing gap validation...")
    try:
        from app.services.gap_analyzer.models import ResearchGap
        
        test_gap = ResearchGap(
            gap_id="test_gap_1",
            description="Machine learning models require too much training data for practical deployment",
            source_paper="test_paper_url",
            source_paper_title="Test Paper"
        )
        
        # Test validation queries
        validation_queries = await orchestrator.gap_validator.generate_validation_queries(test_gap)
        print(f"   Validation queries: {validation_queries}")
        
        if any("GEMINI API KEY EXHAUSTED" in query for query in validation_queries):
            print("   ⚠️ Validation queries contain exhaustion messages")
        else:
            print("   ✅ Validation queries generated successfully")
            
    except Exception as e:
        print(f"   ❌ Gap validation error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Gap analysis flow test completed!")

if __name__ == "__main__":
    asyncio.run(test_gap_analysis_flow()) 