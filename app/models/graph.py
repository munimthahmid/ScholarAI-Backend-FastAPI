from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchJobInput(BaseModel):
    query: str = Field(..., min_length=2)
    domain: str = Field(default="Computer Science")
    target_size: int = Field(default=3, ge=1, le=20)


class ResearchEvent(BaseModel):
    run_id: str
    type: str
    node: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=datetime.utcnow)


class ResearchResult(BaseModel):
    run_id: str
    query: str
    domain: str
    papers: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class GapJobInput(BaseModel):
    # One of: raw_text or pdf_url
    raw_text: Optional[str] = None
    pdf_url: Optional[str] = None
    title: Optional[str] = None
    domain: str = Field(default="Computer Science")


class GapItem(BaseModel):
    description: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class GapResult(BaseModel):
    run_id: str
    title: Optional[str] = None
    domain: str
    gaps: List[GapItem] = Field(default_factory=list)
    analysis: Dict[str, Any] = Field(default_factory=dict)
