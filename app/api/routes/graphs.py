from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator, Dict, Any

import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from app.models.graph import (
    ResearchJobInput,
    ResearchEvent,
    ResearchResult,
    GapJobInput,
    GapResult,
    GapItem,
)
from app.graph.graphs.research import graph as research_graph
from app.graph.graphs.gap import graph as gap_graph


router = APIRouter()

_RUN_INPUTS: Dict[str, ResearchJobInput] = {}
_RUN_RESULTS: Dict[str, ResearchResult] = {}
_RUN_TASKS: Dict[str, asyncio.Task] = {}


def _safe_str(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return ""


def map_langgraph_event(ev: Dict[str, Any], run_id: str) -> ResearchEvent:
    etype = ev.get("event", "message")
    node = ev.get("name")
    data = ev.get("data", {})

    # Token streaming from LLMs
    if etype in ("on_chat_model_stream", "on_llm_stream"):
        chunk = None
        if isinstance(data, dict):
            chunk = data.get("chunk")
        token = None
        if chunk is not None:
            # Try common attributes first
            token = getattr(chunk, "content", None)
            if not token and isinstance(chunk, dict):
                token = chunk.get("content") or chunk.get("delta")
        token = token or _safe_str(chunk)
        return ResearchEvent(run_id=run_id, type="token", node=node, data={"token": token})

    # Default: sanitize data to avoid unserializable content
    if not isinstance(data, dict):
        data = {"repr": _safe_str(data)}
    return ResearchEvent(run_id=run_id, type=etype, node=node, data=data)


async def _run_graph(run_id: str, payload: ResearchJobInput) -> None:
    state = {"query": payload.query, "domain": payload.domain, "target_size": payload.target_size}
    final = await research_graph.ainvoke(state, config={"configurable": {"thread_id": run_id}})
    res = ResearchResult(
        run_id=run_id,
        query=payload.query,
        domain=payload.domain,
        papers=final.get("results", []) or [],
        summary=final.get("summary", ""),
    )
    _RUN_RESULTS[run_id] = res


def _require_auth(request: Request):
    if os.getenv("GRAPHS_REQUIRE_AUTH", "false").lower() != "true":
        return
    token = os.getenv("GRAPHS_AUTH_TOKEN", "")
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    provided = header.split(" ", 1)[1].strip()
    if token and provided != token:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/research:start")
async def start_research_job(request: Request, payload: ResearchJobInput, background_tasks: BackgroundTasks) -> Dict[str, str]:
    _require_auth(request)
    run_id = str(uuid.uuid4())
    _RUN_INPUTS[run_id] = payload
    # Fire-and-forget background run using FastAPI background tasks
    background_tasks.add_task(_run_graph, run_id, payload)
    return {"run_id": run_id}


@router.get("/research:stream/{run_id}")
async def stream_research_events(request: Request, run_id: str):
    _require_auth(request)
    if run_id not in _RUN_INPUTS:
        raise HTTPException(status_code=404, detail="run_id not found")

    async def event_gen() -> AsyncGenerator[str, None]:
        input_model = _RUN_INPUTS[run_id]
        initial_state = {
            "query": input_model.query,
            "domain": input_model.domain,
            "target_size": input_model.target_size,
        }

        async for ev in research_graph.astream_events(
            initial_state, config={"configurable": {"thread_id": run_id}}
        ):
            evt = map_langgraph_event(ev, run_id)

            # Capture final state when graph ends
            if evt.type == "on_end":
                d = ev.get("data", {})
                final_state = d.get("state", {}) if isinstance(d, dict) else {}
                res = ResearchResult(
                    run_id=run_id,
                    query=initial_state["query"],
                    domain=initial_state.get("domain", ""),
                    papers=final_state.get("results", []) or [],
                    summary=final_state.get("summary", ""),
                )
                _RUN_RESULTS[run_id] = res
            yield f"data: {evt.model_dump_json()}\n\n"

        # Send an explicit finished event after the stream completes
        final_evt = ResearchEvent(run_id=run_id, type="finished", data={})
        yield f"data: {final_evt.model_dump_json()}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    res = _RUN_RESULTS.get(run_id)
    if not res:
        return {"run_id": run_id, "status": "running"}
    return res


# Gap graph endpoints

@router.post("/gap:start")
async def start_gap_job(request: Request, payload: GapJobInput, background_tasks: BackgroundTasks) -> Dict[str, str]:
    _require_auth(request)
    run_id = str(uuid.uuid4())
    _RUN_INPUTS[run_id] = payload  # type: ignore[assignment]

    async def _run_gap():
        state = {
            "title": payload.title,
            "domain": payload.domain,
            "raw_text": payload.raw_text,
            "pdf_url": payload.pdf_url,
        }
        final = await gap_graph.ainvoke(state, config={"configurable": {"thread_id": run_id}})
        gaps = [GapItem(**g) if not isinstance(g, GapItem) else g for g in final.get("gaps", [])]
        res = GapResult(run_id=run_id, title=payload.title, domain=payload.domain, gaps=gaps, analysis=final.get("analysis", {}))
        _RUN_RESULTS[run_id] = res  # type: ignore[assignment]

    background_tasks.add_task(_run_gap)
    return {"run_id": run_id}


@router.get("/gap:stream/{run_id}")
async def stream_gap_events(request: Request, run_id: str):
    _require_auth(request)
    if run_id not in _RUN_INPUTS:
        raise HTTPException(status_code=404, detail="run_id not found")

    async def event_gen() -> AsyncGenerator[str, None]:
        input_model = _RUN_INPUTS[run_id]
        initial_state = {
            "title": getattr(input_model, "title", None),
            "domain": getattr(input_model, "domain", "Computer Science"),
            "raw_text": getattr(input_model, "raw_text", None),
            "pdf_url": getattr(input_model, "pdf_url", None),
        }

        async for ev in gap_graph.astream_events(initial_state, config={"configurable": {"thread_id": run_id}}):
            evt = map_langgraph_event(ev, run_id)
            if evt.type == "on_end":
                d = ev.get("data", {})
                final_state = d.get("state", {}) if isinstance(d, dict) else {}
                gaps = [GapItem(**g) if not isinstance(g, GapItem) else g for g in final_state.get("gaps", [])]
                res = GapResult(
                    run_id=run_id,
                    title=initial_state.get("title"),
                    domain=initial_state.get("domain", ""),
                    gaps=gaps,
                    analysis=final_state.get("analysis", {}),
                )
                _RUN_RESULTS[run_id] = res  # type: ignore[assignment]
            yield f"data: {evt.model_dump_json()}\n\n"

        final_evt = ResearchEvent(run_id=run_id, type="finished", data={})
        yield f"data: {final_evt.model_dump_json()}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
