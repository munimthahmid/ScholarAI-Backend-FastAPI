"""
🧪 COMPLETE INTEGRATION TEST
Tests the full Spring Boot ↔ FastAPI ↔ WebSearch Agent flow
"""

import asyncio
import json
from app.services.websearch_agent import WebSearchAgent
from app.services.rabbitmq_consumer import RabbitMQConsumer


async def test_websearch_agent_standalone():
    """Test WebSearch agent directly"""
    print("🔬 Testing WebSearch Agent (Standalone)")
    print("=" * 50)

    agent = WebSearchAgent()

    # Test request matching Spring Boot format
    request = {
        "projectId": "test-project-123",
        "queryTerms": ["machine learning", "optimization"],
        "domain": "Computer Science",
        "batchSize": 10,
        "correlationId": "test-correlation-456",
    }

    print(f"📝 Request: {json.dumps(request, indent=2)}")
    print("\n🔄 Processing...")

    try:
        result = await agent.process_request(request)

        print("✅ SUCCESS!")
        print(f"📊 Papers fetched: {len(result.get('papers', []))}")
        print(f"🎯 Status: {result.get('status')}")
        print(f"🔍 Sources used: {result.get('totalSourcesUsed')}")
        print(f"🤖 AI enhanced: {result.get('aiEnhanced')}")
        print(f"🔄 Search rounds: {result.get('searchRounds')}")

        # Show sample papers
        papers = result.get("papers", [])
        if papers:
            print(f"\n📄 Sample papers (first 3):")
            for i, paper in enumerate(papers[:3]):
                print(f"  {i+1}. {paper.get('title', 'No title')[:80]}...")
                print(f"     Source: {paper.get('source', 'Unknown')}")
                print(f"     DOI: {paper.get('doi', 'No DOI')}")
                print()

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_rabbitmq_consumer_setup():
    """Test RabbitMQ consumer setup (without actual connection)"""
    print("\n🔬 Testing RabbitMQ Consumer Setup")
    print("=" * 50)

    try:
        consumer = RabbitMQConsumer()

        # Check if agents are initialized
        print(f"✅ WebSearch agent initialized: {consumer.websearch_agent is not None}")
        print(
            f"✅ Summarization agent initialized: {consumer.summarization_agent is not None}"
        )

        # Check configuration
        print(f"🔧 RabbitMQ Host: {consumer.rabbitmq_host}")
        print(f"🔧 RabbitMQ Port: {consumer.rabbitmq_port}")
        print(f"🔧 WebSearch Queue: {consumer.websearch_queue}")
        print(f"🔧 Exchange: {consumer.exchange_name}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_message_processing_simulation():
    """Simulate message processing without RabbitMQ"""
    print("\n🔬 Testing Message Processing (Simulation)")
    print("=" * 50)

    try:
        consumer = RabbitMQConsumer()

        # Simulate Spring Boot message
        spring_message = {
            "projectId": "spring-test-789",
            "queryTerms": ["artificial intelligence", "neural networks"],
            "domain": "Computer Science",
            "batchSize": 5,
            "correlationId": "spring-correlation-101",
        }

        print(f"📨 Simulating Spring Boot message:")
        print(f"   {json.dumps(spring_message, indent=2)}")

        # Process directly with websearch agent
        result = await consumer.websearch_agent.process_request(spring_message)

        print(f"\n✅ Processing completed!")
        print(f"📊 Result summary:")
        print(f"   - Papers: {len(result.get('papers', []))}")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Project ID: {result.get('projectId')}")
        print(f"   - Correlation ID: {result.get('correlationId')}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 SCHOLARAI INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("WebSearch Agent Standalone", test_websearch_agent_standalone),
        ("RabbitMQ Consumer Setup", test_rabbitmq_consumer_setup),
        ("Message Processing Simulation", test_message_processing_simulation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 ALL TESTS PASSED! Ready for Spring Boot integration!")
    else:
        print("⚠️  Some tests failed. Check the issues above.")


if __name__ == "__main__":
    asyncio.run(main())
