"""
Springer fetcher for special issues
"""

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def fetch_springer_special_issues(domain="machine learning"):
    """
    Fetch special issues from Springer journals
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of special issue dictionaries
    """
    try:
        url = "https://www.springer.com/gp/editors/special-issues"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        issues = []
        for li in soup.select("li a"):
            try:
                href = li.get("href", "")
                text = li.text.strip()

                if (href.startswith("/journal/") and 
                    domain.lower() in text.lower() and 
                    text and href):
                    
                    issues.append({
                        "title": text,
                        "link": "https://www.springer.com" + href,
                        "type": "journal",
                        "source": "Springer"
                    })
            except Exception as e:
                logger.warning(f"Error parsing Springer issue: {e}")
                continue

        logger.info(f"Found {len(issues)} Springer special issues for domain: {domain}")
        return issues
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from Springer: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Springer fetcher: {e}")
        return [] 