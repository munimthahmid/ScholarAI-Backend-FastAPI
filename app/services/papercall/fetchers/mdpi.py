"""
MDPI fetcher for special issues
"""

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def fetch_mdpi_special_issues(domain="machine learning"):
    """
    Fetch special issues from MDPI journals
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of special issue dictionaries
    """
    try:
        url = f"https://www.mdpi.com/search?q={domain}&section=SpecialIssue"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        issues = []
        for card in soup.select(".search-result .title-link"):
            try:
                title = card.text.strip()
                link = "https://www.mdpi.com" + card["href"]
                
                if title and link:
                    issues.append({
                        "title": title,
                        "link": link,
                        "type": "journal",
                        "source": "MDPI"
                    })
            except Exception as e:
                logger.warning(f"Error parsing MDPI issue: {e}")
                continue
                
        logger.info(f"Found {len(issues)} MDPI special issues for domain: {domain}")
        return issues
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from MDPI: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in MDPI fetcher: {e}")
        return [] 