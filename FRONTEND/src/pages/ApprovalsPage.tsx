import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  Filter,
  RefreshCw,
  History,
  FileCheck,
} from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Tabs, TabItem } from '../components/ui/Tabs';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { useToast } from '../components/ui/Toast';
import { api, PendingActionItem, ActionHistoryItem } from '../lib/api';

export const ApprovalsPage: React.FC = () => {
  const { toast, success, error: showError } = useToast();
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending');
  const [pendingActions, setPendingActions] = useState<PendingActionItem[]>([]);
  const [actionHistory, setActionHistory] = useState<ActionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Decision Modal
  const [actionModal, setActionModal] = useState<{
    isOpen: boolean;
    type: 'approve' | 'reject';
    item: PendingActionItem | null;
    notes: string;
    isSubmitting: boolean;
  }>({
    isOpen: false,
    type: 'approve',
    item: null,
    notes: '',
    isSubmitting: false,
  });

  const fetchActions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [pending, history] = await Promise.all([
        api.getPendingActions(),
        api.getActionHistory().catch(() => []),
      ]);
      setPendingActions(pending);
      setActionHistory(history);
    } catch (err: any) {
      setError(err.message || 'Failed to load action items.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const openDecisionModal = (type: 'approve' | 'reject', item: PendingActionItem) => {
    setActionModal({
      isOpen: true,
      type,
      item,
      notes: type === 'approve' ? 'Approved by lead fraud analyst.' : 'Rejected by lead fraud analyst.',
      isSubmitting: false,
    });
  };

  const handleDecision = async () => {
    if (!actionModal.item) return;
    setActionModal((prev) => ({ ...prev, isSubmitting: true }));

    try {
      if (actionModal.type === 'approve') {
        await api.approveAction(actionModal.item.case_id, actionModal.item.action_id, actionModal.notes);
        success('Action Approved', `Approved ${actionModal.item.action} for case ${actionModal.item.case_id}.`);
      } else {
        await api.rejectAction(actionModal.item.case_id, actionModal.item.action_id, actionModal.notes);
        success('Action Rejected', `Rejected ${actionModal.item.action} for case ${actionModal.item.case_id}.`);
      }
      setActionModal((prev) => ({ ...prev, isOpen: false }));
      await fetchActions();
    } catch (err: any) {
      showError('Action Failed', err.message || 'Could not record decision.');
    } finally {
      setActionModal((prev) => ({ ...prev, isSubmitting: false }));
    }
  };

  const tabs: TabItem[] = [
    {
      id: 'pending',
      label: 'Pending Reviews',
      badge: <Badge variant="uncertain" size="sm">{pendingActions.length}</Badge>,
      icon: <Clock className="w-3.5 h-3.5" />,
    },
    {
      id: 'history',
      label: 'Decided History',
      badge: <Badge variant="neutral" size="sm">{actionHistory.length}</Badge>,
      icon: <History className="w-3.5 h-3.5" />,
    },
  ];

  if (error) {
    return <ErrorState message={error} onRetry={fetchActions} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-medium text-[#141413]">
            Analyst Approvals Hub
          </h1>
          <p className="text-xs text-[#6B6A65] mt-1">
            Governance queue for human-in-the-loop decisions across policy tiers (L1 Analyst & L2 Supervisor)
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchActions}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh queue
        </Button>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={(id) => setActiveTab(id as any)} />

      {/* Tab: Pending Reviews */}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="p-5 space-y-3">
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-8 w-1/4 ml-auto" />
              </Card>
            ))
          ) : pendingActions.length === 0 ? (
            <EmptyState
              icon={<CheckCircle2 className="w-6 h-6 text-[#2F855A]" />}
              title="All caught up!"
              description="No human-routed actions are currently awaiting analyst review."
            />
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {pendingActions.map((item) => (
                <Card key={`${item.case_id}-${item.action_id}`} className="p-5 bg-white border border-[#E8E6DC] shadow-xs hover:border-[#D5D3C8] transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#E8E6DC]">
                    <div className="flex flex-wrap items-center gap-3">
                      <Link
                        to={`/app/cases/${item.case_id}`}
                        className="font-mono font-bold text-sm text-[#141413] hover:text-[#D97757] transition-colors"
                      >
                        {item.case_id}
                      </Link>
                      <Badge variant={item.route} size="sm">
                        {item.route} Tier
                      </Badge>
                      <Badge variant={item.verdict} size="sm">
                        {item.verdict}
                      </Badge>
                      <span className="text-xs text-[#6B6A65]">
                        Exposure: <strong className="text-[#141413]">${item.exposure_usd.toFixed(2)}</strong>
                      </span>
                    </div>

                    <Link
                      to={`/app/cases/${item.case_id}`}
                      className="text-xs text-[#D97757] hover:underline flex items-center gap-1 font-medium"
                    >
                      View full case subgraph →
                    </Link>
                  </div>

                  <div className="py-3 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs text-[#141413] bg-[#FAF9F5] px-2 py-0.5 rounded-md border border-[#E8E6DC]">
                        {item.action}
                      </span>
                      <span className="text-xs text-[#6B6A65]">• {item.pattern.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-xs text-[#6B6A65] leading-relaxed pt-1">{item.reason}</p>
                  </div>

                  <div className="pt-3 border-t border-[#E8E6DC] flex items-center justify-between">
                    <span className="text-[11px] text-[#6B6A65]">
                      Target Card: <span className="font-mono text-[#141413]">{item.customer_id}</span>
                    </span>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openDecisionModal('reject', item)}
                        leftIcon={<XCircle className="w-3.5 h-3.5 text-[#C0392B]" />}
                      >
                        Reject Action
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => openDecisionModal('approve', item)}
                        leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                      >
                        Approve Action
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Decided History */}
      {activeTab === 'history' && (
        <Card className="overflow-hidden bg-white">
          <CardHeader
            title="Action Audit Log"
            subtitle="Permanent history of human analyst decisions and timestamps"
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#E8E6DC] bg-[#FAF9F5] text-[#6B6A65]">
                  <th className="p-3.5 pl-5 font-medium">Case ID</th>
                  <th className="p-3.5 font-medium">Action & Route</th>
                  <th className="p-3.5 font-medium">Decision Status</th>
                  <th className="p-3.5 font-medium">Investigator</th>
                  <th className="p-3.5 font-medium">Audit Notes</th>
                  <th className="p-3.5 pr-5 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E6DC]/80">
                {actionHistory.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-[#6B6A65]">
                      No decided actions recorded in memory yet. Approve or reject an action to view records here.
                    </td>
                  </tr>
                ) : (
                  actionHistory.map((h, idx) => (
                    <tr key={idx} className="hover:bg-[#FAF9F5] transition-colors">
                      <td className="p-3.5 pl-5 font-mono font-medium text-[#141413]">
                        <Link to={`/app/cases/${h.case_id}`} className="hover:text-[#D97757]">
                          {h.case_id}
                        </Link>
                      </td>
                      <td className="p-3.5">
                        <div className="font-mono font-semibold text-[#141413]">{h.action}</div>
                        <span className="text-[10px] text-[#6B6A65]">{h.route}</span>
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                            h.status === 'APPROVED'
                              ? 'bg-[#E6F4EA] text-[#2F855A] border-[#C3E6CB]'
                              : 'bg-[#FBEAE7] text-[#C0392B] border-[#F5C7BE]'
                          }`}
                        >
                          {h.status}
                        </span>
                      </td>
                      <td className="p-3.5 font-medium text-[#141413]">{h.analyst_id || 'analyst_1'}</td>
                      <td className="p-3.5 text-[#6B6A65] max-w-xs truncate">{h.notes}</td>
                      <td className="p-3.5 pr-5 text-[#6B6A65] text-[11px] font-mono">
                        {h.timestamp ? new Date(h.timestamp).toLocaleString() : 'Recent'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={actionModal.isOpen}
        onClose={() => setActionModal((prev) => ({ ...prev, isOpen: false }))}
        title={actionModal.type === 'approve' ? 'Approve Policy Action' : 'Reject Policy Action'}
        description={`Record signed decision for case ${actionModal.item?.case_id}`}
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
              onClick={handleDecision}
              isLoading={actionModal.isSubmitting}
            >
              {actionModal.type === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] text-xs space-y-1">
            <div>
              <span className="text-[#6B6A65]">Action:</span>{' '}
              <strong className="text-[#141413] font-mono">{actionModal.item?.action}</strong>
            </div>
            <div>
              <span className="text-[#6B6A65]">Governance Level:</span>{' '}
              <strong className="text-[#141413]">{actionModal.item?.route}</strong>
            </div>
            <div>
              <span className="text-[#6B6A65]">Policy Reason:</span>{' '}
              <span className="text-[#6B6A65]">{actionModal.item?.reason}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#141413] mb-1.5">
              Investigator Rationale & Audit Notes
            </label>
            <textarea
              rows={3}
              value={actionModal.notes}
              onChange={(e) => setActionModal((prev) => ({ ...prev, notes: e.target.value }))}
              className="w-full px-3 py-2 text-xs rounded-xl bg-[#FAF9F5] border border-[#E8E6DC] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D97757]/30"
              placeholder="Rationale recorded for compliance..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
