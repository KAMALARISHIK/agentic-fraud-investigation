from typing import Dict, Any, Optional

def simulate_evidence_response(
    req_type: str,
    trigger_type: str,
    verdict_hypothesis: str,
    pattern: str,
    is_recurring: bool = False,
) -> str:
    """
    Deterministically simulates realistic cardholder, step-up auth, or analyst responses.
    """
    if is_recurring:
        return "Customer recognized the recurring subscription service upon reminder and confirmed the merchant."

    if req_type == "customer_validation":
        if verdict_hypothesis == "legitimate":
            return "Customer confirms they authorized and completed this purchase while shopping online."
        elif verdict_hypothesis == "fraud":
            return "Customer states they did not make this purchase, did not share credentials, and still has the physical card."
        else:
            return "Customer could not be reached via SMS or telephone within the initial verification window."

    elif req_type == "step_up_auth":
        if verdict_hypothesis == "legitimate":
            return "Cardholder successfully completed biometric step-up authentication via mobile banking app."
        else:
            return "Step-up OTP authentication failed; no response received from registered mobile device."

    elif req_type == "analyst_info":
        if pattern == "undocumented" or "device" in pattern:
            return "Analyst confirms device profile was observed across multiple unrelated accounts during November coordinated attacks."
        return "Analyst confirms device and network attributes correlate with historical compromise records."

    return "No response received."
