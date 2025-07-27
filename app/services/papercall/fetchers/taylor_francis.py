"""
Taylor & Francis fetcher for special issues
"""

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def fetch_taylor_special_issues(domain="machine learning"):
    """
    Fetch special issues from Taylor & Francis journals
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of special issue dictionaries
    """
    try:
        url = "https://think.taylorandfrancis.com/special_issues/"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        issues = []
        for card in soup.select(".listing-item__content"):
            try:
                title_tag = card.select_one("h2 a")
                summary = card.select_one("p")
                
                if not title_tag:
                    continue

                title = title_tag.text.strip()
                link = title_tag["href"]
                description = summary.text.strip() if summary else ""

                # Check if domain matches title or description
                if (domain.lower() in title.lower() or 
                    domain.lower() in description.lower()):
                    
                    issues.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "type": "journal",
                        "source": "Taylor & Francis"
                    })
            except Exception as e:
                logger.warning(f"Error parsing Taylor & Francis issue: {e}")
                continue

        logger.info(f"Found {len(issues)} Taylor & Francis special issues for domain: {domain}")
        return issues
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from Taylor & Francis: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Taylor & Francis fetcher: {e}")
        return [] 