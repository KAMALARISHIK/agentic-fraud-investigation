import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.graph import investigation_agent

def test_agent_investigate_hhg_001():
    # HHG-001 (Risk score trigger)
    alert = {
        "case_id": "HHG-001",
        "customer_id": "C12382",
        "card_id": "C12382-K1",
        "flagged_txn_id": "3514030",
        "trigger_type": "risk_score",
        "trigger_text": "Real-time model scored transaction 3514030 at 0.61.",
        "risk_score": 0.61
    }
    result = investigation_agent.investigate(alert)
    assert result["case_id"] == "HHG-001"
    assert "case" in result
    assert "next_best_actions" in result
    assert "sar" in result
    assert result["case"]["status"] in ["closed_fraud", "closed_legitimate", "escalated"]
    assert isinstance(result["case"]["fraud_probability"], float)
    assert isinstance(result["next_best_actions"]["initial"], list)
    assert isinstance(result["next_best_actions"]["final"], list)

def test_agent_investigate_card_testing_hhg_017():
    # HHG-017 (Card testing trigger)
    alert = {
        "case_id": "HHG-017",
        "customer_id": "C04570",
        "card_id": "C04570-K1",
        "flagged_txn_id": "3450629",
        "trigger_type": "risk_score",
        "trigger_text": "Real-time model scored transaction 3450629 at 0.57.",
        "risk_score": 0.57
    }
    result = investigation_agent.investigate(alert)
    assert result["case_id"] == "HHG-017"
    assert result["case"]["verdict"] in ["fraud", "legitimate", "uncertain"]
    assert result["case"]["exposure_usd"] >= 0.0

def test_policy_routing_and_sar_agreement():
    # Customer report trigger
    alert = {
        "case_id": "HHG-003",
        "customer_id": "C08623",
        "card_id": "C08623-K2",
        "flagged_txn_id": "3530164",
        "trigger_type": "customer_report",
        "trigger_text": "Customer message: I never made this $49.00 purchase.",
        "risk_score": None
    }
    result = investigation_agent.investigate(alert)
    final_action_names = [a["action"] for a in result["next_best_actions"]["final"]]
    sar_file = result["sar"]["file"]
    
    # Must strictly agree: sar.file == ("FILE_REPORT" in final_actions)
    assert sar_file == ("FILE_REPORT" in final_action_names)
