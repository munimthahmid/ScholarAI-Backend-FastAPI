"""
PaperCall fetchers for different sources
"""

from .wikicfp import fetch_cfp_info
from .crossref import fetch_crossref_special_issues, fetch_crossref_conferences
from .fallback_data import get_fallback_conferences, get_fallback_journals, should_use_fallback

__all__ = [
    "fetch_cfp_info",
    "fetch_crossref_special_issues",
    "fetch_crossref_conferences",
    "get_fallback_conferences",
    "get_fallback_journals",
    "should_use_fallback"
] 