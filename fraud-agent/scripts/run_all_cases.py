import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import duckdb
from agent.graph import investigation_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.run_all_cases")

def run_all_cases():
    """
    Runs the fraud investigation agent on all 20 exam cases in case_pack.csv,
    generates structured answer JSON files in cases/<case_id>.json,
    and writes each case into TigerGraph.
    """
    con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
    cases_df = con.execute("SELECT * FROM case_pack_raw ORDER BY case_id ASC").df()
    con.close()

    logger.info(f"Loaded {len(cases_df)} exam cases from case_pack.csv.")
    config.CASES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, row in cases_df.iterrows():
        case_alert = row.to_dict()
        case_id = str(case_alert["case_id"])
        logger.info(f"[{idx+1}/20] Processing {case_id} ({case_alert.get('trigger_type')})...")

        res = investigation_agent.investigate(case_alert)
        out_file = config.CASES_OUTPUT_DIR / f"{case_id}.json"
        
        # Clean helper fields from top-level before saving answer JSON
        res_to_save = {k: v for k, v in res.items() if k not in ["customer_id", "card_id"]}

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(res_to_save, f, indent=2)

        results.append(res)
        logger.info(f"Saved answer to {out_file} (Verdict: {res['case']['verdict']}, Pattern: {res['case']['pattern']}, Exposure: ${res['case']['exposure_usd']:,.2f})")

    logger.info(f"All {len(results)} cases investigated and written to {config.CASES_OUTPUT_DIR}!")

if __name__ == "__main__":
    run_all_cases()
