import json
import os, sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app


client = TestClient(app)


def _iter_sse_lines(resp):
    for chunk in resp.iter_lines():
        if not chunk:
            continue
        line = chunk.decode("utf-8") if isinstance(chunk, (bytes, bytearray)) else str(chunk)
        if line.startswith("data: "):
            yield line[len("data: ") :]


def test_gap_graph_stream_and_result():
    raw_text = (
        "Title: Sample Paper\n\nResults: We achieve 85% accuracy.\n"
        "Limitations: Requires large training data; high compute.\n"
        "Future Work: Reduce compute; transfer learning.\n"
    )
    # Start run (with raw_text to avoid network)
    r = client.post("/api/graphs/gap:start", json={"raw_text": raw_text, "title": "Sample Paper", "domain": "Computer Science"})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert run_id

    # Stream
    with client.stream("GET", f"/api/graphs/gap:stream/{run_id}") as resp:
        assert resp.status_code == 200
        # Read a few lines, ensure stream is active
        got_any = False
        for i, data_line in enumerate(_iter_sse_lines(resp)):
            got_any = True
            if i > 5:
                break
        assert got_any

    # Poll result
    for _ in range(30):
        r2 = client.get(f"/api/graphs/run/{run_id}")
        assert r2.status_code == 200
        result = r2.json()
        if result.get("status") != "running":
            break

    assert result.get("status") != "running"
    assert result["run_id"] == run_id
    assert isinstance(result.get("gaps", []), list)
    # Should identify at least one gap from limitations or future work
    assert len(result.get("gaps", [])) >= 1

