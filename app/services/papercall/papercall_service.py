"""
Main PaperCall service
"""

import logging
from typing import List, Dict, Any, Optional
from .aggregator import aggregate_all, get_paper_calls_by_type

logger = logging.getLogger(__name__)


class PaperCallService:
    """
    Main service for fetching and aggregating paper calls
    """
    
    def __init__(self):
        """Initialize the PaperCall service"""
        logger.info("PaperCall service initialized")
    
    def get_paper_calls(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get all paper calls for a given domain
        
        Args:
            domain: Research domain to search for
            
        Returns:
            List of paper call dictionaries
        """
        try:
            logger.info(f"Fetching paper calls for domain: {domain}")
            return aggregate_all(domain)
        except Exception as e:
            logger.error(f"Error fetching paper calls: {e}")
            return []
    
    def get_conferences(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get conference calls for papers for a given domain
        
        Args:
            domain: Research domain to search for
            
        Returns:
            List of conference call dictionaries
        """
        try:
            logger.info(f"Fetching conferences for domain: {domain}")
            grouped = get_paper_calls_by_type(domain, "conference")
            return grouped.get("conference", [])
        except Exception as e:
            logger.error(f"Error fetching conferences: {e}")
            return []
    
    def get_journals(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get journal special issues for a given domain
        
        Args:
            domain: Research domain to search for
            
        Returns:
            List of journal special issue dictionaries
        """
        try:
            logger.info(f"Fetching journal special issues for domain: {domain}")
            grouped = get_paper_calls_by_type(domain, "journal")
            return grouped.get("journal", [])
        except Exception as e:
            logger.error(f"Error fetching journals: {e}")
            return []
    
    def get_paper_calls_by_source(self, domain: str, source: str) -> List[Dict[str, Any]]:
        """
        Get paper calls from a specific source
        
        Args:
            domain: Research domain to search for
            source: Source name (WikiCFP, MDPI, Taylor & Francis, Springer)
            
        Returns:
            List of paper call dictionaries from the specified source
        """
        try:
            logger.info(f"Fetching paper calls from {source} for domain: {domain}")
            all_calls = aggregate_all(domain)
            filtered = [call for call in all_calls if call.get("source") == source]
            return filtered
        except Exception as e:
            logger.error(f"Error fetching from {source}: {e}")
            return []
    
    def get_statistics(self, domain: str) -> Dict[str, Any]:
        """
        Get statistics about paper calls for a given domain
        
        Args:
            domain: Research domain to search for
            
        Returns:
            Dictionary with statistics
        """
        try:
            logger.info(f"Getting statistics for domain: {domain}")
            all_calls = aggregate_all(domain)
            
            # Count by type
            conferences = len([call for call in all_calls if call.get("type") == "conference"])
            journals = len([call for call in all_calls if call.get("type") == "journal"])
            
            # Count by source
            source_counts = {}
            for call in all_calls:
                source = call.get("source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                "domain": domain,
                "total_calls": len(all_calls),
                "conferences": conferences,
                "journals": journals,
                "sources": source_counts,
                "timestamp": "2024-01-01T00:00:00Z"  # Could use actual timestamp
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "domain": domain,
                "total_calls": 0,
                "conferences": 0,
                "journals": 0,
                "sources": {},
                "error": str(e)
            }


# Global service instance
papercall_service = PaperCallService() 