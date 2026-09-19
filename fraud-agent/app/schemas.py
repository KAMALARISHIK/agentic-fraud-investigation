from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str
    tigergraph_connected: bool
    duckdb_connected: bool
    cases_loaded: int
    version: str = "1.0.0"

class ActionItem(BaseModel):
    action: str
    route: str
    reason: str
    status: Optional[str] = "pending"
    action_id: Optional[str] = None
    target_id: Optional[str] = None

class NextBestActions(BaseModel):
    initial: List[Dict[str, Any]]
    final: List[Dict[str, Any]]
    what_changed: Optional[str] = None

class SARReport(BaseModel):
    file: bool
    narrative: str
    subjects: List[Dict[str, Any]]
    total_amount_usd: float
    activity_dates: List[str]

class CaseSummary(BaseModel):
    case_id: str
    customer_id: Optional[str] = None
    card_id: Optional[str] = None
    verdict: str
    fraud_probability: float
    pattern: str
    exposure_usd: float
    status: str
    sar_required: bool
    actions_count: int

class EvidenceRequest(BaseModel):
    id: str
    type: str
    target: str
    prompt: str
    simulated_reply: Optional[Dict[str, Any]] = None

class CaseDetail(BaseModel):
    case_id: str
    case: Dict[str, Any]
    evidence_requests: List[Dict[str, Any]] = Field(default_factory=list)
    next_best_actions: Dict[str, Any] = Field(default_factory=dict)
    sar: Dict[str, Any] = Field(default_factory=dict)
    stop_reason: Optional[str] = None
    tool_calls: Any = 0
    tokens: Any = 0
    latency_s: Optional[float] = 0.0

class InvestigateRequest(BaseModel):
    case_id: Optional[str] = None
    customer_id: Optional[str] = None
    card_id: Optional[str] = None
    flagged_txn_id: Optional[str] = None
    trigger_type: Optional[str] = "risk_score"
    trigger_text: Optional[str] = None
    risk_score: Optional[float] = 0.85

class EvidenceSubmitRequest(BaseModel):
    evidence_type: str = "customer_confirmation"
    response_text: str = "Transaction recognized and authorized"
    verified: bool = True

class ActionDecisionRequest(BaseModel):
    analyst_id: str = "analyst_1"
    notes: Optional[str] = "Decision recorded by fraud analyst"

class ActionDecisionResponse(BaseModel):
    case_id: str
    action_id: str
    status: str
    analyst_id: str
    notes: str
    timestamp: str

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    from_id: str
    to_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphData(BaseModel):
    case_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class PatternItem(BaseModel):
    pattern: str
    description: str
    risk_level: str
    applicable_rules: List[str]
    sample_cases: List[str]

class StatsResponse(BaseModel):
    total_cases: int
    verdict_distribution: Dict[str, int]
    pattern_distribution: Dict[str, int]
    total_exposure_usd: float
    total_sar_filed: int
    avg_latency_s: float
    total_tokens_used: int
    tool_calls_breakdown: Dict[str, int]
