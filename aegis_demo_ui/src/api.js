const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const seedDemo = () => request('POST', '/demo/seed');

export const startChat = (agentKey, message) =>
  request('POST', '/demo/chat', { agent_key: agentKey, message });

export const pollChat = (sessionId) =>
  request('GET', `/demo/chat/${sessionId}`);

export const getEvents = (sessionId) =>
  request('GET', `/demo/events/${sessionId}`);

export const fetchPendingApprovals = () =>
  request('GET', '/approvals/pending');

export const decideApproval = (id, decision) =>
  request('POST', `/approvals/${id}/decide`, { decision });
