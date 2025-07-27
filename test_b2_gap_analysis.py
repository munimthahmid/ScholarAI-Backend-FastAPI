#!/usr/bin/env python3
"""
Test script to verify B2 authentication fix for gap analysis.
"""

import asyncio
import logging
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_b2_gap_analysis():
    """Test gap analysis with B2 URL to verify authentication works."""
    
    # Test B2 URL (this should be a real B2 URL from your system)
    test_b2_url = "https://f003.backblazeb2.com/b2api/v3/b2_download_file_by_id?fileId=4_z64a715e19e4932e197750a19_f107b65fcd78b8f15_d20250714_m162507_c003_v0312025_t0045_u01752510307340"
    
    logger.info("🧪 Testing B2 authentication fix for gap analysis...")
    
    try:
        # Initialize orchestrator
        orchestrator = GapAnalysisOrchestrator()
        await orchestrator.initialize()
        logger.info("✅ Orchestrator initialized successfully")
        
        # Test with B2 URL
        logger.info(f"🔍 Testing gap analysis with B2 URL: {test_b2_url}")
        
        # Create a simple request
        from app.services.gap_analyzer.models import GapAnalysisRequest
        request = GapAnalysisRequest(
            url=test_b2_url,
            max_papers=5,  # Small number for testing
            validation_threshold=1
        )
        
        # Run analysis
        result = await orchestrator.analyze_research_gaps(request)
        
        logger.info("✅ Gap analysis completed successfully!")
        logger.info(f"📊 Found {len(result.validated_gaps)} validated gaps")
        logger.info(f"⏱️ Processing time: {result.process_metadata.processing_time_seconds:.2f} seconds")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_b2_gap_analysis()) 