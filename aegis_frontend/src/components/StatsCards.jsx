export default function StatsCards({ stats }) {
  if (!stats) return null;

  const items = [
    { label: 'Registered agents', value: stats.registered_agents },
    { label: 'Active agents', value: stats.active_agents, color: 'text-positive' },
    { label: 'Blocks (24h)', value: stats.total_blocks_24h, color: stats.total_blocks_24h > 0 ? 'text-negative' : undefined },
    { label: 'Pending approvals', value: stats.pending_approvals, color: stats.pending_approvals > 0 ? 'text-caution' : undefined },
    { label: 'Risk level', value: stats.risk_level, color: riskColor(stats.risk_level) },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      {items.map((item) => (
        <div key={item.label} className="border border-divider rounded-lg p-4 sm:p-5">
          <p className="text-xs text-ink-faint">{item.label}</p>
          <p className={`text-xl sm:text-2xl font-bold mt-1 ${item.color || 'text-ink'}`}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}

function riskColor(level) {
  switch (level) {
    case 'LOW': return 'text-positive';
    case 'MEDIUM': return 'text-caution';
    case 'HIGH': return 'text-negative';
    case 'CRITICAL': return 'text-negative';
    default: return 'text-ink';
  }
}
