import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Path as FPath

import config
from app.schemas import ActionDecisionRequest, ActionDecisionResponse

router = APIRouter(prefix="/cases", tags=["Actions"])
logger = logging.getLogger("fraud_agent.api.actions")

# In-memory store for analyst decisions
ACTION_DECISIONS: Dict[str, Dict[str, Any]] = {}

@router.post("/{case_id}/actions/{action_id}/approve", response_model=ActionDecisionResponse)
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

@router.post("/{case_id}/actions/{action_id}/reject", response_model=ActionDecisionResponse)
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
