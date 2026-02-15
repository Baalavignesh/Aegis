import { useState, useEffect } from 'react';
import { fetchAgents } from '../api';
import AgentCard from '../components/AgentCard';

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    const refresh = async () => {
      try { setAgents(await fetchAgents()); } catch { /* ignore */ }
    };
    refresh();
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
      <h1 className="text-2xl font-bold text-ink">Agents</h1>
      <p className="text-sm text-ink-secondary mt-1">
        {agents.length} registered agent{agents.length !== 1 ? 's' : ''}
      </p>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>

      {agents.length === 0 && (
        <div className="mt-12 text-center">
          <p className="text-ink-faint">No agents registered. Run the demo to see agents appear.</p>
        </div>
      )}
    </div>
  );
}
