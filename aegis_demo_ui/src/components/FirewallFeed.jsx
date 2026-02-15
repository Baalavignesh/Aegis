import { useEffect, useRef } from 'react';
import { Shield } from 'lucide-react';
import FirewallEvent from './FirewallEvent';
import InlineApproval from './InlineApproval';

export default function FirewallFeed({ events, approvals, onApprovalDecided }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events, approvals]);

  const pendingApprovals = approvals.filter((a) => a.status === 'PENDING');

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-divider">
        <Shield size={16} className="text-accent" />
        <h3 className="text-sm font-semibold">Firewall Activity</h3>
        {events.length > 0 && (
          <span className="ml-auto text-xs text-ink-faint">{events.length} events</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {events.length === 0 && pendingApprovals.length === 0 && (
          <p className="text-sm text-ink-faint text-center py-8">
            Firewall events will appear here as the agent executes tools...
          </p>
        )}
        {events.map((evt) => (
          <FirewallEvent key={evt.id} event={evt} />
        ))}
        {pendingApprovals.map((appr) => (
          <InlineApproval key={appr.id} approval={appr} onDecided={onApprovalDecided} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
