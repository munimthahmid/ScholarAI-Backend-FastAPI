import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.api.routes.graphs import map_langgraph_event


def test_map_token_event_simple():
    ev = {"event": "on_chat_model_stream", "name": "writer", "data": {"chunk": {"content": "tok"}}}
    mapped = map_langgraph_event(ev, run_id="r1")
    assert mapped.type == "token"
    assert mapped.node == "writer"
    assert mapped.data.get("token") == "tok"
