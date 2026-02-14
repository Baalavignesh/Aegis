import {
    Shield,
    ShieldCheck,
    ShieldAlert,
    AlertTriangle,
    Clock,
} from 'lucide-react';

export default function StatsCards({ stats }) {
    if (!stats) return null;

    const cards = [
        {
            label: 'Total Agents',
            value: stats.registered_agents,
            icon: Shield,
            color: 'text-neon-blue',
            bg: 'bg-neon-blue/10',
            border: 'border-neon-blue/20',
        },
        {
            label: 'Active Agents',
            value: stats.active_agents,
            icon: ShieldCheck,
            color: 'text-neon-green',
            bg: 'bg-neon-green/10',
            border: 'border-neon-green/20',
        },
        {
            label: 'Blocks (24h)',
            value: stats.total_blocks_24h,
            icon: ShieldAlert,
            color: 'text-neon-red',
            bg: 'bg-neon-red/10',
            border: 'border-neon-red/20',
        },
        {
            label: 'Pending Approvals',
            value: stats.pending_approvals,
            icon: Clock,
            color: stats.pending_approvals > 0 ? 'text-neon-amber' : 'text-text-muted',
            bg: stats.pending_approvals > 0 ? 'bg-neon-amber/10' : 'bg-bg-card',
            border: stats.pending_approvals > 0 ? 'border-neon-amber/20' : 'border-border',
        },
        {
            label: 'Risk Level',
            value: stats.risk_level,
            icon: AlertTriangle,
            color: riskColor(stats.risk_level),
            bg: riskBg(stats.risk_level),
            border: riskBorder(stats.risk_level),
        },
    ];

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {cards.map((card) => {
                const Icon = card.icon;
                return (
                    <div
                        key={card.label}
                        className={`relative overflow-hidden rounded-xl border ${card.border} ${card.bg} p-5 transition-all duration-300 hover:scale-[1.02]`}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-text-muted text-xs font-medium uppercase tracking-wider">
                                    {card.label}
                                </p>
                                <p className={`mt-2 text-3xl font-bold font-mono ${card.color}`}>
                                    {card.value}
                                </p>
                            </div>
                            <div className={`p-3 rounded-lg ${card.bg}`}>
                                <Icon className={`w-6 h-6 ${card.color}`} />
                            </div>
                        </div>
                        <div className={`absolute bottom-0 left-0 right-0 h-[2px] ${card.bg}`} />
                    </div>
                );
            })}
        </div>
    );
}

function riskColor(level) {
    switch (level) {
        case 'LOW': return 'text-neon-green';
        case 'MEDIUM': return 'text-neon-amber';
        case 'HIGH': return 'text-neon-red';
        case 'CRITICAL': return 'text-neon-red';
        default: return 'text-text-muted';
    }
}
function riskBg(level) {
    switch (level) {
        case 'LOW': return 'bg-neon-green/10';
        case 'MEDIUM': return 'bg-neon-amber/10';
        case 'HIGH': return 'bg-neon-red/10';
        case 'CRITICAL': return 'bg-neon-red/10';
        default: return 'bg-bg-card';
    }
}
function riskBorder(level) {
    switch (level) {
        case 'LOW': return 'border-neon-green/20';
        case 'MEDIUM': return 'border-neon-amber/20';
        case 'HIGH': return 'border-neon-red/20';
        case 'CRITICAL': return 'border-neon-red/20';
        default: return 'border-border';
    }
}
