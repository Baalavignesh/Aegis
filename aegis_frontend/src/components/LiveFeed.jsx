import { useEffect, useRef } from 'react';
import { Activity, CheckCircle2, XCircle, Skull, Clock, ThumbsUp, ThumbsDown, Timer } from 'lucide-react';

const statusConfig = {
    ALLOWED: { icon: CheckCircle2, color: 'text-neon-green', dotClass: 'bg-neon-green', label: 'Allowed', glow: 'glow-green' },
    BLOCKED: { icon: XCircle, color: 'text-neon-red', dotClass: 'bg-neon-red', label: 'Blocked', glow: 'glow-red' },
    KILLED: { icon: Skull, color: 'text-neon-red', dotClass: 'bg-neon-red animate-pulse-glow', label: 'Killed', glow: 'glow-red' },
    PENDING: { icon: Clock, color: 'text-neon-amber', dotClass: 'bg-neon-amber animate-pulse-glow', label: 'Pending', glow: 'glow-amber' },
    APPROVED: { icon: ThumbsUp, color: 'text-neon-green', dotClass: 'bg-neon-green', label: 'Approved', glow: 'glow-green' },
    DENIED: { icon: ThumbsDown, color: 'text-neon-red', dotClass: 'bg-neon-red', label: 'Denied', glow: 'glow-red' },
    TIMEOUT: { icon: Timer, color: 'text-neon-red', dotClass: 'bg-neon-red', label: 'Timeout', glow: 'glow-red' },
};

export default function LiveFeed({ logs, agentName }) {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = 0;
        }
    }, [logs]);

    return (
        <div className="rounded-xl border border-border bg-bg-card overflow-hidden flex flex-col h-full">
            {/* Header */}
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-neon-green" />
                    <h2 className="text-sm font-semibold text-text-primary">Live Feed</h2>
                    {agentName && (
                        <span className="ml-2 px-2 py-0.5 rounded-md bg-neon-green/10 text-neon-green text-[10px] font-mono font-bold">
                            {agentName}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse-glow" />
                    <span className="text-[10px] text-text-dim font-mono">Polling 2s</span>
                </div>
            </div>

            {/* Log entries */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1">
                {(!logs || logs.length === 0) && (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-text-dim text-sm">
                            {agentName ? 'No logs yet...' : 'Select an agent to view logs'}
                        </p>
                    </div>
                )}

                {logs?.map((entry) => {
                    const config = statusConfig[entry.status] || statusConfig.ALLOWED;
                    const Icon = config.icon;
                    return (
                        <div
                            key={entry.id}
                            className="group flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-card-hover transition-colors duration-150"
                        >
                            {/* Status dot */}
                            <div className="pt-1 flex-shrink-0">
                                <span className={`block w-2.5 h-2.5 rounded-full ${config.dotClass}`} />
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`font-mono text-sm font-semibold ${config.color} ${config.glow}`}>
                                        {entry.action}
                                    </span>
                                    {!agentName && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-bg-card hover:bg-bg-card-hover border border-border text-text-dim">
                                            {entry.agent_name}
                                        </span>
                                    )}
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold
                    ${entry.status === 'ALLOWED' || entry.status === 'APPROVED'
                                            ? 'bg-neon-green/10 text-neon-green'
                                            : entry.status === 'PENDING'
                                                ? 'bg-neon-amber/10 text-neon-amber'
                                                : 'bg-neon-red/10 text-neon-red'
                                        }`}
                                    >
                                        {config.label}
                                    </span>
                                </div>
                                {entry.details && (
                                    <p className="text-[11px] text-text-dim mt-0.5 truncate font-mono">
                                        {entry.details}
                                    </p>
                                )}
                            </div>

                            {/* Timestamp */}
                            <span className="text-[10px] text-text-dim font-mono flex-shrink-0 pt-0.5">
                                {entry.timestamp?.split(' ')[1] || entry.timestamp}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
