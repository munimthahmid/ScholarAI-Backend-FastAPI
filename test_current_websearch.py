"""
Simple test to verify the current WebSearch agent implementation.
Tests both Round 1 (multi-source fetching) and Round 2 (AI refinement).
"""

import asyncio
import json
from app.services.websearch_agent import WebSearchAgent


async def test_current_websearch():
    """Test the current WebSearch agent implementation"""

    print("🚀 Testing Current WebSearch Agent Implementation")
    print("=" * 60)

    # Create WebSearch agent instance
    agent = WebSearchAgent()

    # Test request data
    request_data = {
        "projectId": "test-project-123",
        "queryTerms": ["machine learning", "optimization"],
        "domain": "Computer Science",
        "batchSize": 2,  # Start small for testing
        "correlationId": "test-correlation-456",
    }

    print(f"📝 Test Request:")
    print(f"   Query Terms: {request_data['queryTerms']}")
    print(f"   Domain: {request_data['domain']}")
    print(f"   Batch Size: {request_data['batchSize']}")
    print()

    try:
        # Process the request
        print("🔄 Processing WebSearch request...")
        result = await agent.process_request(request_data)

        # Display results
        print("✅ WebSearch completed successfully!")
        print(f"📊 Results Summary:")
        print(f"   Total Papers Found: {result['batchSize']}")
        print(f"   Sources Used: {result['totalSourcesUsed']}")
        print(f"   AI Enhanced: {result['aiEnhanced']}")
        print(f"   Search Rounds: {result.get('searchRounds', 1)}")
        print(f"   Status: {result['status']}")
        print()

        # Show sample papers
        papers = result.get("papers", [])
        if papers:
            print("📄 Sample Papers Found:")
            for i, paper in enumerate(papers[:3]):  # Show first 3 papers
                print(f"   {i+1}. {paper.get('title', 'No title')[:80]}...")
                print(f"      Source: {paper.get('source', 'Unknown')}")
                print(f"      DOI: {paper.get('doi', 'No DOI')}")
                print(f"      Citations: {paper.get('citationCount', 0)}")
                print(f"      Authors: {len(paper.get('authors', []))} authors")
                print()

        # Check message size
        result_json = json.dumps(result)
        size_kb = len(result_json.encode("utf-8")) / 1024
        print(f"📏 Message Size: {size_kb:.2f} KB")

        if size_kb > 1024:  # > 1MB
            print(
                "⚠️  WARNING: Message size is large (>1MB) - might cause RabbitMQ issues"
            )
        elif size_kb > 512:  # > 512KB
            print("⚠️  CAUTION: Message size is getting large (>512KB)")
        else:
            print("✅ Message size looks good for RabbitMQ")

        print()
        print("🎉 Test completed successfully!")

        return result

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None

    finally:
        # Clean up
        await agent.close()


async def test_individual_sources():
    """Test individual academic sources to see which ones work"""

    print("\n🔍 Testing Individual Academic Sources")
    print("=" * 60)

    agent = WebSearchAgent()

    # Test each source individually
    sources = [
        ("Semantic Scholar", agent.semantic_scholar.search_papers),
        ("arXiv", agent.arxiv.search_papers),
        ("Crossref", agent.crossref.search_papers),
        ("PubMed", agent.pubmed.search_papers),
        ("Google Scholar", agent.google_scholar.search_papers),
    ]

    query = "machine learning"
    limit = 5

    for source_name, search_func in sources:
        try:
            print(f"🔍 Testing {source_name}...")
            papers = await search_func(query=query, limit=limit)

            if papers:
                print(f"   ✅ {source_name}: Found {len(papers)} papers")
                # Show first paper title
                if papers[0].get("title"):
                    print(f"   📄 Sample: {papers[0]['title'][:60]}...")
            else:
                print(f"   ⚠️  {source_name}: No papers found")

        except Exception as e:
            print(f"   ❌ {source_name}: Error - {str(e)}")

    await agent.close()


if __name__ == "__main__":
    print("🧪 WebSearch Agent Test Suite")
    print("=" * 60)

    # Run tests
    asyncio.run(test_current_websearch())
    asyncio.run(test_individual_sources())
