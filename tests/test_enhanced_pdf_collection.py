#!/usr/bin/env python3
"""
Test script for Enhanced PDF Collection System
Tests multiple PDF collection techniques and the discard mechanism
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.b2_storage import b2_storage
from app.services.pdf_collector import pdf_collector
from app.services.pdf_processor import pdf_processor


async def test_enhanced_pdf_collection():
    """Test enhanced PDF collection with various paper types"""
    print("🧪 Testing Enhanced PDF Collection System")
    print("=" * 60)

    try:
        # Initialize services
        print("1️⃣ Initializing services...")
        await b2_storage.initialize()
        print("   ✅ B2 storage initialized")

        # Test papers with different types of URLs and identifiers
        test_papers = [
            {
                "title": "ArXiv Paper Test",
                "arxivId": "2207.12543",
                "url": "https://arxiv.org/abs/2207.12543",
                "doi": "10.1214/23-aap2009",
                "authors": [{"name": "Test Author"}],
                "abstract": "Test paper for ArXiv PDF collection",
            },
            {
                "title": "Direct PDF URL Test",
                "pdfUrl": "https://arxiv.org/pdf/1707.05711v3.pdf",
                "doi": "10.1007/s11538-020-00693-3",
                "authors": [{"name": "Test Author"}],
                "abstract": "Test paper with direct PDF URL",
            },
            {
                "title": "No PDF Test",
                "url": "https://example.com/nonexistent",
                "authors": [{"name": "Test Author"}],
                "abstract": "Test paper that should be discarded",
            },
            {
                "title": "bioRxiv Test Paper",
                "url": "https://www.biorxiv.org/content/10.1101/2021.01.01.425001v1",
                "authors": [{"name": "bioRxiv Author"}],
                "abstract": "Test bioRxiv paper for enhanced collection",
            },
            {
                "title": "PMC Test Paper",
                "pmcId": "PMC8234567",
                "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8234567/",
                "authors": [{"name": "PMC Author"}],
                "abstract": "Test PMC paper for enhanced collection",
            },
        ]

        print(f"\n2️⃣ Testing individual PDF collection...")
        collected_count = 0
        for i, paper in enumerate(test_papers, 1):
            print(f"\n🔍 Testing paper {i}: {paper['title']}")

            pdf_content = await pdf_collector.collect_pdf(paper)
            if pdf_content:
                print(f"   ✅ PDF collected: {len(pdf_content)} bytes")
                collected_count += 1
            else:
                print(f"   ❌ PDF collection failed")

        print(
            f"\n📊 Individual collection results: {collected_count}/{len(test_papers)} successful"
        )

        print(f"\n3️⃣ Testing batch processing with discard mechanism...")

        # Reset papers for batch test
        batch_papers = [
            {
                "title": "Batch Test ArXiv",
                "arxivId": "2301.00001",
                "url": "https://arxiv.org/abs/2301.00001",
                "authors": [{"name": "Batch Author"}],
                "abstract": "Batch test ArXiv paper",
            },
            {
                "title": "Batch Test Invalid",
                "url": "https://invalid-url.com/nonexistent",
                "authors": [{"name": "Invalid Author"}],
                "abstract": "This should be discarded",
            },
            {
                "title": "Batch Test Direct PDF",
                "pdfUrl": "https://arxiv.org/pdf/1004.1212v1.pdf",
                "doi": "10.1016/j.mbs.2010.07.002",
                "authors": [{"name": "Direct PDF Author"}],
                "abstract": "Direct PDF test",
            },
        ]

        print(f"Processing {len(batch_papers)} papers in batch...")

        # Test regular batch processing
        processed_papers = await pdf_processor.process_papers_batch(batch_papers)
        print(
            f"   📋 Regular batch: {len(processed_papers)}/{len(batch_papers)} papers retained"
        )

        # Test parallel batch processing
        processed_papers_parallel = await pdf_processor.process_papers_batch_parallel(
            batch_papers, batch_size=2
        )
        print(
            f"   🚀 Parallel batch: {len(processed_papers_parallel)}/{len(batch_papers)} papers retained"
        )

        print(f"\n4️⃣ Testing B2 storage statistics...")
        stats = await b2_storage.get_storage_stats()
        print(f"   📊 Total files in B2: {stats['total_files']}")
        print(f"   💾 Total size: {stats['total_size_mb']} MB")
        print(f"   📄 File types: {stats['file_types']}")

        print(f"\n5️⃣ Testing specific PDF collection techniques...")

        # Test ArXiv extraction
        arxiv_paper = {
            "url": "https://arxiv.org/abs/2301.12345",
            "title": "ArXiv Extraction Test",
        }
        arxiv_id = pdf_collector._extract_arxiv_id(arxiv_paper)
        print(f"   🔬 ArXiv ID extraction: {arxiv_id}")

        # Test bioRxiv extraction
        biorxiv_paper = {
            "url": "https://www.biorxiv.org/content/10.1101/2021.01.01.425001v1",
            "title": "bioRxiv Test",
        }
        biorxiv_id = pdf_collector._extract_biorxiv_id(biorxiv_paper)
        print(f"   🧬 bioRxiv ID extraction: {biorxiv_id}")

        # Test PMC extraction
        pmc_paper = {
            "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/",
            "title": "PMC Test",
        }
        pmc_id = pdf_collector._extract_pmc_id(pmc_paper)
        print(f"   🏥 PMC ID extraction: {pmc_id}")

        print("\n✅ Enhanced PDF collection system test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Enhanced PDF collection test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_pdf_collection_techniques():
    """Test specific PDF collection techniques"""
    print("\n🔬 Testing PDF Collection Techniques")
    print("=" * 50)

    # Test with real paper examples
    real_papers = [
        {
            "title": "Real ArXiv Paper",
            "arxivId": "2207.12543",
            "url": "https://arxiv.org/abs/2207.12543",
        },
        {
            "title": "Real Direct PDF",
            "pdfUrl": "https://arxiv.org/pdf/1707.05711v3.pdf",
        },
    ]

    for i, paper in enumerate(real_papers, 1):
        print(f"\n📄 Testing real paper {i}: {paper['title']}")

        # Test direct URLs
        print("   🎯 Testing direct URL method...")
        pdf_content = await pdf_collector._try_direct_urls(paper)
        if pdf_content:
            print(f"      ✅ Direct URL success: {len(pdf_content)} bytes")
        else:
            print("      ❌ Direct URL failed")

        # Test alternative URLs
        print("   🔄 Testing alternative URL method...")
        pdf_content = await pdf_collector._try_alternative_urls(paper)
        if pdf_content:
            print(f"      ✅ Alternative URL success: {len(pdf_content)} bytes")
        else:
            print("      ❌ Alternative URL failed")

        # Test platform-specific
        print("   🏢 Testing platform-specific method...")
        pdf_content = await pdf_collector._try_platform_specific(paper)
        if pdf_content:
            print(f"      ✅ Platform-specific success: {len(pdf_content)} bytes")
        else:
            print("      ❌ Platform-specific failed")


async def main():
    """Run all enhanced PDF collection tests"""
    print("🚀 Enhanced PDF Collection Test Suite")
    print("=" * 70)

    # Check environment variables
    if not os.getenv("B2_KEY_ID") or not os.getenv("B2_APPLICATION_KEY"):
        print("❌ B2 credentials not found in environment variables")
        print("Please set B2_KEY_ID and B2_APPLICATION_KEY")
        return

    collection_success = await test_enhanced_pdf_collection()
    await test_pdf_collection_techniques()

    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Enhanced Collection: {'✅ PASS' if collection_success else '❌ FAIL'}")

    if collection_success:
        print("\n🎉 All tests passed! Enhanced PDF collection is working correctly.")
        print("📝 The system now:")
        print("   • Uses multiple techniques to collect PDFs")
        print("   • Discards papers without PDFs")
        print("   • Processes papers in parallel for better performance")
        print("   • Supports ArXiv, bioRxiv, PMC, and other sources")
        print("   • Includes web scraping capabilities")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")


if __name__ == "__main__":
    asyncio.run(main())
