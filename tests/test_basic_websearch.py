#!/usr/bin/env python3
"""
Basic test script for the WebSearch agent without Gemini dependency
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.services.websearch_agent import WebSearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_websearch_basic():
    """Test the WebSearch agent basic functionality without Gemini"""

    logger.info("🧪 Starting Basic WebSearch Agent Test (No Gemini)")

    # Create the agent
    agent = WebSearchAgent()

    # Disable Gemini for this test
    agent.ai_available = False
    agent.gemini_client = None

    # Sample request data
    test_request = {
        "projectId": "test-project-123",
        "queryTerms": ["machine learning"],
        "domain": "Computer Science",
        "batchSize": 3,  # Small batch for testing
        "correlationId": "test-correlation-456",
    }

    try:
        logger.info("📡 Sending test request to WebSearch agent...")
        result = await agent.process_request(test_request)

        logger.info("✅ WebSearch agent completed successfully!")
        logger.info(f"📊 Result summary:")
        logger.info(f"   - Project ID: {result.get('projectId')}")
        logger.info(f"   - Papers found: {result.get('batchSize')}")
        logger.info(f"   - Search strategy: {result.get('searchStrategy')}")
        logger.info(f"   - AI enhanced: {result.get('aiEnhanced')}")
        logger.info(f"   - Total sources used: {result.get('totalSourcesUsed')}")

        # Show sample papers
        papers = result.get("papers", [])
        if papers:
            logger.info(f"📚 Sample papers found:")
            for i, paper in enumerate(papers[:2]):  # Show first 2 papers
                logger.info(f"   {i+1}. {paper.get('title', 'No title')[:80]}...")
                logger.info(f"      Authors: {len(paper.get('authors', []))} authors")
                logger.info(f"      Venue: {paper.get('venueName', 'Unknown')}")
                logger.info(f"      Citations: {paper.get('citationCount', 0)}")
                logger.info(
                    f"      Relevance Score: {paper.get('relevanceScore', 0):.3f}"
                )
                logger.info(f"      AI Scored: {paper.get('aiScored', False)}")
                logger.info(f"      Source: {paper.get('source', 'Unknown')}")
                logger.info("")
        else:
            logger.warning("⚠️ No papers found - this might indicate API issues")

        return True

    except Exception as e:
        logger.error(f"❌ WebSearch agent test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        try:
            await agent.close()
        except:
            pass


async def test_api_clients():
    """Test individual API clients"""
    logger.info("🔍 Testing individual API clients...")

    try:
        from app.services.academic_apis import SemanticScholarClient, ArxivClient

        # Test Semantic Scholar
        logger.info("📚 Testing Semantic Scholar...")
        ss_client = SemanticScholarClient()
        ss_papers = await ss_client.search_papers("machine learning", limit=2)
        logger.info(f"   - Semantic Scholar: {len(ss_papers)} papers found")

        # Test arXiv
        logger.info("📄 Testing arXiv...")
        arxiv_client = ArxivClient()
        arxiv_papers = await arxiv_client.search_papers("neural networks", limit=2)
        logger.info(f"   - arXiv: {len(arxiv_papers)} papers found")

        await ss_client.close()
        await arxiv_client.close()

        return len(ss_papers) > 0 or len(arxiv_papers) > 0

    except Exception as e:
        logger.error(f"❌ API client test failed: {str(e)}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting basic WebSearch agent tests")

    # Test 1: API clients
    api_ok = await test_api_clients()

    # Test 2: Basic WebSearch agent
    websearch_ok = await test_websearch_basic()

    # Summary
    logger.info("📋 Test Summary:")
    logger.info(f"   - API Clients: {'✅ PASS' if api_ok else '❌ FAIL'}")
    logger.info(f"   - WebSearch Agent: {'✅ PASS' if websearch_ok else '❌ FAIL'}")

    if api_ok and websearch_ok:
        logger.info(
            "🎉 Basic tests passed! The WebSearch agent core functionality works!"
        )
        logger.info(
            "💡 Note: Gemini AI integration can be tested separately when quota is available"
        )
    else:
        logger.error("💥 Some basic tests failed. Please check the logs above.")

    return api_ok and websearch_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
