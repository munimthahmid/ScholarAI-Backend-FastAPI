# ScholarAI LangGraph Refactor — Working Principles

Purpose: keep the codebase minimal, clean, and independently deployable while moving research workflows to LangChain + LangGraph. Favor correctness and simplicity over features you won’t use immediately.

- Minimal first, expand later
  - Ship a small, working multi‑agent graph; add tools/nodes incrementally.
  - Prefer composition over inheritance and avoid deep class trees.

- Single orchestration surface
  - All long‑running research jobs run through LangGraph graphs with a single FastAPI layer for start/stream/status.
  - Remove RabbitMQ + Spring coupling; HTTP/SSE is the default integration for a Next.js frontend.

- Clear, typed contracts
  - Define Pydantic v2 models for inputs/outputs per graph. Keep them small and explicit.
  - Use structured outputs from LLMs instead of ad‑hoc JSON parsing.

- Provider‑agnostic LLM interface
  - Start with `langchain-openai` (or Anthropic) via env variables; swap providers with one place in config.

- Deterministic non‑LLM logic
  - Dedup, filtering, ranking, and glue logic are pure Python nodes (no hidden global state).

- Simple persistence and streaming
  - Use LangGraph checkpointer (SQLite by default) for resumability.
  - Use SSE for event streaming to the frontend; keep payloads small and typed.

- Safe environment handling
  - Read secrets only in config layers; never hard‑code API keys.

- Logging and observability
  - Use structured logging (json or key=val) and per‑run IDs.
  - Keep logs concise; large artifacts go to storage if needed.

- Testing focus
  - Unit test each pure node; a single E2E test per graph happy path.
  - Prefer fixtures with static inputs over network calls when possible.

