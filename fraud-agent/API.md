# Agentic Fraud Investigation API Documentation

The **Agentic Fraud Investigation API** is a high-performance FastAPI service providing autonomous fraud investigation, TigerGraph sub-graph extractions, vector similarity matching, policy engine routing, evidence simulation, and SAR filing.

**Base URL**: `http://localhost:8000`  
**Interactive Swagger UI**: `http://localhost:8000/docs`  
**OpenAPI Specification**: `http://localhost:8000/openapi.json`  
**CORS Allowed Origins**: `http://localhost:8443`, `http://127.0.0.1:8443`, `http://localhost:5173`, `http://localhost:3000`

---

## Quick Navigation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check (TigerGraph & DuckDB status) |
| `GET` | `/cases` | List all 20 investigated cases with summary status |
| `GET` | `/cases/{case_id}` | Full case record, evidence, actions, and SAR |
| `POST` | `/cases/{case_id}/investigate` | Trigger autonomous investigation on a case alert |
| `POST` | `/cases/{case_id}/evidence` | Submit customer verification and run policy reassessment |
| `GET` | `/cases/{case_id}/timeline` | Detailed audit log with rule triggers and tool calls |
| `GET` | `/cases/{case_id}/graph` | Graph nodes & edges for visual graph exploration |
| `GET` | `/cases/{case_id}/transactions` | List all transaction records for case cards |
| `GET` | `/cases/{case_id}/similar` | Vector similarity match against historical closed cases |
| `POST` | `/cases/{case_id}/actions/{action_id}/approve` | Approve human-routed analyst action (`L1`/`L2`) |
| `POST` | `/cases/{case_id}/actions/{action_id}/reject` | Reject human-routed analyst action |
| `GET` | `/actions/pending` | List all pending human-in-the-loop (`L1`/`L2`) actions across cases |
| `GET` | `/actions/history` | List all decided (approved/rejected) analyst actions |
| `GET` | `/memory/patterns` | Catalog of recognized fraud typologies and policy rules |
| `GET` | `/stats` | Operational performance metrics and token analytics |

---

## Endpoints

### 1. System Health Check

```http
GET /health
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/health"
```

#### Example Response (200 OK):
```json
{
  "status": "healthy",
  "tigergraph_connected": true,
  "duckdb_connected": true,
  "cases_loaded": 20,
  "version": "1.0.0"
}
```

---

### 2. List All Cases

```http
GET /cases
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/cases"
```

#### Example Response (200 OK):
```json
[
  {
    "case_id": "HHG-001",
    "customer_id": "CUST-001",
    "card_id": "CUST-001-K1",
    "verdict": "fraud",
    "fraud_probability": 0.94,
    "pattern": "card_testing",
    "exposure_usd": 1245.80,
    "status": "CLOSED",
    "sar_required": false,
    "actions_count": 3
  },
  {
    "case_id": "HHG-002",
    "customer_id": "CUST-002",
    "card_id": "CUST-002-K1",
    "verdict": "fraud",
    "fraud_probability": 0.96,
    "pattern": "card_not_present_fraud",
    "exposure_usd": 15420.00,
    "status": "CLOSED",
    "sar_required": true,
    "actions_count": 4
  }
]
```

---

### 3. Get Case Detail

```http
GET /cases/{case_id}
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/cases/HHG-002"
```

#### Example Response (200 OK):
```json
{
  "case_id": "HHG-002",
  "case": {
    "status": "CLOSED",
    "verdict": "fraud",
    "fraud_probability": 0.96,
    "pattern": "card_not_present_fraud",
    "pattern_description": "Multiple high-velocity CNP transactions without physical card presence.",
    "affected_txn_ids": [3001450, 3001452, 3001460],
    "first_suspicious_txn_id": "3001450",
    "connected_card_ids": ["CUST-002-K1"],
    "connected_device_profiles": ["iOS 15.2 / Safari"],
    "exposure_usd": 15420.00,
    "evidence": {
      "customer_confirmed": false,
      "dispute_filed": true
    },
    "similar_prior_cases": [
      {
        "case_id": "CC-0012",
        "pattern": "card_not_present_fraud",
        "outcome": "confirmed_fraud",
        "similarity_score": 0.91
      }
    ],
    "summary": "Confirmed Card-Not-Present fraud across 3 sequential transactions.",
    "written_to_graph": true,
    "graph_case_id": "CASE-HHG-002"
  },
  "evidence_requests": [
    {
      "id": "EV-1",
      "type": "customer_confirmation",
      "target": "CUST-002",
      "prompt": "Verify transaction of $5,000.00 on card CUST-002-K1",
      "simulated_reply": {
        "verified": false,
        "response_text": "Card was stolen; not recognized."
      }
    }
  ],
  "next_best_actions": {
    "initial": [
      {"action": "DECLINE_TRANSACTION", "route": "L1", "reason": "High fraud probability velocity"},
      {"action": "BLOCK_CARD", "route": "L2", "reason": "Exposure exceeds $2,500 threshold"}
    ],
    "final": [
      {"action": "BLOCK_CARD", "route": "L2", "reason": "Confirmed unauthorized fraud"},
      {"action": "FILE_REPORT", "route": "L2", "reason": "SAR required due to exposure > $10,000"}
    ],
    "what_changed": "Customer confirmed unauthorized activity. Escalated to SAR filing."
  },
  "sar": {
    "file": true,
    "narrative": "A suspicious activity investigation was conducted regarding customer CUST-002...",
    "subjects": [{"id": "CUST-002", "role": "Victim / Account Owner"}],
    "total_amount_usd": 15420.00,
    "activity_dates": ["2017-12-01", "2017-12-02"]
  },
  "stop_reason": "FINAL_EVIDENCE_REASSESSMENT_COMPLETE",
  "tool_calls": [
    {"tool": "get_card_profile", "args": {"card_id": "CUST-002-K1"}},
    {"tool": "find_connected_entities", "args": {"customer_id": "CUST-002"}}
  ],
  "tokens": {"prompt": 1420, "completion": 510, "total": 1930},
  "latency_s": 4.12
}
```

---

### 4. Trigger Autonomous Investigation

```http
POST /cases/{case_id}/investigate
```

#### Example Request:
```bash
curl -X POST "http://localhost:8000/cases/HHG-001/investigate" \
     -H "Content-Type: application/json" \
     -d '{
       "risk_score": 0.88,
       "trigger_type": "risk_score"
     }'
```

---

### 5. Submit Case Evidence & Reassess

```http
POST /cases/{case_id}/evidence
```

#### Example Request:
```bash
curl -X POST "http://localhost:8000/cases/HHG-001/evidence" \
     -H "Content-Type: application/json" \
     -d '{
       "evidence_type": "customer_confirmation",
       "response_text": "I made this transaction while traveling.",
       "verified": true
     }'
```

---

### 6. Case Timeline & Audit Log

```http
GET /cases/{case_id}/timeline
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/cases/HHG-001/timeline"
```

#### Example Response (200 OK):
```json
{
  "case_id": "HHG-001",
  "total_steps": 6,
  "timeline": [
    {
      "step": 1,
      "phase": "ALERT_INGESTION",
      "title": "Alert Ingested & Triaged",
      "description": "Triggered by card_testing alert."
    },
    {
      "step": 2,
      "phase": "GRAPH_TRAVERSAL_AND_TOOLS",
      "title": "Tool Execution: get_card_profile",
      "description": "Executed tool 'get_card_profile' with args {'card_id': 'CUST-001-K1'}"
    },
    {
      "step": 3,
      "phase": "INITIAL_POLICY_EVALUATION",
      "title": "Policy Rules Evaluated & Initial Actions Staged",
      "description": "Assigned preliminary pattern 'card_testing' with verdict 'fraud'."
    },
    {
      "step": 4,
      "phase": "EVIDENCE_SIMULATION",
      "title": "Evidence Request: customer_confirmation",
      "description": "Dispatched verification prompt to customer."
    },
    {
      "step": 5,
      "phase": "FINAL_REASSESSMENT",
      "title": "Final Policy Reassessment & Action Routing",
      "description": "Finalized actions after evidence review."
    },
    {
      "step": 6,
      "phase": "GRAPH_PERSISTENCE",
      "title": "Graph Case Memory Persistence",
      "description": "Persisted case into TigerGraph with ID 'CASE-HHG-001'."
    }
  ]
}
```

---

### 7. Visual Subgraph Network

```http
GET /cases/{case_id}/graph
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/cases/HHG-001/graph"
```

#### Example Response (200 OK):
```json
{
  "case_id": "HHG-001",
  "nodes": [
    {"id": "CUST-001", "label": "CUST-001", "type": "Customer", "properties": {}},
    {"id": "CUST-001-K1", "label": "CUST-001-K1", "type": "Card", "properties": {}},
    {"id": "3000010", "label": "TXN-3000010 ($4.50)", "type": "Transaction", "properties": {"amount_usd": 4.50}},
    {"id": "Windows / Chrome", "label": "Windows / Chrome", "type": "DeviceProfile", "properties": {}}
  ],
  "edges": [
    {"from_id": "CUST-001", "to_id": "CUST-001-K1", "type": "CUSTOMER_HAS_CARD", "properties": {}},
    {"from_id": "CUST-001-K1", "to_id": "3000010", "type": "PERFORMED_TRANSACTION", "properties": {}},
    {"from_id": "3000010", "to_id": "Windows / Chrome", "type": "USED_DEVICE", "properties": {}}
  ]
}
```

---

### 8. Vector Similarity Prior Cases

```http
GET /cases/{case_id}/similar
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/cases/HHG-001/similar"
```

---

### 9. Approve / Reject Analyst Action

```http
POST /cases/{case_id}/actions/{action_id}/approve
POST /cases/{case_id}/actions/{action_id}/reject
```

#### Example Request:
```bash
curl -X POST "http://localhost:8000/cases/HHG-001/actions/ACT-1/approve" \
     -H "Content-Type: application/json" \
     -d '{
       "analyst_id": "lead_analyst_42",
       "notes": "Confirmed compromised card signature. Approved immediate block."
     }'
```

---

### 10. Memory Patterns Catalog

```http
GET /memory/patterns
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/memory/patterns"
```

---

### 11. Operational Analytics & Performance

```http
GET /stats
```

#### Example Request:
```bash
curl -X GET "http://localhost:8000/stats"
```

#### Example Response (200 OK):
```json
{
  "total_cases": 20,
  "verdict_distribution": {
    "fraud": 17,
    "legitimate": 3
  },
  "pattern_distribution": {
    "card_testing": 3,
    "card_not_present_fraud": 5,
    "card_not_present_new_device": 4,
    "out_of_region_use": 3,
    "account_takeover": 2,
    "none": 3
  },
  "total_exposure_usd": 128450.75,
  "total_sar_filed": 9,
  "avg_latency_s": 4.85,
  "total_tokens_used": 68420,
  "tool_calls_breakdown": {
    "get_card_profile": 20,
    "find_connected_entities": 20,
    "find_shared_attributes": 18,
    "search_similar_closed_cases": 20
  }
}
```
