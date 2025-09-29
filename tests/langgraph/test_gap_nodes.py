import os, sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.graph.graphs import gap as gap_graph


@pytest.mark.asyncio
async def test_analyze_node_fallback_parses_sections(monkeypatch):
    # Force fallback by ensuring no LLM
    monkeypatch.setattr(gap_graph, "get_chat_model", lambda: None)

    text = (
        "Title: A Tiny Paper\n\nResults: 80% accuracy\nLimitations: requires huge data\nFuture Work: reduce compute"
    )
    out = await gap_graph.analyze_node({"raw_text": text})
    analysis = out.get("analysis")
    assert isinstance(analysis, dict)
    assert analysis.get("title") == "A Tiny Paper"
    assert any("Limitations".lower() in s.lower() or "requires" in s.lower() for s in analysis.get("limitations", []))
    assert any("Future Work".lower() in s.lower() or "reduce compute" in s.lower() for s in analysis.get("future_work", []))


@pytest.mark.asyncio
async def test_identify_node_builds_gaps():
    state = {
        "analysis": {
            "title": "A Tiny Paper",
            "limitations": ["requires huge data"],
            "future_work": ["reduce compute"],
        }
    }
    out = await gap_graph.identify_node(state)
    gaps = out.get("gaps")
    assert isinstance(gaps, list)
    assert len(gaps) >= 2
    assert all("description" in g for g in gaps)


class _FakeOrchestrator:
    def __init__(self, cfg):
        self.calls = 0

    async def search_papers(self, q, d, n):
        self.calls += 1
        # First call returns hit, others no hit
        return [{}] if self.calls == 1 else []


@pytest.mark.asyncio
async def test_validate_node_updates_confidence(monkeypatch):
    # Monkeypatch orchestrator to deterministic behavior
    monkeypatch.setattr(gap_graph, "MultiSourceSearchOrchestrator", _FakeOrchestrator)

    state = {
        "domain": "CS",
        "gaps": [
            {"description": "reduce compute", "confidence": 0.3, "evidence": []},
            {"description": "transfer learning", "confidence": 0.3, "evidence": []},
        ],
    }
    out = await gap_graph.validate_node(state)
    gaps = out.get("gaps")
    assert isinstance(gaps, list)
    assert gaps[0]["confidence"] >= 0.6
    assert gaps[1]["confidence"] <= 0.4


@pytest.mark.asyncio
async def test_pdf_or_text_node_prefers_raw_text(monkeypatch):
    called = {"extract": False}

    class _FakeExtractor:
        async def extract_text_from_pdf(self, pdf_url: str, paper_id: str):
            called["extract"] = True
            raise AssertionError("Should not be called when raw_text is provided")

    monkeypatch.setattr(gap_graph, "TextExtractorAgent", lambda client: _FakeExtractor())

    state = {"raw_text": "Hello", "pdf_url": "http://example.com/doc.pdf"}
    out = await gap_graph.pdf_or_text_node(state)
    assert out.get("raw_text") == "Hello"
    assert called["extract"] is False

