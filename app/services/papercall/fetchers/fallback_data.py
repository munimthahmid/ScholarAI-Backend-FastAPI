"""
Fallback data for paper calls when all sources fail
This is used for testing and development purposes
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_fallback_conferences(domain="machine learning"):
    """
    Get fallback conference data for testing
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of fallback conference dictionaries
    """
    # Generate some realistic fallback data
    current_date = datetime.now()
    
    fallback_conferences = [
        {
            "title": f"International Conference on {domain} (IC{domain.replace(' ', '')})",
            "link": f"https://example.com/ic{domain.replace(' ', '').lower()}",
            "type": "conference",
            "source": "Fallback",
            "dates": f"{(current_date + timedelta(days=90)).strftime('%B %Y')}",
            "location": "Virtual/Online",
            "deadline": f"{(current_date + timedelta(days=30)).strftime('%m/%d/%Y')}"
        },
        {
            "title": f"Workshop on {domain} Applications",
            "link": f"https://example.com/workshop-{domain.replace(' ', '-').lower()}",
            "type": "conference",
            "source": "Fallback",
            "dates": f"{(current_date + timedelta(days=120)).strftime('%B %Y')}",
            "location": "TBD",
            "deadline": f"{(current_date + timedelta(days=45)).strftime('%m/%d/%Y')}"
        },
        {
            "title": f"Annual {domain} Symposium",
            "link": f"https://example.com/symposium-{domain.replace(' ', '-').lower()}",
            "type": "conference",
            "source": "Fallback",
            "dates": f"{(current_date + timedelta(days=180)).strftime('%B %Y')}",
            "location": "Conference Center",
            "deadline": f"{(current_date + timedelta(days=60)).strftime('%m/%d/%Y')}"
        }
    ]
    
    logger.info(f"Using fallback data: {len(fallback_conferences)} conferences for domain: {domain}")
    return fallback_conferences


def get_fallback_journals(domain="machine learning"):
    """
    Get fallback journal data for testing
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of fallback journal dictionaries
    """
    fallback_journals = [
        {
            "title": f"Special Issue on {domain} in Modern Applications",
            "link": f"https://example.com/journal-{domain.replace(' ', '-').lower()}",
            "type": "journal",
            "source": "Fallback",
            "journal": f"Journal of {domain} Research",
            "deadline": f"{(datetime.now() + timedelta(days=45)).strftime('%m/%d/%Y')}"
        },
        {
            "title": f"Advances in {domain}: Theory and Practice",
            "link": f"https://example.com/advances-{domain.replace(' ', '-').lower()}",
            "type": "journal",
            "source": "Fallback",
            "journal": f"Advances in {domain}",
            "deadline": f"{(datetime.now() + timedelta(days=60)).strftime('%m/%d/%Y')}"
        }
    ]
    
    logger.info(f"Using fallback data: {len(fallback_journals)} journals for domain: {domain}")
    return fallback_journals


def should_use_fallback():
    """
    Determine if fallback data should be used
    This can be controlled by environment variables or configuration
    
    Returns:
        Boolean indicating if fallback should be used
    """
    import os
    return os.getenv("USE_PAPERCALL_FALLBACK", "false").lower() == "true" 