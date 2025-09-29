from __future__ import annotations

import asyncio
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END
from app.graph.config import get_checkpointer

from app.models.graph import ResearchJobInput, ResearchResult
from app.graph.config import get_chat_model

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.websearch.config import SearchConfig
from app.services.websearch.search_orchestrator import (
    MultiSourceSearchOrchestrator,
)


class ResearchState(TypedDict, total=False):
    query: str
    domain: str
    target_size: int
    refined_queries: List[str]
    results: List[Dict[str, Any]]
    summary: str


async def plan_node(state: ResearchState) -> ResearchState:
    # Minimal planner: use the input query as a single refined query
    query = state["query"].strip()
    return {**state, "refined_queries": [query]}


async def search_node(state: ResearchState) -> ResearchState:
    # Use existing orchestrator to perform real multi-source search
    refined = state.get("refined_queries") or [state["query"]]
    domain = state.get("domain", "Computer Science")
    target_size = int(state.get("target_size", 3))

    # Keep search very light for tests
    cfg = SearchConfig(
        papers_per_source=1,
        max_search_rounds=1,
        target_batch_size=target_size,
        enable_ai_refinement=False,
        recent_years_filter=5,
    )
    orchestrator = MultiSourceSearchOrchestrator(cfg)
    papers = await orchestrator.search_papers(refined, domain, target_size)
    return {**state, "results": papers}


async def write_node(state: ResearchState) -> ResearchState:
    """Summarize results using LLM if available; fallback to deterministic text."""
    results = state.get("results", [])
    n = len(results)
    query = state.get("query", "")
    domain = state.get("domain", "")

    # Try LLM summarization
    llm = get_chat_model()
    if llm and n > 0:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You write concise research digests."),
                (
                    "human",
                    (
                        "Summarize the following {n} papers for the query '{query}'"
                        " in domain '{domain}'. Provide a 2-3 sentence summary and list up to"
                        " 3 top titles separated by semicolons.\n\nPapers JSON: {papers_json}"
                    ),
                ),
            ]
        )
        from json import dumps

        chain = prompt | llm | StrOutputParser()
        text = await chain.ainvoke(
            {
                "n": n,
                "query": query,
                "domain": domain,
                "papers_json": dumps(results[:5], ensure_ascii=False),
            }
        )
        return {**state, "summary": text}

    # Fallback summary
    titles = ", ".join([r.get("title", "?") for r in results[:3]])
    summary = f"Found {n} papers for '{query}' in domain '{domain}'."
    if titles:
        summary += f" Top titles: {titles}"
    return {**state, "summary": summary}


def build_research_graph(checkpointer=None):
    builder = StateGraph(ResearchState)
    builder.add_node("plan", plan_node)
    builder.add_node("search", search_node)
    builder.add_node("write", write_node)

    builder.set_entry_point("plan")
    builder.add_edge("plan", "search")
    builder.add_edge("search", "write")
    builder.add_edge("write", END)

    if checkpointer is None:
        checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


# Global compiled graph
graph = build_research_graph()
