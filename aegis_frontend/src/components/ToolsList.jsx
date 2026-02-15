export default function ToolsList({ policies }) {
  if (!policies) return null;

  const { allowed, blocked, requires_review } = policies;
  const total = allowed.length + blocked.length + requires_review.length;

  return (
    <div className="border border-divider rounded-lg overflow-hidden">
      <div className="px-5 sm:px-6 py-4 border-b border-divider">
        <h3 className="text-base font-bold text-ink">Tool Policies</h3>
        <p className="text-xs text-ink-faint mt-0.5">{total} tools configured</p>
      </div>

      <div className="divide-y divide-divider">
        {allowed.length > 0 && (
          <div className="px-5 sm:px-6 py-4">
            <p className="text-xs font-semibold text-positive uppercase tracking-wider mb-3">
              Allowed ({allowed.length})
            </p>
            <div className="space-y-2">
              {allowed.map((tool) => (
                <div key={tool} className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-positive" />
                  <span className="text-sm text-ink">{tool}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {blocked.length > 0 && (
          <div className="px-5 sm:px-6 py-4">
            <p className="text-xs font-semibold text-negative uppercase tracking-wider mb-3">
              Blocked ({blocked.length})
            </p>
            <div className="space-y-2">
              {blocked.map((tool) => (
                <div key={tool} className="flex items-center gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-negative" />
                  <span className="text-sm text-ink-secondary line-through">{tool}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {requires_review.length > 0 && (
          <div className="px-5 sm:px-6 py-4">
            <p className="text-xs font-semibold text-caution uppercase tracking-wider mb-3">
              Requires Review ({requires_review.length})
            </p>
            <div className="space-y-2">
              {requires_review.map((tool) => (
                <div key={tool} className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-caution" />
                    <span className="text-sm text-ink">{tool}</span>
                  </div>
                  <span className="text-[10px] text-ink-faint uppercase tracking-wider">human-in-loop</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {total === 0 && (
          <div className="px-6 py-8 text-center">
            <p className="text-sm text-ink-faint">No policies configured</p>
          </div>
        )}
      </div>
    </div>
  );
}
