import { Bot, ShieldCheck, ShieldOff, LayoutGrid } from 'lucide-react';

export default function Sidebar({ agents, selected, onSelect }) {
    return (
        <aside className="w-72 min-h-screen bg-bg-sidebar border-r border-border flex flex-col">
            {/* Logo / Title */}
            <div className="p-5 border-b border-border">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-neon-green/10">
                        <ShieldCheck className="w-6 h-6 text-neon-green" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold tracking-tight text-text-primary">
                            Agent Sentinel
                        </h1>
                        <p className="text-xs text-text-dim font-mono">v0.1.0 — live</p>
                    </div>
                </div>
            </div>

            {/* Agent list */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-text-dim">
                    Global view
                </p>
                <button
                    onClick={() => onSelect(null)}
                    className={`w-full text-left rounded-lg px-3 py-3 transition-all duration-200 border transform
            ${!selected
                            ? 'bg-neon-blue/10 border-neon-blue/25 text-neon-blue shadow-[0_0_15px_rgba(0,176,255,0.1)]'
                            : 'bg-transparent border-transparent text-text-muted hover:bg-bg-card-hover hover:text-text-primary'
                        }`}
                >
                    <div className="flex items-center gap-3">
                        <div className={`p-1.5 rounded-md ${!selected ? 'bg-neon-blue/15' : 'bg-bg-card'}`}>
                            <LayoutGrid className={`w-4 h-4 ${!selected ? 'text-neon-blue' : 'text-text-dim'}`} />
                        </div>
                        <span className="text-sm font-semibold">All Connected Agents</span>
                    </div>
                </button>

                <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-text-dim mt-4">
                    Registered Agents
                </p>

                {agents.length === 0 && (
                    <p className="px-2 py-4 text-sm text-text-dim text-center">
                        No agents found
                    </p>
                )}

                {agents.map((agent) => {
                    const isActive = agent.name === selected;
                    const isPaused = agent.status === 'PAUSED';
                    return (
                        <button
                            key={agent.name}
                            onClick={() => onSelect(agent.name)}
                            className={`w-full text-left rounded-lg px-3 py-3 transition-all duration-200 border
                ${isActive
                                    ? 'bg-neon-green/8 border-neon-green/25 shadow-[0_0_15px_rgba(57,255,20,0.05)]'
                                    : 'bg-transparent border-transparent hover:bg-bg-card-hover hover:border-border-hover'
                                }`}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`p-1.5 rounded-md ${isPaused ? 'bg-neon-red/15' : 'bg-neon-green/15'}`}>
                                    {isPaused
                                        ? <ShieldOff className="w-4 h-4 text-neon-red" />
                                        : <Bot className="w-4 h-4 text-neon-green" />
                                    }
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className={`text-sm font-semibold truncate ${isActive ? 'text-neon-green' : 'text-text-primary'}`}>
                                        {agent.name}
                                    </p>
                                    <p className="text-[10px] text-text-dim font-mono mt-0.5">
                                        {agent.framework}
                                    </p>
                                </div>
                                {/* Status dot */}
                                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isPaused ? 'bg-neon-red animate-pulse-glow' : 'bg-neon-green'
                                    }`} />
                            </div>

                            {/* Risk score bar */}
                            <div className="mt-2.5">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-[10px] text-text-dim">Risk Score</span>
                                    <span className={`text-[10px] font-mono font-bold ${agent.risk_score > 50 ? 'text-neon-red' : agent.risk_score > 20 ? 'text-neon-amber' : 'text-neon-green'
                                        }`}>
                                        {agent.risk_score}%
                                    </span>
                                </div>
                                <div className="w-full h-1.5 rounded-full bg-bg-primary overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all duration-500 ${agent.risk_score > 50 ? 'bg-neon-red' : agent.risk_score > 20 ? 'bg-neon-amber' : 'bg-neon-green'
                                            }`}
                                        style={{ width: `${Math.min(agent.risk_score, 100)}%` }}
                                    />
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border">
                <p className="text-[10px] text-text-dim text-center font-mono">
                    Sentinel Guardrails © 2026
                </p>
            </div>
        </aside>
    );
}
