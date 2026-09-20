/**
 * FraudSight Agent - Real API Client Layer
 * Strictly typed against FastAPI backend endpoints.
 * ZERO mock data.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== SCHEMAS & TYPES ====================

export interface HealthResponse {
  status: string;
  tigergraph_connected: boolean;
  duckdb_connected: boolean;
  cases_loaded: number;
  version: string;
  vertex_counts?: Record<string, number>;
  installed_query_count?: number;
  vector_index_status?: string;
  mcp_status?: string;
}

export interface CaseSummary {
  case_id: string;
  customer_id: string | null;
  card_id: string | null;
  verdict: 'fraud' | 'legitimate' | 'uncertain' | string;
  fraud_probability: number;
  pattern: string;
  exposure_usd: number;
  status: string;
  sar_required: boolean;
  actions_count: number;
}

export interface EvidenceItem {
  claim?: string;
  source?: string;
  ref?: string;
  entity_ids?: string[];
  [key: string]: any;
}

export interface CaseData {
  status: string;
  verdict: string;
  fraud_probability: number;
  pattern: string;
  pattern_description?: string;
  affected_txn_ids?: (string | number)[];
  first_suspicious_txn_id?: string | number;
  connected_card_ids?: string[];
  connected_device_profiles?: string[];
  exposure_usd: number;
  evidence?: EvidenceItem[] | Record<string, any>;
  similar_prior_cases?: (string | { case_id: string; similarity_score?: number; pattern?: string; outcome?: string })[];
  summary?: string;
  written_to_graph?: boolean;
  graph_case_id?: string;
  [key: string]: any;
}

export interface EvidenceRequestItem {
  id?: string;
  type: 'customer_validation' | 'step_up_authentication' | 'analyst_info' | 'customer_confirmation' | string;
  target?: string;
  prompt?: string;
  asked_after_step?: number;
  assumed_response?: string;
  simulated_reply?: {
    evidence_type?: string;
    response_text?: string;
    customer_verified?: boolean;
    device_recognized?: boolean;
    location_authorized?: boolean;
    verified?: boolean;
    [key: string]: any;
  } | null;
}

export interface ActionItem {
  action: string;
  route: 'auto' | 'L1' | 'L2' | string;
  reason: string;
  status?: 'pending' | 'APPROVED' | 'REJECTED' | string;
  action_id?: string;
  target_id?: string;
}

export interface NextBestActions {
  initial?: ActionItem[];
  final?: ActionItem[];
  what_changed?: string;
}

export interface SARSubject {
  id?: string;
  role?: string;
  [key: string]: any;
}

export interface SARReport {
  file: boolean;
  narrative?: string;
  subjects?: SARSubject[];
  total_amount_usd?: number;
  activity_dates?: string[];
}

export interface CaseDetail {
  case_id: string;
  case: CaseData;
  evidence_requests: EvidenceRequestItem[];
  next_best_actions: NextBestActions;
  sar: SARReport;
  stop_reason?: string | null;
  tool_calls?: any;
  tokens?: any;
  latency_s?: number;
}

export interface TimelineStep {
  step: number;
  phase: string;
  title: string;
  description: string;
  details?: Record<string, any>;
}

export interface TimelineResponse {
  case_id: string;
  total_steps: number;
  timeline: TimelineStep[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  from_id: string;
  to_id: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  case_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CaseTransaction {
  id: string | number;
  card_id?: string;
  amount: number;
  timestamp: number;
  is_fraud?: number;
  location?: string | number;
  device?: string;
  merchant_category?: string;
  email?: string;
}

export interface SimilarCase {
  case_id: string;
  similarity_score?: number;
  pattern?: string;
  outcome?: string;
}

export interface ActionDecisionResponse {
  case_id: string;
  action_id: string;
  status: 'APPROVED' | 'REJECTED';
  analyst_id: string;
  notes: string;
  timestamp: string;
}

export interface PendingActionItem {
  case_id: string;
  action_id: string;
  action: string;
  route: string;
  reason: string;
  status: string;
  exposure_usd: number;
  pattern: string;
  verdict: string;
  fraud_probability: number;
  customer_id: string;
}

export interface ActionHistoryItem {
  case_id: string;
  action_id: string;
  action: string;
  route: string;
  reason: string;
  status: string;
  analyst_id: string;
  notes: string;
  timestamp: string;
  exposure_usd: number;
  pattern: string;
  verdict: string;
}

export interface PatternItem {
  pattern: string;
  description: string;
  risk_level: string;
  applicable_rules: string[];
  sample_cases: string[];
}

export interface StatsResponse {
  total_cases: number;
  verdict_distribution: Record<string, number>;
  pattern_distribution: Record<string, number>;
  total_exposure_usd: number;
  total_sar_filed: number;
  avg_latency_s: number;
  total_tokens_used: number;
  tool_calls_breakdown: Record<string, number>;
}

// ==================== FETCH HELPER ====================

async function request<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 30000, retryCount = 0): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    clearTimeout(id);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status} ${res.statusText}`;
      try {
        const body = await res.json();
        if (body?.detail) errorDetail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      } catch {}
      throw new Error(errorDetail);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(id);
    if (retryCount > 0 && (err.name === 'AbortError' || err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError'))) {
      // Retry once for network or timeout (workspace waking up)
      return request<T>(endpoint, options, timeoutMs, retryCount - 1);
    }
    throw err;
  }
}

// ==================== API METHODS ====================

export const api = {
  // System Health
  getHealth: () => request<HealthResponse>('/health', { method: 'GET' }, 15000),

  // Cases List
  getCases: () => request<CaseSummary[]>('/cases', { method: 'GET' }, 20000),

  // Case Detail
  getCaseDetail: (caseId: string) => request<CaseDetail>(`/cases/${caseId}`, { method: 'GET' }, 20000),

  // Trigger Investigation (120s timeout + 1 retry for workspace wakeup)
  investigateCase: (caseId: string, payload?: { risk_score?: number; trigger_type?: string; trigger_text?: string }) =>
    request<{ status: string; case_id: string; initial_result: any }>(
      `/cases/${caseId}/investigate`,
      {
        method: 'POST',
        body: JSON.stringify(payload || { risk_score: 0.85, trigger_type: 'risk_score' }),
      },
      120000,
      1
    ),

  // Submit Evidence Reply
  submitEvidence: (
    caseId: string,
    payload: {
      evidence_type: string;
      response_text: string;
      verified: boolean;
    }
  ) =>
    request<{ status: string; case_id: string; reassessed_case: CaseDetail }>(
      `/cases/${caseId}/evidence`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      30000
    ),

  // Timeline
  getTimeline: (caseId: string) => request<TimelineResponse>(`/cases/${caseId}/timeline`, { method: 'GET' }, 20000),

  // Graph
  getGraph: (caseId: string) => request<GraphData>(`/cases/${caseId}/graph`, { method: 'GET' }, 20000),

  // Transactions
  getTransactions: (caseId: string) => request<CaseTransaction[]>(`/cases/${caseId}/transactions`, { method: 'GET' }, 20000),

  // Similar Cases
  getSimilarCases: (caseId: string) => request<SimilarCase[]>(`/cases/${caseId}/similar`, { method: 'GET' }, 20000),

  // Approve Action
  approveAction: (caseId: string, actionId: string, notes = 'Approved by analyst') =>
    request<ActionDecisionResponse>(
      `/cases/${caseId}/actions/${actionId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ analyst_id: 'analyst_lead', notes }),
      },
      20000
    ),

  // Reject Action
  rejectAction: (caseId: string, actionId: string, notes = 'Rejected by analyst') =>
    request<ActionDecisionResponse>(
      `/cases/${caseId}/actions/${actionId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ analyst_id: 'analyst_lead', notes }),
      },
      20000
    ),

  // Pending Actions
  getPendingActions: () => request<PendingActionItem[]>('/actions/pending', { method: 'GET' }, 20000),

  // Action History
  getActionHistory: () => request<ActionHistoryItem[]>('/actions/history', { method: 'GET' }, 20000),

  // Memory Patterns
  getMemoryPatterns: () => request<PatternItem[]>('/memory/patterns', { method: 'GET' }, 20000),

  // Operational Stats
  getStats: () => request<StatsResponse>('/stats', { method: 'GET' }, 20000),
};
