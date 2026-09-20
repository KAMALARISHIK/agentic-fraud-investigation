import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Database,
  Search,
  Layers,
  ShieldAlert,
  ArrowRight,
  BookOpen,
  GitFork,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { api, PatternItem, CaseSummary } from '../lib/api';

export const CaseMemoryPage: React.FC = () => {
  const [patterns, setPatterns] = useState<PatternItem[]>([]);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [pats, caseList] = await Promise.all([
        api.getMemoryPatterns(),
        api.getCases(),
      ]);
      setPatterns(pats);
      setCases(caseList);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch memory patterns.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredPatterns = useMemo(() => {
    return patterns.filter(
      (p) =>
        p.pattern.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.applicable_rules.some((r) => r.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [patterns, searchQuery]);

  const closedCases = useMemo(() => {
    return cases.filter(
      (c) =>
        c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.pattern && c.pattern.toLowerCase().includes(searchQuery.toLowerCase())) ||
        c.verdict.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [cases, searchQuery]);

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#141413]">
            Graph Memory & Typology Catalog
          </h1>
          <p className="text-xs text-[#6B6A65] mt-1">
            Standardized fraud typology rings and vectorized closed case memory stored in TigerGraph
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchData}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh catalog
        </Button>
      </div>

      {/* Search Input */}
      <Card className="p-4 bg-white">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search typologies, rule codes (e.g. R2), or historical cases..."
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
          />
          <Search className="w-4 h-4 text-[#6B6A65] absolute left-3.5 top-2.5" />
        </div>
      </Card>

      {/* Fraud Typologies Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-xl font-medium text-[#141413] flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[#D97757]" />
            Recurring Fraud Patterns & Graph Rings
          </h2>
          <span className="text-xs text-[#6B6A65]">{filteredPatterns.length} catalog patterns</span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="p-5 space-y-3">
                <Skeleton className="h-5 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredPatterns.map((p) => {
              const isHigh = p.risk_level === 'HIGH' || p.risk_level === 'CRITICAL';
              return (
                <Card
                  key={p.pattern}
                  className="p-5 bg-white border border-[#E8E6DC] shadow-2xs hover:border-[#D5D3C8] transition-all flex flex-col justify-between"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-serif text-base font-semibold text-[#141413] capitalize">
                        {p.pattern.replace(/_/g, ' ')}
                      </h3>
                      <Badge
                        variant={isHigh ? 'fraud' : p.risk_level === 'LOW' ? 'legitimate' : 'uncertain'}
                        size="sm"
                      >
                        {p.risk_level}
                      </Badge>
                    </div>

                    <p className="text-xs text-[#6B6A65] leading-relaxed">{p.description}</p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-[#E8E6DC] space-y-2">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[11px] text-[#6B6A65]">Triggered Rules:</span>
                      {p.applicable_rules.map((r) => (
                        <span
                          key={r}
                          className="text-[10px] font-mono font-semibold bg-[#FAF9F5] px-2 py-0.5 rounded-md border border-[#E8E6DC] text-[#141413]"
                        >
                          {r}
                        </span>
                      ))}
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-[#6B6A65]">
                      <span>Sample Cases:</span>
                      {p.sample_cases.map((sc) => (
                        <Link
                          key={sc}
                          to={`/app/cases/${sc}`}
                          className="text-[#D97757] hover:underline font-mono text-[10px] font-medium"
                        >
                          {sc}
                        </Link>
                      ))}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Historical Closed Cases Memory Table */}
      <Card className="overflow-hidden bg-white">
        <CardHeader
          title="Vectorized Closed Cases in Graph Memory"
          subtitle="Past closed investigations referenced for vector similarity scoring"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E8E6DC] bg-[#FAF9F5] text-[#6B6A65]">
                <th className="p-3.5 pl-5">Case ID</th>
                <th className="p-3.5">Identified Typology</th>
                <th className="p-3.5">Verdict</th>
                <th className="p-3.5">Risk Score</th>
                <th className="p-3.5">Exposure</th>
                <th className="p-3.5 pr-5 text-right">View Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E6DC]/80">
              {closedCases.map((c) => (
                <tr key={c.case_id} className="hover:bg-[#FAF9F5] transition-colors">
                  <td className="p-3.5 pl-5 font-mono font-semibold text-[#141413]">
                    <Link to={`/app/cases/${c.case_id}`} className="hover:text-[#D97757]">
                      {c.case_id}
                    </Link>
                  </td>
                  <td className="p-3.5 capitalize text-[#141413]">
                    {c.pattern && c.pattern !== 'none' ? c.pattern.replace(/_/g, ' ') : 'Baseline activity'}
                  </td>
                  <td className="p-3.5">
                    <Badge variant={c.verdict} size="sm">{c.verdict}</Badge>
                  </td>
                  <td className="p-3.5 font-mono text-[#6B6A65]">
                    {(c.fraud_probability * 100).toFixed(0)}%
                  </td>
                  <td className="p-3.5 font-semibold text-[#141413]">
                    ${c.exposure_usd.toFixed(2)}
                  </td>
                  <td className="p-3.5 pr-5 text-right">
                    <Link to={`/app/cases/${c.case_id}`}>
                      <Button size="sm" variant="secondary" rightIcon={<ArrowRight className="w-3 h-3" />}>
                        Inspect
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
