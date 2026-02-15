import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Shield } from 'lucide-react';

export default function AgentCard({ agent }) {
  const isPaused = agent.status === 'PAUSED';
  const statusColor = isPaused ? 'bg-negative' : 'bg-positive';
  const statusLabel = isPaused ? 'Paused' : 'Active';
  const riskBarColor =
    agent.risk_score > 50 ? 'bg-negative' : agent.risk_score > 20 ? 'bg-caution' : 'bg-accent';

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.15 }}>
      <Link
        to={`/agents/${encodeURIComponent(agent.name)}`}
        className="block rounded-xl border border-divider bg-surface p-5 hover:border-divider-dark transition-colors"
      >
        {/* Top row: name + icon */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-base font-bold text-ink truncate">{agent.name}</h3>
            <p className="text-sm text-ink-faint mt-0.5">{agent.owner || '—'}</p>
          </div>
          <div className="w-9 h-9 rounded-lg bg-accent-bg flex items-center justify-center shrink-0">
            <Shield className="w-4.5 h-4.5 text-accent" strokeWidth={2} />
          </div>
        </div>

        {/* Status row: dot + label */}
        <div className="flex items-center gap-2 mt-4">
          <span className={`w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-sm text-ink-secondary">{statusLabel}</span>
        </div>

        {/* Risk progress bar */}
        <div className="mt-4">
          <div className="h-2 rounded-full bg-surface-hover overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${riskBarColor}`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(agent.risk_score, 100)}%` }}
              transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
            />
          </div>
        </div>

        {/* Bottom: description + percentage */}
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-ink-faint">
            {agent.total_logs} actions · {agent.allowed_count} allowed
          </span>
          <span className="text-xs font-bold text-ink tabular-nums">{agent.risk_score}%</span>
        </div>
      </Link>
    </motion.div>
  );
}
