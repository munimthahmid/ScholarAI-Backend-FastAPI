"""
PaperCall aggregator service
"""

import logging
from typing import List, Dict, Any
from .fetchers.wikicfp import fetch_cfp_info
from .fetchers.mdpi import fetch_mdpi_special_issues
from .fetchers.taylor_francis import fetch_taylor_special_issues
from .fetchers.springer import fetch_springer_special_issues

logger = logging.getLogger(__name__)


def aggregate_all(domain: str) -> List[Dict[str, Any]]:
    """
    Aggregate paper calls from all sources
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of aggregated paper call dictionaries
    """
    try:
        logger.info(f"🔍 Starting paper call aggregation for domain: {domain}")
        
        # Fetch from all sources
        conferences = fetch_cfp_info(domain)
        journals_mdpi = fetch_mdpi_special_issues(domain)
        journals_taylor = fetch_taylor_special_issues(domain)
        journals_springer = fetch_springer_special_issues(domain)
        
        # Log results
        logger.info(f"Found {len(conferences)} conferences, {len(journals_mdpi)} MDPI journals, "
                   f"{len(journals_taylor)} Taylor & Francis journals, {len(journals_springer)} Springer journals")
        
        # Combine all results
        combined = conferences + journals_mdpi + journals_taylor + journals_springer
        
        if not combined:
            logger.warning(f"No paper calls found for domain: {domain}")
            return []
        
        # Deduplicate by title
        seen_titles = set()
        deduped = []

        for item in combined:
            title = item.get("title", "").strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                deduped.append(item)

        logger.info(f"Aggregation completed: {len(deduped)} unique paper calls found")
        return deduped
        
    except Exception as e:
        logger.error(f"Error in paper call aggregation: {e}")
        return []


def get_paper_calls_by_type(domain: str, call_type: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get paper calls grouped by type
    
    Args:
        domain: Research domain to search for
        call_type: Optional filter for specific type ('conference' or 'journal')
        
    Returns:
        Dictionary with paper calls grouped by type
    """
    try:
        all_calls = aggregate_all(domain)
        
        if call_type:
            # Filter by specific type
            filtered = [call for call in all_calls if call.get("type") == call_type]
            return {call_type: filtered}
        
        # Group by type
        grouped = {"conference": [], "journal": []}
        for call in all_calls:
            call_type = call.get("type", "journal")
            if call_type in grouped:
                grouped[call_type].append(call)
        
        return grouped
        
    except Exception as e:
        logger.error(f"Error grouping paper calls: {e}")
        return {"conference": [], "journal": []} 