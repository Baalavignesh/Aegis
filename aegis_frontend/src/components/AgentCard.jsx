import { Link } from 'react-router-dom';

export default function AgentCard({ agent }) {
  const isPaused = agent.status === 'PAUSED';

  return (
    <Link
      to={`/agents/${encodeURIComponent(agent.name)}`}
      className="border border-divider rounded-lg p-5 hover:bg-surface-hover transition-colors block"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold text-ink">{agent.name}</h3>
          <span className={`w-2 h-2 rounded-full ${isPaused ? 'bg-negative' : 'bg-positive'}`} />
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
          isPaused ? 'bg-negative-bg text-negative' : 'bg-positive-bg text-positive'
        }`}>
          {agent.status}
        </span>
      </div>

      <p className="text-xs text-ink-faint">{agent.owner}</p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <div>
          <p className="text-lg font-bold text-ink">{agent.total_logs}</p>
          <p className="text-xs text-ink-faint">Actions</p>
        </div>
        <div>
          <p className="text-lg font-bold text-positive">{agent.allowed_count}</p>
          <p className="text-xs text-ink-faint">Allowed</p>
        </div>
        <div>
          <p className="text-lg font-bold text-negative">{agent.blocked_count}</p>
          <p className="text-xs text-ink-faint">Blocked</p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-divider flex items-center justify-between">
        <span className="text-xs text-ink-faint">Risk score</span>
        <span className={`text-sm font-semibold ${
          agent.risk_score > 50 ? 'text-negative'
            : agent.risk_score > 20 ? 'text-caution' : 'text-positive'
        }`}>
          {agent.risk_score}%
        </span>
      </div>
    </Link>
  );
}
