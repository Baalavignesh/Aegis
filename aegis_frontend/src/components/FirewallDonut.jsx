import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const STATUS_GROUPS = {
  Allowed: ['ALLOWED', 'APPROVED'],
  Blocked: ['BLOCKED', 'KILLED', 'DENIED', 'TIMEOUT'],
  Pending: ['PENDING'],
};

const COLORS = {
  Allowed: '#16A34A',
  Blocked: '#DC2626',
  Pending: '#D97706',
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value, percent } = payload[0].payload;
  return (
    <div className="bg-surface border border-divider rounded-lg px-3 py-2 shadow-lg">
      <p className="text-sm font-semibold text-ink">{name}</p>
      <p className="text-xs text-ink-faint">
        {value} action{value !== 1 ? 's' : ''} ({(percent * 100).toFixed(0)}%)
      </p>
    </div>
  );
}

export default function FirewallDonut({ logs }) {
  const counts = {};
  for (const group of Object.keys(STATUS_GROUPS)) counts[group] = 0;
  for (const log of logs) {
    for (const [group, statuses] of Object.entries(STATUS_GROUPS)) {
      if (statuses.includes(log.status)) {
        counts[group]++;
        break;
      }
    }
  }

  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-ink-faint">No data yet</p>
      </div>
    );
  }

  const data = Object.entries(counts)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value, percent: value / total }));

  return (
    <div className="flex items-center gap-6">
      <div className="w-40 h-40 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="space-y-3">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center gap-2.5">
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ backgroundColor: COLORS[entry.name] }}
            />
            <div>
              <p className="text-sm font-semibold text-ink tabular-nums">
                {entry.value}
                <span className="text-ink-faint font-normal ml-1.5">
                  ({(entry.percent * 100).toFixed(0)}%)
                </span>
              </p>
              <p className="text-xs text-ink-faint">{entry.name}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
