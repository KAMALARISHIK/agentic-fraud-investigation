import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  FileText,
  Copy,
  Download,
  Send,
  Sparkles,
  GitBranch,
  Layers,
  Database,
  ExternalLink,
  MessageSquare,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Tabs, TabItem } from '../components/ui/Tabs';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { useToast } from '../components/ui/Toast';
import { CaseGraphView } from '../components/case/CaseGraphView';
import {
  api,
  CaseDetail,
  TimelineResponse,
  GraphData,
  CaseTransaction,
  SimilarCase,
  ActionItem,
} from '../lib/api';

export const CaseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const caseId = id || 'HHG-001';
  const { toast, success, error: showError } = useToast();

  const [activeTab, setActiveTab] = useState('summary');
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [transactions, setTransactions] = useState<CaseTransaction[]>([]);
  const [similarCases, setSimilarCases] = useState<SimilarCase[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Investigation Running State & Real Elapsed Timer
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationElapsed, setInvestigationElapsed] = useState(0);
  const timerRef = useRef<any>(null);

  // Action Approval / Rejection Modal State
  const [actionModal, setActionModal] = useState<{
    isOpen: boolean;
    type: 'approve' | 'reject';
    action: ActionItem | null;
    actionId: string;
    notes: string;
    isSubmitting: boolean;
  }>({
    isOpen: false,
    type: 'approve',
    action: null,
    actionId: '',
    notes: '',
    isSubmitting: false,
  });

  // Evidence Simulation State
  const [isSubmittingEvidence, setIsSubmittingEvidence] = useState(false);
  const [evidenceReplyText, setEvidenceReplyText] = useState('Transaction authorized and recognized.');
  const [evidenceVerified, setEvidenceVerified] = useState(true);

  // Fetch all real case data
  const fetchAllCaseData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [detail, timeline, graph, txns, similar] = await Promise.all([
        api.getCaseDetail(caseId),
        api.getTimeline(caseId).catch(() => null),
        api.getGraph(caseId).catch(() => null),
        api.getTransactions(caseId).catch(() => []),
        api.getSimilarCases(caseId).catch(() => []),
      ]);

      setCaseDetail(detail);
      setTimelineData(timeline);
      setGraphData(graph);
      setTransactions(txns);
      setSimilarCases(similar);
    } catch (err: any) {
      setError(err.message || `Failed to load data for case ${caseId}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllCaseData();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [caseId]);

  // Trigger Autonomous Investigation
  const handleInvestigate = async () => {
    setIsInvestigating(true);
    setInvestigationElapsed(0);
    timerRef.current = setInterval(() => {
      setInvestigationElapsed((prev) => prev + 1);
    }, 1000);

    try {
      await api.investigateCase(caseId, {
        risk_score: caseDetail?.case?.fraud_probability || 0.85,
        trigger_type: caseDetail?.case?.pattern || 'risk_score',
        trigger_text: caseDetail?.case?.summary || `Triggered investigation on case ${caseId}`,
      });
      clearInterval(timerRef.current);
      success('Investigation Completed', `Autonomous agent finished graph traversal for ${caseId}.`);
      await fetchAllCaseData();
      setActiveTab('timeline');
    } catch (err: any) {
      clearInterval(timerRef.current);
      showError('Investigation Failed', err.message || 'Error occurred while contacting TigerGraph agent.');
    } finally {
      setIsInvestigating(false);
    }
  };

  // Submit Evidence Reply
  const handleSimulateEvidence = async () => {
    setIsSubmittingEvidence(true);
    try {
      await api.submitEvidence(caseId, {
        evidence_type: 'customer_confirmation',
        response_text: evidenceReplyText,
        verified: evidenceVerified,
      });
      success('Evidence Recorded', 'Policy engine reassessment completed.');
      await fetchAllCaseData();
      setActiveTab('actions');
    } catch (err: any) {
      showError('Evidence Submission Failed', err.message || 'Could not record evidence.');
    } finally {
      setIsSubmittingEvidence(false);
    }
  };

  // Open Action Modal
  const openActionModal = (type: 'approve' | 'reject', action: ActionItem, index: number) => {
    const actionId = action.action_id || `ACT-${index + 1}`;
    setActionModal({
      isOpen: true,
      type,
      action,
      actionId,
      notes: type === 'approve' ? 'Approved by lead fraud analyst.' : 'Rejected following risk policy assessment.',
      isSubmitting: false,
    });
  };

  // Submit Action Decision
  const handleActionDecision = async () => {
    if (!actionModal.action) return;
    setActionModal((prev) => ({ ...prev, isSubmitting: true }));

    try {
      if (actionModal.type === 'approve') {
        await api.approveAction(caseId, actionModal.actionId, actionModal.notes);
        success('Action Approved', `Approved "${actionModal.action.action}" for case ${caseId}.`);
      } else {
        await api.rejectAction(caseId, actionModal.actionId, actionModal.notes);
        success('Action Rejected', `Rejected "${actionModal.action.action}" for case ${caseId}.`);
      }
      setActionModal((prev) => ({ ...prev, isOpen: false }));
      await fetchAllCaseData();
    } catch (err: any) {
      showError('Decision Failed', err.message || 'Could not update action status.');
    } finally {
      setActionModal((prev) => ({ ...prev, isSubmitting: false }));
    }
  };

  // Copy SAR to Clipboard
  const handleCopySAR = () => {
    const narrative = caseDetail?.sar?.narrative;
    if (narrative) {
      navigator.clipboard.writeText(narrative);
      success('SAR Copied', 'Report narrative copied to clipboard.');
    }
  };

  // Download SAR
  const handleDownloadSAR = () => {
    const sar = caseDetail?.sar;
    if (!sar) return;
    const textContent = `SUSPICIOUS ACTIVITY REPORT (SAR)
=====================================
Case ID: ${caseId}
Filing Status: ${sar.file ? 'FILED' : 'NOT REQUIRED'}
Total Exposure (USD): $${sar.total_amount_usd || 0}
Activity Dates: ${(sar.activity_dates || []).join(', ')}

SUBJECTS:
${(sar.subjects || []).map((s) => `- ${s.id} (${s.role || 'Subject'})`).join('\n')}

NARRATIVE:
${sar.narrative || 'No narrative generated.'}
`;

    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SAR_${caseId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    success('SAR Downloaded', `Saved SAR_${caseId}.txt`);
  };

  if (error) {
    return <ErrorState message={error} onRetry={fetchAllCaseData} />;
  }

  const caseObj = caseDetail?.case || ({} as any);
  const evidenceRequests = caseDetail?.evidence_requests || [];
  const nextActions = caseDetail?.next_best_actions || {};
  const finalActions = nextActions.final || nextActions.initial || [];
  const initialActions = nextActions.initial || [];
  const sarObj = caseDetail?.sar || ({} as any);
  const fraudProbability = caseObj.fraud_probability ?? 0.0;
  const exposureUsd = caseObj.exposure_usd ?? 0.0;
  const verdict = caseObj.verdict || 'uncertain';
  const pattern = caseObj.pattern || 'none';

  // Tabs Definition
  const tabs: TabItem[] = [
    { id: 'summary', label: 'Summary' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'graph', label: 'TigerGraph', badge: <Badge variant="outline" size="sm">2D</Badge> },
    { id: 'timeline', label: 'Timeline & Audit', badge: <Badge variant="neutral" size="sm">{timelineData?.total_steps || 0}</Badge> },
    { id: 'actions', label: 'Policy Actions', badge: <Badge variant="terracotta" size="sm">{finalActions.length}</Badge> },
    {
      id: 'evidence_request',
      label: 'Evidence Request',
      badge: evidenceRequests.length > 0 ? <Badge variant="uncertain" size="sm">{evidenceRequests.length}</Badge> : undefined,
    },
    {
      id: 'sar',
      label: 'SAR Report',
      badge: sarObj.file ? <Badge variant="fraud" size="sm">Required</Badge> : undefined,
    },
    { id: 'similar', label: 'Similar Cases', badge: <Badge variant="neutral" size="sm">{similarCases.length}</Badge> },
  ];

  return (
    <div className="space-y-6">
      {/* Back Link & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/app/cases"
          className="inline-flex items-center gap-1.5 text-xs text-[#6B6A65] hover:text-[#141413] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Investigations
        </Link>
        <span className="text-xs font-mono text-[#6B6A65]">
          Case Reference: <strong className="text-[#141413]">{caseId}</strong>
        </span>
      </div>

      {/* Case Header Card */}
      <Card className="p-6 bg-white border border-[#E8E6DC] shadow-sm">
        {isLoading ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Skeleton className="h-7 w-48" />
              <Skeleton className="h-10 w-36 rounded-xl" />
            </div>
            <Skeleton className="h-16 w-full" />
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="font-serif text-3xl font-semibold text-[#141413]">{caseId}</h1>
                <Badge variant={verdict} size="md">
                  {verdict.toUpperCase()}
                </Badge>
                <Badge variant="outline" size="md">
                  {caseObj.status || 'CLOSED'}
                </Badge>
                <Badge variant="terracotta" size="md">
                  {pattern && pattern !== 'none' ? pattern.replace(/_/g, ' ') : 'Legitimate baseline'}
                </Badge>
              </div>

              <p className="text-xs text-[#6B6A65] max-w-3xl leading-relaxed">
                {caseObj.summary || 'Investigation initialized for anomalous cardholder activity.'}
              </p>
            </div>

            {/* Right Header Metrics & Primary Button */}
            <div className="flex flex-wrap items-center gap-5 lg:shrink-0 pt-3 lg:pt-0 border-t lg:border-t-0 border-[#E8E6DC]">
              {/* Exposure */}
              <div className="text-left lg:text-right">
                <div className="text-[10px] uppercase font-semibold text-[#6B6A65]">Exposure</div>
                <div className="text-xl font-serif font-bold text-[#141413]">
                  ${exposureUsd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>

              {/* Fraud Probability Meter */}
              <div className="text-left lg:text-right min-w-[110px]">
                <div className="text-[10px] uppercase font-semibold text-[#6B6A65] flex items-center gap-1">
                  <span>Risk Score</span>
                  <span className="font-mono font-bold text-[#141413]">
                    {(fraudProbability * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-[#E8E6DC] h-2 rounded-full overflow-hidden mt-1.5">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      fraudProbability > 0.7
                        ? 'bg-[#C0392B]'
                        : fraudProbability > 0.3
                        ? 'bg-[#B7791F]'
                        : 'bg-[#2F855A]'
                    }`}
                    style={{ width: `${Math.min(100, fraudProbability * 100)}%` }}
                  />
                </div>
              </div>

              {/* Primary Investigate Button */}
              <Button
                size="md"
                onClick={handleInvestigate}
                isLoading={isInvestigating}
                disabled={isInvestigating}
                leftIcon={!isInvestigating && <Play className="w-4 h-4 fill-current" />}
              >
                {isInvestigating ? `Agent working... (${investigationElapsed}s)` : 'Investigate Case'}
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Tabs Navigation */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: SUMMARY */}
      {activeTab === 'summary' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-5 lg:col-span-2 space-y-4">
              <h3 className="font-serif text-lg font-medium text-[#141413]">
                Investigation Narrative
              </h3>
              <p className="text-xs text-[#141413] leading-relaxed bg-[#FAF9F5] p-4 rounded-xl border border-[#E8E6DC]">
                {caseObj.summary || 'Investigation record verified in knowledge graph memory.'}
              </p>

              {caseObj.pattern_description && (
                <div>
                  <h4 className="text-xs font-semibold text-[#141413] mb-1">Typology Characteristics</h4>
                  <p className="text-xs text-[#6B6A65] leading-relaxed">{caseObj.pattern_description}</p>
                </div>
              )}

              {caseObj.first_suspicious_txn_id && (
                <div className="flex items-center gap-2 text-xs pt-2">
                  <span className="text-[#6B6A65]">First Flagged Transaction:</span>
                  <span className="font-mono font-semibold text-[#D97757] bg-[#F5E6DF] px-2 py-0.5 rounded-md">
                    TXN-{caseObj.first_suspicious_txn_id}
                  </span>
                </div>
              )}
            </Card>

            {/* Connected Cards & Devices */}
            <Card className="p-5 space-y-4">
              <h3 className="font-serif text-lg font-medium text-[#141413]">Connected Entities</h3>
              <div>
                <div className="text-[11px] font-semibold text-[#6B6A65] uppercase mb-1.5">
                  Associated Cards
                </div>
                <div className="space-y-1">
                  {(caseObj.connected_card_ids || []).length > 0 ? (
                    caseObj.connected_card_ids.map((c: string) => (
                      <div key={c} className="font-mono text-xs p-2 bg-[#FAF9F5] rounded-lg border border-[#E8E6DC] text-[#141413]">
                        {c}
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-[#6B6A65]">None connected</div>
                  )}
                </div>
              </div>

              <div>
                <div className="text-[11px] font-semibold text-[#6B6A65] uppercase mb-1.5">
                  Device Hardware Profiles
                </div>
                <div className="space-y-1">
                  {(caseObj.connected_device_profiles || []).length > 0 ? (
                    caseObj.connected_device_profiles.map((d: string) => (
                      <div key={d} className="text-xs p-2 bg-[#FAF9F5] rounded-lg border border-[#E8E6DC] text-[#141413]">
                        {d}
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-[#6B6A65]">Standard browser/OS profile</div>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* Transactions Table */}
          <Card className="overflow-hidden">
            <CardHeader
              title="Related Card Transactions"
              subtitle={`Extracted from DuckDB transaction logs (${transactions.length} records)`}
            />
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#E8E6DC] bg-[#FAF9F5] text-[#6B6A65]">
                    <th className="p-3 pl-5">TXN ID</th>
                    <th className="p-3">Card ID</th>
                    <th className="p-3">Amount</th>
                    <th className="p-3">Merchant Category</th>
                    <th className="p-3">Device / OS</th>
                    <th className="p-3">Email Domain</th>
                    <th className="p-3 pr-5">Ground Truth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E8E6DC]/80">
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-6 text-center text-[#6B6A65]">
                        No individual transaction rows found for connected cards.
                      </td>
                    </tr>
                  ) : (
                    transactions.map((t) => (
                      <tr key={t.id} className="hover:bg-[#FAF9F5] transition-colors">
                        <td className="p-3 pl-5 font-mono font-medium text-[#141413]">
                          TXN-{t.id}
                        </td>
                        <td className="p-3 font-mono text-[11px] text-[#6B6A65]">{t.card_id}</td>
                        <td className="p-3 font-semibold text-[#141413]">
                          ${Number(t.amount || 0).toFixed(2)}
                        </td>
                        <td className="p-3 text-[#6B6A65]">{t.merchant_category || 'General (W)'}</td>
                        <td className="p-3 text-[#6B6A65]">{t.device || 'N/A'}</td>
                        <td className="p-3 font-mono text-[11px] text-[#6B6A65]">{t.email || 'N/A'}</td>
                        <td className="p-3 pr-5">
                          {t.is_fraud ? (
                            <Badge variant="fraud" size="sm">Fraud</Badge>
                          ) : (
                            <Badge variant="legitimate" size="sm">Legit</Badge>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: EVIDENCE */}
      {activeTab === 'evidence' && (
        <Card className="p-6 space-y-6">
          <CardHeader
            title="Grounded Investigation Evidence"
            subtitle="Verified multi-source claims and graph findings discovered by the agent"
          />

          <div className="space-y-4">
            {Array.isArray(caseObj.evidence) && caseObj.evidence.length > 0 ? (
              caseObj.evidence.map((ev: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[#E8E6DC] bg-[#FAF9F5] space-y-2 hover:border-[#D5D3C8] transition-colors"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold text-xs text-[#141413]">{ev.claim || 'Evidence Claim'}</span>
                    <Badge variant="terracotta" size="sm">
                      {ev.source || 'graph'}
                    </Badge>
                  </div>
                  {ev.ref && (
                    <div className="text-[11px] text-[#6B6A65] font-mono">
                      Query Ref: <strong>{ev.ref}</strong>
                    </div>
                  )}
                  {ev.entity_ids && ev.entity_ids.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[11px] text-[#6B6A65]">Entities:</span>
                      {ev.entity_ids.map((ent: string) => (
                        <span key={ent} className="text-[10px] font-mono bg-white px-2 py-0.5 rounded-md border border-[#E8E6DC] text-[#141413]">
                          {ent}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="p-4 rounded-xl border border-[#E8E6DC] bg-[#FAF9F5] text-xs text-[#6B6A65]">
                {typeof caseObj.evidence === 'object' && caseObj.evidence !== null ? (
                  <pre className="text-xs font-mono overflow-x-auto">{JSON.stringify(caseObj.evidence, null, 2)}</pre>
                ) : (
                  'Evidence gathered directly from TigerGraph sub-graph query executions.'
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Tab 3: GRAPH VIEW */}
      {activeTab === 'graph' && (
        <CaseGraphView graphData={graphData} isLoading={isLoading} />
      )}

      {/* Tab 4: TIMELINE & AUDIT */}
      {activeTab === 'timeline' && (
        <Card className="p-6">
          <CardHeader
            title="Autonomous Deliberation Timeline"
            subtitle={`Step-by-step audit trail (${timelineData?.total_steps || 0} executed stages)`}
          />

          <div className="relative border-l-2 border-[#E8E6DC] ml-4 pl-6 space-y-6 py-2">
            {timelineData?.timeline?.map((step) => (
              <div key={step.step} className="relative group">
                <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-white border-2 border-[#D97757]" />
                <div className="bg-[#FAF9F5] p-4 rounded-xl border border-[#E8E6DC] hover:border-[#D5D3C8] transition-colors space-y-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono font-bold text-[#D97757]">
                        STEP {step.step}
                      </span>
                      <span className="text-xs font-semibold text-[#141413]">{step.title}</span>
                    </div>
                    <Badge variant="outline" size="sm">
                      {step.phase}
                    </Badge>
                  </div>
                  <p className="text-xs text-[#6B6A65] leading-relaxed">{step.description}</p>
                  {step.details && (
                    <div className="pt-2 text-[11px] font-mono text-[#6B6A65] bg-white p-2.5 rounded-lg border border-[#E8E6DC] overflow-x-auto">
                      {JSON.stringify(step.details, null, 2)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Tab 5: ACTIONS */}
      {activeTab === 'actions' && (
        <div className="space-y-6">
          {/* What Changed Highlight Box */}
          {nextActions.what_changed && (
            <div className="p-4 rounded-xl border border-[#E8C5B8] bg-[#F5E6DF]/60 text-xs flex items-start gap-3">
              <Sparkles className="w-4 h-4 text-[#D97757] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[#141413]">What changed and why:</strong>
                <p className="text-[#6B6A65] mt-0.5 leading-relaxed">{nextActions.what_changed}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Initial Staged Actions */}
            <Card className="p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#E8E6DC]">
                <div>
                  <h3 className="font-serif text-lg font-medium text-[#141413]">
                    Initial Recommendation
                  </h3>
                  <p className="text-xs text-[#6B6A65]">Generated prior to interactive evidence verification</p>
                </div>
                <Badge variant="outline" size="sm">Staged</Badge>
              </div>

              <div className="space-y-3">
                {initialActions.length === 0 ? (
                  <div className="text-xs text-[#6B6A65] py-4 text-center">No initial actions staged.</div>
                ) : (
                  initialActions.map((act, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl border border-[#E8E6DC] bg-[#FAF9F5] space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs font-mono text-[#141413]">{act.action}</span>
                        <Badge variant={act.route} size="sm">{act.route}</Badge>
                      </div>
                      <p className="text-xs text-[#6B6A65] leading-relaxed">{act.reason}</p>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* Final Reassessed Actions */}
            <Card className="p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#E8E6DC]">
                <div>
                  <h3 className="font-serif text-lg font-medium text-[#141413]">
                    Final Recommendation
                  </h3>
                  <p className="text-xs text-[#6B6A65]">Active policy decisions pending or approved</p>
                </div>
                <Badge variant="terracotta" size="sm">Active</Badge>
              </div>

              <div className="space-y-3">
                {finalActions.length === 0 ? (
                  <div className="text-xs text-[#6B6A65] py-4 text-center">No final actions recorded.</div>
                ) : (
                  finalActions.map((act, idx) => {
                    const status = (act.status || 'pending').toUpperCase();
                    const isApproved = status === 'APPROVED';
                    const isRejected = status === 'REJECTED';
                    const isHumanRoute = act.route === 'L1' || act.route === 'L2';

                    return (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-xl border transition-all space-y-2.5 ${
                          isApproved
                            ? 'bg-[#E6F4EA]/40 border-[#C3E6CB]'
                            : isRejected
                            ? 'bg-[#FBEAE7]/40 border-[#F5C7BE]'
                            : 'bg-white border-[#E8E6DC] shadow-xs'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs font-mono text-[#141413]">{act.action}</span>
                          <div className="flex items-center gap-1.5">
                            <Badge variant={act.route} size="sm">{act.route}</Badge>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                                isApproved
                                  ? 'bg-[#E6F4EA] text-[#2F855A] border-[#C3E6CB]'
                                  : isRejected
                                  ? 'bg-[#FBEAE7] text-[#C0392B] border-[#F5C7BE]'
                                  : 'bg-[#FBF1DC] text-[#B7791F] border-[#F2DCA5]'
                              }`}
                            >
                              {status}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-[#6B6A65] leading-relaxed">{act.reason}</p>

                        {/* Working Approve & Reject Buttons */}
                        {isHumanRoute && !isApproved && !isRejected && (
                          <div className="pt-2 border-t border-[#E8E6DC] flex items-center justify-end gap-2">
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => openActionModal('reject', act, idx)}
                              leftIcon={<XCircle className="w-3.5 h-3.5 text-[#C0392B]" />}
                            >
                              Reject
                            </Button>
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => openActionModal('approve', act, idx)}
                              leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                            >
                              Approve
                            </Button>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 6: EVIDENCE REQUEST */}
      {activeTab === 'evidence_request' && (
        <div className="space-y-6">
          {evidenceRequests.length === 0 ? (
            <EmptyState
              icon={<CheckCircle2 className="w-6 h-6 text-[#2F855A]" />}
              title="No pending evidence requests"
              description="The agent gathered sufficient certainty from TigerGraph baseline queries and did not require step-up customer verification."
            />
          ) : (
            evidenceRequests.map((ev, idx) => (
              <Card key={idx} className="p-6 bg-white border border-[#E8E6DC] shadow-sm space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-[#E8E6DC]">
                  <div>
                    <Badge variant="uncertain" size="sm" className="mb-1.5">
                      {ev.type?.replace(/_/g, ' ').toUpperCase() || 'EVIDENCE REQUEST'}
                    </Badge>
                    <h3 className="font-serif text-xl font-medium text-[#141413]">
                      Target: {ev.target || 'Account Cardholder'}
                    </h3>
                  </div>
                  {ev.asked_after_step && (
                    <span className="text-xs text-[#6B6A65]">Dispatched after step {ev.asked_after_step}</span>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] space-y-1">
                  <div className="text-[11px] font-semibold text-[#6B6A65] uppercase">Verification Prompt</div>
                  <p className="text-sm font-medium text-[#141413]">
                    "{ev.prompt || 'Please verify whether you authorized this suspicious transaction.'}"
                  </p>
                </div>

                {ev.assumed_response && (
                  <div className="text-xs text-[#6B6A65]">
                    <strong className="text-[#141413]">Why asked:</strong> {ev.assumed_response}
                  </div>
                )}

                {/* Simulated Reply Form */}
                <div className="pt-4 border-t border-[#E8E6DC] space-y-4">
                  <h4 className="text-xs font-semibold text-[#141413]">Simulate Response / Customer Reply</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-[#6B6A65] mb-1">Response Message</label>
                      <input
                        type="text"
                        value={evidenceReplyText}
                        onChange={(e) => setEvidenceReplyText(e.target.value)}
                        className="w-full px-3.5 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
                      />
                    </div>

                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 text-xs text-[#141413] cursor-pointer">
                        <input
                          type="radio"
                          name="evidenceVerdict"
                          checked={evidenceVerified}
                          onChange={() => setEvidenceVerified(true)}
                          className="accent-[#D97757]"
                        />
                        <span>Cardholder Confirmed / Authorized</span>
                      </label>
                      <label className="flex items-center gap-2 text-xs text-[#141413] cursor-pointer">
                        <input
                          type="radio"
                          name="evidenceVerdict"
                          checked={!evidenceVerified}
                          onChange={() => setEvidenceVerified(false)}
                          className="accent-[#D97757]"
                        />
                        <span>Cardholder Denied / Fraudulent</span>
                      </label>
                    </div>

                    <Button
                      size="md"
                      onClick={handleSimulateEvidence}
                      isLoading={isSubmittingEvidence}
                      rightIcon={<Send className="w-3.5 h-3.5" />}
                    >
                      Submit reply & Reassess Policy
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab 7: SAR REPORT */}
      {activeTab === 'sar' && (
        <Card className="p-6 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-[#E8E6DC]">
            <div>
              <h3 className="font-serif text-xl font-medium text-[#141413]">
                Suspicious Activity Report (SAR)
              </h3>
              <p className="text-xs text-[#6B6A65]">
                Compliant FinCEN regulatory filing narrative generated from graph evidence
              </p>
            </div>
            {sarObj.file && (
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleCopySAR}
                  leftIcon={<Copy className="w-3.5 h-3.5" />}
                >
                  Copy narrative
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleDownloadSAR}
                  leftIcon={<Download className="w-3.5 h-3.5" />}
                >
                  Download (.txt)
                </Button>
              </div>
            )}
          </div>

          {sarObj.file ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-xs">
                <div>
                  <span className="text-[#6B6A65] block">Filing Obligation:</span>
                  <span className="font-semibold text-[#C0392B]">Mandatory (Exceeds $2,500)</span>
                </div>
                <div>
                  <span className="text-[#6B6A65] block">Total Amount:</span>
                  <span className="font-semibold text-[#141413]">${sarObj.total_amount_usd || exposureUsd}</span>
                </div>
                <div>
                  <span className="text-[#6B6A65] block">Activity Period:</span>
                  <span className="font-semibold text-[#141413]">
                    {(sarObj.activity_dates || ['2017-12-01', '2017-12-02']).join(' to ')}
                  </span>
                </div>
                <div>
                  <span className="text-[#6B6A65] block">Identified Subjects:</span>
                  <span className="font-semibold text-[#141413]">
                    {(sarObj.subjects || []).length || 1} entities
                  </span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-[#141413] mb-2">Narrative Report</h4>
                <div className="p-5 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] font-mono text-xs text-[#141413] whitespace-pre-wrap leading-relaxed">
                  {sarObj.narrative ||
                    `A suspicious activity investigation was conducted regarding case ${caseId}. Graph traversal confirmed coordinated multi-card velocity exceeding policy thresholds.`}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={<ShieldCheck className="w-6 h-6 text-[#2F855A]" />}
              title="No SAR Filing Required"
              description="Exposure did not breach the regulatory reporting threshold ($2,500+) or the alert was cleared as a legitimate cardholder baseline."
            />
          )}
        </Card>
      )}

      {/* Tab 8: SIMILAR CASES */}
      {activeTab === 'similar' && (
        <Card className="p-6 space-y-4">
          <CardHeader
            title="Vector Similarity Prior Cases"
            subtitle="Historical closed cases matched in TigerGraph vector embeddings memory"
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {similarCases.length === 0 ? (
              <div className="col-span-3 text-xs text-[#6B6A65] text-center py-8">
                No vector matched historical cases found.
              </div>
            ) : (
              similarCases.map((sc, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[#E8E6DC] bg-[#FAF9F5] hover:border-[#D5D3C8] transition-colors space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-[#141413]">{sc.case_id}</span>
                    <Badge variant="neutral" size="sm">
                      {Math.round((sc.similarity_score || 0.88) * 100)}% Match
                    </Badge>
                  </div>
                  <div className="text-xs text-[#6B6A65] capitalize">
                    Pattern: <strong className="text-[#141413]">{sc.pattern || 'card_fraud'}</strong>
                  </div>
                  <div className="text-xs text-[#6B6A65]">
                    Outcome: <strong className="text-[#141413]">{sc.outcome || 'confirmed_fraud'}</strong>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Approve / Reject Modal */}
      <Modal
        isOpen={actionModal.isOpen}
        onClose={() => setActionModal((prev) => ({ ...prev, isOpen: false }))}
        title={actionModal.type === 'approve' ? 'Approve Policy Action' : 'Reject Policy Action'}
        description={`Confirm decision for action "${actionModal.action?.action}"`}
        footer={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setActionModal((prev) => ({ ...prev, isOpen: false }))}
            >
              Cancel
            </Button>
            <Button
              variant={actionModal.type === 'approve' ? 'primary' : 'danger'}
              size="sm"
              onClick={handleActionDecision}
              isLoading={actionModal.isSubmitting}
            >
              {actionModal.type === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-xs">
            <div>
              <span className="text-[#6B6A65]">Action:</span>{' '}
              <strong className="text-[#141413] font-mono">{actionModal.action?.action}</strong>
            </div>
            <div>
              <span className="text-[#6B6A65]">Route:</span>{' '}
              <strong className="text-[#141413]">{actionModal.action?.route}</strong>
            </div>
            <div>
              <span className="text-[#6B6A65]">Reason:</span>{' '}
              <span className="text-[#6B6A65]">{actionModal.action?.reason}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#141413] mb-1.5">
              Investigator Audit Notes
            </label>
            <textarea
              rows={3}
              value={actionModal.notes}
              onChange={(e) => setActionModal((prev) => ({ ...prev, notes: e.target.value }))}
              className="w-full px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
              placeholder="Record rationale for compliance audit trail..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
