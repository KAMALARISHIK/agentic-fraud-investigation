import json
from typing import List, Dict, Any
from fastapi import APIRouter

import config
from app.schemas import PatternItem

router = APIRouter(prefix="/memory", tags=["Memory"])

FRAUD_PATTERNS_CATALOG = [
    PatternItem(
        pattern="card_testing",
        description="High-frequency micro-authorization attempts under $15 followed by large high-ticket purchases once card validity is confirmed.",
        risk_level="HIGH",
        applicable_rules=["R1", "R8", "R9"],
        sample_cases=["HHG-001", "HHG-008", "HHG-015"]
    ),
    PatternItem(
        pattern="card_not_present_fraud",
        description="Uncharacteristic e-commerce or digital transactions occurring without physical card presentation, often across velocity spikes.",
        risk_level="HIGH",
        applicable_rules=["R2", "R8", "R9"],
        sample_cases=["HHG-002", "HHG-007", "HHG-014"]
    ),
    PatternItem(
        pattern="card_not_present_new_device",
        description="CNP transactions initiated from previously unseen device hardware fingerprints, new browser agents, or unmapped OS profiles.",
        risk_level="CRITICAL",
        applicable_rules=["R3", "R8", "R9"],
        sample_cases=["HHG-003", "HHG-011", "HHG-018"]
    ),
    PatternItem(
        pattern="out_of_region_use",
        description="Geographically anomalous activity occurring in non-standard billing regions or international locations with extreme distance jump from home zip.",
        risk_level="HIGH",
        applicable_rules=["R4", "R8", "R9"],
        sample_cases=["HHG-004", "HHG-006", "HHG-016"]
    ),
    PatternItem(
        pattern="account_takeover",
        description="Credential stuffing or identity compromise leading to rapid multi-card draining, immediate contact domain changes, or sudden high-velocity volume.",
        risk_level="CRITICAL",
        applicable_rules=["R5", "R6", "R8", "R9", "R10"],
        sample_cases=["HHG-005", "HHG-013", "HHG-020"]
    ),
    PatternItem(
        pattern="undocumented",
        description="Novel or emerging fraud typology identified via graph clustering, dense shared device rings, or multi-hop synthetic identity networks.",
        risk_level="VARIABLE",
        applicable_rules=["R7", "R8", "R9"],
        sample_cases=["HHG-009", "HHG-012", "HHG-017"]
    ),
    PatternItem(
        pattern="none",
        description="Legitimate customer transaction confirmed through benign historical baseline, customer verification, or cleared false alarm.",
        risk_level="LOW",
        applicable_rules=["R8"],
        sample_cases=["HHG-010", "HHG-019"]
    )
]

@router.get("/patterns", response_model=List[PatternItem])
def get_memory_patterns():
    """Retrieve recurring fraud typologies and rules catalog from graph memory."""
    return FRAUD_PATTERNS_CATALOG
