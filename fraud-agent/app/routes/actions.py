import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Path as FPath

import config
from app.schemas import ActionDecisionRequest, ActionDecisionResponse

router = APIRouter(tags=["Actions"])
logger = logging.getLogger("fraud_agent.api.actions")

# In-memory store for analyst decisions
ACTION_DECISIONS: Dict[str, Dict[str, Any]] = {}

@router.post("/cases/{case_id}/actions/{action_id}/approve", response_model=ActionDecisionResponse)
def approve_action(
    case_id: str = FPath(..., description="Case ID"),
    action_id: str = FPath(..., description="Action ID or index, e.g. ACT-1 or 0"),
    decision: Optional[ActionDecisionRequest] = None
):
    """
    Approve an L1 or L2 human-routed action (e.g. BLOCK_CARD, FILE_REPORT).
    Updates action status to 'APPROVED' and records audit record.
    """
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    nba = data.get("next_best_actions", {})
    final_actions = nba.get("final", [])
    
    # Locate action
    matched = False
    for idx, act in enumerate(final_actions):
        cur_id = act.get("action_id") or f"ACT-{idx+1}"
        if cur_id == action_id or str(idx) == action_id or act.get("action") == action_id:
            act["status"] = "APPROVED"
            matched = True
            break
            
    if not matched and final_actions:
        # Fallback approve first matching
        final_actions[0]["status"] = "APPROVED"
        
    # Save back
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    analyst_id = decision.analyst_id if decision else "analyst_1"
    notes = decision.notes if decision else "Action approved by investigator"
    now_str = datetime.now(timezone.utc).isoformat()
    
    ACTION_DECISIONS[f"{case_id}:{action_id}"] = {
        "status": "APPROVED",
        "analyst_id": analyst_id,
        "notes": notes,
        "timestamp": now_str
    }
    
    return ActionDecisionResponse(
        case_id=case_id,
        action_id=action_id,
        status="APPROVED",
        analyst_id=analyst_id,
        notes=notes,
        timestamp=now_str
    )

@router.post("/cases/{case_id}/actions/{action_id}/reject", response_model=ActionDecisionResponse)
def reject_action(
    case_id: str = FPath(..., description="Case ID"),
    action_id: str = FPath(..., description="Action ID or index, e.g. ACT-1 or 0"),
    decision: Optional[ActionDecisionRequest] = None
):
    """
    Reject an L1 or L2 human-routed action.
    Updates action status to 'REJECTED' with investigator notes.
    """
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    nba = data.get("next_best_actions", {})
    final_actions = nba.get("final", [])
    
    # Locate action
    matched = False
    for idx, act in enumerate(final_actions):
        cur_id = act.get("action_id") or f"ACT-{idx+1}"
        if cur_id == action_id or str(idx) == action_id or act.get("action") == action_id:
            act["status"] = "REJECTED"
            matched = True
            break
            
    if not matched and final_actions:
        final_actions[0]["status"] = "REJECTED"
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    analyst_id = decision.analyst_id if decision else "analyst_1"
    notes = decision.notes if decision else "Action rejected by investigator"
    now_str = datetime.now(timezone.utc).isoformat()
    
    ACTION_DECISIONS[f"{case_id}:{action_id}"] = {
        "status": "REJECTED",
        "analyst_id": analyst_id,
        "notes": notes,
        "timestamp": now_str
    }
    
    return ActionDecisionResponse(
        case_id=case_id,
        action_id=action_id,
        status="REJECTED",
        analyst_id=analyst_id,
        notes=notes,
        timestamp=now_str
    )

@router.get("/actions/pending", response_model=List[Dict[str, Any]])
def list_pending_actions():
    """Returns all pending L1 / L2 human-in-the-loop actions across all cases."""
    pending = []
    cases_dir = config.CASES_OUTPUT_DIR
    for file_path in sorted(cases_dir.glob("HHG-*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            case_id = data.get("case_id", file_path.stem)
            case_obj = data.get("case", {})
            nba = data.get("next_best_actions", {})
            final_actions = nba.get("final", []) or nba.get("initial", [])
            for idx, act in enumerate(final_actions):
                route = act.get("route", "").upper()
                status = act.get("status", "pending").upper()
                act_id = act.get("action_id") or f"ACT-{idx+1}"
                if route in ["L1", "L2"] and status not in ["APPROVED", "REJECTED"]:
                    pending.append({
                        "case_id": case_id,
                        "action_id": act_id,
                        "action": act.get("action"),
                        "route": route,
                        "reason": act.get("reason"),
                        "status": "pending",
                        "exposure_usd": case_obj.get("exposure_usd", 0.0),
                        "pattern": case_obj.get("pattern", "none"),
                        "verdict": case_obj.get("verdict", "uncertain"),
                        "fraud_probability": case_obj.get("fraud_probability", 0.0),
                        "customer_id": case_obj.get("connected_card_ids", ["UNKNOWN"])[0].split("-K")[0] if case_obj.get("connected_card_ids") else "UNKNOWN"
                    })
        except Exception as e:
            logger.error(f"Error reading actions for {file_path.name}: {e}")
    return pending

@router.get("/actions/history", response_model=List[Dict[str, Any]])
def list_action_history():
    """Returns all decided (approved/rejected) analyst actions across all cases."""
    history = []
    cases_dir = config.CASES_OUTPUT_DIR
    for file_path in sorted(cases_dir.glob("HHG-*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            case_id = data.get("case_id", file_path.stem)
            case_obj = data.get("case", {})
            nba = data.get("next_best_actions", {})
            final_actions = nba.get("final", [])
            for idx, act in enumerate(final_actions):
                status = act.get("status", "").upper()
                act_id = act.get("action_id") or f"ACT-{idx+1}"
                if status in ["APPROVED", "REJECTED"]:
                    decision_meta = ACTION_DECISIONS.get(f"{case_id}:{act_id}", {})
                    history.append({
                        "case_id": case_id,
                        "action_id": act_id,
                        "action": act.get("action"),
                        "route": act.get("route", "").upper(),
                        "reason": act.get("reason"),
                        "status": status,
                        "analyst_id": decision_meta.get("analyst_id", "analyst_1"),
                        "notes": decision_meta.get("notes", f"Action {status.lower()} by investigator"),
                        "timestamp": decision_meta.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "exposure_usd": case_obj.get("exposure_usd", 0.0),
                        "pattern": case_obj.get("pattern", "none"),
                        "verdict": case_obj.get("verdict", "uncertain")
                    })
        except Exception as e:
            logger.error(f"Error reading history for {file_path.name}: {e}")
    return history

