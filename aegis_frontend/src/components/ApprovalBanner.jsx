import { useState } from 'react';
import { AlertTriangle, Check, X, Clock, Loader2 } from 'lucide-react';

export default function ApprovalBanner({ approvals, onDecide }) {
    const [deciding, setDeciding] = useState({});

    if (!approvals || approvals.length === 0) return null;

    const handleDecide = async (id, decision) => {
        setDeciding((prev) => ({ ...prev, [id]: decision }));
        try {
            await onDecide(id, decision);
        } finally {
            setDeciding((prev) => {
                const next = { ...prev };
                delete next[id];
                return next;
            });
        }
    };

    return (
        <div className="space-y-3">
            {approvals.map((approval) => {
                const isDeciding = deciding[approval.id];
                return (
                    <div
                        key={approval.id}
                        className="rounded-xl border border-neon-amber/30 bg-neon-amber/5 p-4 shadow-[0_0_20px_rgba(255,171,0,0.05)]"
                    >
                        <div className="flex items-start gap-3">
                            {/* Icon */}
                            <div className="p-2 rounded-lg bg-neon-amber/15 flex-shrink-0">
                                <AlertTriangle className="w-5 h-5 text-neon-amber" />
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-semibold text-neon-amber">
                                        Human Approval Required
                                    </span>
                                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-neon-amber/15 text-neon-amber">
                                        #{approval.id}
                                    </span>
                                </div>

                                <p className="text-sm text-text-primary mt-1">
                                    Agent <span className="font-mono font-bold text-neon-blue">{approval.agent_name}</span> wants
                                    to execute <span className="font-mono font-bold text-neon-amber">{approval.action}</span>
                                </p>

                                <div className="flex items-center gap-1.5 mt-1.5">
                                    <Clock className="w-3 h-3 text-text-dim" />
                                    <span className="text-[10px] text-text-dim font-mono">
                                        Waiting since {approval.created_at?.split(' ')[1] || approval.created_at}
                                    </span>
                                </div>
                            </div>

                            {/* Action buttons */}
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <button
                                    onClick={() => handleDecide(approval.id, 'APPROVED')}
                                    disabled={!!isDeciding}
                                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold
                    bg-neon-green/15 text-neon-green border border-neon-green/30
                    hover:bg-neon-green/25 hover:shadow-[0_0_15px_rgba(57,255,20,0.15)]
                    transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isDeciding === 'APPROVED' ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Check className="w-4 h-4" />
                                    )}
                                    Allow
                                </button>

                                <button
                                    onClick={() => handleDecide(approval.id, 'DENIED')}
                                    disabled={!!isDeciding}
                                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold
                    bg-neon-red/15 text-neon-red border border-neon-red/30
                    hover:bg-neon-red/25 hover:shadow-[0_0_15px_rgba(255,23,68,0.15)]
                    transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isDeciding === 'DENIED' ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <X className="w-4 h-4" />
                                    )}
                                    Deny
                                </button>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
