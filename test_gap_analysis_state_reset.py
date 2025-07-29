#!/usr/bin/env python3
"""
Test script to verify gap analysis state reset functionality.
This script helps verify that the orchestrator properly resets state between analyses.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator
from app.services.gap_analyzer.models import GapAnalysisRequest


async def test_state_reset():
    """Test that orchestrator state is properly reset between analyses."""
    
    print("🧪 Testing Gap Analysis State Reset")
    print("=" * 50)
    
    # Create orchestrator instance
    orchestrator = GapAnalysisOrchestrator()
    
    # Initialize first time
    print("📋 Step 1: Initial state setup")
    await orchestrator.initialize()
    
    # Check initial state is clean
    initial_gaps = len(orchestrator.potential_gaps_db)
    initial_papers = len(orchestrator.analyzed_papers)
    initial_final_gaps = len(orchestrator.final_gaps_list)
    
    print(f"   Initial gaps: {initial_gaps}")
    print(f"   Initial papers: {initial_papers}")
    print(f"   Initial final gaps: {initial_final_gaps}")
    
    assert initial_gaps == 0, f"Expected 0 initial gaps, got {initial_gaps}"
    assert initial_papers == 0, f"Expected 0 initial papers, got {initial_papers}"
    assert initial_final_gaps == 0, f"Expected 0 initial final gaps, got {initial_final_gaps}"
    
    print("✅ Initial state is clean")
    
    # Simulate some state accumulation (like what would happen during analysis)
    print("\n📋 Step 2: Simulating state accumulation")
    
    # Add some fake gaps to simulate analysis state
    orchestrator.potential_gaps_db.append("fake_gap_1")
    orchestrator.analyzed_papers.append("fake_paper_1")
    orchestrator.final_gaps_list.append("fake_final_gap_1")
    orchestrator.stats["gaps_discovered"] = 5
    orchestrator.stats["gaps_eliminated"] = 2
    
    accumulated_gaps = len(orchestrator.potential_gaps_db)
    accumulated_papers = len(orchestrator.analyzed_papers)
    accumulated_final_gaps = len(orchestrator.final_gaps_list)
    
    print(f"   Accumulated gaps: {accumulated_gaps}")
    print(f"   Accumulated papers: {accumulated_papers}")
    print(f"   Accumulated final gaps: {accumulated_final_gaps}")
    print(f"   Stats - discovered: {orchestrator.stats['gaps_discovered']}")
    print(f"   Stats - eliminated: {orchestrator.stats['gaps_eliminated']}")
    
    assert accumulated_gaps > 0, "Should have accumulated some gaps"
    assert accumulated_papers > 0, "Should have accumulated some papers"
    assert accumulated_final_gaps > 0, "Should have accumulated some final gaps"
    
    print("✅ State accumulation simulated successfully")
    
    # Now test the reset functionality
    print("\n📋 Step 3: Testing state reset via initialize()")
    await orchestrator.initialize()
    
    # Check that state is clean again
    reset_gaps = len(orchestrator.potential_gaps_db)
    reset_papers = len(orchestrator.analyzed_papers)
    reset_final_gaps = len(orchestrator.final_gaps_list)
    reset_stats_discovered = orchestrator.stats['gaps_discovered']
    reset_stats_eliminated = orchestrator.stats['gaps_eliminated']
    
    print(f"   After reset gaps: {reset_gaps}")
    print(f"   After reset papers: {reset_papers}")
    print(f"   After reset final gaps: {reset_final_gaps}")
    print(f"   After reset stats - discovered: {reset_stats_discovered}")
    print(f"   After reset stats - eliminated: {reset_stats_eliminated}")
    
    # Verify everything is reset
    assert reset_gaps == 0, f"Expected 0 gaps after reset, got {reset_gaps}"
    assert reset_papers == 0, f"Expected 0 papers after reset, got {reset_papers}"
    assert reset_final_gaps == 0, f"Expected 0 final gaps after reset, got {reset_final_gaps}"
    assert reset_stats_discovered == 0, f"Expected 0 discovered stats after reset, got {reset_stats_discovered}"
    assert reset_stats_eliminated == 0, f"Expected 0 eliminated stats after reset, got {reset_stats_eliminated}"
    
    print("✅ State reset successful - all accumulators cleared!")
    
    # Test multiple resets to ensure consistency
    print("\n📋 Step 4: Testing multiple consecutive resets")
    
    for i in range(3):
        await orchestrator.initialize()
        gaps_count = len(orchestrator.potential_gaps_db)
        papers_count = len(orchestrator.analyzed_papers)
        assert gaps_count == 0, f"Reset {i+1} failed: gaps = {gaps_count}"
        assert papers_count == 0, f"Reset {i+1} failed: papers = {papers_count}"
    
    print("✅ Multiple consecutive resets working correctly")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 50)
    print("✅ Gap analysis state reset is working correctly")
    print("✅ No accumulation between analyses should occur")
    print("✅ Each analysis will start with clean state")


async def main():
    """Main test function."""
    try:
        await test_state_reset()
        print("\n🎯 CONCLUSION: The gap analysis accumulation bug has been FIXED!")
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("🚨 Gap analysis state reset is not working properly")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)