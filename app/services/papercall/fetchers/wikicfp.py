"""
WikiCFP fetcher for conference calls for papers
"""

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def fetch_cfp_info(domain):
    """
    Fetch conference call for papers information from WikiCFP
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of conference call dictionaries
    """
    try:
        url = f"http://www.wikicfp.com/cfp/servlet/tool.search?q={domain}&year=a"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        contsec_div = soup.find('div', class_='contsec')
        
        if not contsec_div:
            logger.warning(f"No conference data found for domain: {domain}")
            return []

        rows = contsec_div.find_all('tr', bgcolor=['#f6f6f6', '#e6e6e6'])
        results = []

        for i in range(0, len(rows), 2):
            try:
                if i + 1 >= len(rows):
                    break
                    
                row1 = rows[i].find_all('td')
                row2 = rows[i + 1].find_all('td')

                if len(row1) < 1 or len(row2) < 3:
                    continue

                conf_name = row1[0].text.strip()
                link_tag = row1[0].find('a')
                link = "http://www.wikicfp.com" + link_tag['href'] if link_tag else ""

                when = row2[0].text.strip()
                where = row2[1].text.strip()
                deadline = row2[2].text.strip()

                results.append({
                    "title": conf_name,
                    "when": when,
                    "where": where,
                    "deadline": deadline,
                    "link": link,
                    "type": "conference",
                    "source": "WikiCFP"
                })
            except Exception as e:
                logger.warning(f"Error parsing conference row: {e}")
                continue
                
        logger.info(f"Found {len(results)} conferences for domain: {domain}")
        return results
        
    except requests.RequestException as e:
        logger.error(f"Error fetching from WikiCFP: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in WikiCFP fetcher: {e}")
        return [] 