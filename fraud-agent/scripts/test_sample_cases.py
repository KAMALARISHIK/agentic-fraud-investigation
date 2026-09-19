import sys
import json
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import duckdb
from agent.graph import investigation_agent
from scripts.validate_answers import validate_all_answers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.test_sample_cases")

def test_samples():
    con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
    cases_df = con.execute("SELECT * FROM case_pack_raw WHERE case_id IN ('HHG-001', 'HHG-002')").df()
    for _, row in cases_df.iterrows():
        case_alert = row.to_dict()
        cid = str(case_alert["case_id"])
        
        logger.info(f"Running investigation on {cid} via tigergraph-mcp...")
        res = investigation_agent.investigate(case_alert)
        
        # Clean helper fields from top-level before saving answer JSON
        res_to_save = {k: v for k, v in res.items() if k not in ["customer_id", "card_id"]}

        # Write to cases/
        out_file = config.CASES_OUTPUT_DIR / f"{cid}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(res_to_save, f, indent=2)
            
        logger.info(f"Saved {cid}.json: verdict={res['case']['verdict']}, pattern={res['case']['pattern']}, tool_calls={res['tool_calls']}")

    con.close()
    
    # Run validation
    logger.info("Running validation on all 20 answer files...")
    valid = validate_all_answers()
    logger.info(f"Validation Result: {valid}")

if __name__ == "__main__":
    test_samples()
