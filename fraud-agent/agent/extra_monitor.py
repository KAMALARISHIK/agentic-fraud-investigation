import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any

import config
import duckdb
from agent.graph import investigation_agent
from mcp_client import mcp_manager

logger = logging.getLogger("fraud_agent.extra_monitor")

EXTRA_CASES_DIR = config.BASE_DIR / "cases_extra"
EXTRA_CASES_DIR.mkdir(parents=True, exist_ok=True)

class AutonomousFraudMonitor:
    """
    Innovation Extra:
    Autonomous background monitoring engine that scans November-December 2016 transactions
    to identify undocumented fraud rings, high-risk multi-card device clusters,
    and emerging synthetic identity networks beyond the 20 benchmark test alerts.
    """

    def scan_unflagged_rings(self, risk_threshold: float = 0.85, max_cases: int = 5) -> List[Dict[str, Any]]:
        """
        Scans transactions for shared device hardware fingerprints connecting 2+ distinct customers
        where average risk score > risk_threshold.
        """
        logger.info(f"Starting Autonomous Fraud Ring Scan (Risk Threshold > {risk_threshold})...")
        con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
        
        # Query dense multi-customer device clusters in Nov-Dec
        query = f"""
            WITH device_clusters AS (
                SELECT 
                    device_profile_id,
                    count(DISTINCT customer_id) as distinct_customers,
                    count(*) as total_txns,
                    avg(risk_score) as avg_risk,
                    sum(amount) as total_volume,
                    min(id) as first_txn_id,
                    min(customer_id) as primary_customer
                FROM transactions_trimmed
                WHERE ts >= '2016-11-01 00:00:00'
                  AND device_profile_id IS NOT NULL 
                  AND device_profile_id != 'nan'
                GROUP BY device_profile_id
                HAVING count(DISTINCT customer_id) >= 2 AND avg(risk_score) >= {risk_threshold}
                ORDER BY avg_risk DESC, total_volume DESC
                LIMIT {max_cases}
            )
            SELECT * FROM device_clusters
        """
        rings_df = con.execute(query).df()
        con.close()

        discovered_cases = []

        for idx, row in rings_df.iterrows():
            cid = f"EXTRA-RING-{idx+1:03d}"
            dev_id = str(row["device_profile_id"])
            primary_cust = str(row["primary_customer"])
            primary_card = f"{primary_cust}-K1"
            first_txn = str(row["first_txn_id"])
            avg_risk = float(row["avg_risk"])
            vol = float(row["total_volume"])
            num_custs = int(row["distinct_customers"])

            logger.info(f"Discovered Autonomous Fraud Ring: {cid} on device '{dev_id[:30]}' ({num_custs} customers, ${vol:,.2f})")

            # Formulate autonomous alert
            alert = {
                "case_id": cid,
                "customer_id": primary_cust,
                "card_id": primary_card,
                "flagged_txn_id": first_txn,
                "trigger_type": "autonomous_monitor",
                "trigger_text": f"Autonomous Monitor detected device ring '{dev_id[:35]}' shared by {num_custs} distinct customer accounts with average risk {avg_risk:.2f} and volume ${vol:,.2f}.",
                "risk_score": avg_risk
            }

            # Run full investigation
            investigation = investigation_agent.investigate(alert)
            investigation["ring_metadata"] = {
                "shared_device_profile": dev_id,
                "distinct_customers_count": num_custs,
                "total_ring_volume_usd": vol,
                "discovery_mode": "autonomous_graph_clustering"
            }

            # Save to cases_extra/
            out_file = EXTRA_CASES_DIR / f"{cid}.json"
            clean_save = {k: v for k, v in investigation.items() if k not in ["customer_id", "card_id"]}
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(clean_save, f, indent=2)

            discovered_cases.append(investigation)

        logger.info(f"Autonomous Monitor completed. Saved {len(discovered_cases)} extra ring cases to {EXTRA_CASES_DIR}")
        return discovered_cases

autonomous_monitor = AutonomousFraudMonitor()
