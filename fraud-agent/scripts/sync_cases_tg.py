import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "fraud-agent"))

import config
from tg_client import get_tg_connection

def sync_all_cases():
    conn = get_tg_connection()
    if not conn:
        print("Failed to connect to TigerGraph.")
        sys.exit(1)

    cases_dir = config.CASES_OUTPUT_DIR

    for i in range(1, 21):
        case_id = f"HHG-{i:03d}"
        case_file = cases_dir / f"{case_id}.json"
        if not case_file.exists():
            print(f"File {case_file} not found.")
            continue

        with open(case_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        case_body = data.get("case", {})
        
        # Attributes for InvestigationCase vertex
        attrs = {
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": case_body.get("status", "closed_fraud"),
            "verdict": case_body.get("verdict", "fraud"),
            "fraud_probability": float(case_body.get("fraud_probability", 0.0)),
            "pattern": case_body.get("pattern", "none"),
            "pattern_description": case_body.get("pattern_description", ""),
            "exposure_usd": float(case_body.get("exposure_usd", 0.0)),
            "stop_reason": data.get("stop_reason", ""),
            "summary": case_body.get("summary", "")[:1000],
            "written_to_graph": True
        }

        # Upsert single CASE-HHG-XXX vertex
        conn.upsertVertex("InvestigationCase", f"CASE-{case_id}", attrs)

        # Upsert actions
        for action in data.get("actions", []):
            aid = action.get("action_id")
            if aid:
                a_attrs = {
                    "action_type": action.get("action_type", ""),
                    "target_entity_type": action.get("target_entity_type", ""),
                    "target_entity_id": action.get("target_entity_id", ""),
                    "policy_rule_id": action.get("policy_rule_id", ""),
                    "routing": action.get("routing", "auto"),
                    "status": action.get("status", "executed"),
                    "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": action.get("reason", "")[:500]
                }
                conn.upsertVertex("ActionRecord", aid, a_attrs)
                conn.upsertEdge("InvestigationCase", f"CASE-{case_id}", "CASE_RECOMMENDS_ACTION", "ActionRecord", aid)

    print("Successfully synced all 20 benchmark cases into TigerGraph.")

if __name__ == "__main__":
    sync_all_cases()
