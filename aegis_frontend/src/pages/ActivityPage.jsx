import { useState, useEffect } from 'react';
import { fetchAllLogs, fetchAgentLogs, fetchAgents } from '../api';
import LiveFeed from '../components/LiveFeed';

export default function ActivityPage() {
  const [logs, setLogs] = useState([]);
  const [agents, setAgents] = useState([]);
  const [filterAgent, setFilterAgent] = useState('');

  useEffect(() => {
    fetchAgents().then(setAgents).catch(() => {});
  }, []);

  useEffect(() => {
    const refresh = async () => {
      try {
        const data = filterAgent
          ? await fetchAgentLogs(filterAgent)
          : await fetchAllLogs();
        setLogs(data);
      } catch { /* ignore */ }
    };
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, [filterAgent]);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink">Activity</h1>
          <p className="text-sm text-ink-secondary mt-1">Real-time audit log</p>
        </div>

        <select
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
          className="border border-divider rounded-lg px-3 py-2 text-sm text-ink bg-surface focus:outline-none focus:border-divider-dark appearance-none cursor-pointer"
        >
          <option value="">All agents</option>
          {agents.map((a) => (
            <option key={a.name} value={a.name}>{a.name}</option>
          ))}
        </select>
      </div>

      <div className="border border-divider rounded-lg overflow-hidden">
        <LiveFeed logs={logs} agentName={filterAgent || null} fullHeight />
      </div>
    </div>
  );
}
