import { useState, useEffect, useCallback } from 'react';
import { fetchPendingApprovals, decideApproval } from '../api';
import ApprovalCard from '../components/ApprovalCard';
import { CheckCircle2 } from 'lucide-react';

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);

  const refresh = useCallback(async () => {
    try { setApprovals(await fetchPendingApprovals()); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleDecide = async (id, decision) => {
    await decideApproval(id, decision);
    await refresh();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
      <h1 className="text-2xl font-bold text-ink">Approvals</h1>
      <p className="text-sm text-ink-secondary mt-1">
        {approvals.length} pending approval{approvals.length !== 1 ? 's' : ''}
      </p>

      {approvals.length === 0 ? (
        <div className="mt-16 text-center">
          <CheckCircle2 className="w-12 h-12 text-divider mx-auto mb-4" />
          <p className="text-ink-secondary font-medium">No pending approvals</p>
          <p className="text-sm text-ink-faint mt-1">
            Approvals appear here when agents attempt undeclared actions
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {approvals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onDecide={handleDecide}
            />
          ))}
        </div>
      )}
    </div>
  );
}
