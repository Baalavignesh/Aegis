import { useEffect, useRef } from 'react';

const statusStyles = {
  ALLOWED: { dot: 'bg-positive', text: 'text-positive', label: 'Allowed' },
  BLOCKED: { dot: 'bg-negative', text: 'text-negative', label: 'Blocked' },
  KILLED: { dot: 'bg-negative', text: 'text-negative', label: 'Killed' },
  PENDING: { dot: 'bg-caution', text: 'text-caution', label: 'Pending' },
  APPROVED: { dot: 'bg-positive', text: 'text-positive', label: 'Approved' },
  DENIED: { dot: 'bg-negative', text: 'text-negative', label: 'Denied' },
  TIMEOUT: { dot: 'bg-negative', text: 'text-negative', label: 'Timeout' },
};

export default function LiveFeed({ logs, agentName, fullHeight = false }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [logs]);

  return (
    <div>
      {/* Header */}
      <div className="px-5 py-4 border-b border-divider flex items-center justify-between">
        <h3 className="text-base font-bold text-ink">Activity</h3>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-positive" />
          <span className="text-xs text-ink-faint">Live</span>
        </div>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        className="overflow-y-auto"
        style={{ maxHeight: fullHeight ? 'none' : '420px' }}
      >
        {(!logs || logs.length === 0) && (
          <div className="px-5 py-12 text-center">
            <p className="text-sm text-ink-faint">No activity yet</p>
          </div>
        )}

        {logs?.map((entry) => {
          const style = statusStyles[entry.status] || statusStyles.ALLOWED;
          return (
            <div
              key={entry.id}
              className="px-5 py-3 border-b border-divider hover:bg-surface-hover transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
                  <span className="text-sm font-medium text-ink truncate">{entry.action}</span>
                </div>
                <span className={`text-xs font-semibold shrink-0 ml-2 ${style.text}`}>
                  {style.label}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 ml-[18px]">
                {!agentName && (
                  <span className="text-xs text-ink-faint truncate">{entry.agent_name}</span>
                )}
                <span className="text-xs text-ink-faint ml-auto">
                  {entry.timestamp?.split(' ')[1] || entry.timestamp}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
