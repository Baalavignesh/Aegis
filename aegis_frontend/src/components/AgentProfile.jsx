import { useState } from 'react';
import { Power } from 'lucide-react';

export default function AgentProfile({ agent, onToggle }) {
  const [toggling, setToggling] = useState(false);

  if (!agent) {
    return (
      <div className="border border-divider rounded-lg p-12 text-center">
        <p className="text-ink-faint text-sm">Select an agent to view details</p>
      </div>
    );
  }

  const isPaused = agent.status === 'PAUSED';

  const handleToggle = async () => {
    setToggling(true);
    try {
      await onToggle(agent.name, isPaused ? 'ACTIVE' : 'PAUSED');
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="border border-divider rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-5 sm:px-6 py-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-ink">{agent.name}</h2>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              isPaused
                ? 'bg-negative-bg text-negative'
                : 'bg-positive-bg text-positive'
            }`}>
              {agent.status}
            </span>
          </div>
          <p className="text-sm text-ink-faint mt-0.5">{agent.id}</p>
        </div>

        <button
          onClick={handleToggle}
          disabled={toggling}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-colors self-start sm:self-auto ${
            isPaused
              ? 'bg-positive text-white hover:bg-positive/90'
              : 'bg-negative text-white hover:bg-negative/90'
          } disabled:opacity-50`}
        >
          <Power className="w-4 h-4" />
          {toggling ? '...' : isPaused ? 'Revive' : 'Kill'}
        </button>
      </div>

      <div className="border-t border-divider" />

      {/* Details */}
      <div className="grid grid-cols-2 divide-x divide-divider">
        <div className="p-5">
          <p className="text-xs text-ink-faint">Owner</p>
          <p className="text-sm font-medium text-ink mt-1">{agent.owner || 'N/A'}</p>
          <div className="mt-4">
            <p className="text-xs text-ink-faint">Created</p>
            <p className="text-sm font-medium text-ink mt-1">{agent.created_at?.split(' ')[0] || 'N/A'}</p>
          </div>
        </div>
        <div className="p-5">
          <p className="text-xs text-ink-faint">Framework</p>
          <p className="text-sm font-medium text-ink mt-1">{agent.framework}</p>
          <div className="mt-4">
            <p className="text-xs text-ink-faint">Risk score</p>
            <p className={`text-sm font-semibold mt-1 ${
              agent.risk_score > 50 ? 'text-negative'
                : agent.risk_score > 20 ? 'text-caution' : 'text-positive'
            }`}>
              {agent.risk_score}%
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-divider" />

      {/* Stats row */}
      <div className="grid grid-cols-3 divide-x divide-divider">
        <StatCell label="Total actions" value={agent.total_logs} />
        <StatCell label="Allowed" value={agent.allowed_count} color="text-positive" />
        <StatCell label="Blocked" value={agent.blocked_count} color="text-negative" />
      </div>
    </div>
  );
}

function StatCell({ label, value, color = 'text-ink' }) {
  return (
    <div className="p-4 text-center">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-ink-faint mt-0.5">{label}</p>
    </div>
  );
}
