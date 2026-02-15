import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

function bucketLogs(logs) {
  if (logs.length === 0) return [];

  const sorted = [...logs].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
  );

  const first = new Date(sorted[0].timestamp);
  const last = new Date(sorted[sorted.length - 1].timestamp);
  const spanMs = last - first;

  // Pick bucket size: aim for ~8-12 buckets
  let bucketMs, formatLabel;
  if (spanMs <= 1000 * 60 * 60) {
    // <= 1 hour: 5-min buckets
    bucketMs = 1000 * 60 * 5;
    formatLabel = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (spanMs <= 1000 * 60 * 60 * 24) {
    // <= 1 day: 1-hour buckets
    bucketMs = 1000 * 60 * 60;
    formatLabel = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else {
    // > 1 day: 1-day buckets
    bucketMs = 1000 * 60 * 60 * 24;
    formatLabel = (d) => d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  const buckets = new Map();
  const positiveStatuses = new Set(['ALLOWED', 'APPROVED']);

  for (const log of sorted) {
    const t = new Date(log.timestamp).getTime();
    const key = Math.floor(t / bucketMs) * bucketMs;
    if (!buckets.has(key)) buckets.set(key, { allowed: 0, blocked: 0 });
    const b = buckets.get(key);
    if (positiveStatuses.has(log.status)) b.allowed++;
    else b.blocked++;
  }

  return Array.from(buckets.entries())
    .sort(([a], [b]) => a - b)
    .map(([ts, counts]) => ({
      label: formatLabel(new Date(ts)),
      allowed: counts.allowed,
      blocked: counts.blocked,
    }));
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-divider rounded-lg px-3 py-2 shadow-lg">
      <p className="text-xs text-ink-faint mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="text-sm font-semibold" style={{ color: p.color }}>
          {p.value} {p.dataKey}
        </p>
      ))}
    </div>
  );
}

export default function ActivityTimeline({ logs }) {
  const data = bucketLogs(logs);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-ink-faint">No data yet</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="gradAllowed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#16A34A" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#16A34A" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradBlocked" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#DC2626" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#DC2626" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-divider)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: 'var(--color-ink-faint)' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: 'var(--color-ink-faint)' }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="allowed"
          stroke="#16A34A"
          strokeWidth={2}
          fill="url(#gradAllowed)"
        />
        <Area
          type="monotone"
          dataKey="blocked"
          stroke="#DC2626"
          strokeWidth={2}
          fill="url(#gradBlocked)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
