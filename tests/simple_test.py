"""
Simple test to check if WebSearch agent works
"""

import asyncio
from app.services.websearch_agent import WebSearchAgent


async def simple_test():
    print("🧪 Simple WebSearch Test")
    print("=" * 40)

    agent = WebSearchAgent()

    # Very simple request
    request = {
        "projectId": "test-123",
        "queryTerms": ["machine learning"],
        "domain": "Computer Science",
        "batchSize": 5,  # Very small batch
        "correlationId": "test-456",
    }

    print(f"Query: {request['queryTerms']}")
    print(f"Batch Size: {request['batchSize']}")
    print()

    try:
        print("🔄 Processing...")
        result = await agent.process_request(request)

        print("✅ Success!")
        print(f"Papers found: {result['batchSize']}")
        print(f"Status: {result['status']}")

        if result.get("papers"):
            print(
                f"First paper: {result['papers'][0].get('title', 'No title')[:50]}..."
            )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(simple_test())
