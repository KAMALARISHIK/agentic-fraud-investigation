from typing import Dict, Any, List

def get_action_route(action: str, exposure_usd: float = 0.0) -> str:
    """
    Returns exact approval route per Fraud Policy Section 2:
    - auto: ALLOW_TRANSACTION, MONITOR_CARD, MONITOR_CONNECTED_CARDS, WARN_CUSTOMER,
            VERIFY_WITH_CUSTOMER, STEP_UP_AUTH, GENERATE_REPORT, CREATE_CASE,
            ESCALATE_TO_ANALYST, CLOSE_NO_FRAUD
    - L1 (team lead): DECLINE_TRANSACTION; BLOCK_CARD when exposure <= $2,500
    - L2 (fraud manager): BLOCK_CARD when exposure > $2,500; BLOCK_ALL_CARDS always; FILE_REPORT always
    """
    action = action.strip()
    if action == "DECLINE_TRANSACTION":
        return "L1"
    elif action == "BLOCK_CARD":
        return "L1" if exposure_usd <= 2500.0 else "L2"
    elif action in ["BLOCK_ALL_CARDS", "FILE_REPORT"]:
        return "L2"
    elif action in [
        "ALLOW_TRANSACTION",
        "MONITOR_CARD",
        "MONITOR_CONNECTED_CARDS",
        "WARN_CUSTOMER",
        "VERIFY_WITH_CUSTOMER",
        "STEP_UP_AUTH",
        "GENERATE_REPORT",
        "CREATE_CASE",
        "ESCALATE_TO_ANALYST",
        "CLOSE_NO_FRAUD",
    ]:
        return "auto"
    return "auto"
