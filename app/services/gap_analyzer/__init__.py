"""
Gap Analyzer Service for ScholarAI

Autonomous Research Frontier Agent that analyzes research papers and discovers
validated research gaps through iterative exploration and validation.
"""

from .models import (
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResearchGap,
    ProcessMetadata,
    PaperAnalysis,
)
from .orchestrator import GapAnalysisOrchestrator

__all__ = [
    "GapAnalysisRequest",
    "GapAnalysisResponse", 
    "ResearchGap",
    "ProcessMetadata",
    "PaperAnalysis",
    "GapAnalysisOrchestrator",
]