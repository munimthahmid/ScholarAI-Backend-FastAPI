"""
Test script to check all available academic API clients and report their status.
"""

import asyncio
import logging
from typing import List, Tuple, Any, Dict
from datetime import datetime

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define PlaceholderClient in the global scope
class PlaceholderClient:
    async def search_papers(self, query, limit):
        raise NotImplementedError("Client not available due to import error")

    async def close(self):
        pass


# Import all client classes
# Assuming they are all in app.services.academic_apis.clients
try:
    from app.services.academic_apis.clients import (
        ArxivClient,
        BioRxivClient,  # For both bioRxiv and medRxiv
        COREClient,
        CrossrefClient,
        DBLPClient,
        DOAJClient,
        EuropePMCClient,
        OpenAlexClient,
        SemanticScholarClient,
        BASESearchClient,  # Expected to be disabled
        # UnpaywallClient, # Typically used for enrichment, not direct search
    )

    ALL_CLIENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Could not import all clients: {e}. Some tests might be skipped.")
    ALL_CLIENTS_AVAILABLE = False
    # Assign placeholders if import fails
    ArxivClient = BioRxivClient = COREClient = CrossrefClient = DBLPClient = (
        DOAJClient
    ) = EuropePMCClient = OpenAlexClient = SemanticScholarClient = BASESearchClient = (
        PlaceholderClient
    )


# --- Helper for Colored Output ---
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"


async def test_single_client(
    client_instance: Any,
    client_name: str,
    query: str = "artificial intelligence",
    limit: int = 2,
) -> Tuple[str, bool, int, str]:
    """
    Tests a single API client.

    Returns:
        Tuple: (client_name, success_status, papers_found_count, message)
    """
    papers_found_count = 0
    error_message = ""
    success = False

    logger.info(f"Testing {client_name} with query: '{query}'...")

    # Special handling for BASE Search Client as it's expected to be disabled
    if client_name == "BASE Search Client":
        try:
            # It should return [] and log a warning
            papers = await client_instance.search_papers(query=query, limit=limit)
            if not papers:
                success = True  # Considered success if it behaves as disabled (returns empty list)
                message = f"{Colors.YELLOW}SKIPPED (Disabled as expected){Colors.ENDC}"
            else:
                success = False
                message = f"{Colors.RED}ERROR (Expected disabled, but returned {len(papers)} papers){Colors.ENDC}"
            papers_found_count = len(papers)
            await client_instance.close()
            return client_name, success, papers_found_count, message
        except Exception as e:
            logger.error(f"Error testing {client_name}: {e}")
            await client_instance.close()
            return client_name, False, 0, f"{Colors.RED}ERROR: {str(e)}{Colors.ENDC}"

    try:
        papers: List[Dict[str, Any]] = await client_instance.search_papers(
            query=query, limit=limit
        )
        papers_found_count = len(papers)
        if papers_found_count > 0:
            success = True
            message = f"{Colors.GREEN}SUCCESS (Found {papers_found_count} paper(s)){Colors.ENDC}"
            logger.info(
                f"{client_name} found {papers_found_count} paper(s). First title: {papers[0].get('title', 'N/A')}"
            )
        else:
            success = False  # Technically success, but no results found for this query
            message = (
                f"{Colors.YELLOW}OK (Found 0 papers for query '{query}'){Colors.ENDC}"
            )
            logger.warning(f"{client_name} found 0 papers for query '{query}'.")

    except NotImplementedError:
        success = False
        message = (
            f"{Colors.RED}ERROR (Client not available due to import error){Colors.ENDC}"
        )
        logger.error(f"{client_name} test failed: Client not available (ImportError).")
    except Exception as e:
        success = False
        message = f"{Colors.RED}ERROR: {str(e)}{Colors.ENDC}"
        logger.error(f"{client_name} test failed: {str(e)}", exc_info=True)
    finally:
        if hasattr(client_instance, "close"):
            await client_instance.close()

    return client_name, success, papers_found_count, message


async def test_biorxiv_client(
    client_factory, client_name: str
) -> Tuple[str, bool, int, str]:
    """
    Specialized test for bioRxiv/medRxiv clients with biomedical-relevant queries
    """
    # Use biomedical-relevant queries that are more likely to find results
    if "medRxiv" in client_name:
        test_queries = ["COVID-19", "clinical trial", "vaccine", "epidemiology"]
    else:  # bioRxiv
        test_queries = ["CRISPR", "genome", "protein", "molecular biology"]

    client_instance = None
    try:
        client_instance = client_factory()

        # Try multiple biomedical queries to find papers
        for query in test_queries:
            logger.info(f"Testing {client_name} with biomedical query: '{query}'...")

            try:
                papers = await client_instance.search_papers(query=query, limit=2)
                papers_count = len(papers)

                if papers_count > 0:
                    message = f"{Colors.GREEN}SUCCESS (Found {papers_count} paper(s) for '{query}'){Colors.ENDC}"
                    logger.info(
                        f"{client_name} found {papers_count} paper(s) for '{query}'. First title: {papers[0].get('title', 'N/A')}"
                    )
                    await client_instance.close()
                    return client_name, True, papers_count, message

            except Exception as e:
                logger.warning(f"Query '{query}' failed for {client_name}: {str(e)}")
                continue

        # If no query returned results
        message = f"{Colors.YELLOW}OK (Found 0 papers for biomedical queries: {', '.join(test_queries)}){Colors.ENDC}"
        logger.warning(f"{client_name} found 0 papers for any biomedical query.")
        await client_instance.close()
        return client_name, False, 0, message

    except Exception as e:
        message = f"{Colors.RED}ERROR: {str(e)}{Colors.ENDC}"
        logger.error(f"{client_name} test failed: {str(e)}", exc_info=True)
        if client_instance and hasattr(client_instance, "close"):
            await client_instance.close()
        return client_name, False, 0, message


async def main():
    """Main test function that runs through all clients"""
    print("🚀 Starting Academic API Clients Test...")
    print("=" * 60)

    test_query = "machine learning applications"
    results = []

    # List of client classes and their names
    clients_to_test = [
        (ArxivClient, "ArXiv Client"),
        (BioRxivClient, "bioRxiv Client"),
        (lambda: BioRxivClient(server="medrxiv"), "medRxiv Client"),
        (COREClient, "CORE Client"),
        (CrossrefClient, "Crossref Client"),
        (DBLPClient, "DBLP Client"),
        (DOAJClient, "DOAJ Client"),
        (EuropePMCClient, "EuropePMC Client"),
        (OpenAlexClient, "OpenAlex Client"),
        (SemanticScholarClient, "Semantic Scholar Client"),
        (BASESearchClient, "BASE Search Client"),
    ]

    for client_factory, client_name in clients_to_test:
        # Use specialized test for bioRxiv and medRxiv clients
        if "bioRxiv Client" in client_name or "medRxiv Client" in client_name:
            result = await test_biorxiv_client(client_factory, client_name)
        else:
            result = await test_single_client(client_factory(), client_name, test_query)

        client_name_returned, success, paper_count, message = result

        # Determine status based on results
        if "ERROR" in message:
            status = "error"
        elif "SKIPPED" in message or "Disabled" in message:
            status = "skipped"
        elif paper_count == 0 and success:
            status = "warning"
        elif success and paper_count > 0:
            status = "success"
        else:
            status = "error"

        results.append(
            {
                "client": client_name,
                "success": success,
                "count": paper_count,
                "message": message,
                "status": status,
            }
        )

    # Generate comprehensive report
    print("\n🔍 Academic API Clients Test Report 🔍")
    print("=" * 80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Test Query: '{test_query}'")
    print("=" * 80)

    # Count different statuses
    success_count = sum(1 for r in results if r["status"] == "success")
    warning_count = sum(1 for r in results if r["status"] == "warning")
    error_count = sum(1 for r in results if r["status"] == "error")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    print(f"📊 OVERVIEW:")
    print(f"   ✅ Working APIs: {success_count}")
    print(f"   ⚠️  APIs with Issues: {warning_count}")
    print(f"   ❌ Failed APIs: {error_count}")
    print(f"   ⏭️  Skipped APIs: {skipped_count}")
    print(f"   📈 Total Tested: {len(results)}")
    print("=" * 80)

    for result in results:
        client_name = result["client"]
        status = result["status"]
        message = result["message"]

        if status == "success":
            icon = "✅"
            color = "\033[92m"  # Green
        elif status == "warning":
            icon = "⚠️"
            color = "\033[93m"  # Yellow
        elif status == "error":
            icon = "❌"
            color = "\033[91m"  # Red
        elif status == "skipped":
            icon = "⏭️"
            color = "\033[94m"  # Blue
        else:
            icon = "❓"
            color = "\033[90m"  # Gray

        reset_color = "\033[0m"

        # Format client name with fixed width for alignment
        formatted_name = f"{client_name:<25}"
        print(f"[{icon}] {color}{formatted_name}{reset_color} | {message}")

    print("=" * 80)

    # Performance summary
    total_active = len(results) - skipped_count
    if success_count > 0:
        success_rate = (success_count / total_active * 100) if total_active > 0 else 0
        print(
            f"🎯 SUCCESS RATE: \033[92m{success_count}/{total_active} ({success_rate:.1f}%)\033[0m"
        )

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if error_count > 0:
        print(f"   • Fix {error_count} failed API client(s) for better coverage")
    if warning_count > 0:
        print(
            f"   • Investigate {warning_count} API(s) returning no results - may need query tuning"
        )
    if success_count >= total_active - 1:  # Allow 1 failure
        print(f"   • 🎉 Excellent! Most APIs are working well")

    print(f"\n🔗 APIs providing the best results:")
    successful_apis = [r["client"] for r in results if r["status"] == "success"]
    if successful_apis:
        for api in successful_apis[:5]:  # Top 5
            print(f"   • {api}")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
