"""
Test script for the Text Extraction Agent
"""

import asyncio
import json
import uuid
from datetime import datetime

from app.services.extractor.text_extractor import (
    TextExtractorAgent,
    ExtractionRequest,
    ExtractionStatus,
)
from app.services.messaging.handlers.extraction_handler import ExtractionMessageHandler
from app.services.b2_storage import B2StorageService


async def test_extraction_agent():
    """Test the text extraction agent with a mock request"""
    print("🧪 Testing Text Extraction Agent...")

    # Create a mock B2 client (you'd need actual B2 credentials for real testing)
    b2_client = B2StorageService()

    # Create extraction agent
    extractor = TextExtractorAgent(b2_client)

    # Create a test extraction request
    test_request = ExtractionRequest(
        correlation_id=str(uuid.uuid4()),
        paper_id=str(uuid.uuid4()),
        pdf_url="https://example.com/test-paper.pdf",  # This would be a real B2 URL
        requested_by="test-user",
    )

    print(f"📄 Test Request: {test_request.paper_id}")
    print(f"🔗 PDF URL: {test_request.pdf_url}")

    try:
        # Process the extraction request
        result = await extractor.process_extraction_request(test_request)

        print(f"✅ Extraction completed!")
        print(f"📊 Status: {result.status}")
        print(f"📏 Text length: {result.text_length}")
        print(f"🔧 Method: {result.extraction_method}")

        if result.error_message:
            print(f"⚠️ Error: {result.error_message}")

        return result

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None


async def test_extraction_handler():
    """Test the extraction message handler"""
    print("\n🧪 Testing Extraction Message Handler...")

    # Create handler
    handler = ExtractionMessageHandler()

    # Create test message body
    test_body = {
        "correlationId": str(uuid.uuid4()),
        "paperId": str(uuid.uuid4()),
        "pdfUrl": "https://example.com/test-paper.pdf",
        "requestedBy": "test-user",
    }

    print(f"📨 Test Message: {test_body['paperId']}")

    try:
        # Process the message
        result = await handler._process_message(test_body)

        print(f"✅ Handler processing completed!")
        print(f"📊 Result status: {result.get('status')}")
        print(f"🆔 Paper ID: {result.get('paperId')}")

        return result

    except Exception as e:
        print(f"❌ Handler test failed: {str(e)}")
        return None


def test_status_enum():
    """Test the ExtractionStatus enum"""
    print("\n🧪 Testing ExtractionStatus Enum...")

    statuses = [
        ExtractionStatus.PENDING,
        ExtractionStatus.IN_PROGRESS,
        ExtractionStatus.COMPLETED,
        ExtractionStatus.FAILED,
        ExtractionStatus.NEEDS_OCR,
    ]

    for status in statuses:
        print(f"✅ Status: {status.value}")

    return True


async def main():
    """Run all tests"""
    print("🚀 Starting Text Extraction Agent Tests\n")

    # Test 1: Status enum
    test_status_enum()

    # Test 2: Extraction agent (will fail without real PDF URL)
    await test_extraction_agent()

    # Test 3: Message handler (will fail without real PDF URL)
    await test_extraction_handler()

    print("\n✅ Test suite completed!")
    print("\n📝 Note: To test with real PDFs, you need:")
    print("   1. Valid B2 storage credentials")
    print("   2. Actual PDF URLs from your B2 bucket")
    print("   3. Running RabbitMQ instance for end-to-end testing")


if __name__ == "__main__":
    asyncio.run(main())
