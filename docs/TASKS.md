# ScholarAI → LangGraph Migration Tasks

Legend: [P0]=blocker, [P1]=important, [P2]=nice‑to‑have

## Phase 0 — Foundations
- [DONE] Create LangGraph scaffolding under `app/graph/` (nodes, tools, graphs, config)
- [DONE] Add dependencies: `langgraph`, `langchain`, `langchain-openai`, `langchain-community`, `sse-starlette`
- [SKIPPED] Introduce checkpointer (kept in-memory for now; can switch to SQLite)
- [DONE] Add minimal FastAPI routes: start job, stream SSE, get status

## Phase 1 — Research Graph MVP
- [DONE] Define models: `ResearchJobInput`, `ResearchEvent`, `ResearchResult`
- [DONE] Nodes: planner (simple), websearch (existing orchestrator), dedup/filter (existing), writer/summarizer (LLM+fallback)
- [N/A] Wrap clients as Tools (kept orchestrator for minimal changes)
- [DONE] Streaming event mapping (token events)
- [DONE] E2E test: start → stream → finish

## Phase 2 — Extraction + Gap Analysis
- [DONE] Add text/PDF node (prefers `raw_text`, optional PDF extraction with `TextExtractorAgent`)
- [DONE] Paper analysis node (LLM structured output + heuristic fallback)
- [DONE] Gap identification & validation nodes (uses websearch orchestrator for light validation)
- [DONE] New `/graphs/gap:*` endpoints with E2E tests

## Phase 3 — API Surface + Frontend Integration
- [DONE] Stable REST: `POST /graphs/research:start` → `{run_id}`
- [DONE] SSE: `GET /graphs/research:stream/{run_id}`
- [DONE] Status: `GET /graphs/run/{run_id}`
- [TODO] Add auth hooks (bearer token), tighten CORS

## Phase 4 — Migration + Cleanup
- [IN-PROGRESS] Replace RabbitMQ entry points with HTTP/SSE flows (new flows exist; legacy untouched for compatibility/tests)
- [P1] Keep optional adapter for RabbitMQ if required
- [P1] Deprecate legacy orchestrators behind thin tool wrappers
- [DONE] Remove obvious stray files; more cleanup after adoption

## Phase 5 — Hardening
- [P1] Backoff/retry in tool nodes; per‑tool rate limits
- [P1] Structured logging with run IDs
- [P2] Add checkpoint resume (switch to SQLite/Postgres checkpointer)
- [P2] Horizontal scale notes (multi‑process workers, Postgres checkpointer)
