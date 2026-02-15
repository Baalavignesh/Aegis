import { useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';

export default function ApprovalCard({ approval, onDecide }) {
  const [deciding, setDeciding] = useState(null);

  const handleDecide = async (decision) => {
    setDeciding(decision);
    try {
      await onDecide(approval.id, decision);
    } finally {
      setDeciding(null);
    }
  };

  return (
    <div className="rounded-lg border border-divider p-5">
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        <AlertTriangle className="w-5 h-5 text-caution shrink-0 mt-0.5" />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-ink">
            Approval required
            <span className="text-ink-faint font-normal ml-1">#{approval.id}</span>
          </p>
          <p className="text-sm text-ink-secondary mt-1">
            <span className="font-semibold text-ink">{approval.agent_name}</span>
            {' '}wants to execute{' '}
            <span className="font-semibold text-ink">{approval.action}</span>
          </p>
          {approval.args_json && approval.args_json !== '{}' && (
            <p className="text-xs text-ink-faint mt-1 font-mono truncate">
              Args: {approval.args_json}
            </p>
          )}
          <p className="text-xs text-ink-faint mt-1.5">
            Waiting since {approval.created_at?.split(' ')[1] || approval.created_at}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => handleDecide('APPROVED')}
            disabled={!!deciding}
            className="px-5 py-2 rounded-full text-sm font-semibold bg-positive text-white hover:bg-positive/90 transition-colors disabled:opacity-50"
          >
            {deciding === 'APPROVED' ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Approve'}
          </button>
          <button
            onClick={() => handleDecide('DENIED')}
            disabled={!!deciding}
            className="px-5 py-2 rounded-full text-sm font-semibold text-negative border border-divider hover:bg-surface-hover transition-colors disabled:opacity-50"
          >
            {deciding === 'DENIED' ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Deny'}
          </button>
        </div>
      </div>
    </div>
  );
}
