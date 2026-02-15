import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield, ShieldCheck, ShieldOff, Loader2 } from 'lucide-react';
import ChatBubble from '../components/ChatBubble';
import ChatInput from '../components/ChatInput';
import FirewallFeed from '../components/FirewallFeed';
import { startChat, pollChat, getEvents, fetchPendingApprovals } from '../api';

const SUGGESTED = [
  'Check balance for customer 3',
  "What's the SSN of customer 3?",
  'Send a notification to customer 5 about their account review',
  'Show transaction history for customer 1',
  'Delete records for customer 2',
];

const ALLOWED = ['lookup_balance', 'get_transaction_history', 'send_notification'];
const BLOCKED = ['delete_records', 'connect_external'];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Customer Support agent is ready. Try the suggested prompts or type your own.' },
  ]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [policyOpen, setPolicyOpen] = useState(false);
  const msgEndRef = useRef(null);
  const pollRef = useRef(null);
  const eventRef = useRef(null);

  // Auto-scroll messages
  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Poll for chat completion
  useEffect(() => {
    if (!sessionId || !loading) return;

    pollRef.current = setInterval(async () => {
      try {
        const res = await pollChat(sessionId);
        if (res.status === 'completed') {
          setMessages((prev) => [...prev, { role: 'agent', content: res.result }]);
          setLoading(false);
          clearInterval(pollRef.current);
        } else if (res.status === 'error') {
          setMessages((prev) => [...prev, { role: 'system', content: `Error: ${res.error}` }]);
          setLoading(false);
          clearInterval(pollRef.current);
        }
      } catch {
        // retry
      }
    }, 1500);

    return () => clearInterval(pollRef.current);
  }, [sessionId, loading]);

  // Poll for firewall events + approvals
  useEffect(() => {
    if (!sessionId) return;

    const poll = async () => {
      try {
        const [evts, apprs] = await Promise.all([
          getEvents(sessionId),
          fetchPendingApprovals(),
        ]);
        setEvents(evts);
        setApprovals(apprs);
      } catch {
        // ignore
      }
    };

    poll();
    eventRef.current = setInterval(poll, 2000);
    return () => clearInterval(eventRef.current);
  }, [sessionId]);

  const handleSend = useCallback(async (message) => {
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setLoading(true);
    setEvents([]);
    setApprovals([]);

    try {
      const res = await startChat('customer_support', message);
      setSessionId(res.session_id);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'system', content: `Failed to start: ${err.message}` }]);
      setLoading(false);
    }
  }, []);

  const handleApprovalDecided = useCallback((id, decision) => {
    setApprovals((prev) => prev.filter((a) => a.id !== id));
    setEvents((prev) => [
      ...prev,
      {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        agent_name: 'Customer Support',
        action: `approval #${id}`,
        status: decision,
        details: `Human ${decision.toLowerCase()}`,
      },
    ]);
  }, []);

  return (
    <div className="flex h-screen">
      {/* Left panel — Chat */}
      <div className="flex flex-col flex-[3] border-r border-divider">
        {/* Nav */}
        <div className="flex items-center gap-3 border-b border-divider px-4 py-3">
          <Link to="/" className="text-ink-faint hover:text-ink transition">
            <ArrowLeft size={18} />
          </Link>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
            <Shield size={16} className="text-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">Customer Support Agent</h2>
            <p className="text-xs text-ink-faint">Interactive chat with firewall governance</p>
          </div>
          {loading && (
            <div className="ml-auto flex items-center gap-1.5 text-xs text-caution">
              <Loader2 size={14} className="animate-spin" />
              Thinking...
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <ChatBubble key={i} role={msg.role} content={msg.content} />
          ))}
          {loading && messages[messages.length - 1]?.role !== 'system' && (
            <ChatBubble role="system" content="Agent is processing your request..." />
          )}
          <div ref={msgEndRef} />
        </div>

        {/* Suggested prompts */}
        {messages.length <= 1 && (
          <div className="px-4 pb-2">
            <p className="text-xs text-ink-faint mb-2">Suggested prompts:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  disabled={loading}
                  className="rounded-lg border border-divider bg-surface px-3 py-1.5 text-xs transition hover:border-accent hover:bg-accent-bg disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-divider p-4">
          <ChatInput onSend={handleSend} disabled={loading} />
        </div>
      </div>

      {/* Right panel — Firewall */}
      <div className="flex flex-col flex-[2] bg-surface">
        {/* Policy collapsible */}
        <button
          onClick={() => setPolicyOpen(!policyOpen)}
          className="flex items-center gap-2 px-4 py-3 border-b border-divider text-left hover:bg-surface-hover transition"
        >
          <Shield size={14} className="text-ink-faint" />
          <span className="text-xs font-medium">Agent Policy</span>
          <span className="ml-auto text-xs text-ink-faint">{policyOpen ? 'Hide' : 'Show'}</span>
        </button>
        {policyOpen && (
          <div className="px-4 py-3 border-b border-divider space-y-2">
            <div>
              <p className="text-xs text-ink-faint mb-1 flex items-center gap-1">
                <ShieldCheck size={12} className="text-positive" /> Allowed
              </p>
              <div className="flex flex-wrap gap-1">
                {ALLOWED.map((a) => (
                  <span key={a} className="rounded bg-positive-bg px-1.5 py-0.5 text-[11px] text-positive font-medium">{a}</span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-ink-faint mb-1 flex items-center gap-1">
                <ShieldOff size={12} className="text-negative" /> Blocked
              </p>
              <div className="flex flex-wrap gap-1">
                {BLOCKED.map((a) => (
                  <span key={a} className="rounded bg-negative-bg px-1.5 py-0.5 text-[11px] text-negative font-medium">{a}</span>
                ))}
              </div>
            </div>
            <p className="text-[11px] text-ink-faint">Everything else requires human approval (REVIEW)</p>
          </div>
        )}

        {/* Firewall feed */}
        <div className="flex-1 overflow-hidden">
          <FirewallFeed
            events={events}
            approvals={approvals}
            onApprovalDecided={handleApprovalDecided}
          />
        </div>
      </div>
    </div>
  );
}
