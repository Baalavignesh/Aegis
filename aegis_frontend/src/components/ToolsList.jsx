import { CheckCircle2, XCircle, Eye } from 'lucide-react';

export default function ToolsList({ policies }) {
    if (!policies) return null;

    const { allowed, blocked, requires_review } = policies;

    return (
        <div className="rounded-xl border border-border bg-bg-card overflow-hidden">
            {/* Header */}
            <div className="px-5 py-4 border-b border-border">
                <h2 className="text-sm font-semibold text-text-primary">Tool Policies</h2>
                <p className="text-[10px] text-text-dim font-mono mt-0.5">
                    {allowed.length + blocked.length + requires_review.length} tools configured
                </p>
            </div>

            <div className="p-4 space-y-4">
                {/* Allowed tools */}
                {allowed.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <CheckCircle2 className="w-3.5 h-3.5 text-neon-green" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-neon-green">
                                Allowed ({allowed.length})
                            </span>
                        </div>
                        <div className="space-y-1">
                            {allowed.map((tool) => (
                                <div
                                    key={tool}
                                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neon-green/5 border border-neon-green/10"
                                >
                                    <span className="w-1.5 h-1.5 rounded-full bg-neon-green flex-shrink-0" />
                                    <span className="text-sm font-mono text-neon-green">{tool}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Blocked tools */}
                {blocked.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <XCircle className="w-3.5 h-3.5 text-neon-red" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-neon-red">
                                Blocked ({blocked.length})
                            </span>
                        </div>
                        <div className="space-y-1">
                            {blocked.map((tool) => (
                                <div
                                    key={tool}
                                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neon-red/5 border border-neon-red/10"
                                >
                                    <span className="w-1.5 h-1.5 rounded-full bg-neon-red flex-shrink-0" />
                                    <span className="text-sm font-mono text-neon-red line-through opacity-70">{tool}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Review-required tools */}
                {requires_review.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Eye className="w-3.5 h-3.5 text-neon-amber" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-neon-amber">
                                Requires Review ({requires_review.length})
                            </span>
                        </div>
                        <div className="space-y-1">
                            {requires_review.map((tool) => (
                                <div
                                    key={tool}
                                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neon-amber/5 border border-neon-amber/10"
                                >
                                    <span className="w-1.5 h-1.5 rounded-full bg-neon-amber animate-pulse-glow flex-shrink-0" />
                                    <span className="text-sm font-mono text-neon-amber">{tool}</span>
                                    <span className="ml-auto text-[9px] text-text-dim font-mono">HUMAN-IN-LOOP</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty state */}
                {allowed.length === 0 && blocked.length === 0 && requires_review.length === 0 && (
                    <p className="text-sm text-text-dim text-center py-4">No policies configured</p>
                )}
            </div>
        </div>
    );
}
