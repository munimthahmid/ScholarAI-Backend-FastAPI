#!/usr/bin/env python3
"""
Test script for Unpaywall client functionality.
Tests both DOI lookup and search functionality.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add app to path
import sys

sys.path.append("app")

from app.services.academic_apis.clients import UnpaywallClient

# Set environment variable for the test
os.environ["UNPAYWALL_EMAIL"] = "trisn.eclipse@gmail.com"


async def test_doi_lookup():
    """Test DOI lookup functionality"""
    print("\n" + "=" * 60)
    print("TESTING DOI LOOKUP")
    print("=" * 60)

    client = UnpaywallClient(email="trisn.eclipse@gmail.com")

    # Test with a known open access DOI
    test_doi = "10.1371/journal.pone.0000308"

    try:
        paper = await client.get_paper_by_doi(test_doi)

        if paper:
            print(f"✅ Successfully retrieved paper for DOI: {test_doi}")
            print(f"Title: {paper.get('title', 'N/A')}")
            print(f"DOI: {paper.get('doi', 'N/A')}")
            print(f"Journal: {paper.get('venueName', 'N/A')}")
            print(f"Year: {paper.get('year', 'N/A')}")
            print(f"Open Access: {paper.get('isOpenAccess', False)}")
            print(f"PDF URL: {paper.get('pdfUrl', 'N/A')}")
            print(f"OA Types: {paper.get('oa_types', [])}")
            print(f"Licenses: {paper.get('licenses', [])}")
        else:
            print(f"❌ No paper found for DOI: {test_doi}")

    except Exception as e:
        print(f"❌ Error testing DOI lookup: {str(e)}")

    await client.close()


async def test_search_functionality():
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("TESTING SEARCH FUNCTIONALITY")
    print("=" * 60)

    client = UnpaywallClient(email="trisn.eclipse@gmail.com")

    test_queries = [
        "machine learning",
        "deep learning neural networks",
        "covid vaccine efficacy",
    ]

    for query in test_queries:
        try:
            print(f"\nSearching for: '{query}'")
            papers = await client.search_papers(query, limit=5)

            if papers:
                print(f"✅ Found {len(papers)} papers")
                for i, paper in enumerate(papers, 1):
                    print(f"  {i}. {paper.get('title', 'N/A')[:80]}...")
                    print(f"     DOI: {paper.get('doi', 'N/A')}")
                    print(f"     OA: {paper.get('isOpenAccess', False)}")
                    if paper.get("search_score"):
                        print(f"     Score: {paper.get('search_score')}")
            else:
                print(f"❌ No papers found for query: '{query}'")

        except Exception as e:
            print(f"❌ Error searching for '{query}': {str(e)}")

    await client.close()


async def test_open_access_search():
    """Test open access only search"""
    print("\n" + "=" * 60)
    print("TESTING OPEN ACCESS ONLY SEARCH")
    print("=" * 60)

    client = UnpaywallClient(email="trisn.eclipse@gmail.com")

    try:
        query = "artificial intelligence"
        print(f"Searching for open access papers: '{query}'")

        papers = await client.search_open_access_only(query, limit=5)

        if papers:
            print(f"✅ Found {len(papers)} open access papers")
            for i, paper in enumerate(papers, 1):
                print(f"  {i}. {paper.get('title', 'N/A')[:80]}...")
                print(f"     DOI: {paper.get('doi', 'N/A')}")
                print(f"     OA: {paper.get('isOpenAccess', False)}")
                print(f"     PDF: {paper.get('pdfUrl', 'N/A')[:60]}...")
        else:
            print(f"❌ No open access papers found for query: '{query}'")

    except Exception as e:
        print(f"❌ Error testing open access search: {str(e)}")

    await client.close()


async def test_bulk_doi_check():
    """Test bulk DOI checking"""
    print("\n" + "=" * 60)
    print("TESTING BULK DOI CHECK")
    print("=" * 60)

    client = UnpaywallClient(email="trisn.eclipse@gmail.com")

    test_dois = [
        "10.1371/journal.pone.0000308",  # Known OA
        "10.1038/nature12373",  # Nature paper (likely not OA)
        "10.1103/PhysRevLett.116.061102",  # Physics paper (might be OA)
    ]

    try:
        print(f"Checking OA status for {len(test_dois)} DOIs...")
        oa_status = await client.get_oa_status_bulk(test_dois)

        print("Results:")
        for doi, is_oa in oa_status.items():
            status = "✅ Open Access" if is_oa else "❌ Closed Access"
            print(f"  {doi}: {status}")

    except Exception as e:
        print(f"❌ Error testing bulk DOI check: {str(e)}")

    await client.close()


async def main():
    """Run all tests"""
    print("🔬 Unpaywall Client Test Suite")
    print("Testing with email: trisn.eclipse@gmail.com")

    try:
        await test_doi_lookup()
        await test_search_functionality()
        await test_open_access_search()
        await test_bulk_doi_check()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
