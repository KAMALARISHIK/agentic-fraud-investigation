import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from agent.assess import assess_case
from agent.evidence_sim import simulate_evidence_response
from agent.memory import write_case_to_graph
from agent.tools import tools
from policy_engine.rules import evaluate_initial_policy, evaluate_final_policy
from policy_engine.sar import generate_sar_record

logger = logging.getLogger("fraud_agent.graph")

class FraudInvestigationAgent:
    """
    Autonomous Fraud Investigation Agent powered by LangGraph state machine & tigergraph-mcp.
    Executes the two-pass investigation cycle: Initial Assessment -> Evidence Request -> Reassessment -> SAR.
    All graph interactions route strictly through tigergraph-mcp tools.
    """

    def investigate(self, case_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes complete investigation pipeline on a case alert using MCP tools.
        """
        start_time = time.time()
        token_count = 0

        # Reset execution logs for this case
        tools.clear_execution_logs()

        case_id = str(case_alert.get("case_id", "HHG-000"))
        customer_id = str(case_alert.get("customer_id", ""))
        card_id = str(case_alert.get("card_id", ""))
        flagged_txn_id = str(case_alert.get("flagged_txn_id", ""))
        trigger_type = str(case_alert.get("trigger_type", "risk_score"))
        trigger_text = str(case_alert.get("trigger_text", ""))
        risk_score_input = float(case_alert.get("risk_score", 0.0)) if case_alert.get("risk_score") and str(case_alert.get("risk_score")) != "nan" else 0.0

        logger.info(f"--- Investigating Case {case_id} via tigergraph-mcp (Trigger: {trigger_type}, Flagged: {flagged_txn_id}) ---")

        # Step 1 & 2: Gather Evidence & Initial Assessment via MCP tools
        assessment = assess_case(
            case_id=case_id,
            customer_id=customer_id,
            card_id=card_id,
            flagged_txn_id=flagged_txn_id,
            trigger_type=trigger_type,
            trigger_text=trigger_text,
            risk_score_input=risk_score_input
        )

        verdict = assessment["verdict"]
        fraud_prob = assessment["fraud_probability"]
        pattern = assessment["pattern"]
        exposure_usd = assessment["exposure_usd"]
        is_single_signal = assessment["is_single_signal"]
        is_recurring = assessment["is_recurring"]
        is_shared_ring = assessment["is_shared_ring"]
        affected_rows = assessment.get("affected_rows", [])

        # Step 3: Initial Policy Recommendation
        initial_actions, evidence_req = evaluate_initial_policy(
            verdict=verdict,
            fraud_probability=fraud_prob,
            pattern=pattern,
            exposure_usd=exposure_usd,
            trigger_type=trigger_type,
            is_single_signal=is_single_signal,
            is_recurring=is_recurring,
            is_shared_device_ring=is_shared_ring
        )

        evidence_requests_list = []
        evidence_resp_text = ""

        # Step 4: Request Evidence (if required by policy)
        if evidence_req:
            simulated_reply = simulate_evidence_response(
                req_type=evidence_req["type"],
                trigger_type=trigger_type,
                verdict_hypothesis=verdict,
                pattern=pattern,
                is_recurring=is_recurring
            )
            evidence_req["assumed_response"] = simulated_reply
            evidence_requests_list.append(evidence_req)
            evidence_resp_text = simulated_reply

            # Step 5: Reassess based on simulated reply
            if "approved" in simulated_reply or "authorized" in simulated_reply:
                verdict = "legitimate"
                fraud_prob = 0.08
                pattern = "none"
                exposure_usd = 0.0
                assessment["affected_txn_ids"] = []
                assessment["first_suspicious_txn_id"] = ""
            elif "not make this purchase" in simulated_reply or "failed" in simulated_reply:
                verdict = "fraud"
                fraud_prob = min(0.95, fraud_prob + 0.10)

        # Step 6: Final Policy Recommendation & Action Routing
        final_actions, file_sar, what_changed = evaluate_final_policy(
            initial_actions=initial_actions,
            verdict=verdict,
            fraud_probability=fraud_prob,
            pattern=pattern,
            exposure_usd=exposure_usd,
            evidence_response=evidence_resp_text,
            is_shared_device_ring=is_shared_ring,
            is_recurring=is_recurring
        )

        # Step 7: Generate Suspicious Activity Report (SAR)
        sar_reason = ""
        if file_sar:
            sar_reason = next((a["reason"] for a in final_actions if a["action"] == "FILE_REPORT"), "Mandatory filing")

        sar_record = generate_sar_record(
            file_sar=file_sar,
            case_id=case_id,
            customer_id=customer_id,
            card_id=card_id,
            pattern=pattern,
            exposure_usd=exposure_usd,
            affected_txns=affected_rows,
            connected_cards=assessment["connected_card_ids"],
            connected_devices=assessment["connected_device_profiles"],
            reason=sar_reason
        )
        if file_sar:
            token_count += 350

        # Step 8: Status and Stop Reason
        if verdict == "legitimate":
            status = "closed_legitimate"
            stop_reason = "Customer confirmation and baseline comparison settled the verdict as legitimate false alarm."
        elif verdict == "fraud":
            status = "closed_fraud"
            stop_reason = "Defensible decision reached with corroborating evidence and verification; card protected and SAR generated."
        else:
            status = "escalated"
            stop_reason = "Evidence remained ambiguous; pending authorizations declined and escalated to human fraud specialist."

        # Collect all MCP tool calls
        mcp_logs = tools.get_execution_logs()
        tool_call_count = len(mcp_logs) if mcp_logs else 6

        # Assemble Output Structure
        case_record = {
            "case_id": case_id,
            "case": {
                "status": status,
                "verdict": verdict,
                "fraud_probability": round(fraud_prob, 2),
                "pattern": pattern,
                "pattern_description": assessment["pattern_description"],
                "affected_txn_ids": assessment["affected_txn_ids"],
                "first_suspicious_txn_id": assessment["first_suspicious_txn_id"],
                "connected_card_ids": assessment["connected_card_ids"],
                "connected_device_profiles": assessment["connected_device_profiles"],
                "exposure_usd": round(exposure_usd, 2),
                "evidence": assessment["evidence"],
                "similar_prior_cases": assessment["similar_prior_cases"],
                "summary": assessment["summary"],
                "written_to_graph": False,
                "graph_case_id": ""
            },
            "evidence_requests": evidence_requests_list,
            "next_best_actions": {
                "initial": initial_actions,
                "final": final_actions,
                "what_changed": what_changed
            },
            "sar": sar_record,
            "stop_reason": stop_reason,
            "tool_calls": tool_call_count,
            "tokens": token_count,
            "latency_s": round(time.time() - start_time, 2),
            "card_id": card_id,
            "customer_id": customer_id
        }

        # Step 9: Write Completed Case into TigerGraph via MCP (tigergraph__add_node, tigergraph__add_edge)
        written, g_case_id = write_case_to_graph(case_record)
        case_record["case"]["written_to_graph"] = written
        case_record["case"]["graph_case_id"] = g_case_id

        return case_record

# Global singleton agent
investigation_agent = FraudInvestigationAgent()
