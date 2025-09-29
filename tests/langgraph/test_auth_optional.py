import os, sys
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app


client = TestClient(app)


def test_auth_not_required_by_default():
    r = client.post("/api/graphs/research:start", json={"query": "ml", "domain": "CS", "target_size": 1})
    assert r.status_code == 200


def test_auth_required_with_env(monkeypatch):
    monkeypatch.setenv("GRAPHS_REQUIRE_AUTH", "true")
    monkeypatch.setenv("GRAPHS_AUTH_TOKEN", "secret")

    r = client.post("/api/graphs/research:start", json={"query": "ml", "domain": "CS", "target_size": 1})
    assert r.status_code == 401

    r2 = client.post(
        "/api/graphs/research:start",
        json={"query": "ml", "domain": "CS", "target_size": 1},
        headers={"Authorization": "Bearer secret"},
    )
    assert r2.status_code == 200

