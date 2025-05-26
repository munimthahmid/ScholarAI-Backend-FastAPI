"""
Academic APIs module for sophisticated paper discovery and retrieval.
"""

from .crossref_client import CrossrefClient
from .semantic_scholar_client import SemanticScholarClient
from .arxiv_client import ArxivClient
from .pubmed_client import PubMedClient
from .google_scholar_client import GoogleScholarClient

__all__ = [
    "CrossrefClient",
    "SemanticScholarClient",
    "ArxivClient",
    "PubMedClient",
    "GoogleScholarClient",
]
