"""
Search filter implementations for different academic sources
"""
from .base import BaseSearchFilter, DateFilterMixin
from .semantic_scholar import SemanticScholarFilter
from .pubmed import PubMedFilter
from .arxiv import ArxivFilter
from .crossref import CrossrefFilter
from .google_scholar import GoogleScholarFilter

from typing import Dict, Type


class FilterFactory:
    """
    Factory class for creating appropriate filter instances based on source name.
    """
    
    _filters: Dict[str, Type[BaseSearchFilter]] = {
        "Semantic Scholar": SemanticScholarFilter,
        "PubMed": PubMedFilter,
        "arXiv": ArxivFilter,
        "Crossref": CrossrefFilter,
        "Google Scholar": GoogleScholarFilter,
    }
    
    @classmethod
    def create_filter(cls, source_name: str, recent_years_filter: int = 5) -> BaseSearchFilter:
        """
        Create a filter instance for the specified source.
        
        Args:
            source_name: Name of the academic source
            recent_years_filter: Number of recent years to filter
            
        Returns:
            Appropriate filter instance
            
        Raises:
            ValueError: If source_name is not supported
        """
        filter_class = cls._filters.get(source_name)
        if not filter_class:
            raise ValueError(f"No filter implementation for source: {source_name}")
        
        return filter_class(recent_years_filter=recent_years_filter)
    
    @classmethod
    def get_supported_sources(cls) -> list:
        """Get list of supported academic sources"""
        return list(cls._filters.keys())
    
    @classmethod
    def register_filter(cls, source_name: str, filter_class: Type[BaseSearchFilter]):
        """
        Register a new filter implementation.
        
        Args:
            source_name: Name of the academic source
            filter_class: Filter class that extends BaseSearchFilter
        """
        cls._filters[source_name] = filter_class


__all__ = [
    "BaseSearchFilter",
    "DateFilterMixin", 
    "SemanticScholarFilter",
    "PubMedFilter",
    "ArxivFilter", 
    "CrossrefFilter",
    "GoogleScholarFilter",
    "FilterFactory"
] 