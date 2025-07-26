"""
PaperCall fetchers for different sources
"""

from .wikicfp import fetch_cfp_info
from .mdpi import fetch_mdpi_special_issues
from .taylor_francis import fetch_taylor_special_issues
from .springer import fetch_springer_special_issues

__all__ = [
    "fetch_cfp_info",
    "fetch_mdpi_special_issues", 
    "fetch_taylor_special_issues",
    "fetch_springer_special_issues"
] 