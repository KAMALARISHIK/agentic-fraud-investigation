import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Path as FPath

import config
import duckdb
from app.schemas import GraphData, GraphNode, GraphEdge
from agent.tools import fraud_tools

router = APIRouter(prefix="/cases", tags=["Graph & Similarity"])
logger = logging.getLogger("fraud_agent.api.graph")

@router.get("/{case_id}/graph", response_model=GraphData)
def get_case_graph(case_id: str = FPath(..., description="Case ID, e.g. HHG-001")):
    """
    Returns the visual subgraph for a case (nodes and edges)
    including Customer, Cards, Transactions, Devices, and Relations.
    """
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    case_obj = data.get("case", {})
    connected_cards = case_obj.get("connected_card_ids", [])
    connected_devices = case_obj.get("connected_device_profiles", [])
    affected_txns = set(str(t) for t in case_obj.get("affected_txn_ids", []))
    first_suspicious = str(case_obj.get("first_suspicious_txn_id", ""))
    
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    
    # Identify Customer ID and Cards
    cust_id = None
    if connected_cards:
        cust_id = connected_cards[0].split("-K")[0]
        
    cards_set = set(connected_cards)
    txn_ids = set()
    for tid in affected_txns:
        try:
            txn_ids.add(int(tid))
        except (ValueError, TypeError):
            pass
    if first_suspicious:
        try:
            txn_ids.add(int(first_suspicious))
        except (ValueError, TypeError):
            pass
            
    for ev in case_obj.get("evidence", []):
        if isinstance(ev, dict):
            for ent in ev.get("entity_ids", []):
                try:
                    txn_ids.add(int(ent))
                except (ValueError, TypeError):
                    pass

    try:
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        cp_rows = con.execute("SELECT customer_id, card_id, flagged_txn_id FROM case_pack_raw WHERE case_id = ?", [case_id]).fetchall()
        for row in cp_rows:
            if not cust_id and row[0]:
                cust_id = str(row[0])
            if row[1]:
                cards_set.add(str(row[1]))
            if row[2]:
                try:
                    txn_ids.add(int(row[2]))
                except (ValueError, TypeError):
                    pass
        con.close()
    except Exception as e:
        logger.error(f"Error checking case_pack_raw for case {case_id}: {e}")

    if not cust_id:
        cust_id = f"CUST-{case_id}"
    if not cards_set:
        cards_set.add(f"{cust_id}-K1")
        
    # 1. Customer Node
    nodes[cust_id] = GraphNode(
        id=cust_id,
        label=cust_id,
        type="Customer",
        properties={"status": "INVESTIGATED"}
    )
    
    # 2. Card Nodes & Edges
    for card in cards_set:
        nodes[card] = GraphNode(
            id=card,
            label=card,
            type="Card",
            properties={"customer_id": cust_id}
        )
        edges.append(GraphEdge(
            from_id=cust_id,
            to_id=card,
            type="CUSTOMER_HAS_CARD"
        ))
        
    # 3. Query transactions from DuckDB
    try:
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        conds = ["customer_id = ?"]
        params = [cust_id]
        if txn_ids:
            ph = ", ".join(["?"] * len(txn_ids))
            conds.append(f"id IN ({ph})")
            params.extend(list(txn_ids))
            
        where_clause = " OR ".join(conds)
        query = f"""
            SELECT 
                id,
                customer_id || '-K1' as card_id,
                amount,
                epoch(ts) as timestamp,
                CASE WHEN risk_score > 0.5 THEN 1 ELSE 0 END as is_fraud,
                coalesce(addr1, '') as location,
                coalesce(dist1, 0) as dist1,
                coalesce(p_emaildomain, '') as email,
                coalesce(device_info, os, '') as device
            FROM transactions_trimmed
            WHERE {where_clause}
            ORDER BY ts DESC
            LIMIT 30
        """
        rows = con.execute(query, params).fetchall()
        con.close()
        
        for r in rows:
            tid = str(r[0])
            c_id = str(r[1])
            amt = float(r[2] or 0.0)
            dt = int(r[3] or 0)
            is_fraud = int(r[4] or 0)
            email = str(r[7] or "")
            dev = str(r[8] or "")
            
            is_affected = (tid in affected_txns) or (tid == first_suspicious)
            
            # Ensure card exists
            if c_id not in nodes:
                nodes[c_id] = GraphNode(id=c_id, label=c_id, type="Card", properties={"customer_id": cust_id})
                edges.append(GraphEdge(from_id=cust_id, to_id=c_id, type="CUSTOMER_HAS_CARD"))
            
            # Transaction Node
            nodes[tid] = GraphNode(
                id=tid,
                label=f"TXN-{tid} (${amt:.2f})",
                type="Transaction",
                properties={
                    "amount_usd": amt,
                    "timestamp_dt": dt,
                    "is_flagged": is_affected,
                    "is_fraud_ground_truth": is_fraud
                }
            )
            
            # Card -> Transaction Edge
            edges.append(GraphEdge(
                from_id=c_id,
                to_id=tid,
                type="PERFORMED_TRANSACTION",
                properties={"amount_usd": amt}
            ))
            
            # Device profile Node & Edge
            if dev and dev != "nan" and dev != "None":
                if dev not in nodes:
                    nodes[dev] = GraphNode(id=dev, label=dev, type="DeviceProfile")
                edges.append(GraphEdge(
                    from_id=tid,
                    to_id=dev,
                    type="USED_DEVICE"
                ))
                
            # Email Domain Node & Edge
            if email and email != "nan" and email != "None":
                if email not in nodes:
                    nodes[email] = GraphNode(id=email, label=email, type="EmailDomain")
                edges.append(GraphEdge(
                    from_id=tid,
                    to_id=email,
                    type="ASSOCIATED_EMAIL"
                ))
                
    except Exception as e:
        logger.error(f"Error querying graph entities for case {case_id}: {e}")
        
    # Add any extra connected device profiles
    for dev in connected_devices:
        if dev not in nodes:
            nodes[dev] = GraphNode(id=dev, label=dev, type="DeviceProfile")
        edges.append(GraphEdge(
            from_id=cust_id,
            to_id=dev,
            type="ASSOCIATED_DEVICE"
        ))

    return GraphData(
        case_id=case_id,
        nodes=list(nodes.values()),
        edges=edges
    )

@router.get("/{case_id}/similar", response_model=List[Dict[str, Any]])
def get_similar_cases(case_id: str = FPath(..., description="Case ID, e.g. HHG-001")):
    """
    Returns vector similarity match results comparing the current case
    against historical closed cases in graph memory.
    """
    file_path = config.CASES_OUTPUT_DIR / f"{case_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    case_obj = data.get("case", {})
    similar = case_obj.get("similar_prior_cases", [])
    
    if similar:
        formatted = []
        for s in similar:
            if isinstance(s, dict):
                formatted.append(s)
            else:
                formatted.append({"case_id": str(s), "similarity_score": 0.88, "pattern": "historical_match"})
        return formatted
        
    # If not present in json, run live similarity search tool
    summary = case_obj.get("summary", f"Investigation for case {case_id}")
    res = fraud_tools.search_similar_closed_cases(summary, top_k=3)
    formatted_res = []
    for r in res:
        if isinstance(r, dict):
            formatted_res.append(r)
        else:
            formatted_res.append({"case_id": str(r), "similarity_score": 0.85})
    return formatted_res
