"""
Debug test to identify where WebSearch agent gets stuck
"""

import asyncio
import logging
from app.services.websearch_agent import WebSearchAgent

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_test():
    print("🐛 Debug WebSearch Test")
    print("=" * 40)

    agent = WebSearchAgent()

    print("✅ Agent created")

    # Test AI initialization first
    try:
        print("🤖 Testing AI initialization...")
        await agent.initialize_ai()
        print("✅ AI initialization completed")
    except Exception as e:
        print(f"❌ AI initialization failed: {e}")

    # Test individual sources with timeout
    print("\n🔍 Testing individual sources...")

    sources = [
        ("Semantic Scholar", agent.semantic_scholar.search_papers),
        ("arXiv", agent.arxiv.search_papers),
        ("Crossref", agent.crossref.search_papers),
        ("PubMed", agent.pubmed.search_papers),
    ]

    for source_name, search_func in sources:
        try:
            print(f"🔍 Testing {source_name}...")

            # Add timeout to prevent hanging
            papers = await asyncio.wait_for(
                search_func(query="machine learning", limit=2),
                timeout=30.0,  # 30 second timeout
            )

            if papers:
                print(f"   ✅ {source_name}: Found {len(papers)} papers")
            else:
                print(f"   ⚠️  {source_name}: No papers found")

        except asyncio.TimeoutError:
            print(f"   ⏰ {source_name}: Timeout after 30 seconds")
        except Exception as e:
            print(f"   ❌ {source_name}: Error - {str(e)}")

    # Test the full process with timeout
    print("\n🔄 Testing full WebSearch process...")

    request = {
        "projectId": "test-123",
        "queryTerms": ["AI"],  # Simple query
        "domain": "Computer Science",
        "batchSize": 3,  # Very small
        "correlationId": "test-456",
    }

    try:
        result = await asyncio.wait_for(
            agent.process_request(request), timeout=60.0  # 1 minute timeout
        )

        print("✅ Full process completed!")
        print(f"Papers found: {result['batchSize']}")

    except asyncio.TimeoutError:
        print("⏰ Full process timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Full process failed: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(debug_test())
