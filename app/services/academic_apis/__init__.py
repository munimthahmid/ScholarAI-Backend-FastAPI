"""
Academic APIs module for sophisticated paper discovery and retrieval.

This module provides a unified interface to multiple academic databases including:
- Semantic Scholar: Comprehensive citation network and AI-powered paper analysis
- PubMed: Biomedical and life sciences literature
- ArXiv: Preprints in physics, mathematics, computer science
- Crossref: DOI resolution and bibliographic metadata
- Google Scholar: Broad academic search across disciplines

The module uses common utilities and normalizers to provide consistent
paper data structures across all sources.
"""

from .clients import (
    SemanticScholarClient,
    PubMedClient,
    ArxivClient,
    CrossrefClient,
    GoogleScholarClient,
)

from .common import (
    BaseAcademicClient,
    PaperNormalizer,
    RateLimitError,
    APIError,
    InvalidResponseError,
)

__all__ = [
    # Client classes
    "SemanticScholarClient",
    "PubMedClient", 
    "ArxivClient",
    "CrossrefClient",
    "GoogleScholarClient",
    
    # Base classes and utilities
    "BaseAcademicClient",
    "PaperNormalizer",
    
    # Exceptions
    "RateLimitError",
    "APIError",
    "InvalidResponseError",
]

__version__ = "2.0.0"
