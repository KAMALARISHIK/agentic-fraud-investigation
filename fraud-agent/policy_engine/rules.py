from typing import List, Dict, Any, Tuple, Optional
from policy_engine.routing import get_action_route

def evaluate_initial_policy(
    verdict: str,
    fraud_probability: float,
    pattern: str,
    exposure_usd: float,
    trigger_type: str,
    is_single_signal: bool,
    is_recurring: bool,
    is_shared_device_ring: bool,
    cleared_large_purchase: bool = False,
) -> Tuple[List[Dict[str, str]], Optional[Dict[str, Any]]]:
    """
    Evaluates policy rules before any evidence requests (INITIAL recommendation).
    Returns (initial_actions, evidence_request_needed).
    """
    actions = []
    evidence_req = None

    # Legitimate verdict upfront
    if verdict == "legitimate" or fraud_probability <= 0.15:
        actions.append({"action": "ALLOW_TRANSACTION", "route": "auto", "reason": "Activity matches customer baseline and historical patterns"})
        actions.append({"action": "CLOSE_NO_FRAUD", "route": "auto", "reason": "R3: Alert cleared as legitimate activity"})
        return actions, None

    # R7: Disputed recurring charge
    if is_recurring:
        actions.append({"action": "CREATE_CASE", "route": "auto", "reason": "R7: Recurring subscription charge disputed"})
        actions.append({"action": "VERIFY_WITH_CUSTOMER", "route": "auto", "reason": "R7: Confirm recurring merchant authorization with cardholder"})
        actions.append({"action": "WARN_CUSTOMER", "route": "auto", "reason": "R7: Inform cardholder of active recurring billing profile"})
        evidence_req = {
            "type": "customer_validation",
            "asked_after_step": 3,
            "assumed_response": "Customer recognized the recurring service subscription upon reminder and approved the billing."
        }
        return actions, evidence_req

    # R5: Card testing sequence
    if pattern == "card_testing":
        actions.append({"action": "DECLINE_TRANSACTION", "route": get_action_route("DECLINE_TRANSACTION"), "reason": "R5: Card testing micro-authorization sequence identified"})
        if cleared_large_purchase or exposure_usd > 100:
            actions.append({"action": "BLOCK_CARD", "route": get_action_route("BLOCK_CARD", exposure_usd), "reason": "R5: Testing sequence followed by cleared high-value purchase"})
        else:
            actions.append({"action": "STEP_UP_AUTH", "route": "auto", "reason": "R5: Require step-up authentication before further authorizations"})
        
        evidence_req = {
            "type": "customer_validation",
            "asked_after_step": 3,
            "assumed_response": "Customer states they did not initiate these micro-authorizations and remains in possession of the card."
        }
        return actions, evidence_req

    # Customer report trigger (customer already denied transaction)
    if trigger_type == "customer_report":
        actions.append({"action": "DECLINE_TRANSACTION", "route": get_action_route("DECLINE_TRANSACTION"), "reason": "Customer initiated dispute regarding unauthorized charge"})
        actions.append({"action": "VERIFY_WITH_CUSTOMER", "route": "auto", "reason": "R1: Confirm details of unauthorized activity with cardholder"})
        evidence_req = {
            "type": "customer_validation",
            "asked_after_step": 3,
            "assumed_response": "Customer confirmed they did not authorize the transaction and requested card replacement."
        }
        return actions, evidence_req

    # Analyst request trigger (investigate device ring)
    if trigger_type == "analyst_request" or is_shared_device_ring:
        actions.append({"action": "CREATE_CASE", "route": "auto", "reason": "R6: Multi-card activity linked to shared device profile"})
        actions.append({"action": "MONITOR_CARD", "route": "auto", "reason": "R6: Placed card under heightened surveillance"})
        evidence_req = {
            "type": "analyst_info",
            "asked_after_step": 3,
            "assumed_response": "Analyst confirmed device profile is associated with a coordinated multi-account credential stuffing attack."
        }
        return actions, evidence_req

    # R1: Single signal / risk score alone & fraud probability < 0.70
    if is_single_signal or fraud_probability < 0.70:
        actions.append({"action": "VERIFY_WITH_CUSTOMER", "route": "auto", "reason": "R1: Probability below 0.70 on single risk score signal; verify before block"})
        actions.append({"action": "MONITOR_CARD", "route": "auto", "reason": "R1: Monitor card pending customer verification"})
        evidence_req = {
            "type": "customer_validation",
            "asked_after_step": 3,
            "assumed_response": "Customer states they made this purchase online and verified their identity." if fraud_probability < 0.65 else "Customer states they did not make this purchase."
        }
        return actions, evidence_req

    # High probability fraud (> 0.70) on initial evidence
    actions.append({"action": "DECLINE_TRANSACTION", "route": get_action_route("DECLINE_TRANSACTION"), "reason": "Suspicious transaction exceeding risk parameters"})
    actions.append({"action": "STEP_UP_AUTH", "route": "auto", "reason": "R1: Require step-up authentication on high-risk transaction"})
    evidence_req = {
        "type": "step_up_auth",
        "asked_after_step": 3,
        "assumed_response": "Step-up authentication failed (passcode was not entered within timeout window)."
    }
    return actions, evidence_req

def evaluate_final_policy(
    initial_actions: List[Dict[str, str]],
    verdict: str,
    fraud_probability: float,
    pattern: str,
    exposure_usd: float,
    evidence_response: str,
    is_shared_device_ring: bool,
    is_recurring: bool,
) -> Tuple[List[Dict[str, str]], bool, str]:
    """
    Evaluates final policy rules taking into account evidence response (FINAL recommendation).
    Returns (final_actions, should_file_sar, what_changed).
    """
    final_actions = []
    file_sar = False
    what_changed = "nothing"

    # Case 1: Cleared / Legitimate response
    if "approved the billing" in evidence_response or "made this purchase" in evidence_response or verdict == "legitimate":
        final_actions.append({"action": "ALLOW_TRANSACTION", "route": "auto", "reason": "R3: Customer validated authentic activity"})
        final_actions.append({"action": "CLOSE_NO_FRAUD", "route": "auto", "reason": "R3: Customer confirmed transaction; alert closed as false alarm"})
        what_changed = "Customer confirmation established authentic use, clearing the alert under R3."
        return final_actions, False, what_changed

    # Case 2: Recurring charge dispute (R7)
    if is_recurring:
        final_actions.append({"action": "CREATE_CASE", "route": "auto", "reason": "R7: Internal record of recurring billing dispute opened"})
        final_actions.append({"action": "WARN_CUSTOMER", "route": "auto", "reason": "R7: Advised customer regarding subscription merchant contact"})
        what_changed = "Customer confirmed recurring subscription service; card kept active under R7."
        return final_actions, False, what_changed

    # Case 3: Confirmed Fraud (Customer denied / Step-up failed / Analyst confirmed ring)
    if verdict == "fraud" or fraud_probability >= 0.70:
        # Block Card (L1 if <= 2500, L2 if > 2500)
        route_block = get_action_route("BLOCK_CARD", exposure_usd)
        final_actions.append({
            "action": "BLOCK_CARD",
            "route": route_block,
            "reason": f"R2: Customer denied activity; exposure ${exposure_usd:,.2f} ({route_block} approval)"
        })
        final_actions.append({
            "action": "CREATE_CASE",
            "route": "auto",
            "reason": "R2: Internal fraud case opened with evidence graph attached"
        })

        # Check SAR requirement: exposure > $1000 OR shared ring OR undocumented (R9)
        if exposure_usd > 1000.0 or is_shared_device_ring or pattern == "undocumented":
            file_sar = True
            sar_reason = "R2 & Section 3a: Confirmed unauthorized activity exceeding $1,000 threshold" if exposure_usd > 1000.0 else "R6: Fraud network linked across shared device profile"
            if pattern == "undocumented":
                sar_reason = "R9: Undocumented coordinated fraud pattern identified"
            
            final_actions.append({
                "action": "FILE_REPORT",
                "route": "L2",
                "reason": sar_reason
            })

        if is_shared_device_ring:
            final_actions.append({
                "action": "MONITOR_CONNECTED_CARDS",
                "route": "auto",
                "reason": "R6: Placed all cards sharing compromise origin under heightened monitoring"
            })

        what_changed = f"Customer denial confirmed compromise, elevating probability to {fraud_probability:.2f} and triggering BLOCK_CARD and internal case creation."

    elif verdict == "uncertain":
        # R8: Escalate when uncertain and exposed
        final_actions.append({"action": "MONITOR_CARD", "route": "auto", "reason": "R4: Heightened monitoring active for 72 hours"})
        final_actions.append({"action": "DECLINE_TRANSACTION", "route": "L1", "reason": "R4: Declined unverified authorization"})
        if exposure_usd > 500.0:
            final_actions.append({"action": "ESCALATE_TO_ANALYST", "route": "auto", "reason": "R8: Ambiguous signal with exposure exceeding $500 threshold"})
        what_changed = "Evidence remained inconclusive; pending authorizations declined and escalated under R8."

    return final_actions, file_sar, what_changed
