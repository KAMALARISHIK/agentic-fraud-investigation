import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from mcp_client import mcp_manager
from llm import generate_embedding

logger = logging.getLogger("fraud_agent.memory")

def write_case_to_graph(case_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Stores the completed investigation record into TigerGraph as active case memory
    using tigergraph__add_node and tigergraph__add_edge MCP tools.
    """
    case_id = str(case_data.get("case_id", "CASE_UNKNOWN")).strip()
    
    # Do not persist backtest/historical closed cases as active InvestigationCase vertices
    if case_id.startswith("CC-") or case_id.startswith("CASE-CC-") or case_data.get("is_backtest"):
        logger.info(f"Skipping graph memory write for historical backtest case {case_id}")
        return False, f"CASE-{case_id}"

    case_body = case_data.get("case", {})
    clean_id = case_id[5:] if case_id.startswith("CASE-") else case_id
    graph_case_id = f"CASE-{clean_id}"

    try:
        # 1. Generate Case Embedding for Semantic Case Memory
        summary_text = case_body.get("summary", "")
        emb = generate_embedding(f"Case {clean_id}: {summary_text}")

        # 2. Add InvestigationCase Vertex via MCP tigergraph__add_node (Upsert)
        case_attrs = {
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": case_body.get("status", "closed_fraud"),
            "verdict": case_body.get("verdict", "fraud"),
            "fraud_probability": float(case_body.get("fraud_probability", 0.0)),
            "pattern": case_body.get("pattern", "none"),
            "pattern_description": case_body.get("pattern_description", ""),
            "exposure_usd": float(case_body.get("exposure_usd", 0.0)),
            "stop_reason": case_data.get("stop_reason", ""),
            "summary": summary_text[:1000],
            "written_to_graph": True,
            "embedding": emb
        }
        res, dur, succ = mcp_manager.add_node("InvestigationCase", graph_case_id, case_attrs)

        # 3. Link to Card, Transactions, and Devices via MCP tigergraph__add_edge
        card_id = case_data.get("card_id")
        if card_id:
            mcp_manager.add_edge("CASE_ON_CARD", "InvestigationCase", graph_case_id, "Card", str(card_id))

        for tid in case_body.get("affected_txn_ids", []):
            mcp_manager.add_edge("CASE_INVOLVES_TXN", "InvestigationCase", graph_case_id, "Transaction", str(tid))

        for dev in case_body.get("connected_device_profiles", []):
            mcp_manager.add_edge("CASE_SHARES_DEVICE", "InvestigationCase", graph_case_id, "DeviceProfile", str(dev))

        # 4. Link Findings (Evidence Claims) via MCP (Upsert)
        for idx, ev in enumerate(case_body.get("evidence", [])):
            fid = f"FINDING-{clean_id}-{idx+1}"
            f_attrs = {
                "claim": ev.get("claim", "")[:500],
                "source": ev.get("source", "graph"),
                "ref": ev.get("ref", "")[:100],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            mcp_manager.add_node("Finding", fid, f_attrs)
            mcp_manager.add_edge("CASE_HAS_FINDING", "InvestigationCase", graph_case_id, "Finding", fid)

        # 5. Link Action Records via MCP (Upsert)
        for idx, act in enumerate(case_data.get("next_best_actions", {}).get("final", [])):
            aid = f"ACTION-{clean_id}-{idx+1}"
            a_attrs = {
                "action": act.get("action", ""),
                "route": act.get("route", "auto"),
                "reason": act.get("reason", "")[:500],
                "status": "executed" if act.get("route") == "auto" else "pending_approval",
                "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            mcp_manager.add_node("ActionRecord", aid, a_attrs)
            mcp_manager.add_edge("CASE_HAS_ACTION", "InvestigationCase", graph_case_id, "ActionRecord", aid)

        # 6. Link Similar Closed Cases via MCP
        for sim_cc in case_body.get("similar_prior_cases", []):
            mcp_manager.add_edge("SIMILAR_TO", "InvestigationCase", graph_case_id, "ClosedCase", str(sim_cc), {"similarity": 0.88})

        logger.info(f"Successfully stored case {case_id} to TigerGraph via MCP graph_case_id={graph_case_id}")
        return True, graph_case_id

    except Exception as e:
        logger.warning(f"Failed writing case {case_id} to TigerGraph via MCP: {e}")
        return False, graph_case_id
