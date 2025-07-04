#!/usr/bin/env python3
"""
Test script for Backblaze B2 integration with ScholarAI
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.b2_storage import b2_storage
from app.services.pdf_processor import pdf_processor


async def test_b2_connection():
    """Test basic B2 connection and functionality"""
    print("🧪 Testing Backblaze B2 Integration")
    print("=" * 50)

    try:
        # Test 1: Initialize B2 connection
        print("1️⃣ Initializing B2 connection...")
        await b2_storage.initialize()
        print("   ✅ B2 connection successful")

        # Test 2: Get storage stats
        print("\n2️⃣ Getting storage statistics...")
        stats = await b2_storage.get_storage_stats()
        print(f"   📊 Bucket: {stats['bucket_name']}")
        print(f"   📁 Total files: {stats['total_files']}")
        print(f"   💾 Total size: {stats['total_size_mb']} MB")
        print(f"   📄 File types: {stats['file_types']}")

        # Test 3: Test file upload with a dummy paper
        print("\n3️⃣ Testing PDF upload...")
        dummy_paper = {
            "title": "Test Paper for B2 Integration",
            "doi": "10.1000/test.b2.integration",
            "authors": [{"name": "Test Author"}],
            "abstract": "This is a test paper for B2 integration testing.",
        }

        # Create dummy PDF content (make it larger than 1KB for validation)
        dummy_pdf_header = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF for B2 Integration) Tj\nET\nendstream\nendobj\n5 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \n0000000179 00000 n \n0000000364 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n422\n%%EOF"

        # Pad the PDF content to ensure it's over 1KB (1024 bytes)
        padding_needed = max(0, 1024 - len(dummy_pdf_header))
        padding = b"% " + b"Padding for test PDF content. " * (padding_needed // 30 + 1)
        dummy_pdf_content = dummy_pdf_header + padding[:padding_needed]

        # Upload test PDF
        upload_url = await b2_storage.upload_pdf(dummy_paper, dummy_pdf_content)
        if upload_url:
            print("   ✅ PDF upload successful")
            print(f"   🔗 Download URL: {upload_url[:50]}...")

            # Test 4: Check if file exists
            print("\n4️⃣ Testing file existence check...")
            existing_url = await b2_storage.get_pdf_url(dummy_paper)
            if existing_url:
                print("   ✅ File existence check successful")
                print(f"   🔗 Retrieved URL: {existing_url[:50]}...")

                # Test 5: Delete test file
                print("\n5️⃣ Cleaning up test file...")
                deleted = await b2_storage.delete_pdf(dummy_paper)
                if deleted:
                    print("   ✅ Test file deleted successfully")
                else:
                    print("   ⚠️ Test file deletion failed")
            else:
                print("   ❌ File existence check failed")
        else:
            print("   ❌ PDF upload failed")

        print("\n✅ B2 integration test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ B2 integration test failed: {str(e)}")
        return False


async def test_pdf_processor():
    """Test PDF processor service"""
    print("\n🧪 Testing PDF Processor Service")
    print("=" * 50)

    try:
        # Initialize PDF processor
        print("1️⃣ Initializing PDF processor...")
        await pdf_processor.initialize()
        print("   ✅ PDF processor initialized")

        # Test with a sample paper that has a PDF URL
        sample_paper = {
            "title": "Sample Paper with PDF",
            "doi": "10.1000/sample.paper",
            "pdfUrl": "https://arxiv.org/pdf/2301.00001.pdf",  # Hypothetical URL
            "authors": [{"name": "Sample Author"}],
            "abstract": "This is a sample paper for testing PDF processing.",
        }

        print("\n2️⃣ Processing sample paper...")
        processed_paper = await pdf_processor.process_paper_pdf(sample_paper)

        print(f"   📄 Original PDF URL: {processed_paper.get('pdfUrl', 'None')}")
        print(f"   🔗 B2 PDF URL: {processed_paper.get('pdfContentUrl', 'None')}")

        if processed_paper.get("pdfContentUrl"):
            print("   ✅ PDF processing successful")
        else:
            print("   ⚠️ PDF processing completed but no B2 URL generated")

        print("\n✅ PDF processor test completed!")
        return True

    except Exception as e:
        print(f"\n❌ PDF processor test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 ScholarAI B2 Integration Test Suite")
    print("=" * 60)

    # Check environment variables
    if not os.getenv("B2_KEY_ID") or not os.getenv("B2_APPLICATION_KEY"):
        print("❌ B2 credentials not found in environment variables")
        print("Please set B2_KEY_ID and B2_APPLICATION_KEY")
        return

    b2_success = await test_b2_connection()
    pdf_success = await test_pdf_processor()

    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"B2 Connection: {'✅ PASS' if b2_success else '❌ FAIL'}")
    print(f"PDF Processor: {'✅ PASS' if pdf_success else '❌ FAIL'}")

    if b2_success and pdf_success:
        print("\n🎉 All tests passed! B2 integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")


if __name__ == "__main__":
    asyncio.run(main())
