#!/usr/bin/env python3
"""
Test script for the sophisticated WebSearch agent
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


async def test_gemini_connection():
    """Test Gemini AI connection separately"""
    logger.info("🤖 Testing Gemini AI connection...")

    try:
        import google.generativeai as genai

        genai.configure(api_key="AIzaSyDvrZ_rv1kd115j4-O1cO3skyt6JJ4MJeE")
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        response = model.generate_content(
            "Say 'Hello from Gemini!' in exactly those words."
        )

        logger.info(f"✅ Gemini response: {response.text}")
        return True

    except Exception as e:
        logger.error(f"❌ Gemini connection failed: {str(e)}")
        return False


async def test_websearch_agent():
    """Test the WebSearch agent with a sample request"""

    logger.info("🧪 Starting WebSearch Agent Test")

    # Create the agent
    agent = WebSearchAgent()

    # Sample request data
    test_request = {
        "projectId": "test-project-123",
        "queryTerms": ["machine learning", "neural networks"],
        "domain": "Computer Science",
        "batchSize": 5,
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
            for i, paper in enumerate(papers[:3]):  # Show first 3 papers
                logger.info(f"   {i+1}. {paper.get('title', 'No title')}")
                logger.info(f"      Authors: {len(paper.get('authors', []))} authors")
                logger.info(f"      Venue: {paper.get('venueName', 'Unknown')}")
                logger.info(f"      Citations: {paper.get('citationCount', 0)}")
                logger.info(
                    f"      Relevance Score: {paper.get('relevanceScore', 0):.3f}"
                )
                logger.info(f"      AI Scored: {paper.get('aiScored', False)}")
                logger.info(f"      Source: {paper.get('source', 'Unknown')}")
                logger.info("")

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


async def main():
    """Main test function"""
    logger.info("🚀 Starting comprehensive WebSearch agent tests")

    # Test 1: Gemini connection
    gemini_ok = await test_gemini_connection()

    # Test 2: Full WebSearch agent
    if gemini_ok:
        websearch_ok = await test_websearch_agent()
    else:
        logger.warning("⚠️ Skipping WebSearch test due to Gemini connection failure")
        websearch_ok = False

    # Summary
    logger.info("📋 Test Summary:")
    logger.info(f"   - Gemini AI: {'✅ PASS' if gemini_ok else '❌ FAIL'}")
    logger.info(f"   - WebSearch Agent: {'✅ PASS' if websearch_ok else '❌ FAIL'}")

    if gemini_ok and websearch_ok:
        logger.info("🎉 All tests passed! The sophisticated WebSearch agent is ready!")
    else:
        logger.error("💥 Some tests failed. Please check the logs above.")

    return gemini_ok and websearch_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
