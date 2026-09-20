import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  Play,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { api, CaseSummary } from '../lib/api';
import { useToast } from '../components/ui/Toast';

export const InvestigationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('ALL');
  const [patternFilter, setPatternFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortField, setSortField] = useState<'case_id' | 'fraud_probability' | 'exposure_usd'>('case_id');
  const [sortAsc, setSortAsc] = useState(true);

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getCases();
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cases from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  // Unique patterns for filter dropdown
  const uniquePatterns = useMemo(() => {
    const set = new Set<string>();
    cases.forEach((c) => {
      if (c.pattern) set.add(c.pattern);
    });
    return Array.from(set);
  }, [cases]);

  // Filtered & Sorted Cases
  const filteredCases = useMemo(() => {
    return cases
      .filter((c) => {
        const matchesSearch =
          c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (c.card_id && c.card_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
          (c.customer_id && c.customer_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
          (c.pattern && c.pattern.toLowerCase().includes(searchQuery.toLowerCase()));

        const matchesVerdict =
          verdictFilter === 'ALL' || c.verdict.toLowerCase() === verdictFilter.toLowerCase();

        const matchesPattern =
          patternFilter === 'ALL' || c.pattern.toLowerCase() === patternFilter.toLowerCase();

        const matchesStatus =
          statusFilter === 'ALL' || c.status.toLowerCase() === statusFilter.toLowerCase();

        return matchesSearch && matchesVerdict && matchesPattern && matchesStatus;
      })
      .sort((a, b) => {
        let valA = a[sortField] ?? '';
        let valB = b[sortField] ?? '';
        if (typeof valA === 'string') {
          return sortAsc
            ? (valA as string).localeCompare(valB as string)
            : (valB as string).localeCompare(valA as string);
        }
        return sortAsc ? (valA as number) - (valB as number) : (valB as number) - (valA as number);
      });
  }, [cases, searchQuery, verdictFilter, patternFilter, statusFilter, sortField, sortAsc]);

  const toggleSort = (field: 'case_id' | 'fraud_probability' | 'exposure_usd') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false); // Default descending for scores/amounts
    }
  };

  if (error) {
    return <ErrorState message={error} onRetry={fetchCases} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#141413]">
            Investigations Queue
          </h1>
          <p className="text-xs text-[#6B6A65] mt-1">
            Browse, triage, and inspect all {cases.length} autonomous fraud investigation cases
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchCases}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh queue
        </Button>
      </div>

      {/* Search & Filter Bar */}
      <Card className="p-4 bg-white">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search case ID (e.g. HHG-001), card, pattern..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30 focus:border-[#D97757] transition-all"
            />
            <Search className="w-4 h-4 text-[#6B6A65] absolute left-3 top-2.5" />
          </div>

          {/* Verdict Filter */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-[#141413] focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
            >
              <option value="ALL">All Verdicts</option>
              <option value="fraud">Fraud</option>
              <option value="legitimate">Legitimate</option>
              <option value="uncertain">Uncertain</option>
            </select>

            {/* Pattern Filter */}
            <select
              value={patternFilter}
              onChange={(e) => setPatternFilter(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-[#141413] focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
            >
              <option value="ALL">All Typologies</option>
              {uniquePatterns.map((p) => (
                <option key={p} value={p}>
                  {p.replace(/_/g, ' ')}
                </option>
              ))}
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-[#141413] focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
            >
              <option value="ALL">All Statuses</option>
              <option value="CLOSED">Closed</option>
              <option value="closed_fraud">Closed Fraud</option>
              <option value="closed_legitimate">Closed Legitimate</option>
            </select>

            {(searchQuery || verdictFilter !== 'ALL' || patternFilter !== 'ALL' || statusFilter !== 'ALL') && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setVerdictFilter('ALL');
                  setPatternFilter('ALL');
                  setStatusFilter('ALL');
                }}
                className="text-xs text-[#D97757] hover:underline px-2 py-1 cursor-pointer"
              >
                Reset filters
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* Cases Table */}
      <Card className="overflow-hidden bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E8E6DC] bg-[#FAF9F5] text-[#6B6A65]">
                <th
                  onClick={() => toggleSort('case_id')}
                  className="p-3.5 pl-5 font-medium cursor-pointer hover:text-[#141413] transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Case ID</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3.5 font-medium">Trigger & Typology</th>
                <th className="p-3.5 font-medium">Card Identifier</th>
                <th
                  onClick={() => toggleSort('exposure_usd')}
                  className="p-3.5 font-medium cursor-pointer hover:text-[#141413] transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Exposure (USD)</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('fraud_probability')}
                  className="p-3.5 font-medium cursor-pointer hover:text-[#141413] transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Risk Score</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3.5 font-medium">Verdict</th>
                <th className="p-3.5 font-medium">SAR</th>
                <th className="p-3.5 pr-5 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E6DC]/80">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="p-3.5 pl-5"><Skeleton className="h-4 w-20" /></td>
                    <td className="p-3.5"><Skeleton className="h-4 w-32" /></td>
                    <td className="p-3.5"><Skeleton className="h-4 w-24" /></td>
                    <td className="p-3.5"><Skeleton className="h-4 w-16" /></td>
                    <td className="p-3.5"><Skeleton className="h-4 w-12" /></td>
                    <td className="p-3.5"><Skeleton className="h-5 w-20 rounded-full" /></td>
                    <td className="p-3.5"><Skeleton className="h-4 w-10" /></td>
                    <td className="p-3.5 pr-5 text-right"><Skeleton className="h-8 w-24 ml-auto rounded-lg" /></td>
                  </tr>
                ))
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8">
                    <EmptyState
                      title="No cases match your filters"
                      description="Try clearing search keywords or changing the verdict filter."
                      action={
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setSearchQuery('');
                            setVerdictFilter('ALL');
                            setPatternFilter('ALL');
                            setStatusFilter('ALL');
                          }}
                        >
                          Clear all filters
                        </Button>
                      }
                    />
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr
                    key={c.case_id}
                    onClick={() => navigate(`/app/cases/${c.case_id}`)}
                    className="hover:bg-[#FAF9F5] transition-colors cursor-pointer group"
                  >
                    <td className="p-3.5 pl-5 font-mono font-semibold text-[#141413] group-hover:text-[#D97757]">
                      {c.case_id}
                    </td>
                    <td className="p-3.5">
                      <div className="font-medium text-[#141413] capitalize">
                        {c.pattern && c.pattern !== 'none' ? c.pattern.replace(/_/g, ' ') : 'Legitimate baseline'}
                      </div>
                      <div className="text-[10px] text-[#6B6A65]">
                        {c.actions_count} policy actions evaluated
                      </div>
                    </td>
                    <td className="p-3.5 font-mono text-[11px] text-[#6B6A65]">
                      {c.card_id || 'N/A (Multi-entity)'}
                    </td>
                    <td className="p-3.5 font-semibold text-[#141413]">
                      ${c.exposure_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-12 bg-[#E8E6DC] h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              c.fraud_probability > 0.7
                                ? 'bg-[#C0392B]'
                                : c.fraud_probability > 0.3
                                ? 'bg-[#B7791F]'
                                : 'bg-[#2F855A]'
                            }`}
                            style={{ width: `${Math.min(100, c.fraud_probability * 100)}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-mono text-[#6B6A65]">
                          {(c.fraud_probability * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <Badge variant={c.verdict} size="sm">
                        {c.verdict}
                      </Badge>
                    </td>
                    <td className="p-3.5">
                      {c.sar_required ? (
                        <span className="text-[11px] font-medium text-[#C0392B] bg-[#FBEAE7] px-2 py-0.5 rounded-md border border-[#F5C7BE]">
                          Filed
                        </span>
                      ) : (
                        <span className="text-[11px] text-[#6B6A65]">None</span>
                      )}
                    </td>
                    <td className="p-3.5 pr-5 text-right">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/app/cases/${c.case_id}`);
                        }}
                        rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                      >
                        Investigate
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="p-3 px-5 border-t border-[#E8E6DC] bg-[#FAF9F5] text-xs text-[#6B6A65] flex items-center justify-between">
          <span>
            Showing <strong>{filteredCases.length}</strong> of <strong>{cases.length}</strong> total cases
          </span>
          <span className="text-[11px]">Click any row to open full sub-graph details</span>
        </div>
      </Card>
    </div>
  );
};
