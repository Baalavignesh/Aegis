import { useState } from 'react';
import { ShieldAlert, Check, X, Loader2 } from 'lucide-react';
import { decideApproval } from '../api';

export default function InlineApproval({ approval, onDecided }) {
  const [loading, setLoading] = useState(null); // 'approve' | 'deny' | null

  const handle = async (decision) => {
    const key = decision === 'APPROVED' ? 'approve' : 'deny';
    setLoading(key);
    try {
      await decideApproval(approval.id, decision);
      onDecided?.(approval.id, decision);
    } catch {
      // ignore
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="rounded-xl border-2 border-caution bg-caution-bg p-3">
      <div className="flex items-center gap-2 mb-2">
        <ShieldAlert size={16} className="text-caution" />
        <span className="text-sm font-semibold text-caution">Human Approval Required</span>
      </div>
      <p className="text-sm mb-1">
        Agent <span className="font-medium">{approval.agent_name}</span> wants to execute:
      </p>
      <p className="text-sm font-mono bg-surface rounded px-2 py-1 mb-3">{approval.action}</p>
      <div className="flex gap-2">
        <button
          onClick={() => handle('APPROVED')}
          disabled={loading !== null}
          className="flex items-center gap-1.5 rounded-lg bg-positive px-3 py-1.5 text-sm font-medium text-white transition hover:bg-positive/90 disabled:opacity-50"
        >
          {loading === 'approve' ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
          Approve
        </button>
        <button
          onClick={() => handle('DENIED')}
          disabled={loading !== null}
          className="flex items-center gap-1.5 rounded-lg bg-negative px-3 py-1.5 text-sm font-medium text-white transition hover:bg-negative/90 disabled:opacity-50"
        >
          {loading === 'deny' ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
          Deny
        </button>
      </div>
    </div>
  );
}
