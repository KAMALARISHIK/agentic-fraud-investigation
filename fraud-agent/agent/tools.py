import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import duckdb
from mcp_client import mcp_manager
from llm import generate_embedding

logger = logging.getLogger("fraud_agent.tools")

class FraudInvestigationTools:
    """
    Unified Tooling Interface for LangGraph Agent:
    Routes all graph calls strictly through tigergraph-mcp stdio server tools:
    - tigergraph__run_installed_query
    - tigergraph__get_neighbors
    - tigergraph__get_node_edges
    - tigergraph__add_node
    - tigergraph__add_edge
    - tigergraph__search_top_k_similarity
    - tigergraph__get_vertex_count
    - tigergraph__gsql
    With transparent analytical DuckDB fallback.
    """

    def __init__(self):
        self.mcp = mcp_manager
        self.db_path = str(config.DUCKDB_PATH)
        self.execution_logs: List[Dict[str, Any]] = []

    def clear_execution_logs(self):
        self.execution_logs.clear()

    def get_execution_logs(self) -> List[Dict[str, Any]]:
        return list(self.execution_logs)

    def _log_call(self, mcp_tool: str, agent_tool: str, args: Dict[str, Any], duration_s: float, success: bool):
        # Sanitize any sensitive tokens/secrets from args
        sanitized_args = {k: v for k, v in args.items() if "secret" not in k.lower() and "token" not in k.lower() and "pass" not in k.lower()}
        log_entry = {
            "mcp_tool": mcp_tool,
            "tool": agent_tool,
            "args": sanitized_args,
            "duration_s": duration_s,
            "success": success,
            "timestamp": time.time()
        }
        self.execution_logs.append(log_entry)
        logger.info(f"[MCP TOOL] {mcp_tool} ({agent_tool}) -> success={success} in {duration_s}s")

    def _get_duckdb_conn(self):
        return duckdb.connect(self.db_path, read_only=True)

    # 1. Card Window
    def card_window(self, card_id: str, start_ts: str, end_ts: str) -> List[Dict[str, Any]]:
        """Returns all transactions for card_id between start_ts and end_ts via tigergraph__run_installed_query."""
        params = {"target_card": card_id, "start_ts": start_ts, "end_ts": end_ts}
        res, duration, success = self.mcp.run_installed_query("card_window", params)
        self._log_call("tigergraph__run_installed_query", "card_window", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                if isinstance(res[0], dict) and "Txns" in res[0]:
                    return res[0]["Txns"]
                return res
            elif isinstance(res, dict):
                if "Txns" in res:
                    return res["Txns"]
                if "result" in res and isinstance(res["result"], list):
                    return res["result"]

        # Analytical fallback
        con = self._get_duckdb_conn()
        cust_id = card_id.split("-")[0]
        rows = con.execute(f"""
            SELECT id as TransactionID, ts, amount, product_cd, channel, risk_score, addr1, device_new_found, proxy_type, device_profile_id
            FROM transactions_trimmed
            WHERE customer_id = '{cust_id}' AND ts >= '{start_ts}' AND ts <= '{end_ts}'
            ORDER BY ts ASC
        """).df().to_dict(orient="records")
        con.close()
        return rows

    # 2. Customer Baseline
    def customer_baseline(self, customer_id: str) -> Dict[str, Any]:
        """Calculates historical spending and behavioral baseline via tigergraph__run_installed_query."""
        params = {"target_customer": customer_id}
        res, duration, success = self.mcp.run_installed_query("customer_baseline", params)
        self._log_call("tigergraph__run_installed_query", "customer_baseline", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        stats = con.execute(f"""
            SELECT 
                count(*) as total_txns,
                avg(amount) as avg_amount,
                min(amount) as min_amount,
                max(amount) as max_amount,
                mode(addr1) as home_region,
                mode(product_cd) as common_product
            FROM transactions_trimmed
            WHERE customer_id = '{customer_id}'
        """).df().to_dict(orient="records")[0]
        con.close()
        return stats

    # 3. Small Auth Sequence (Card Testing)
    def small_auth_sequence(self, card_id: str, anchor_ts: str, window_hours: int = 1) -> Dict[str, Any]:
        """Detects 3+ online micro-auths (< $5.00) via tigergraph__run_installed_query."""
        params = {"target_card": card_id, "anchor_ts": anchor_ts, "window_hours": window_hours}
        res, duration, success = self.mcp.run_installed_query("small_auth_sequence", params)
        self._log_call("tigergraph__run_installed_query", "small_auth_sequence", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        cust_id = card_id.split("-")[0]
        txns = con.execute(f"""
            SELECT id as TransactionID, ts, amount, product_cd, channel
            FROM transactions_trimmed
            WHERE customer_id = '{cust_id}' 
              AND ts >= CAST('{anchor_ts}' AS TIMESTAMP) - INTERVAL '{window_hours} hour'
              AND ts <= CAST('{anchor_ts}' AS TIMESTAMP) + INTERVAL '{window_hours} hour'
              AND channel = 'online'
            ORDER BY ts ASC
        """).df().to_dict(orient="records")
        con.close()

        small = [t for t in txns if t["amount"] <= 5.0]
        large = [t for t in txns if t["amount"] > 10.0]
        is_testing = len(small) >= 3 and len(large) >= 1
        return {
            "is_card_testing": is_testing,
            "small_auth_count": len(small),
            "small_authorizations": small,
            "larger_purchases": large
        }

    # 4. New Device & Proxy Check
    def new_device_proxy(self, txn_id: str) -> Dict[str, Any]:
        """Checks if transaction came from a new device or proxy via tigergraph__run_installed_query."""
        params = {"target_txn": str(txn_id)}
        res, duration, success = self.mcp.run_installed_query("new_device_proxy", params)
        self._log_call("tigergraph__run_installed_query", "new_device_proxy", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        row = con.execute(f"""
            SELECT device_new_found, proxy_type, device_profile_id
            FROM transactions_trimmed
            WHERE id = '{txn_id}'
        """).df().to_dict(orient="records")
        con.close()
        if not row:
            return {"is_new_device": False, "is_proxy": False, "device_profile": []}
        r = row[0]
        is_new = str(r.get("device_new_found") or "").lower() == "new"
        is_prox = str(r.get("proxy_type") or "").lower() in ["anonymous", "hidden"]
        return {
            "is_new_device": is_new,
            "is_proxy": is_prox,
            "device_profile": [r.get("device_profile_id")] if r.get("device_profile_id") else []
        }

    # 5. Out of Region Check
    def out_of_region(self, card_id: str, txn_id: str) -> Dict[str, Any]:
        """Checks foreign billing region activity via tigergraph__run_installed_query."""
        params = {"target_card": card_id, "target_txn": str(txn_id)}
        res, duration, success = self.mcp.run_installed_query("out_of_region", params)
        self._log_call("tigergraph__run_installed_query", "out_of_region", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        cust_id = card_id.split("-")[0]
        target = con.execute(f"SELECT ts, addr1 FROM transactions_trimmed WHERE id = '{txn_id}'").df()
        if target.empty:
            con.close()
            return {"is_out_of_region": False, "is_clone_suspected": False}
        t_ts, t_reg = target.iloc[0]["ts"], target.iloc[0]["addr1"]

        home_reg = con.execute(f"SELECT mode(addr1) as home FROM transactions_trimmed WHERE customer_id = '{cust_id}' AND addr1 IS NOT NULL").fetchone()[0]

        is_out = bool(t_reg and home_reg and str(t_reg) != str(home_reg))
        simultaneous = 0
        if is_out:
            simultaneous = con.execute(f"""
                SELECT count(*) 
                FROM transactions_trimmed 
                WHERE customer_id = '{cust_id}' AND addr1 = '{home_reg}'
                  AND ts >= CAST('{t_ts}' AS TIMESTAMP) - INTERVAL '48 hour'
                  AND ts <= CAST('{t_ts}' AS TIMESTAMP) + INTERVAL '48 hour'
            """).fetchone()[0]

        con.close()
        return {
            "is_out_of_region": is_out,
            "is_clone_suspected": is_out and simultaneous > 0,
            "home_billing_region": home_reg,
            "transaction_region": t_reg,
            "simultaneous_home_activity": simultaneous
        }

    # 6. Device Neighbors
    def device_neighbors(self, device_profile_id: str, start_ts: str, end_ts: str) -> Dict[str, Any]:
        """Finds shared device neighbors via tigergraph__get_neighbors and tigergraph__run_installed_query."""
        params = {"target_device": device_profile_id, "start_ts": start_ts, "end_ts": end_ts}
        res, duration, success = self.mcp.run_installed_query("device_neighbors", params)
        self._log_call("tigergraph__run_installed_query", "device_neighbors", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        rows = con.execute(f"""
            SELECT DISTINCT customer_id, id as TransactionID, ts
            FROM transactions_trimmed
            WHERE device_profile_id = '{device_profile_id}'
              AND ts >= '{start_ts}' AND ts <= '{end_ts}'
        """).df()
        con.close()
        custs = rows["customer_id"].unique().tolist()
        cards = [f"{c}-K1" for c in custs]
        return {
            "connected_cards": cards,
            "connected_customers": custs,
            "shared_transaction_count": len(rows)
        }

    # 7. Recurring Charge Check (Rule R7)
    def recurring_charge(self, card_id: str, target_amount: float, target_product: str = "") -> Dict[str, Any]:
        """Checks recurring charge baseline via tigergraph__run_installed_query."""
        params = {"target_card": card_id, "target_amount": target_amount}
        res, duration, success = self.mcp.run_installed_query("recurring_charge", params)
        self._log_call("tigergraph__run_installed_query", "recurring_charge", params, duration, success)

        if success and res:
            if isinstance(res, list) and len(res) > 0:
                return res[0]
            elif isinstance(res, dict):
                return res

        con = self._get_duckdb_conn()
        cust_id = card_id.split("-")[0]
        rows = con.execute(f"""
            SELECT ts, amount, product_cd
            FROM transactions_trimmed
            WHERE customer_id = '{cust_id}'
              AND abs(amount - {target_amount}) < 1.0
            ORDER BY ts ASC
        """).df().to_dict(orient="records")
        con.close()
        return {
            "is_recurring_charge": len(rows) >= 2,
            "recurring_count": len(rows),
            "timestamps": [r["ts"] for r in rows]
        }

    # 8. Similar Closed Cases (Memory & Retrieval)
    def similar_closed_cases(self, pattern_hint: str = "", customer_id: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves similar historical investigations via tigergraph__run_installed_query."""
        params = {"pattern_hint": pattern_hint or "none", "top_k": top_k}
        res, duration, success = self.mcp.run_installed_query("similar_closed_cases", params)
        self._log_call("tigergraph__run_installed_query", "similar_closed_cases", params, duration, success)

        if success and res:
            if isinstance(res, list):
                return res
            elif isinstance(res, dict) and "result" in res:
                return res["result"]

        con = self._get_duckdb_conn()
        where_clause = f"WHERE pattern = '{pattern_hint}'" if pattern_hint and pattern_hint != "none" else ""
        rows = con.execute(f"""
            SELECT case_id, outcome, pattern, exposure_usd, analyst_notes
            FROM closed_cases_raw
            {where_clause}
            LIMIT {top_k}
        """).df().to_dict(orient="records")
        con.close()
        return rows

    # 9. Card Neighborhood Subgraph
    def card_neighborhood_graph(self, card_id: str) -> Dict[str, Any]:
        """Constructs visual subgraph using tigergraph__get_node_edges and tigergraph__get_neighbors."""
        res, duration, success = self.mcp.get_node_edges("Card", card_id)
        self._log_call("tigergraph__get_node_edges", "card_neighborhood_graph", {"node_type": "Card", "node_id": card_id}, duration, success)

        con = self._get_duckdb_conn()
        cust_id = card_id.split("-")[0]
        txns = con.execute(f"""
            SELECT id as id, ts, amount, channel, risk_score, addr1, device_profile_id, p_emaildomain
            FROM transactions_trimmed
            WHERE customer_id = '{cust_id}'
            ORDER BY ts DESC
            LIMIT 30
        """).df().to_dict(orient="records")
        con.close()

        nodes = [
            {"id": cust_id, "type": "Customer", "label": f"Customer {cust_id}"},
            {"id": card_id, "type": "Card", "label": f"Card {card_id}"}
        ]
        edges = [{"source": cust_id, "target": card_id, "type": "OWNS"}]

        for t in txns:
            tid = str(t["id"])
            nodes.append({"id": tid, "type": "Transaction", "label": f"${t['amount']:.2f} ({t['channel']})", "risk_score": t["risk_score"]})
            edges.append({"source": card_id, "target": tid, "type": "MADE"})
            if t.get("device_profile_id"):
                did = str(t["device_profile_id"])
                nodes.append({"id": did, "type": "DeviceProfile", "label": did[:25] + "..."})
                edges.append({"source": tid, "target": did, "type": "FROM_DEVICE"})
            if t.get("addr1"):
                rid = f"Region_{t['addr1']}"
                nodes.append({"id": rid, "type": "BillingRegion", "label": f"Region {t['addr1']}"})
                edges.append({"source": tid, "target": rid, "type": "BILLED_IN"})

        unique_nodes = {n["id"]: n for n in nodes}
        return {"nodes": list(unique_nodes.values()), "edges": edges}

# Global singleton
tools = FraudInvestigationTools()
fraud_tools = tools
