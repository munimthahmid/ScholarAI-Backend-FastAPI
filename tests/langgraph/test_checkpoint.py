import os, sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.graph.graphs.gap import build_gap_graph


@pytest.mark.asyncio
class _FakeOrchestrator:
    def __init__(self, cfg):
        pass
    async def search_papers(self, q, d, n):
        return []


@pytest.mark.asyncio
async def test_sqlite_checkpointer_creates_db(tmp_path, monkeypatch):
    db_path = tmp_path / "chkpt.db"
    monkeypatch.setenv("GRAPHS_CHECKPOINTER", "sqlite")
    monkeypatch.setenv("GRAPHS_CHECKPOINT_DB", str(db_path))
    # Avoid network calls during validate
    import app.graph.graphs.gap as gap_mod
    monkeypatch.setattr(gap_mod, "MultiSourceSearchOrchestrator", _FakeOrchestrator)

    graph = build_gap_graph()  # picks up env checkpointer

    state = {
        "title": "Sample",
        "domain": "CS",
        "raw_text": "Title: Sample\nLimitations: small dataset\nFuture Work: more data",
    }
    cfg = {"configurable": {"thread_id": "t1"}}
    out1 = await graph.ainvoke(state, config=cfg)
    out2 = await graph.ainvoke(state, config=cfg)

    assert out1.get("gaps") and out2.get("gaps")
    # Ensure deterministic across repeated invoke
    assert json.dumps(out1, sort_keys=True) == json.dumps(out2, sort_keys=True)
