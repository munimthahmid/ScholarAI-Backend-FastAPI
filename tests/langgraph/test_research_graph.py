import json
from typing import Iterator

from fastapi.testclient import TestClient
import os, sys

# Ensure repo root is on path for `import app`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app


client = TestClient(app)


def _iter_sse_lines(resp) -> Iterator[str]:
    for chunk in resp.iter_lines():
        if not chunk:
            continue
        line = chunk.decode("utf-8") if isinstance(chunk, (bytes, bytearray)) else str(chunk)
        if line.startswith("data: "):
            yield line[len("data: ") :]


def test_research_graph_stream_and_result():
    # Start a run
    start_payload = {"query": "machine learning", "domain": "Computer Science", "target_size": 1}
    r = client.post("/api/graphs/research:start", json=start_payload)
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert run_id

    # Stream events
    # Stream a few events (best effort)
    with client.stream("GET", f"/api/graphs/research:stream/{run_id}") as resp:
        assert resp.status_code == 200
        # Consume some lines then close; background run continues
        read_any = False
        for idx, data_line in enumerate(_iter_sse_lines(resp)):
            read_any = True
            if idx > 5:
                break
        assert read_any

    # Poll for completion
    for _ in range(30):
        r2 = client.get(f"/api/graphs/run/{run_id}")
        assert r2.status_code == 200
        result = r2.json()
        if result.get("status") != "running":
            break
    assert result.get("status") != "running"
    assert result["run_id"] == run_id
    assert isinstance(result.get("papers", []), list)
    assert "summary" in result
