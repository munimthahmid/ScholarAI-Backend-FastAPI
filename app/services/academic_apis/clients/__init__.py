"""
Academic API client implementations.
"""

from .semantic_scholar_client import SemanticScholarClient
from .pubmed_client import PubMedClient
from .arxiv_client import ArxivClient
from .crossref_client import CrossrefClient

__all__ = [
    "SemanticScholarClient",
    "PubMedClient",
    "ArxivClient", 
    "CrossrefClient",
] 