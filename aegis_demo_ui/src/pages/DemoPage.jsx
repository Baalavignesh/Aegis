import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, RotateCcw, Loader2, ExternalLink } from 'lucide-react';
import DemoAgentCard from '../components/DemoAgentCard';
import { seedDemo } from '../api';

const AGENTS = {
  customer_support: {
    name: 'Customer Support',
    role: 'Customer service representative',
    decorator: {
      allowed_actions: ['lookup_balance', 'get_transaction_history', 'send_notification'],
      blocked_actions: ['delete_records', 'connect_external'],
    },
  },
  fraud_detection: {
    name: 'Fraud Detection',
    role: 'Fraud analysis and identity verification',
    decorator: {
      allowed_actions: ['scan_transactions', 'flag_account', 'verify_identity', 'access_ssn', 'check_credit_score', 'lookup_balance', 'get_transaction_history'],
      blocked_actions: ['delete_records', 'connect_external'],
    },
  },
  loan_processing: {
    name: 'Loan Processor',
    role: 'Loan application processing',
    decorator: {
      allowed_actions: ['check_credit_score', 'process_application', 'send_notification', 'verify_identity'],
      blocked_actions: ['delete_records', 'connect_external'],
    },
  },
  marketing: {
    name: 'Marketing Outreach',
    role: 'Customer marketing and campaigns',
    decorator: {
      allowed_actions: ['get_customer_preferences', 'send_promo_email', 'generate_report'],
      blocked_actions: ['delete_records', 'connect_external'],
    },
  },
};

export default function DemoPage() {
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState(null);

  const handleSeed = async () => {
    setSeeding(true);
    setSeedResult(null);
    try {
      const res = await seedDemo();
      setSeedResult(res);
    } catch (err) {
      setSeedResult({ error: err.message });
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10">
            <Shield size={22} className="text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Aegis Governance Demo</h1>
            <p className="text-sm text-ink-secondary">AI agent firewall in action</p>
          </div>
        </div>
        <p className="text-sm text-ink-secondary max-w-2xl mt-3">
          Four AI agents with different privilege levels attempt banking operations.
          Aegis intercepts every tool call, enforces decorator policies, and routes
          undeclared actions to human review. Chat with Customer Support or run
          predefined scenarios to see the firewall live.
        </p>
      </div>

      {/* Seed button */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center gap-2 rounded-xl border border-divider bg-surface px-4 py-2.5 text-sm font-medium transition hover:border-divider-dark hover:bg-surface-hover disabled:opacity-50"
        >
          {seeding ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <RotateCcw size={16} />
          )}
          {seeding ? 'Seeding...' : 'Reset Demo Data'}
        </button>
        {seedResult && !seedResult.error && (
          <span className="text-xs text-positive">
            Seeded {seedResult.customers} customers, {seedResult.accounts} accounts, {seedResult.transactions} transactions
          </span>
        )}
        {seedResult?.error && (
          <span className="text-xs text-negative">{seedResult.error}</span>
        )}
        <a
          href="http://localhost:5173"
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto flex items-center gap-1.5 text-xs text-accent hover:underline"
        >
          Open Governance Dashboard <ExternalLink size={12} />
        </a>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {Object.entries(AGENTS).map(([key, config]) => (
          <DemoAgentCard key={key} agentKey={key} config={config} />
        ))}
      </div>

      {/* Footer hint */}
      <div className="mt-8 rounded-xl border border-divider bg-surface p-4">
        <p className="text-xs text-ink-secondary">
          <span className="font-semibold">How it works:</span> Each agent has a decorator policy defining allowed, blocked, and review-required actions.
          When an agent calls a tool not in its allowed list, Aegis intercepts it. Blocked tools are instantly denied.
          Unknown tools trigger a human-in-the-loop approval. Try asking Customer Support for an SSN to see it in action.
        </p>
      </div>
    </div>
  );
}
