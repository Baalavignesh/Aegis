import { Shield, ShieldCheck, ShieldOff, MessageSquare, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const AGENT_ICONS = {
  customer_support: MessageSquare,
  fraud_detection: ShieldCheck,
  loan_processing: Shield,
  marketing: Play,
};

const AGENT_COLORS = {
  customer_support: 'accent',
  fraud_detection: 'positive',
  loan_processing: 'caution',
  marketing: 'negative',
};

export default function DemoAgentCard({ agentKey, config }) {
  const navigate = useNavigate();
  const Icon = AGENT_ICONS[agentKey] || Shield;
  const color = AGENT_COLORS[agentKey] || 'accent';

  const allowed = config.decorator.allowed_actions || [];
  const blocked = config.decorator.blocked_actions || [];
  return (
    <div className="rounded-2xl border border-divider bg-surface p-5 transition hover:border-divider-dark hover:shadow-sm">
      <div className="flex items-start gap-3 mb-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-${color}/10`}>
          <Icon size={20} className={`text-${color}`} />
        </div>
        <div>
          <h3 className="font-semibold">{config.name}</h3>
          <p className="text-xs text-ink-secondary">{config.role}</p>
        </div>
      </div>

      <div className="flex gap-3 mb-4 text-xs">
        <span className="flex items-center gap-1 text-positive">
          <ShieldCheck size={12} />
          {allowed.length} allowed
        </span>
        <span className="flex items-center gap-1 text-negative">
          <ShieldOff size={12} />
          {blocked.length} blocked
        </span>
      </div>

      <div className="mb-4">
        <p className="text-xs text-ink-faint mb-1.5">Allowed tools:</p>
        <div className="flex flex-wrap gap-1">
          {allowed.map((a) => (
            <span key={a} className="rounded-md bg-positive-bg px-1.5 py-0.5 text-[11px] text-positive font-medium">
              {a}
            </span>
          ))}
        </div>
      </div>

      <button
        onClick={() => navigate(`/scenario/${agentKey}`)}
        className="w-full rounded-xl py-2.5 text-sm font-medium text-white transition bg-ink hover:bg-ink/80"
      >
        Run Scenario
      </button>
    </div>
  );
}
