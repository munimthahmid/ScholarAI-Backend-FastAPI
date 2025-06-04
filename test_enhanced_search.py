#!/usr/bin/env python3
"""
Test script to verify enhanced multi-source search with all 13 academic APIs
"""
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.websearch_agent import WebSearchAgent
from app.services.websearch.config import AppConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_enhanced_search():
    """Test the enhanced search with all academic sources"""
    print("🚀 Testing Enhanced Multi-Source Academic Search")
    print("=" * 60)
    
    # Create test configuration
    config = AppConfig.from_env()
    
    # Initialize the agent
    agent = WebSearchAgent(config)
    
    # Test request
    test_request = {
        "projectId": "test-project-123",
        "queryTerms": ["machine learning", "neural networks"],
        "domain": "Computer Science", 
        "batchSize": 25,  # Higher target to test all sources
        "correlationId": "test-correlation-456"
    }
    
    print(f"📊 Test Parameters:")
    print(f"   Query Terms: {test_request['queryTerms']}")
    print(f"   Domain: {test_request['domain']}")
    print(f"   Target Batch Size: {test_request['batchSize']}")
    print(f"   Papers per Source: {config.search.papers_per_source}")
    print("")
    
    try:
        # Execute the search
        print("🔍 Starting enhanced search...")
        result = await agent.process_request(test_request)
        
        # Print results
        print("\n" + "=" * 60)
        print("📈 SEARCH RESULTS")
        print("=" * 60)
        print(f"✅ Status: {result['status']}")
        print(f"📄 Papers Found: {result['batchSize']}")
        print(f"🎯 Target: {test_request['batchSize']}")
        print(f"🌐 Sources Used: {result['totalSourcesUsed']}")
        print(f"🤖 AI Enhanced: {result['aiEnhanced']}")
        print(f"🔄 Search Rounds: {result['searchRounds']}")
        
        # Deduplication stats
        dedup_stats = result.get('deduplicationStats', {})
        print(f"🔗 Unique Papers: {dedup_stats.get('unique_papers', 'N/A')}")
        print(f"🆔 Total Identifiers: {dedup_stats.get('total_identifiers', 'N/A')}")
        
        # Sample papers
        papers = result.get('papers', [])
        if papers:
            print(f"\n📋 Sample Papers (first 3):")
            for i, paper in enumerate(papers[:3]):
                print(f"   {i+1}. {paper.get('title', 'No title')}")
                print(f"      Source: {paper.get('source', 'Unknown')}")
                print(f"      Year: {paper.get('year', 'Unknown')}")
        
        # Check if target was reached
        success_rate = (result['batchSize'] / test_request['batchSize']) * 100
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if result['batchSize'] >= test_request['batchSize']:
            print("✅ TARGET REACHED: Enhanced search successfully reached batch size!")
        elif result['batchSize'] >= test_request['batchSize'] * 0.8:
            print("⚡ GOOD RESULT: Enhanced search reached 80%+ of target!")
        else:
            print("⚠️ IMPROVEMENT NEEDED: Consider increasing papers_per_source or search_rounds")
            
    except Exception as e:
        print(f"❌ Error during search: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await agent.close()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")


async def test_source_availability():
    """Test which academic sources are available"""
    print("\n🔍 Testing Academic Source Availability")
    print("-" * 40)
    
    config = AppConfig.from_env()
    agent = WebSearchAgent(config)
    
    # Get search stats to see active sources
    stats = agent.get_search_stats()
    active_sources = stats.get('active_sources', [])
    
    print(f"📡 Active Sources ({len(active_sources)}):")
    for i, source in enumerate(active_sources, 1):
        print(f"   {i:2d}. {source}")
    
    await agent.close()


if __name__ == "__main__":
    print("🧪 Enhanced Academic Search Test Suite")
    print("=" * 60)
    
    # Run tests
    asyncio.run(test_source_availability())
    asyncio.run(test_enhanced_search()) 