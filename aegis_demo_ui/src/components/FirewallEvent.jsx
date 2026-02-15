import { Shield, ShieldOff, Clock, ShieldAlert } from 'lucide-react';

const STATUS_CONFIG = {
  ALLOWED: { color: 'text-positive', bg: 'bg-positive-bg', icon: Shield, label: 'ALLOWED' },
  APPROVED: { color: 'text-positive', bg: 'bg-positive-bg', icon: Shield, label: 'APPROVED' },
  BLOCKED: { color: 'text-negative', bg: 'bg-negative-bg', icon: ShieldOff, label: 'BLOCKED' },
  DENIED: { color: 'text-negative', bg: 'bg-negative-bg', icon: ShieldOff, label: 'DENIED' },
  KILLED: { color: 'text-negative', bg: 'bg-negative-bg', icon: ShieldOff, label: 'KILLED' },
  PENDING: { color: 'text-caution', bg: 'bg-caution-bg', icon: Clock, label: 'PENDING' },
  TIMEOUT: { color: 'text-ink-faint', bg: 'bg-surface-hover', icon: ShieldAlert, label: 'TIMEOUT' },
};

export default function FirewallEvent({ event }) {
  const cfg = STATUS_CONFIG[event.status] || STATUS_CONFIG.BLOCKED;
  const Icon = cfg.icon;
  const time = event.timestamp.split(' ')[1] || event.timestamp;

  return (
    <div className={`flex items-center gap-3 rounded-lg px-3 py-2 ${cfg.bg}`}>
      <Icon size={16} className={cfg.color} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{event.action}</p>
        <p className="text-xs text-ink-faint">{time}</p>
      </div>
      <span className={`text-xs font-semibold ${cfg.color}`}>{cfg.label}</span>
    </div>
  );
}
