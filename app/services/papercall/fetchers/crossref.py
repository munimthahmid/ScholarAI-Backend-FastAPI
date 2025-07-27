"""
CrossRef API fetcher for journal special issues and calls for papers
Uses the official CrossRef API for reliable results
"""

import requests
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def fetch_crossref_special_issues(domain="machine learning"):
    """
    Fetch special issues from CrossRef using the official API
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of journal special issue dictionaries
    """
    try:
        # CrossRef API endpoint
        url = "https://api.crossref.org/works"
        
        # Search for special issues in the domain
        search_terms = [
            f'"{domain}" AND "special issue"',
            f'"{domain}" AND "call for papers"',
            f'"{domain}" AND "cfp"'
        ]
        
        all_results = []
        
        for search_query in search_terms:
            try:
                params = {
                    "query": search_query,
                    "rows": 20,
                    "sort": "published",
                    "order": "desc"
                }
                
                headers = {
                    "User-Agent": "ScholarAI/1.0 (https://github.com/scholarai; scholarai@example.com)"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("message", {}).get("items", [])
                
                for item in items:
                    try:
                        # Extract title
                        title = item.get("title", [""])[0] if item.get("title") else ""
                        
                        # Extract DOI
                        doi = item.get("DOI", "")
                        
                        # Extract journal name
                        container_title = item.get("container-title", [""])[0] if item.get("container-title") else ""
                        
                        # Extract published date
                        published = item.get("published", {}).get("date-parts", [[]])[0]
                        published_date = "-".join(map(str, published)) if published else ""
                        
                        # Extract authors
                        authors = []
                        for author in item.get("author", []):
                            given = author.get("given", "")
                            family = author.get("family", "")
                            if given or family:
                                authors.append(f"{given} {family}".strip())
                        
                        # Extract link
                        link = f"https://doi.org/{doi}" if doi else ""
                        
                        # Determine if it's a special issue
                        is_special_issue = any(term in title.lower() for term in ["special issue", "call for papers", "cfp"])
                        
                        if is_special_issue:
                            # Extract deadline from title
                            deadline = extract_deadline_from_text(title)
                            
                            result = {
                                "title": title,
                                "link": link,
                                "type": "journal",
                                "source": "CrossRef",
                                "journal": container_title,
                                "doi": doi,
                                "published": published_date,
                                "authors": authors,
                                "deadline": deadline
                            }
                            
                            # Avoid duplicates
                            if not any(r.get("title") == title for r in all_results):
                                all_results.append(result)
                    
                    except Exception as e:
                        logger.warning(f"Error parsing CrossRef item: {e}")
                        continue
                
                # Small delay to be respectful to the API
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error fetching from CrossRef with query '{search_query}': {e}")
                continue
        
        logger.info(f"Found {len(all_results)} CrossRef special issues for domain: {domain}")
        return all_results
        
    except Exception as e:
        logger.error(f"Unexpected error in CrossRef API fetcher: {e}")
        return []


def fetch_crossref_conferences(domain="machine learning"):
    """
    Fetch conference proceedings from CrossRef
    
    Args:
        domain: Research domain to search for
        
    Returns:
        List of conference dictionaries
    """
    try:
        url = "https://api.crossref.org/works"
        
        search_terms = [
            f'"{domain}" AND "conference" AND "proceedings"',
            f'"{domain}" AND "workshop" AND "proceedings"'
        ]
        
        all_results = []
        
        for search_query in search_terms:
            try:
                params = {
                    "query": search_query,
                    "rows": 20,
                    "sort": "published",
                    "order": "desc"
                }
                
                headers = {
                    "User-Agent": "ScholarAI/1.0 (https://github.com/scholarai; scholarai@example.com)"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("message", {}).get("items", [])
                
                for item in items:
                    try:
                        title = item.get("title", [""])[0] if item.get("title") else ""
                        doi = item.get("DOI", "")
                        container_title = item.get("container-title", [""])[0] if item.get("container-title") else ""
                        
                        # Extract event information
                        event = item.get("event", {})
                        event_name = event.get("name", "")
                        event_location = event.get("location", "")
                        event_date = event.get("date", "")
                        
                        # Extract published date
                        published = item.get("published", {}).get("date-parts", [[]])[0]
                        published_date = "-".join(map(str, published)) if published else ""
                        
                        link = f"https://doi.org/{doi}" if doi else ""
                        
                        # Determine if it's a conference proceeding
                        is_conference = any(term in title.lower() for term in ["conference", "workshop", "symposium"])
                        
                        if is_conference:
                            result = {
                                "title": title,
                                "link": link,
                                "type": "conference",
                                "source": "CrossRef",
                                "conference": event_name or container_title,
                                "doi": doi,
                                "published": published_date,
                                "event_date": event_date,
                                "location": event_location,
                                "deadline": extract_deadline_from_text(title)
                            }
                            
                            # Avoid duplicates
                            if not any(r.get("title") == title for r in all_results):
                                all_results.append(result)
                    
                    except Exception as e:
                        logger.warning(f"Error parsing CrossRef conference item: {e}")
                        continue
                
                # Small delay to be respectful to the API
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error fetching from CrossRef conferences with query '{search_query}': {e}")
                continue
        
        logger.info(f"Found {len(all_results)} CrossRef conferences for domain: {domain}")
        return all_results
        
    except Exception as e:
        logger.error(f"Unexpected error in CrossRef conference fetcher: {e}")
        return []


def extract_deadline_from_text(text):
    """
    Extract deadline from text using various patterns
    
    Args:
        text: Text to search for deadlines
        
    Returns:
        Extracted deadline or None
    """
    try:
        # Common deadline patterns
        deadline_patterns = [
            r"deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"submission[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"cfp[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"due[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ]
        
        text_lower = text.lower()
        
        for pattern in deadline_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Return the first match
                return matches[0]
        
        return None
        
    except Exception:
        return None 