"""
Academic API services for research paper search and retrieval.

This module provides clients for various academic databases and APIs:
- Semantic Scholar: AI-powered semantic search and citation analysis
- arXiv: Physics, mathematics, computer science preprints
- Crossref: DOI metadata and citation information  
- PubMed: Biomedical and life sciences literature

Each client implements a standardized interface for searching papers,
retrieving metadata, and accessing citations/references.
"""

from .clients import (
    SemanticScholarClient,
    ArxivClient,
    CrossrefClient,
    PubMedClient,
)

from .common import (
    BaseAcademicClient,
    RateLimitError,
    APIError,
    PaperNormalizer,
)

__all__ = [
    # Clients
    "SemanticScholarClient",
    "ArxivClient", 
    "CrossrefClient",
    "PubMedClient",
    
    # Common
    "BaseAcademicClient",
    "RateLimitError",
    "APIError",
    "PaperNormalizer",
]

__version__ = "2.0.0"
