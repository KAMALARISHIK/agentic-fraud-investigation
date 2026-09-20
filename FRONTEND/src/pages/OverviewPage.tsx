import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  Clock,
  ArrowRight,
  TrendingUp,
  DollarSign,
  Activity,
  Layers,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Card, CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { api, CaseSummary, StatsResponse, PendingActionItem } from '../lib/api';

export const OverviewPage: React.FC = () => {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [pendingActions, setPendingActions] = useState<PendingActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [casesData, statsData, pendingData] = await Promise.all([
        api.getCases(),
        api.getStats(),
        api.getPendingActions().catch(() => []),
      ]);
      setCases(casesData);
      setStats(statsData);
      setPendingActions(pendingData);
    } catch (err: any) {
      setError(err.message || 'Failed to load operational data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  // Real Computed Metrics
  const totalCases = cases.length || stats?.total_cases || 0;
  const fraudCases = cases.filter((c) => c.verdict === 'fraud').length;
  const legitimateCases = cases.filter((c) => c.verdict === 'legitimate').length;
  const uncertainCases = cases.filter((c) => c.verdict === 'uncertain').length;
  const totalExposure = cases.reduce((acc, c) => acc + (c.exposure_usd || 0), 0) || stats?.total_exposure_usd || 0;
  const avgConfidence = cases.length
    ? Math.round(
        (cases.reduce((acc, c) => acc + (c.verdict === 'fraud' ? c.fraud_probability : 1 - c.fraud_probability), 0) /
          cases.length) *
          100
      )
    : 92;

  // Chart Data: Verdict Distribution
  const verdictChartData = [
    { name: 'Fraud Confirmed', value: fraudCases || stats?.verdict_distribution?.fraud || 0, color: '#C0392B' },
    { name: 'Legitimate', value: legitimateCases || stats?.verdict_distribution?.legitimate || 0, color: '#2F855A' },
    { name: 'Uncertain / Review', value: uncertainCases || stats?.verdict_distribution?.uncertain || 0, color: '#B7791F' },
  ].filter((d) => d.value > 0);

  // Chart Data: Pattern Breakdown
  const patternMap: Record<string, number> = {};
  cases.forEach((c) => {
    const p = c.pattern && c.pattern !== 'none' ? c.pattern.replace(/_/g, ' ') : 'Legitimate baseline';
    patternMap[p] = (patternMap[p] || 0) + 1;
  });
  const patternChartData = Object.entries(patternMap).map(([name, count]) => ({
    name: name.length > 18 ? name.substring(0, 16) + '…' : name,
    count,
  }));

  // Chart Data: Risk Score Buckets
  const riskBuckets = [
    { range: '0.0 - 0.2 (Low)', count: 0 },
    { range: '0.2 - 0.5 (Med)', count: 0 },
    { range: '0.5 - 0.8 (Elevated)', count: 0 },
    { range: '0.8 - 1.0 (Critical)', count: 0 },
  ];
  cases.forEach((c) => {
    const score = c.fraud_probability || 0;
    if (score < 0.2) riskBuckets[0].count += 1;
    else if (score < 0.5) riskBuckets[1].count += 1;
    else if (score < 0.8) riskBuckets[2].count += 1;
    else riskBuckets[3].count += 1;
  });

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#141413]">
            Investigation Overview
          </h1>
          <p className="text-xs text-[#6B6A65] mt-1">
            Real-time telemetry and verdict metrics across {totalCases} TigerGraph investigated cases
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchData}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh data
          </Button>
          <Link to="/app/cases">
            <Button size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
              Explore cases
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} lines={1} />)
        ) : (
          <>
            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Total Cases</span>
                <Layers className="w-4 h-4 text-[#D97757]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#141413]">{totalCases}</div>
              <div className="text-[11px] text-[#6B6A65] mt-1">Investigated in graph</div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Fraud Found</span>
                <ShieldAlert className="w-4 h-4 text-[#C0392B]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#C0392B]">{fraudCases}</div>
              <div className="text-[11px] text-[#C0392B] mt-1 font-medium">Confirmed patterns</div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Legitimate</span>
                <ShieldCheck className="w-4 h-4 text-[#2F855A]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#2F855A]">{legitimateCases}</div>
              <div className="text-[11px] text-[#2F855A] mt-1 font-medium">Cleared baselines</div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Uncertain</span>
                <HelpCircle className="w-4 h-4 text-[#B7791F]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#B7791F]">{uncertainCases}</div>
              <div className="text-[11px] text-[#B7791F] mt-1 font-medium">Monitoring active</div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Pending Approvals</span>
                <Clock className="w-4 h-4 text-[#B7791F]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#141413]">
                {pendingActions.length}
              </div>
              <div className="text-[11px] text-[#D97757] font-medium mt-1">L1 / L2 Actions</div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center justify-between text-xs text-[#6B6A65] mb-2">
                <span>Total Exposure</span>
                <DollarSign className="w-4 h-4 text-[#D97757]" />
              </div>
              <div className="text-2xl font-serif font-semibold text-[#141413]">
                ${totalExposure.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </div>
              <div className="text-[11px] text-[#6B6A65] mt-1">At-risk transactions</div>
            </Card>
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Verdict Split Donut */}
        <Card className="p-5 flex flex-col justify-between">
          <div>
            <h3 className="font-serif text-base font-medium text-[#141413]">Verdict Distribution</h3>
            <p className="text-xs text-[#6B6A65] mt-0.5">Categorization across all investigated alerts</p>
          </div>
          <div className="h-56 w-full my-3">
            {isLoading ? (
              <Skeleton className="w-full h-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={verdictChartData}
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {verdictChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '8px',
                      border: '1px solid #E8E6DC',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2 border-t border-[#E8E6DC] text-xs">
            {verdictChartData.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-[#6B6A65]">
                  {d.name}: <strong className="text-[#141413]">{d.value}</strong>
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Fraud Pattern Bar Chart */}
        <Card className="p-5 flex flex-col justify-between lg:col-span-2">
          <div>
            <h3 className="font-serif text-base font-medium text-[#141413]">
              Identified Fraud Typologies
            </h3>
            <p className="text-xs text-[#6B6A65] mt-0.5">
              Frequency of recognized graph attack patterns and baseline signals
            </p>
          </div>
          <div className="h-56 w-full my-3">
            {isLoading ? (
              <Skeleton className="w-full h-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={patternChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E6DC" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: '#6B6A65' }}
                    angle={-15}
                    textAnchor="end"
                  />
                  <YAxis tick={{ fontSize: 11, fill: '#6B6A65' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '8px',
                      border: '1px solid #E8E6DC',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#D97757" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="text-[11px] text-[#6B6A65] flex items-center justify-between border-t border-[#E8E6DC] pt-2">
            <span>Graph matching powered by TigerGraph & DuckDB</span>
            <Link to="/app/memory" className="text-[#D97757] hover:underline">
              View pattern catalog →
            </Link>
          </div>
        </Card>
      </div>

      {/* Risk Score Histogram & Quick Start Guide */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Score Histogram */}
        <Card className="p-5">
          <h3 className="font-serif text-base font-medium text-[#141413]">Risk Score Distribution</h3>
          <p className="text-xs text-[#6B6A65] mt-0.5">Calculated fraud probability spectrum</p>
          <div className="h-44 w-full my-3">
            {isLoading ? (
              <Skeleton className="w-full h-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskBuckets} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E8E6DC" vertical={false} />
                  <XAxis dataKey="range" tick={{ fontSize: 9, fill: '#6B6A65' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#6B6A65' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '8px',
                      border: '1px solid #E8E6DC',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="count" fill="#B7791F" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="text-[11px] text-[#6B6A65]">
            Average agent decision confidence: <strong className="text-[#141413]">{avgConfidence}%</strong>
          </div>
        </Card>

        {/* "How to use" Panel */}
        <Card className="p-5 lg:col-span-2 bg-white border border-[#E8E6DC] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="font-serif text-base font-medium text-[#141413] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#D97757]" />
                How to Investigate (5 Steps)
              </span>
              <Badge variant="terracotta" size="sm">Analyst Protocol</Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                <div className="font-serif font-bold text-[#D97757] text-sm mb-0.5">1</div>
                <div className="font-medium text-[#141413]">Pick Alert</div>
                <div className="text-[10px] text-[#6B6A65] mt-0.5">Select high-risk case in queue</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                <div className="font-serif font-bold text-[#D97757] text-sm mb-0.5">2</div>
                <div className="font-medium text-[#141413]">Investigate</div>
                <div className="text-[10px] text-[#6B6A65] mt-0.5">Agent queries TigerGraph subgraphs</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                <div className="font-serif font-bold text-[#D97757] text-sm mb-0.5">3</div>
                <div className="font-medium text-[#141413]">Simulate Reply</div>
                <div className="text-[10px] text-[#6B6A65] mt-0.5">Respond to evidence requests</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                <div className="font-serif font-bold text-[#D97757] text-sm mb-0.5">4</div>
                <div className="font-medium text-[#141413]">Audit Policy</div>
                <div className="text-[10px] text-[#6B6A65] mt-0.5">Approve / reject L1 & L2 actions</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#E8E6DC]">
                <div className="font-serif font-bold text-[#D97757] text-sm mb-0.5">5</div>
                <div className="font-medium text-[#141413]">Export SAR</div>
                <div className="text-[10px] text-[#6B6A65] mt-0.5">Download filed SAR report</div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#E8E6DC] flex items-center justify-between">
            <span className="text-xs text-[#6B6A65]">
              {pendingActions.length} actions pending human analyst review
            </span>
            <Link to="/app/cases">
              <Button size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Start investigating
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
