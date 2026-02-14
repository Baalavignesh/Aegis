import { useState, useEffect, useCallback } from 'react';
import {
  fetchStats,
  fetchAgents,
  fetchAgentLogs,
  fetchAgentPolicies,
  fetchPendingApprovals,
  toggleAgent,
  decideApproval,
} from './api';
import Sidebar from './components/Sidebar';
import StatsCards from './components/StatsCards';
import AgentProfile from './components/AgentProfile';
import LiveFeed from './components/LiveFeed';
import ToolsList from './components/ToolsList';
import ApprovalBanner from './components/ApprovalBanner';

export default function App() {
  const [stats, setStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [logs, setLogs] = useState([]);
  const [policies, setPolicies] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [error, setError] = useState(null);

  // ── Fetch stats, agents & pending approvals ─────────────────────
  const refreshData = useCallback(async () => {
    try {
      const [s, a, p] = await Promise.all([
        fetchStats(),
        fetchAgents(),
        fetchPendingApprovals(),
      ]);
      setStats(s);
      setAgents(a);
      setPendingApprovals(p);
      setError(null);
    } catch (err) {
      setError('Cannot connect to backend. Is uvicorn running on :8000?');
    }
  }, []);

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 2000);
    return () => clearInterval(interval);
  }, [refreshData]);

  // ── Fetch logs for selected agent (2s polling) ──────────────────
  useEffect(() => {
    if (!selectedAgent) {
      setLogs([]);
      return;
    }

    const fetchLogs = async () => {
      try {
        const data = await fetchAgentLogs(selectedAgent);
        setLogs(data);
      } catch { /* ignore */ }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [selectedAgent]);

  // ── Fetch policies for selected agent ───────────────────────────
  useEffect(() => {
    if (!selectedAgent) {
      setPolicies(null);
      return;
    }

    const fetchPolicies = async () => {
      try {
        const data = await fetchAgentPolicies(selectedAgent);
        setPolicies(data);
      } catch { /* ignore */ }
    };

    fetchPolicies();
  }, [selectedAgent]);

  // ── Auto-select first agent ─────────────────────────────────────
  useEffect(() => {
    if (!selectedAgent && agents.length > 0) {
      setSelectedAgent(agents[0].name);
    }
  }, [agents, selectedAgent]);

  // ── Handlers ────────────────────────────────────────────────────
  const handleToggle = async (name, newStatus) => {
    await toggleAgent(name, newStatus);
    await refreshData();
  };

  const handleDecide = async (approvalId, decision) => {
    await decideApproval(approvalId, decision);
    await refreshData();
  };

  const currentAgent = agents.find((a) => a.name === selectedAgent) || null;

  // ── Error screen ────────────────────────────────────────────────
  if (error && agents.length === 0) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center p-8 rounded-xl border border-neon-red/30 bg-neon-red/5 max-w-md">
          <p className="text-neon-red font-mono text-sm">{error}</p>
          <p className="text-text-dim text-xs mt-3">
            Run: <code className="text-neon-amber">uvicorn backend:app --reload</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-bg-primary">
      {/* Sidebar */}
      <Sidebar
        agents={agents}
        selected={selectedAgent}
        onSelect={setSelectedAgent}
      />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Header */}
        <header className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Dashboard</h2>
            <p className="text-xs text-text-dim font-mono">Real-time agent monitoring</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse-glow" />
            <span className="text-xs text-text-dim font-mono">System Online</span>
          </div>
        </header>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Pending Approvals Banner (top, always visible) */}
          <ApprovalBanner approvals={pendingApprovals} onDecide={handleDecide} />

          {/* Stats row */}
          <StatsCards stats={stats} />

          {/* Agent Profile + Tools */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Left: Agent profile + Tools (2 cols) */}
            <div className="lg:col-span-2 space-y-6">
              <AgentProfile agent={currentAgent} onToggle={handleToggle} />
              <ToolsList policies={policies} />
            </div>

            {/* Right: Live feed (3 cols) */}
            <div className="lg:col-span-3 min-h-[500px]">
              <LiveFeed logs={logs} agentName={selectedAgent} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
