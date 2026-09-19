import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query

import config
from agent.extra_monitor import autonomous_monitor, EXTRA_CASES_DIR

router = APIRouter(prefix="/extra", tags=["Innovation Extra: Autonomous Monitor"])

@router.get("/scan", response_model=Dict[str, Any])
def run_autonomous_scan(
    risk_threshold: float = Query(0.80, description="Minimum average risk score for device clusters"),
    limit: int = Query(5, description="Maximum number of extra fraud rings to investigate")
):
    """
    Triggers the Innovation Extra Autonomous Monitor to scan November-December transactions
    for undocumented multi-card device clusters and emerging synthetic identity networks.
    """
    cases = autonomous_monitor.scan_unflagged_rings(risk_threshold=risk_threshold, max_cases=limit)
    return {
        "status": "success",
        "discovered_rings_count": len(cases),
        "cases_directory": str(EXTRA_CASES_DIR),
        "cases": cases
    }

@router.get("/cases", response_model=List[Dict[str, Any]])
def list_extra_cases():
    """List all extra autonomous ring cases stored in cases_extra/."""
    extra_files = sorted(EXTRA_CASES_DIR.glob("EXTRA-RING-*.json"))
    cases = []
    for fp in extra_files:
        with open(fp, "r", encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases
