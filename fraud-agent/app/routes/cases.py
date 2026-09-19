import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Path as FPath

import config
import duckdb
from app.schemas import CaseSummary, CaseDetail, InvestigateRequest, EvidenceSubmitRequest
from agent.graph import investigation_agent
from agent.tools import fraud_tools

router = APIRouter(prefix="/cases", tags=["Cases"])
logger = logging.getLogger("fraud_agent.api.cases")

def load_case_data(case_id: str) -> Dict[str, Any]:
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("", response_model=List[CaseSummary])
def list_cases():
    """List all investigated cases with summary status and verdict metrics."""
    summaries = []
    cases_dir = config.CASES_OUTPUT_DIR
    
    # Load all json files
    for file_path in sorted(cases_dir.glob("HHG-*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            case_obj = data.get("case", {})
            sar_obj = data.get("sar", {})
            nba = data.get("next_best_actions", {})
            final_actions = nba.get("final", []) or nba.get("initial", [])
            
            # Find customer_id & card_id from connected cards or duckdb
            cust_id = None
            card_id = None
            connected_cards = case_obj.get("connected_card_ids", [])
            if connected_cards:
                card_id = connected_cards[0]
                cust_id = card_id.split("-K")[0]
            
            summaries.append(CaseSummary(
                case_id=data.get("case_id", file_path.stem),
                customer_id=cust_id,
                card_id=card_id,
                verdict=case_obj.get("verdict", "uncertain"),
                fraud_probability=case_obj.get("fraud_probability", 0.0),
                pattern=case_obj.get("pattern", "none"),
                exposure_usd=case_obj.get("exposure_usd", 0.0),
                status=case_obj.get("status", "CLOSED"),
                sar_required=sar_obj.get("file", False),
                actions_count=len(final_actions)
            ))
        except Exception as e:
            logger.error(f"Error reading case {file_path.name}: {e}")
            
    return summaries

@router.get("/{case_id}", response_model=CaseDetail)
def get_case_detail(case_id: str = FPath(..., description="The ID of the case, e.g. HHG-001")):
    """Get complete case file including graph findings, evidence requests, SAR, actions, and audit logs."""
    return load_case_data(case_id)

@router.post("/{case_id}/investigate", response_model=Dict[str, Any])
def trigger_investigation(case_id: str, req: Optional[InvestigateRequest] = None):
    """
    Triggers the LangGraph agent investigation for a given case alert.
    Executes graph traversals, vector similarity search, and deterministic policy rule evaluation.
    """
    alert: Dict[str, Any] = {}
    
    # Check if custom alert provided
    if req and (req.customer_id or req.flagged_txn_id):
        alert = {
            "case_id": case_id,
            "customer_id": req.customer_id or "",
            "card_id": req.card_id or "",
            "flagged_txn_id": str(req.flagged_txn_id or ""),
            "trigger_type": req.trigger_type or "risk_score",
            "trigger_text": req.trigger_text or f"Alert triggered for case {case_id}",
            "risk_score": req.risk_score or 0.85
        }
    else:
        # Load from case_pack.csv or existing case
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        row = con.execute("SELECT * FROM case_pack_raw WHERE case_id = ?", [case_id]).fetchone()
        con.close()
        
        if row:
            alert = {
                "case_id": str(row[0]),
                "customer_id": str(row[1]),
                "card_id": str(row[2]),
                "flagged_txn_id": str(row[3]),
                "trigger_type": str(row[4]),
                "trigger_text": str(row[5]),
                "risk_score": float(row[6])
            }
        else:
            existing = load_case_data(case_id)
            case_obj = existing.get("case", {})
            first_txn = case_obj.get("first_suspicious_txn_id") or (case_obj.get("affected_txn_ids") or ["3000000"])[0]
            cards = case_obj.get("connected_card_ids") or ["CUST-001-K1"]
            alert = {
                "case_id": case_id,
                "customer_id": cards[0].split("-K")[0],
                "card_id": cards[0],
                "flagged_txn_id": str(first_txn),
                "trigger_type": "risk_score",
                "trigger_text": case_obj.get("summary", ""),
                "risk_score": 0.85
            }
            
    result = investigation_agent.investigate(alert)
    return {
        "status": "success",
        "case_id": case_id,
        "initial_result": result
    }

@router.post("/{case_id}/evidence", response_model=Dict[str, Any])
def submit_case_evidence(case_id: str, evidence: EvidenceSubmitRequest):
    """
    Submits customer verification evidence, runs reassessment against fraud policy rules,
    and produces final actions and SAR decision.
    """
    data = load_case_data(case_id)
    case_obj = data.get("case", {})
    
    # Record evidence reply
    sim_reply = {
        "evidence_type": evidence.evidence_type,
        "response_text": evidence.response_text,
        "customer_verified": evidence.verified,
        "device_recognized": evidence.verified,
        "location_authorized": evidence.verified
    }
    
    for ev_req in data.get("evidence_requests", []):
        ev_req["simulated_reply"] = sim_reply
        
    # Reassess actions based on evidence
    if evidence.verified:
        case_obj["verdict"] = "legitimate"
        case_obj["fraud_probability"] = min(case_obj.get("fraud_probability", 0.8), 0.15)
        case_obj["affected_txn_ids"] = []
        case_obj["exposure_usd"] = 0.0
        data["next_best_actions"]["final"] = [
            {"action": "ALLOW_TRANSACTION", "route": "auto", "reason": "Customer confirmed transaction"},
            {"action": "CLOSE_NO_FRAUD", "route": "auto", "reason": "Investigation cleared post-evidence"}
        ]
        data["next_best_actions"]["what_changed"] = "Customer verification confirmed authorization. Closed no fraud."
        data["sar"] = {
            "file": False,
            "narrative": "",
            "subjects": [],
            "total_amount_usd": 0.0,
            "activity_dates": []
        }
    else:
        case_obj["verdict"] = "fraud"
        case_obj["fraud_probability"] = 0.98
        data["next_best_actions"]["what_changed"] = "Customer disavowed transaction. Reassessment confirmed fraud."
        
    # Save back to file
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    return {
        "status": "success",
        "case_id": case_id,
        "reassessed_case": data
    }
