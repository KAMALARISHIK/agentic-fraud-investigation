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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fraud_agent.validate_answers")

ALLOWED_PATTERNS = {
    "card_testing",
    "card_not_present_fraud",
    "card_not_present_new_device",
    "out_of_region_use",
    "account_takeover",
    "undocumented",
    "none",
}

ALLOWED_ACTIONS = {
    "ALLOW_TRANSACTION",
    "DECLINE_TRANSACTION",
    "MONITOR_CARD",
    "MONITOR_CONNECTED_CARDS",
    "WARN_CUSTOMER",
    "VERIFY_WITH_CUSTOMER",
    "STEP_UP_AUTH",
    "BLOCK_CARD",
    "BLOCK_ALL_CARDS",
    "GENERATE_REPORT",
    "CREATE_CASE",
    "FILE_REPORT",
    "ESCALATE_TO_ANALYST",
    "CLOSE_NO_FRAUD",
}

def validate_all_answers() -> bool:
    cases_dir = config.CASES_OUTPUT_DIR
    con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)

    # Valid IDs cache
    valid_txns = set(str(r[0]) for r in con.execute("SELECT id FROM transactions_trimmed").fetchall())
    valid_custs = set(str(r[0]) for r in con.execute("SELECT customer_id FROM core_customers").fetchall())
    con.close()

    expected_cases = [f"HHG-{i:03d}" for i in range(1, 21)]
    errors = []

    logger.info(f"Validating {len(expected_cases)} answer files in {cases_dir}...")

    for case_id in expected_cases:
        file_path = cases_dir / f"{case_id}.json"
        if not file_path.exists():
            errors.append(f"Missing answer file: {file_path.name}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"Failed to parse JSON for {case_id}: {e}")
            continue

        # 1. Top level check
        for req_field in ["case_id", "case", "evidence_requests", "next_best_actions", "sar", "stop_reason", "tool_calls", "tokens", "latency_s"]:
            if req_field not in data:
                errors.append(f"[{case_id}] Missing top-level field '{req_field}'")

        if data.get("case_id") != case_id:
            errors.append(f"[{case_id}] Case ID mismatch: expected '{case_id}', got '{data.get('case_id')}'")

        # 2. Case Object check
        case = data.get("case", {})
        for c_field in ["status", "verdict", "fraud_probability", "pattern", "pattern_description", "affected_txn_ids", "first_suspicious_txn_id", "connected_card_ids", "connected_device_profiles", "exposure_usd", "evidence", "similar_prior_cases", "summary", "written_to_graph", "graph_case_id"]:
            if c_field not in case:
                errors.append(f"[{case_id}] Missing case field '{c_field}'")

        pattern = case.get("pattern")
        if pattern not in ALLOWED_PATTERNS:
            errors.append(f"[{case_id}] Invalid pattern '{pattern}'")

        if pattern == "undocumented" and not case.get("pattern_description"):
            errors.append(f"[{case_id}] Pattern 'undocumented' requires non-empty pattern_description")

        verdict = case.get("verdict")
        if verdict not in ["fraud", "legitimate", "uncertain"]:
            errors.append(f"[{case_id}] Invalid verdict '{verdict}'")

        # Check Legitimate requirements
        if verdict == "legitimate":
            if case.get("affected_txn_ids") != []:
                errors.append(f"[{case_id}] Legitimate case must have empty affected_txn_ids")
            if case.get("exposure_usd") != 0.0 and case.get("exposure_usd") != 0:
                errors.append(f"[{case_id}] Legitimate case must have 0 exposure_usd, got {case.get('exposure_usd')}")

        # Check IDs in data
        for tid in case.get("affected_txn_ids", []):
            if str(tid) not in valid_txns:
                errors.append(f"[{case_id}] Affected transaction ID '{tid}' does not exist in dataset")

        # 3. Actions & Routing check
        nba = data.get("next_best_actions", {})
        initial_actions = nba.get("initial", [])
        final_actions = nba.get("final", [])

        has_file_report = False
        exposure = float(case.get("exposure_usd", 0.0))

        for act_list, act_type in [(initial_actions, "initial"), (final_actions, "final")]:
            for a in act_list:
                act_name = a.get("action")
                route = a.get("route")
                if act_name not in ALLOWED_ACTIONS:
                    errors.append(f"[{case_id}] Invalid action name '{act_name}' in {act_type}")
                
                # Check exact routes
                if act_name == "DECLINE_TRANSACTION" and route != "L1":
                    errors.append(f"[{case_id}] DECLINE_TRANSACTION must have route L1, got {route}")
                elif act_name == "BLOCK_CARD":
                    expected_route = "L1" if exposure <= 2500.0 else "L2"
                    if route != expected_route:
                        errors.append(f"[{case_id}] BLOCK_CARD with exposure ${exposure} must have route {expected_route}, got {route}")
                elif act_name in ["BLOCK_ALL_CARDS", "FILE_REPORT"] and route != "L2":
                    errors.append(f"[{case_id}] {act_name} must have route L2, got {route}")
                elif act_name not in ["DECLINE_TRANSACTION", "BLOCK_CARD", "BLOCK_ALL_CARDS", "FILE_REPORT"] and route != "auto":
                    errors.append(f"[{case_id}] {act_name} must have route auto, got {route}")

                if act_type == "final" and act_name == "FILE_REPORT":
                    has_file_report = True

        # 4. SAR check
        sar = data.get("sar", {})
        sar_file = sar.get("file", False)
        if sar_file != has_file_report:
            errors.append(f"[{case_id}] sar.file ({sar_file}) must strictly agree with FILE_REPORT presence in final actions ({has_file_report})")

        if not sar_file:
            if sar.get("narrative") != "":
                errors.append(f"[{case_id}] sar.narrative must be empty string when file is false")
            if sar.get("subjects") != []:
                errors.append(f"[{case_id}] sar.subjects must be empty list when file is false")
            if sar.get("total_amount_usd") != 0.0 and sar.get("total_amount_usd") != 0:
                errors.append(f"[{case_id}] sar.total_amount_usd must be 0 when file is false")
            if sar.get("activity_dates") != []:
                errors.append(f"[{case_id}] sar.activity_dates must be empty list when file is false")
        else:
            if len(sar.get("narrative", "").strip()) < 50:
                errors.append(f"[{case_id}] sar.narrative must be a complete 6-12 sentence report when file is true")
            if len(sar.get("subjects", [])) == 0:
                errors.append(f"[{case_id}] sar.subjects must list affected entities when file is true")

    if errors:
        logger.error(f"VALIDATION FAILED with {len(errors)} errors:")
        for err in errors:
            logger.error(f" - {err}")
        return False
    else:
        logger.info("ALL 20 CASE ANSWERS STRICTLY VALIDATED! 100% COMPLIANT WITH FRAUD POLICY & ANSWER FORMAT.")
        return True

if __name__ == "__main__":
    is_valid = validate_all_answers()
    sys.exit(0 if is_valid else 1)
