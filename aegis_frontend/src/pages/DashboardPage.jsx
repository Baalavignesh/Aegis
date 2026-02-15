import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchStats, fetchAgents, fetchAllLogs, fetchPendingApprovals } from '../api';
import DashboardStatCards from '../components/DashboardStatCards';
import FirewallDonut from '../components/FirewallDonut';
import ActivityTimeline from '../components/ActivityTimeline';
import { ArrowRight, AlertTriangle } from 'lucide-react';

const statusLabel = {
  ALLOWED: 'Allowed', BLOCKED: 'Blocked', KILLED: 'Killed',
  PENDING: 'Pending', APPROVED: 'Approved', DENIED: 'Denied', TIMEOUT: 'Timeout',
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const [logs, setLogs] = useState([]);
  const [allLogs, setAllLogs] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const [s, a, l, p] = await Promise.all([
        fetchStats(), fetchAgents(), fetchAllLogs(), fetchPendingApprovals(),
      ]);
      setStats(s);
      setAgents(a);
      setAllLogs(l);
      setLogs(l.slice(0, 10));
      setPendingCount(p.length);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-8 space-y-6 sm:space-y-8">
      {/* Pending approvals alert */}
      {pendingCount > 0 && (
        <Link
          to="/approvals"
          className="flex items-center gap-3 p-4 rounded-lg bg-caution-bg border border-caution/20 hover:border-caution/40 transition-colors"
        >
          <AlertTriangle className="w-5 h-5 text-caution shrink-0" />
          <span className="text-sm font-medium text-ink">
            {pendingCount} pending approval{pendingCount > 1 ? 's' : ''} require your attention
          </span>
          <ArrowRight className="w-4 h-4 text-ink-faint ml-auto shrink-0" />
        </Link>
      )}

      {/* Dark stat cards */}
      <DashboardStatCards stats={stats} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 sm:gap-8">
        <div className="lg:col-span-2 rounded-lg border border-divider bg-surface p-5">
          <h2 className="text-lg font-bold text-ink mb-4">Firewall decisions</h2>
          <div className="h-44">
            <FirewallDonut logs={allLogs} />
          </div>
        </div>
        <div className="lg:col-span-3 rounded-lg border border-divider bg-surface p-5">
          <h2 className="text-lg font-bold text-ink mb-4">Activity over time</h2>
          <div className="h-44">
            <ActivityTimeline logs={allLogs} />
          </div>
        </div>
      </div>

      {/* Two columns: agents + activity */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 sm:gap-8">
        {/* Agents overview */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-ink">Agents</h2>
            <Link to="/agents" className="text-sm text-accent font-medium hover:underline">
              View all
            </Link>
          </div>
          <div className="rounded-lg border border-divider bg-surface overflow-hidden divide-y divide-divider">
            {agents.map((agent) => {
              const isPaused = agent.status === 'PAUSED';
              return (
                <Link
                  key={agent.name}
                  to={`/agents/${encodeURIComponent(agent.name)}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-surface-hover transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-ink truncate">{agent.name}</span>
                      <span className={`w-2 h-2 rounded-full shrink-0 ${
                        isPaused ? 'bg-negative' : 'bg-positive'
                      }`} />
                    </div>
                    <p className="text-xs text-ink-faint mt-0.5">{agent.owner}</p>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <p className="text-sm font-semibold text-ink tabular-nums">{agent.total_logs} actions</p>
                    <p className="text-xs text-ink-faint tabular-nums">
                      {agent.risk_score}% risk
                    </p>
                  </div>
                </Link>
              );
            })}
            {agents.length === 0 && (
              <div className="px-5 py-8 text-center">
                <p className="text-sm text-ink-faint">No agents registered yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent activity */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-ink">Recent activity</h2>
            <Link to="/activity" className="text-sm text-accent font-medium hover:underline">
              View all
            </Link>
          </div>
          <div className="rounded-lg border border-divider bg-surface overflow-hidden divide-y divide-divider">
            {logs.map((entry) => {
              const isPositive = entry.status === 'ALLOWED' || entry.status === 'APPROVED';
              const isPending = entry.status === 'PENDING';
              return (
                <div key={entry.id} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${
                      isPositive ? 'bg-positive' : isPending ? 'bg-caution' : 'bg-negative'
                    }`} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink truncate">{entry.action}</p>
                      <p className="text-xs text-ink-faint">{entry.agent_name}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-semibold shrink-0 ml-2 ${
                    isPositive ? 'text-positive' : isPending ? 'text-caution' : 'text-negative'
                  }`}>
                    {statusLabel[entry.status] || entry.status}
                  </span>
                </div>
              );
            })}
            {logs.length === 0 && (
              <div className="px-5 py-8 text-center">
                <p className="text-sm text-ink-faint">No activity yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
