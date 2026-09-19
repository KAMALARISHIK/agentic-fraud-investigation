import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "tigergraph_connected" in data
    assert "duckdb_connected" in data
    assert "cases_loaded" in data

def test_list_cases_endpoint():
    res = client.get("/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) == 20
    first_case = cases[0]
    assert "case_id" in first_case
    assert "verdict" in first_case
    assert "exposure_usd" in first_case

def test_get_case_detail_endpoint():
    res = client.get("/cases/HHG-001")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "HHG-001"
    assert "case" in data
    assert "next_best_actions" in data
    assert "sar" in data

def test_case_timeline_endpoint():
    res = client.get("/cases/HHG-001/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "HHG-001"
    assert "timeline" in data
    assert len(data["timeline"]) >= 3

def test_case_graph_endpoint():
    res = client.get("/cases/HHG-001/graph")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "HHG-001"
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0

def test_case_similar_endpoint():
    res = client.get("/cases/HHG-001/similar")
    assert res.status_code == 200
    similar = res.json()
    assert isinstance(similar, list)

def test_action_approve_endpoint():
    res = client.post("/cases/HHG-001/actions/ACT-1/approve", json={
        "analyst_id": "test_analyst",
        "notes": "Test approval"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["case_id"] == "HHG-001"

def test_action_reject_endpoint():
    res = client.post("/cases/HHG-001/actions/ACT-1/reject", json={
        "analyst_id": "test_analyst",
        "notes": "Test rejection"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["case_id"] == "HHG-001"

def test_memory_patterns_endpoint():
    res = client.get("/memory/patterns")
    assert res.status_code == 200
    patterns = res.json()
    assert len(patterns) >= 6
    p_names = [p["pattern"] for p in patterns]
    assert "card_testing" in p_names
    assert "account_takeover" in p_names

def test_stats_endpoint():
    res = client.get("/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 20
    assert "verdict_distribution" in data
    assert "total_exposure_usd" in data
