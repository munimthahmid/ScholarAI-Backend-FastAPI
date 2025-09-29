import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.api.routes.graphs import map_langgraph_event


def test_map_event_sanitizes_non_dict_data():
    ev = {"event": "on_node_end", "name": "writer", "data": object()}
    mapped = map_langgraph_event(ev, run_id="r1")
    assert mapped.type == "on_node_end"
    assert mapped.node == "writer"
    assert isinstance(mapped.data, dict)
    assert "repr" in mapped.data

