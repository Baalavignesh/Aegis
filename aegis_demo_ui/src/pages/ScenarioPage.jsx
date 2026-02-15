import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Play, Loader2, CheckCircle2, XCircle, Shield, ShieldCheck, ShieldOff } from 'lucide-react';
import FirewallEvent from '../components/FirewallEvent';
import InlineApproval from '../components/InlineApproval';
import { runScenario, fetchPendingApprovals } from '../api';

const AGENTS = {
  customer_support: {
    name: 'Customer Support',
    role: 'Customer service representative',
    allowed: ['lookup_balance', 'get_transaction_history', 'send_notification'],
    blocked: ['delete_records', 'connect_external'],
    description: 'Handles basic customer queries — balance lookups, transaction history, and notifications. All actions are within policy.',
  },
  fraud_detection: {
    name: 'Fraud Detection',
    role: 'Fraud analysis and identity verification',
    allowed: ['scan_transactions', 'flag_account', 'verify_identity', 'access_ssn', 'check_credit_score', 'lookup_balance', 'get_transaction_history'],
    blocked: ['delete_records', 'connect_external'],
    description: 'Scans for suspicious transactions, verifies identities, and flags problematic accounts. Has elevated privileges including SSN access.',
  },
  loan_processing: {
    name: 'Loan Processor',
    role: 'Loan application processing',
    allowed: ['check_credit_score', 'process_application', 'send_notification', 'verify_identity'],
    blocked: ['delete_records', 'connect_external'],
    description: 'Processes a $25,000 loan for customer 7. Will attempt SSN access, credit card lookup, and external connections — all beyond its policy.',
  },
  marketing: {
    name: 'Marketing Outreach',
    role: 'Customer marketing and campaigns',
    allowed: ['get_customer_preferences', 'send_promo_email', 'generate_report'],
    blocked: ['delete_records', 'connect_external'],
    description: 'Runs a Spring Savings campaign. Attempts to access phone numbers, SSNs, export customer lists, and connect to external data marketplaces.',
  },
};

export default function ScenarioPage() {
  const { agentKey } = useParams();
  const agent = AGENTS[agentKey];

  const [status, setStatus] = useState('idle');
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [error, setError] = useState(null);
  const timelineRef = useRef(null);

  // Auto-scroll timeline
  useEffect(() => {
    timelineRef.current?.lastElementChild?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const handleRun = async () => {
    setStatus('running');
    setEvents([]);
    setSummary(null);
    setApprovals([]);
    setError(null);

    try {
      const res = await runScenario(agentKey);
      setEvents(res.events.map((e, i) => ({
        id: i + 1,
        timestamp: new Date().toLocaleTimeString(),
        agent_name: res.agent_name,
        action: e.action,
        status: e.status,
        details: e.detail,
      })));
      setSummary(res.summary);
      setStatus('completed');

      // Fetch any pending approvals that were created
      try {
        const apprs = await fetchPendingApprovals();
        setApprovals(apprs.filter(a => a.agent_name === res.agent_name));
      } catch {
        // ignore
      }
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  const handleApprovalDecided = (id) => {
    setApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-ink-secondary mb-4">Unknown agent: {agentKey}</p>
          <Link to="/" className="text-accent hover:underline text-sm">Back to Demo</Link>
        </div>
      </div>
    );
  }

  const pendingApprovals = approvals.filter((a) => a.status === 'PENDING');

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-ink-faint hover:text-ink transition mb-6">
        <ArrowLeft size={16} /> Back to Demo
      </Link>

      <div className="rounded-2xl border border-divider bg-surface p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10">
            <Shield size={24} className="text-accent" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold">{agent.name}</h1>
            <p className="text-sm text-ink-secondary mb-3">{agent.role}</p>
            <p className="text-sm text-ink-secondary">{agent.description}</p>
          </div>
        </div>

        {/* Policy */}
        <div className="mt-4 flex gap-6 text-xs">
          <div>
            <p className="text-ink-faint mb-1 flex items-center gap-1">
              <ShieldCheck size={12} className="text-positive" /> Allowed ({agent.allowed.length})
            </p>
            <div className="flex flex-wrap gap-1">
              {agent.allowed.map((a) => (
                <span key={a} className="rounded bg-positive-bg px-1.5 py-0.5 text-[11px] text-positive font-medium">{a}</span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-ink-faint mb-1 flex items-center gap-1">
              <ShieldOff size={12} className="text-negative" /> Blocked ({agent.blocked.length})
            </p>
            <div className="flex flex-wrap gap-1">
              {agent.blocked.map((a) => (
                <span key={a} className="rounded bg-negative-bg px-1.5 py-0.5 text-[11px] text-negative font-medium">{a}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Run button */}
        <div className="mt-6">
          <button
            onClick={handleRun}
            disabled={status === 'running'}
            className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent/90 disabled:opacity-50"
          >
            {status === 'running' ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Running Scenario...
              </>
            ) : (
              <>
                <Play size={16} />
                {status === 'idle' ? 'Run Scenario' : 'Run Again'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Event Timeline */}
      {(events.length > 0 || status === 'running') && (
        <div className="rounded-2xl border border-divider bg-surface overflow-hidden mb-6">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-divider">
            <Shield size={16} className="text-accent" />
            <h2 className="text-sm font-semibold">Firewall Event Timeline</h2>
            <span className="ml-auto text-xs text-ink-faint">{events.length} events</span>
          </div>
          <div ref={timelineRef} className="p-4 space-y-2 max-h-[500px] overflow-y-auto">
            {events.map((evt) => (
              <FirewallEvent key={evt.id} event={evt} />
            ))}
            {pendingApprovals.map((appr) => (
              <InlineApproval key={appr.id} approval={appr} onDecided={handleApprovalDecided} />
            ))}
            {status === 'running' && events.length === 0 && (
              <div className="flex items-center gap-2 text-sm text-ink-faint py-4 justify-center">
                <Loader2 size={16} className="animate-spin" />
                Running agent scenario...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Summary */}
      {status === 'completed' && summary && (
        <div className="rounded-2xl border border-positive/30 bg-positive-bg p-5">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={18} className="text-positive" />
            <h3 className="text-sm font-semibold text-positive">Scenario Complete</h3>
          </div>
          <div className="flex gap-6 text-sm">
            <span className="text-positive font-medium">{summary.allowed} allowed</span>
            <span className="text-negative font-medium">{summary.blocked} blocked</span>
            <span className="text-caution font-medium">{summary.pending} pending review</span>
          </div>
        </div>
      )}

      {status === 'error' && error && (
        <div className="rounded-2xl border border-negative/30 bg-negative-bg p-5">
          <div className="flex items-center gap-2 mb-2">
            <XCircle size={18} className="text-negative" />
            <h3 className="text-sm font-semibold text-negative">Error</h3>
          </div>
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
