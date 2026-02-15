import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchAgents, fetchAgentLogs, fetchAgentPolicies, toggleAgent } from '../api';
import AgentProfile from '../components/AgentProfile';
import ToolsList from '../components/ToolsList';
import LiveFeed from '../components/LiveFeed';
import { ChevronLeft } from 'lucide-react';

export default function AgentDetailPage() {
  const { name } = useParams();
  const decodedName = decodeURIComponent(name);
  const [agent, setAgent] = useState(null);
  const [logs, setLogs] = useState([]);
  const [policies, setPolicies] = useState(null);

  const refreshAgent = useCallback(async () => {
    try {
      const agents = await fetchAgents();
      setAgent(agents.find((a) => a.name === decodedName) || null);
    } catch { /* ignore */ }
  }, [decodedName]);

  useEffect(() => {
    refreshAgent();
    const interval = setInterval(refreshAgent, 2000);
    return () => clearInterval(interval);
  }, [refreshAgent]);

  useEffect(() => {
    const refreshLogs = async () => {
      try { setLogs(await fetchAgentLogs(decodedName)); } catch { /* ignore */ }
    };
    refreshLogs();
    const interval = setInterval(refreshLogs, 2000);
    return () => clearInterval(interval);
  }, [decodedName]);

  useEffect(() => {
    fetchAgentPolicies(decodedName).then(setPolicies).catch(() => {});
  }, [decodedName]);

  const handleToggle = async (agentName, newStatus) => {
    await toggleAgent(agentName, newStatus);
    await refreshAgent();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
      {/* Back link */}
      <Link
        to="/agents"
        className="inline-flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors mb-6"
      >
        <ChevronLeft className="w-4 h-4" />
        Agents
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 sm:gap-8">
        {/* Left: Profile + Tools */}
        <div className="lg:col-span-3 space-y-6">
          <AgentProfile agent={agent} onToggle={handleToggle} />
          <ToolsList policies={policies} />
        </div>

        {/* Right: Activity feed */}
        <div className="lg:col-span-2">
          <div className="border border-divider rounded-lg overflow-hidden lg:sticky lg:top-24">
            <LiveFeed logs={logs} agentName={decodedName} />
          </div>
        </div>
      </div>
    </div>
  );
}
