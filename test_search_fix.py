#!/usr/bin/env python3
"""
Quick test to verify the search agent URL extraction fix.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.gap_analyzer.search_agent import SimpleSearchAgent

async def test_search_fix():
    """Test the search agent with a simple query"""
    print("🧪 TESTING SEARCH AGENT URL EXTRACTION FIX")
    print("=" * 60)
    
    search_agent = SimpleSearchAgent()
    
    # Test with a simple shadow removal query
    test_queries = ["shadow removal", "image shadow detection"]
    
    try:
        print("🔍 Testing ArXiv search with debug logging...")
        paper_urls = await search_agent.search_papers(test_queries, limit_per_query=2)
        
        print(f"\n📊 RESULTS:")
        print(f"   Queries tested: {len(test_queries)}")
        print(f"   URLs found: {len(paper_urls)}")
        
        if paper_urls:
            print(f"\n✅ SUCCESS! Found {len(paper_urls)} paper URLs:")
            for i, url in enumerate(paper_urls[:3], 1):
                print(f"   {i}. {url}")
            print("\n🎉 URL extraction is now working!")
        else:
            print("\n❌ ISSUE: Still no URLs found. Check logs above for details.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_fix())