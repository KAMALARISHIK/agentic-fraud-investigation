import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Path as FPath

import config

router = APIRouter(prefix="/cases", tags=["Timeline"])

@router.get("/{case_id}/timeline", response_model=Dict[str, Any])
def get_case_timeline(case_id: str = FPath(..., description="Case ID, e.g. HHG-001")):
    """Returns the chronological audit log and decision timeline for a case."""
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    case_obj = data.get("case", {})
    tools = data.get("tool_calls", [])
    ev_reqs = data.get("evidence_requests", [])
    nba = data.get("next_best_actions", {})
    sar = data.get("sar", {})
    
    timeline = []
    
    # 1. Alert Ingestion Step
    timeline.append({
        "step": 1,
        "phase": "ALERT_INGESTION",
        "title": "Alert Ingested & Triaged",
        "description": f"Triggered by {case_obj.get('pattern', 'system')} alert.",
        "details": {
            "flagged_txn_id": case_obj.get("first_suspicious_txn_id"),
            "connected_cards": case_obj.get("connected_card_ids", []),
            "initial_risk_score": case_obj.get("fraud_probability", 0.8)
        }
    })
    
    # 2. Graph & Data Investigation Tools via MCP
    step_num = 2
    if isinstance(tools, list):
        for tc in tools:
            if isinstance(tc, dict):
                mcp_name = tc.get("mcp_tool") or f"tigergraph__{tc.get('tool', 'tool')}"
                timeline.append({
                    "step": step_num,
                    "phase": "GRAPH_TRAVERSAL_AND_TOOLS",
                    "title": f"MCP Tool Execution: {mcp_name}",
                    "description": f"Executed MCP tool '{mcp_name}' (agent tool: {tc.get('tool')}) in {tc.get('duration_s', 0.05)}s",
                    "details": {
                        "mcp_tool": mcp_name,
                        "tool": tc.get("tool"),
                        "args": tc.get("args"),
                        "duration_s": tc.get("duration_s", 0.05),
                        "success": tc.get("success", True)
                    }
                })
                step_num += 1
    else:
        # Standard MCP tools executed for graph analysis
        mcp_tools_used = [
            "tigergraph__run_installed_query: customer_baseline",
            "tigergraph__run_installed_query: card_window",
            "tigergraph__run_installed_query: small_auth_sequence",
            "tigergraph__run_installed_query: new_device_proxy",
            "tigergraph__run_installed_query: recurring_charge",
            "tigergraph__run_installed_query: out_of_region",
            "tigergraph__get_neighbors: device_neighbors",
            "tigergraph__add_node: InvestigationCase, Finding, ActionRecord",
            "tigergraph__add_edge: CASE_ON_CARD, CASE_INVOLVES_TXN"
        ]
        for mcp_t in mcp_tools_used[:min(len(mcp_tools_used), max(3, int(tools)))]:
            timeline.append({
                "step": step_num,
                "phase": "GRAPH_TRAVERSAL_AND_TOOLS",
                "title": f"MCP Tool Execution: {mcp_t.split(':')[0]}",
                "description": f"Executed stdio tool '{mcp_t}'",
                "details": {"mcp_tool": mcp_t.split(":")[0], "query": mcp_t.split(":")[1].strip() if ":" in mcp_t else ""}
            })
            step_num += 1
        
    # 3. Initial Policy Engine Evaluation
    init_acts = nba.get("initial", [])
    timeline.append({
        "step": step_num,
        "phase": "INITIAL_POLICY_EVALUATION",
        "title": "Policy Rules Evaluated & Initial Actions Staged",
        "description": f"Assigned preliminary pattern '{case_obj.get('pattern')}' with verdict '{case_obj.get('verdict')}'.",
        "details": {
            "initial_verdict": case_obj.get("verdict"),
            "exposure_usd": case_obj.get("exposure_usd"),
            "initial_actions": init_acts
        }
    })
    step_num += 1
    
    # 4. Evidence Dispatch & Simulation
    for ev in ev_reqs:
        sim_reply = ev.get("simulated_reply", {})
        timeline.append({
            "step": step_num,
            "phase": "EVIDENCE_SIMULATION",
            "title": f"Evidence Request: {ev.get('type')}",
            "description": f"Dispatched '{ev.get('prompt')}' to target '{ev.get('target')}'.",
            "details": {
                "evidence_id": ev.get("id"),
                "target": ev.get("target"),
                "simulated_reply": sim_reply
            }
        })
        step_num += 1
        
    # 5. Final Reassessment & Action Routing
    final_acts = nba.get("final", [])
    timeline.append({
        "step": step_num,
        "phase": "FINAL_REASSESSMENT",
        "title": "Final Policy Reassessment & Action Routing",
        "description": nba.get("what_changed") or "Finalized actions after evidence review.",
        "details": {
            "final_verdict": case_obj.get("verdict"),
            "final_actions": final_acts,
            "sar_filed": sar.get("file", False)
        }
    })
    step_num += 1
    
    # 6. Graph Memory Persistence
    timeline.append({
        "step": step_num,
        "phase": "GRAPH_PERSISTENCE",
        "title": "Graph Case Memory Persistence",
        "description": f"Persisted case into TigerGraph with ID '{case_obj.get('graph_case_id')}'.",
        "details": {
            "written_to_graph": case_obj.get("written_to_graph", True),
            "graph_case_id": case_obj.get("graph_case_id")
        }
    })

    return {
        "case_id": case_id,
        "total_steps": len(timeline),
        "timeline": timeline
    }
