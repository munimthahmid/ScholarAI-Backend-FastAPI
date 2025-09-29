from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from app.graph.config import get_checkpointer

from app.models.graph import GapJobInput, GapResult, GapItem
from app.services.extractor.text_extractor import TextExtractorAgent
from app.services.b2_storage import B2StorageService
from app.services.websearch.search_orchestrator import MultiSourceSearchOrchestrator
from app.services.websearch.config import SearchConfig
from app.graph.config import get_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class GapState(TypedDict, total=False):
    title: Optional[str]
    domain: str
    raw_text: Optional[str]
    pdf_url: Optional[str]
    analysis: Dict[str, Any]
    gaps: List[Dict[str, Any]]


async def pdf_or_text_node(state: GapState) -> GapState:
    # Prefer provided raw_text; otherwise try to extract from PDF
    if state.get("raw_text"):
        return state
    pdf_url = state.get("pdf_url")
    if not pdf_url:
        return state

    # Best-effort extraction; do not fail the run
    try:
        agent = TextExtractorAgent(B2StorageService())
        text, method = await agent.extract_text_from_pdf(pdf_url=pdf_url, paper_id=state.get("title") or "paper")
        return {**state, "raw_text": text}
    except Exception:
        return state


def _fallback_analysis(text: str) -> Dict[str, Any]:
    # Very small heuristic parser
    sections = {
        "title": None,
        "key_findings": [],
        "limitations": [],
        "future_work": [],
    }
    # Grab title
    m = re.search(r"^\s*Title\s*:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if m:
        sections["title"] = m.group(1).strip()
    # Split lines into buckets by keywords
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in ("result:", "results:", "finding", "findings")):
            sections["key_findings"].append(ln)
        if any(k in low for k in ("limitation", "challenge", "bottleneck")):
            sections["limitations"].append(ln)
        if any(k in low for k in ("future work", "further work", "next step")):
            sections["future_work"].append(ln)
    return sections


async def analyze_node(state: GapState) -> GapState:
    text = state.get("raw_text") or ""
    if not text:
        return {**state, "analysis": {}}

    llm = get_chat_model()
    if llm:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Extract key findings, limitations, and future work as JSON arrays."),
                (
                    "human",
                    (
                        "From the following paper text, extract: title, key_findings (max 5 short bullets),"
                        " limitations (max 5), and future_work (max 5). Return JSON with keys: title, key_findings,"
                        " limitations, future_work. Text:\n\n{text}"
                    ),
                ),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        try:
            import json

            out = await chain.ainvoke({"text": text})
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                return {**state, "analysis": parsed}
        except Exception:
            pass

    # Fallback
    return {**state, "analysis": _fallback_analysis(text)}


async def identify_node(state: GapState) -> GapState:
    analysis = state.get("analysis") or {}
    gaps: List[Dict[str, Any]] = []
    # Use limitations and future work as gap candidates
    for src_key in ("limitations", "future_work"):
        for item in analysis.get(src_key, []) or []:
            desc = item if isinstance(item, str) else str(item)
            if desc:
                gaps.append({"description": desc, "evidence": [src_key], "confidence": 0.3})
    # If nothing, derive basic gap from title
    if not gaps and analysis.get("title"):
        gaps.append({"description": f"Investigate open problems related to: {analysis['title']}", "evidence": ["title"], "confidence": 0.2})
    return {**state, "gaps": gaps}


async def validate_node(state: GapState) -> GapState:
    gaps = state.get("gaps") or []
    if not gaps:
        return state
    # Light validation via your search orchestrator with tiny budget
    cfg = SearchConfig(papers_per_source=1, max_search_rounds=1, target_batch_size=1, enable_ai_refinement=False)
    orchestrator = MultiSourceSearchOrchestrator(cfg)
    validated: List[Dict[str, Any]] = []
    for g in gaps[:5]:
        query = g.get("description", "")
        papers = await orchestrator.search_papers([query], state.get("domain", "Computer Science"), 1)
        conf = 0.6 if papers else g.get("confidence", 0.3)
        v = {**g, "confidence": conf, "evidence": (g.get("evidence") or []) + (["search_match"] if papers else [])}
        validated.append(v)
    return {**state, "gaps": validated}


def build_gap_graph(checkpointer=None):
    builder = StateGraph(GapState)
    builder.add_node("pdf_or_text", pdf_or_text_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("identify", identify_node)
    builder.add_node("validate", validate_node)

    builder.set_entry_point("pdf_or_text")
    builder.add_edge("pdf_or_text", "analyze")
    builder.add_edge("analyze", "identify")
    builder.add_edge("identify", "validate")
    builder.add_edge("validate", END)

    if checkpointer is None:
        checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


graph = build_gap_graph()
