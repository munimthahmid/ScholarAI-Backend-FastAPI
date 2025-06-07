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
    """Test the search orchestrator to see which sources work"""

    print("\n🔍 Testing Search Orchestrator Sources")
    print("=" * 60)

    from app.services.websearch.search_orchestrator import MultiSourceSearchOrchestrator
    from app.services.websearch.config import SearchConfig

    # Create search orchestrator
    config = SearchConfig()
    orchestrator = MultiSourceSearchOrchestrator(config)

    query_terms = ["machine learning"]
    domain = "Computer Science"
    
    try:
        print(f"🔍 Testing search orchestrator with query: {query_terms}")
        print(f"   Active sources: {orchestrator.active_sources}")
        
        papers = await orchestrator.search_papers(
            query_terms=query_terms,
            domain=domain,
            target_size=5
        )
        
        if papers:
            print(f"   ✅ Found {len(papers)} papers total")
            
            # Show sources that contributed
            sources_found = set(paper.get('source', 'Unknown') for paper in papers)
            for source in sources_found:
                source_papers = [p for p in papers if p.get('source') == source]
                print(f"      - {source}: {len(source_papers)} papers")
        else:
            print(f"   ⚠️  No papers found")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    print("🧪 WebSearch Agent Test Suite")
    print("=" * 60)

    # Run tests
    asyncio.run(test_current_websearch())
    asyncio.run(test_individual_sources())
