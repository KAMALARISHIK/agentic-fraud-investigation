import os
import sys
import json
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("c:/GOA TIGER/fraud-agent"))
from app.main import app

client = TestClient(app)

def test_pages_and_api():
    print("Testing API endpoints for frontend pages:")
    
    # 1. Health
    r = client.get("/health")
    print(f"GET /health: {r.status_code}")
    assert r.status_code == 200
    
    # 2. Cases list (Overview, Cases, Investigations)
    r = client.get("/cases")
    print(f"GET /cases: {r.status_code}, count={len(r.json())}")
    assert r.status_code == 200
    assert len(r.json()) == 20
    
    # 3. Stats (Overview KPIs)
    r = client.get("/stats")
    print(f"GET /stats: {r.status_code}, total_cases={r.json().get('total_cases')}")
    assert r.status_code == 200
    assert r.json().get("total_cases") == 20
    
    # 4. Patterns & Case Memory
    r = client.get("/memory/patterns")
    data = r.json()
    count = len(data) if isinstance(data, list) else len(data.get('patterns', []))
    print(f"GET /memory/patterns: {r.status_code}, patterns={count}")
    assert r.status_code == 200
    
    # Test on Fraud Case HHG-001
    print("\n--- Testing Case HHG-001 (High Risk / Fraud) ---")
    r_detail_1 = client.get("/cases/HHG-001")
    print(f"GET /cases/HHG-001: {r_detail_1.status_code}, verdict={r_detail_1.json()['case']['verdict']}")
    assert r_detail_1.status_code == 200
    
    r_graph_1 = client.get("/cases/HHG-001/graph")
    print(f"GET /cases/HHG-001/graph: {r_graph_1.status_code}, nodes={len(r_graph_1.json().get('nodes', []))}")
    assert r_graph_1.status_code == 200
    
    r_time_1 = client.get("/cases/HHG-001/timeline")
    print(f"GET /cases/HHG-001/timeline: {r_time_1.status_code}, events={len(r_time_1.json())}")
    assert r_time_1.status_code == 200
    
    r_sim_1 = client.get("/cases/HHG-001/similar")
    print(f"GET /cases/HHG-001/similar: {r_sim_1.status_code}, similar={len(r_sim_1.json())}")
    assert r_sim_1.status_code == 200
    
    r_txns_1 = client.get("/cases/HHG-001/transactions")
    txns_data = r_txns_1.json()
    txns_count = len(txns_data) if isinstance(txns_data, list) else len(txns_data.get('transactions', []))
    print(f"GET /cases/HHG-001/transactions: {r_txns_1.status_code}, txns={txns_count}")
    assert r_txns_1.status_code == 200
    
    # Test on Legitimate Case HHG-010
    print("\n--- Testing Case HHG-010 (Legitimate / Low Risk) ---")
    r_detail_10 = client.get("/cases/HHG-010")
    print(f"GET /cases/HHG-010: {r_detail_10.status_code}, verdict={r_detail_10.json()['case']['verdict']}")
    assert r_detail_10.status_code == 200
    
    r_graph_10 = client.get("/cases/HHG-010/graph")
    print(f"GET /cases/HHG-010/graph: {r_graph_10.status_code}, nodes={len(r_graph_10.json().get('nodes', []))}")
    assert r_graph_10.status_code == 200
    
    r_time_10 = client.get("/cases/HHG-010/timeline")
    print(f"GET /cases/HHG-010/timeline: {r_time_10.status_code}, events={len(r_time_10.json())}")
    assert r_time_10.status_code == 200
    
    # Test Evidence Submission flow
    r_ev = client.post("/cases/HHG-001/evidence", json={"verification_response": "Customer confirmed legitimate transaction"})
    print(f"POST /cases/HHG-001/evidence: {r_ev.status_code}")
    assert r_ev.status_code == 200
    
    # Test Action Approve/Reject
    actions = r_detail_1.json().get("actions", [])
    if actions:
        action_id = actions[0]["action_id"]
        r_app = client.post(f"/cases/HHG-001/actions/{action_id}/approve")
        print(f"POST /cases/HHG-001/actions/{action_id}/approve: {r_app.status_code}")
        assert r_app.status_code == 200
        
        r_rej = client.post(f"/cases/HHG-001/actions/{action_id}/reject")
        print(f"POST /cases/HHG-001/actions/{action_id}/reject: {r_rej.status_code}")
        assert r_rej.status_code == 200

    print("\nALL BACKEND ROUTES VERIFIED FOR FRONTEND CONSUMPTION!")

if __name__ == "__main__":
    test_pages_and_api()
