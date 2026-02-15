import { motion } from 'motion/react';
import AnimatedNumber from './AnimatedNumber';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function DashboardStatCards({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: 'Agents',
      value: stats.registered_agents,
      animate: true,
      pill: `${stats.active_agents} active`,
      up: stats.active_agents > 0,
      trend: stats.active_agents > 0 ? 'Agents online' : 'No agents running',
      sub: 'Registered in system',
    },
    {
      label: 'Blocks (24h)',
      value: stats.total_blocks_24h,
      animate: true,
      pill: stats.total_blocks_24h === 0 ? 'Clear' : `${stats.total_blocks_24h} blocked`,
      up: stats.total_blocks_24h === 0,
      trend: stats.total_blocks_24h === 0 ? 'No blocked attempts' : 'Attempts intercepted',
      sub: stats.total_blocks_24h === 0 ? 'Firewall operating normally' : 'Review activity for details',
    },
    {
      label: 'Pending Approvals',
      value: stats.pending_approvals,
      animate: true,
      pill: stats.pending_approvals === 0 ? 'Clear' : 'Needs action',
      up: stats.pending_approvals === 0,
      trend: stats.pending_approvals === 0 ? 'All decisions resolved' : 'Requires your decision',
      sub: stats.pending_approvals === 0 ? 'All caught up' : 'Human-in-the-loop queue',
    },
    {
      label: 'Risk Level',
      value: stats.risk_level,
      animate: false,
      pill: stats.risk_level,
      up: stats.risk_level === 'LOW' || stats.risk_level === 'MEDIUM',
      trend: stats.risk_level === 'LOW' ? 'Within acceptable range' : stats.risk_level === 'MEDIUM' ? 'Monitor activity' : 'Needs attention',
      sub: stats.risk_level === 'LOW' ? 'Meets governance targets' : 'Review agent policies',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => {
        const TrendIcon = card.up ? TrendingUp : TrendingDown;
        return (
          <motion.div
            key={card.label}
            className="rounded-xl bg-surface border border-divider p-5 flex flex-col min-h-[156px]"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.25 }}
          >
            {/* Top row: label + pill */}
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-medium text-ink-faint uppercase tracking-wider">{card.label}</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-surface-hover border border-divider px-2 py-0.5 text-[10px] font-semibold text-ink-secondary">
                <TrendIcon className="w-2.5 h-2.5" />
                {card.pill}
              </span>
            </div>

            {/* Big number */}
            <p className="text-3xl font-bold text-ink mt-3 tabular-nums">
              {card.animate && typeof card.value === 'number' ? (
                <AnimatedNumber value={card.value} duration={0.25} />
              ) : (
                card.value
              )}
            </p>

            {/* Trend text + icon */}
            <div className="flex items-center gap-1.5 mt-auto pt-3">
              <span className="text-xs font-medium text-ink-secondary">{card.trend}</span>
              <TrendIcon className="w-3.5 h-3.5 text-ink-faint" />
            </div>

            {/* Subtitle */}
            <p className="text-[11px] text-ink-faint mt-0.5">{card.sub}</p>
          </motion.div>
        );
      })}
    </div>
  );
}
