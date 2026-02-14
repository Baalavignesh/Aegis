import { useState } from 'react';
import { Power, ShieldOff, ShieldCheck, User, Clock, Hash, BarChart3 } from 'lucide-react';

export default function AgentProfile({ agent, onToggle }) {
    const [toggling, setToggling] = useState(false);

    if (!agent) {
        return (
            <div className="rounded-xl border border-border bg-bg-card p-8 flex items-center justify-center">
                <p className="text-text-dim text-sm">Select an agent from the sidebar</p>
            </div>
        );
    }

    const isPaused = agent.status === 'PAUSED';

    const handleToggle = async () => {
        setToggling(true);
        try {
            await onToggle(agent.name, isPaused ? 'ACTIVE' : 'PAUSED');
        } finally {
            setToggling(false);
        }
    };

    return (
        <div className="rounded-xl border border-border bg-bg-card overflow-hidden">
            {/* Header bar */}
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isPaused ? 'bg-neon-red/15' : 'bg-neon-green/15'}`}>
                        {isPaused
                            ? <ShieldOff className="w-5 h-5 text-neon-red" />
                            : <ShieldCheck className="w-5 h-5 text-neon-green" />
                        }
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-text-primary">{agent.name}</h2>
                        <p className="text-[10px] text-text-dim font-mono">{agent.id}</p>
                    </div>
                    <span className={`ml-3 px-2.5 py-1 rounded-full text-[10px] font-bold font-mono uppercase tracking-wider
            ${isPaused
                            ? 'bg-neon-red/15 text-neon-red border border-neon-red/30'
                            : 'bg-neon-green/15 text-neon-green border border-neon-green/30'
                        }`}
                    >
                        {agent.status}
                    </span>
                </div>

                {/* Kill / Revive button */}
                <button
                    onClick={handleToggle}
                    disabled={toggling}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200
            ${isPaused
                            ? 'bg-neon-green/15 text-neon-green border border-neon-green/30 hover:bg-neon-green/25 hover:shadow-[0_0_20px_rgba(57,255,20,0.15)]'
                            : 'bg-neon-red/15 text-neon-red border border-neon-red/30 hover:bg-neon-red/25 hover:shadow-[0_0_20px_rgba(255,23,68,0.15)]'
                        }
            disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                    <Power className="w-4 h-4" />
                    {toggling ? 'Working...' : isPaused ? 'REVIVE AGENT' : 'BLOCK AGENT'}
                </button>
            </div>

            {/* Details grid */}
            <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
                <DetailItem icon={User} label="Owner" value={agent.owner || 'N/A'} />
                <DetailItem icon={Clock} label="Created" value={agent.created_at?.split(' ')[0] || 'N/A'} />
                <DetailItem icon={Hash} label="Framework" value={agent.framework} />
                <DetailItem icon={BarChart3} label="Risk Score" value={`${agent.risk_score}%`}
                    valueColor={agent.risk_score > 50 ? 'text-neon-red' : agent.risk_score > 20 ? 'text-neon-amber' : 'text-neon-green'}
                />
            </div>

            {/* Stats row */}
            <div className="px-5 pb-5 grid grid-cols-3 gap-3">
                <MiniStat label="Total Logs" value={agent.total_logs} color="text-neon-blue" />
                <MiniStat label="Allowed" value={agent.allowed_count} color="text-neon-green" />
                <MiniStat label="Blocked" value={agent.blocked_count} color="text-neon-red" />
            </div>
        </div>
    );
}

function DetailItem({ icon: Icon, label, value, valueColor = 'text-text-primary' }) {
    return (
        <div className="flex items-start gap-2">
            <Icon className="w-3.5 h-3.5 text-text-dim mt-0.5 flex-shrink-0" />
            <div>
                <p className="text-[10px] text-text-dim uppercase tracking-wider">{label}</p>
                <p className={`text-sm font-mono font-medium mt-0.5 truncate ${valueColor}`}>{value}</p>
            </div>
        </div>
    );
}

function MiniStat({ label, value, color }) {
    return (
        <div className="rounded-lg bg-bg-primary border border-border p-3 text-center">
            <p className={`text-xl font-bold font-mono ${color}`}>{value}</p>
            <p className="text-[10px] text-text-dim mt-1">{label}</p>
        </div>
    );
}
