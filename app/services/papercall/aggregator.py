"""
PaperCall aggregator service
"""

import logging
from typing import List, Dict, Any
from .fetchers.wikicfp import fetch_cfp_info
from .fetchers.crossref import fetch_crossref_special_issues, fetch_crossref_conferences
from .fetchers.fallback_data import get_fallback_conferences, get_fallback_journals, should_use_fallback

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
        
        # Fetch from reliable sources only
        conferences_wikicfp = fetch_cfp_info(domain)
        
        # Try CrossRef with error handling
        try:
            conferences_crossref = fetch_crossref_conferences(domain)
        except Exception as e:
            logger.warning(f"CrossRef conferences failed for {domain}: {e}")
            conferences_crossref = []
        
        # Fetch journals from reliable sources only
        try:
            journals_crossref = fetch_crossref_special_issues(domain)
        except Exception as e:
            logger.warning(f"CrossRef journals failed for {domain}: {e}")
            journals_crossref = []
        
        # Log results
        total_conferences = len(conferences_wikicfp) + len(conferences_crossref)
        total_journals = len(journals_crossref)
        
        logger.info(f"Found {total_conferences} conferences and {total_journals} journals for domain: {domain}")
        logger.info(f"Sources: WikiCFP({len(conferences_wikicfp)}), CrossRef({len(conferences_crossref)}+{len(journals_crossref)})")
        
        # Combine all results
        all_conferences = conferences_wikicfp + conferences_crossref
        all_journals = journals_crossref
        combined = all_conferences + all_journals
        
        if not combined:
            logger.warning(f"No paper calls found for domain: {domain}")
            
            # Use fallback data if enabled
            if should_use_fallback():
                logger.info("Using fallback data for testing purposes")
                fallback_conferences = get_fallback_conferences(domain)
                fallback_journals = get_fallback_journals(domain)
                combined = fallback_conferences + fallback_journals
                logger.info(f"Added {len(combined)} fallback paper calls")
            else:
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