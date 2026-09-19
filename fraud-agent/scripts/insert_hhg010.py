import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "fraud-agent"))

import config
from tg_client import get_tg_connection

def insert_missing():
    conn = get_tg_connection()
    if not conn:
        print("Failed to connect to TigerGraph.")
        sys.exit(1)

    case_file = BASE_DIR / "fraud-agent" / "cases" / "HHG-010.json"
    if not case_file.exists():
        case_file = BASE_DIR / "cases" / "HHG-010.json"

    with open(case_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    case_body = data.get("case", {})
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

    conn.upsertVertex("InvestigationCase", "CASE-HHG-010", attrs)
    print("Upserted CASE-HHG-010")

if __name__ == "__main__":
    insert_missing()
