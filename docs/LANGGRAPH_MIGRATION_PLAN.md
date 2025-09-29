# ScholarAI LangGraph Migration Plan

This plan refactors ScholarAI into a minimal, independent, and scalable multi‑agent system using LangChain + LangGraph with FastAPI. It removes Spring/RabbitMQ coupling and exposes a simple HTTP + SSE surface for a Next.js frontend.

## Goals
- Independent backend: no Spring/RabbitMQ dependency for orchestration
- Minimal code: small, composable nodes and tools
- Multi‑agent via LangGraph: clear graph of planner → tools → analyzers
- Streamed UX: live progress via SSE
- Resumable runs: checkpointing with SQLite (default), Postgres (optional)

## Current State (observed)
- FastAPI app with RabbitMQ consumer and multiple service orchestrators (websearch, gap analyzer, PDF processing)
- Tests and utilities exist; README shows prior reliance on Spring + RabbitMQ
- LLM usage is Gemini‑centric in places; several heavy libs are installed

## Target Architecture
- Graphs
  - research_graph: planner (LLM) → websearch (tool) → dedup/filter (pure) → analyzer/writer (LLM) → result
  - gap_graph (Phase 2): paper_analysis (LLM) → gap_identify (LLM) → validate_gap (LLM+search) → result
- Nodes (minimal set)
  - planner_llm: produce sub‑tasks / refined queries (structured)
  - websearch_tool: call search tools (Tavily or wrapped clients)
  - dedup_filter: merge results; deterministic
  - summarize_writer_llm: compress insight and compile results
  - pdf_extract_tool (Phase 2): wrap existing `app/services/pdf_processor`
  - paper_analyze_llm (Phase 2): structured output with sections/claims/limits
  - gap_identify_llm (Phase 2)
  - gap_validate_llm (Phase 2) → optionally invokes websearch_tool
- State & persistence
  - Use LangGraph checkpointer (SQLite file under `./data/checkpoints.db`)
  - Each run has `run_id`; events stream with that id
- API surface
  - POST ` /graphs/research:start` → `{ run_id }`
  - GET  ` /graphs/research:stream/{run_id}` (SSE)
  - GET  ` /graphs/run/{run_id}` → status/result if finished

## Minimal Directory Layout
- `app/graph/config.py` — model provider, checkpointer setup, settings
- `app/graph/tools/search.py` — Tavily or wrapped academic clients as Tools
- `app/graph/nodes/planner.py` — LLM planner with structured output
- `app/graph/nodes/postprocess.py` — dedup/filter helpers
- `app/graph/nodes/writer.py` — summarizer/composer LLM
- `app/graph/graphs/research.py` — LangGraph wiring and entry points
- `app/models/graph.py` — Pydantic models: inputs, events, results
- `app/api/routes/graphs.py` — FastAPI endpoints (start/stream/status)

## Models (sketch)
- ResearchJobInput: query, domain?, target_size?, constraints?
- ResearchEvent: type (node_started|chunk|node_completed|error|finished), payload, ts, run_id
- ResearchResult: papers[], summary, citations

## Dependencies to add
- langgraph, langchain, langchain-openai, langchain-community
- sse-starlette (SSE streaming)
- Optional: tavily-python (simple search tool); otherwise wrap existing clients

## Graph Wiring (pseudo‑code)
```
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ResearchState(TypedDict):
  query: str
  refined_queries: List[str]
  results: List[dict]
  summary: str

builder = StateGraph(ResearchState)

builder.add_node("plan", planner_llm)
builder.add_node("search", websearch_tool)
builder.add_node("dedup", dedup_filter)
builder.add_node("write", summarize_writer_llm)

builder.set_entry_point("plan")

builder.add_edge("plan", "search")

def need_more_search(state):
  return "search" if len(state.get("results", [])) < target else "write"

builder.add_conditional_edges("dedup", need_more_search, {"search": "search", "write": "write"})

builder.add_edge("search", "dedup")

builder.add_edge("write", END)

graph = builder.compile(checkpointer=sqlite_saver)
```

## API and Streaming
- Start: validate `ResearchJobInput`, create run in checkpointer, kick off `graph.astream_events()` in a background task, return `run_id`.
- Stream: SSE endpoint consumes `graph.astream_events(run_id=...)` and forwards LangGraph events as typed `ResearchEvent`s.
- Status: read from checkpointer; if finished, return `ResearchResult`.

Event types we expect to forward:
- node_started, node_completed, stream_token (for LLM), error, finished

## Migration Strategy (Phased)
1) Foundations (Phase 0)
- Add `app/graph/` scaffold, checkpointer, minimal research graph with mocked tools
- Add start/stream/status endpoints and a basic E2E test

2) Research Graph MVP (Phase 1)
- Use Tavily (or wrapped current clients) in `websearch_tool`
- Implement naive dedup + top‑N selection
- Writer node produces short summary and citations

3) Extraction + Gap Analysis (Phase 2)
- Wrap `pdf_processor` as a tool node
- Add paper analyzer + gap identification/validation nodes
- Conditional edges control validation rounds

4) API Surface + Frontend (Phase 3)
- Stabilize routes and SSE protocol; provide example Next.js consumer

5) Migration + Cleanup (Phase 4)
- Switch existing endpoints to call graphs internally
- Remove RabbitMQ orchestration paths; keep adapter only if needed

6) Hardening (Phase 5)
- Retries, rate limits, structured logs, checkpoint resume tests
- Optional: swap SQLite with Postgres checkpointer for multi‑instance scaling

## Acceptance Criteria per Phase
- Phase 0: `POST /graphs/research:start` returns `run_id`; `GET ...:stream/{run_id}` yields events; test verifies finish event
- Phase 1: Graph returns actual papers and a non‑empty summary for a known query
- Phase 2: Gap analysis returns at least one validated gap for a sample paper
- Phase 3: Next.js demo page streams progress and displays results
- Phase 4: No runtime dependency on Spring/RabbitMQ in default deployment

## Risks & Trade‑offs
- Wrapping existing many clients vs. using Tavily: Tavily reduces code but fewer scholarly‑specific filters; trade precision for simplicity. We can keep both via a `use_wrapped_clients` flag.
- SSE vs WebSocket: SSE is simpler and enough for unidirectional streams; switch later if needed.
- Provider quotas: choose a single default model, make it configurable, and add backoff in nodes.

## Next.js SSE Example (sketch)
```
const res = await fetch(`/api/graphs/research:stream/${runId}`);
const reader = res.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  const text = decoder.decode(value, { stream: true });
  // parse SSE lines and update UI
}
```

## What We Keep vs Replace
- Keep: your PDF processor, dedup/filter logic (as pure nodes), domain parsers, tests where still relevant
- Replace: RabbitMQ orchestrators with LangGraph graphs; ad‑hoc LLM prompting with structured output chains

## Immediate Next Steps
- Add dependencies and scaffold `app/graph/` with a runnable stub graph
- Add minimal FastAPI routes (start/stream/status)
- Prove end‑to‑end event streaming with a trivial graph, then swap in real nodes
