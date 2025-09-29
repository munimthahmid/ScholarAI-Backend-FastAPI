# Frontend SSE Integration (Next.js sketch)

Use Server-Sent Events to stream graph progress.

Basic client utility:

```ts
export async function streamGraph(runId: string, onEvent: (evt: any) => void) {
  const res = await fetch(`/api/graphs/research:stream/${runId}`);
  if (!res.body) throw new Error("Missing body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      for (const line of part.split("\n")) {
        if (line.startsWith("data: ")) {
          const json = line.slice("data: ".length);
          try { onEvent(JSON.parse(json)); } catch {}
        }
      }
    }
  }
}
```

Event shapes:
- token: `{ type: "token", node: "writer", data: { token: string } }`
- node events: `on_start`, `on_end`, etc., from LangGraph
- finished: `{ type: "finished" }` emitted at the end

Start a run first:
```ts
const start = await fetch('/api/graphs/research:start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'machine learning', domain: 'CS', target_size: 3 })
});
const { run_id } = await start.json();
await streamGraph(run_id, (evt) => console.log(evt));
```

Gap graph (same pattern):
- POST `/api/graphs/gap:start` with `{ raw_text?, pdf_url?, title?, domain }`
- GET `/api/graphs/gap:stream/{run_id}`

