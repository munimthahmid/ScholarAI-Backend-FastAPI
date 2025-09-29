import asyncio
import os

import pytest

from app.graph.graphs.research import write_node


@pytest.mark.asyncio
async def test_writer_node_fallback(monkeypatch):
    # Force fallback by clearing OPENAI_API_KEY
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    state = {
        "query": "graph neural networks",
        "domain": "Computer Science",
        "results": [
            {"title": "GNN Survey"},
            {"title": "Message Passing with Attention"},
        ],
    }

    out = await write_node(state)
    assert "summary" in out
    assert "Found 2 papers" in out["summary"]

