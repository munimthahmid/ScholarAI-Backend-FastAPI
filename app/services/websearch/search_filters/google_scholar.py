"""
Google Scholar search filter implementation
"""
from typing import Dict, Any

from .base import BaseSearchFilter, DateFilterMixin


class GoogleScholarFilter(BaseSearchFilter, DateFilterMixin):
    """
    Search filter implementation for Google Scholar.
    
    Google Scholar supports:
    - Year range filtering
    - Sort options
    - Patent exclusion
    - Language filtering
    """
    
    @property
    def source_name(self) -> str:
        return "Google Scholar"
    
    def _add_date_filter(self, filters: Dict[str, Any]):
        """Google Scholar uses year range format: 'YYYY-YYYY'"""
        self._add_year_range_filter(filters)
    
    def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
        """Add domain-specific filtering for Google Scholar"""
        # Google Scholar has limited domain filtering capabilities
        # Most filtering is done through query refinement rather than API filters
        
        if not domain:
            # Default to English for most academic searches
            filters["language"] = "en"
            return
        
        # We can set language preferences for certain domains
        domain_lower = domain.lower()
        
        # Default to English for most academic searches
        filters["language"] = "en"
        
        # Domain-specific optimizations through search parameters
        if any(term in domain_lower for term in ["computer science", "engineering"]):
            filters["cluster_duplicates"] = True
            
        elif any(term in domain_lower for term in ["medicine", "biology"]):
            filters["include_citations"] = True
            
        # Google Scholar doesn't have extensive API filter support
        # Most filtering happens through query construction
    
    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add Google Scholar specific optimizations"""
        # Focus on highly cited and recent papers
        filters["sort"] = "relevance"  # or "date" for recent papers
        filters["include_patents"] = False
        filters["include_citations"] = True
        
        # Scholar-specific quality filters
        filters["min_citations"] = 0  # Could be increased for higher quality
        filters["cluster_duplicates"] = True
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get Google Scholar filter capabilities"""
        base_info = super().get_filter_info()
        base_info.update({
            "date_format": "year_range",
            "available_optimizations": [
                "sort_by_relevance",
                "sort_by_date", 
                "exclude_patents",
                "include_citations",
                "cluster_duplicates",
                "language_filter"
            ],
            "sort_options": ["relevance", "date"],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "zh", "ja"],
            "limitations": [
                "Limited API filter support",
                "Rate limiting and CAPTCHA issues",
                "Filtering mainly through query construction"
            ],
            "note": "Google Scholar has limited programmatic access and is prone to blocking"
        })
        return base_info 