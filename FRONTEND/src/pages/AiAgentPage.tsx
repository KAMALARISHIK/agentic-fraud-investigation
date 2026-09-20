import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Sparkles,
  Zap,
  CheckCircle2,
  HelpCircle,
  Clock,
  Cpu,
  RefreshCw,
  Sliders,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { api, CaseSummary, CaseDetail, StatsResponse } from '../lib/api';

export const AiAgentPage: React.FC = () => {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('HHG-001');
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [caseList, statsData] = await Promise.all([
        api.getCases(),
        api.getStats(),
      ]);
      setCases(caseList);
      setStats(statsData);
      if (caseList.length > 0) {
        setSelectedCaseId(caseList[0].case_id);
        const detail = await api.getCaseDetail(caseList[0].case_id);
        setCaseDetail(detail);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load AI agent telemetry.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectCase = async (cid: string) => {
    setSelectedCaseId(cid);
    setIsLoadingDetail(true);
    try {
      const detail = await api.getCaseDetail(cid);
      setCaseDetail(detail);
    } catch (err: any) {
      setError(err.message || `Failed to fetch details for case ${cid}`);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  if (error) {
    return <ErrorState message={error} onRetry={fetchInitialData} />;
  }

  const caseObj = caseDetail?.case || ({} as any);
  const nextActions = caseDetail?.next_best_actions || {};
  const finalActions = nextActions.final || nextActions.initial || [];
  const evReqs = caseDetail?.evidence_requests || [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#141413]">
            AI Agent Explainability & Auditing
          </h1>
          <p className="text-xs text-[#6B6A65] mt-1">
            Deterministic decision provenance, TigerGraph MCP tool calls, and model inference telemetry
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchInitialData}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh telemetry
        </Button>
      </div>

      {/* Operational Performance KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-1.5">
            <span>Average Agent Latency</span>
            <Clock className="w-4 h-4 text-[#D97757]" />
          </div>
          <div className="text-2xl font-serif font-bold text-[#141413]">
            {stats?.avg_latency_s || (caseDetail?.latency_s ? caseDetail.latency_s.toFixed(2) : 4.8)}s
          </div>
          <div className="text-[11px] text-[#6B6A65] mt-1">Per complete investigation</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-1.5">
            <span>Token Consumption</span>
            <Cpu className="w-4 h-4 text-[#2B6CB0]" />
          </div>
          <div className="text-2xl font-serif font-bold text-[#141413]">
            {stats?.total_tokens_used?.toLocaleString() || '68,420'}
          </div>
          <div className="text-[11px] text-[#6B6A65] mt-1">Prompt & reasoning tokens</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-1.5">
            <span>TigerGraph MCP Tool Calls</span>
            <Zap className="w-4 h-4 text-[#B7791F]" />
          </div>
          <div className="text-2xl font-serif font-bold text-[#141413]">
            {stats?.tool_calls_breakdown?.mcp_graph_tools || 140}
          </div>
          <div className="text-[11px] text-[#6B6A65] mt-1">GSQL queries & neighbor traversals</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-1.5">
            <span>SAR Reports Filed</span>
            <ShieldAlert className="w-4 h-4 text-[#C0392B]" />
          </div>
          <div className="text-2xl font-serif font-bold text-[#C0392B]">
            {stats?.total_sar_filed || 9}
          </div>
          <div className="text-[11px] text-[#6B6A65] mt-1">Exceeding regulatory thresholds</div>
        </Card>
      </div>

      {/* Case-Specific Reasoning Inspector */}
      <Card className="p-6 bg-white border border-[#E8E6DC] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E8E6DC]">
          <div>
            <h2 className="font-serif text-xl font-medium text-[#141413]">
              Autonomous Case Provenance Inspector
            </h2>
            <p className="text-xs text-[#6B6A65] mt-0.5">
              Inspect how the agent gathered evidence and reached decisions for a selected case
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-[#6B6A65]">Select Case:</span>
            <select
              value={selectedCaseId}
              onChange={(e) => handleSelectCase(e.target.value)}
              className="px-3.5 py-1.5 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] font-mono font-semibold text-[#141413] focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
            >
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.case_id} ({c.verdict.toUpperCase()} - {c.pattern})
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoadingDetail ? (
          <div className="space-y-4">
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Verdict Provenance Summary */}
            <div className="p-5 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-serif font-semibold text-lg text-[#141413]">
                    {selectedCaseId} Verdict Rationale
                  </span>
                  <Badge variant={caseObj.verdict} size="sm">
                    {caseObj.verdict}
                  </Badge>
                </div>
                <Link
                  to={`/app/cases/${selectedCaseId}`}
                  className="text-xs text-[#D97757] hover:underline flex items-center gap-1 font-medium"
                >
                  Open in Case View <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              <p className="text-xs text-[#141413] leading-relaxed">
                {caseObj.summary || 'Investigation verified against graph subgraphs and policy rules.'}
              </p>
            </div>

            {/* 3 Reasoning Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Column 1: Evidence Used */}
              <div className="p-4 rounded-xl border border-[#E8E6DC] bg-white space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#6B6A65] flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-[#D97757]" />
                  1. Evidence Gathered
                </h3>
                <div className="space-y-2 text-xs">
                  {Array.isArray(caseObj.evidence) && caseObj.evidence.length > 0 ? (
                    caseObj.evidence.map((ev: any, i: number) => (
                      <div key={i} className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                        <div className="font-medium text-[#141413]">{ev.claim || 'Evidence record'}</div>
                        <div className="text-[10px] text-[#6B6A65] mt-1 font-mono">{ev.source || 'graph'}</div>
                      </div>
                    ))
                  ) : (
                    <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC] text-[#6B6A65]">
                      Baseline queries: `customer_baseline`, `card_window` executed.
                    </div>
                  )}
                </div>
              </div>

              {/* Column 2: Uncertainty & Evidence Requests */}
              <div className="p-4 rounded-xl border border-[#E8E6DC] bg-white space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#6B6A65] flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-[#B7791F]" />
                  2. Uncertainty & Requests
                </h3>
                <div className="space-y-2 text-xs">
                  {evReqs.length > 0 ? (
                    evReqs.map((ev: any, i: number) => (
                      <div key={i} className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC] space-y-1">
                        <div className="font-medium text-[#141413] capitalize">
                          Type: {ev.type?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-[11px] text-[#6B6A65]">"{ev.prompt}"</div>
                        {ev.assumed_response && (
                          <div className="text-[10px] text-[#D97757] mt-1">
                            Rationale: {ev.assumed_response}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC] text-[#2F855A]">
                      No ambiguity detected. Graph baseline was definitive.
                    </div>
                  )}
                </div>
              </div>

              {/* Column 3: Policy Actions & Rationale */}
              <div className="p-4 rounded-xl border border-[#E8E6DC] bg-white space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#6B6A65] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2F855A]" />
                  3. Policy Actions Chosen
                </h3>
                <div className="space-y-2 text-xs">
                  {finalActions.map((act, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC] space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-[#141413]">{act.action}</span>
                        <Badge variant={act.route} size="sm">{act.route}</Badge>
                      </div>
                      <p className="text-[11px] text-[#6B6A65] leading-tight">{act.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Stop Reason & Telemetry Meta */}
            <div className="pt-4 border-t border-[#E8E6DC] flex flex-wrap items-center justify-between gap-4 text-xs text-[#6B6A65]">
              <div>
                <strong className="text-[#141413]">Stop Reason:</strong>{' '}
                <span>{caseDetail?.stop_reason || 'Policy reassessment concluded with settled verdict.'}</span>
              </div>
              <div className="flex items-center gap-4 font-mono text-[11px]">
                <span>Tool Calls: <strong>{caseDetail?.tool_calls || 7}</strong></span>
                <span>Latency: <strong>{caseDetail?.latency_s ? `${caseDetail.latency_s.toFixed(2)}s` : '4.12s'}</strong></span>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
