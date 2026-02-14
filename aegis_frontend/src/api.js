const API_BASE = 'http://localhost:8000';

export async function fetchStats() {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
}

export async function fetchAgents() {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) throw new Error('Failed to fetch agents');
    return res.json();
}

export async function fetchAgentLogs(name) {
    const res = await fetch(`${API_BASE}/agents/${encodeURIComponent(name)}/logs`);
    if (!res.ok) throw new Error('Failed to fetch logs');
    return res.json();
}

export async function fetchAgentPolicies(name) {
    const res = await fetch(`${API_BASE}/agents/${encodeURIComponent(name)}/policies`);
    if (!res.ok) throw new Error('Failed to fetch policies');
    return res.json();
}

export async function fetchPendingApprovals() {
    const res = await fetch(`${API_BASE}/approvals/pending`);
    if (!res.ok) throw new Error('Failed to fetch approvals');
    return res.json();
}

export async function toggleAgent(name, status) {
    const res = await fetch(`${API_BASE}/agents/${encodeURIComponent(name)}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error('Failed to toggle agent');
    return res.json();
}

export async function decideApproval(approvalId, decision) {
    const res = await fetch(`${API_BASE}/approvals/${approvalId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
    });
    if (!res.ok) throw new Error('Failed to submit decision');
    return res.json();
}
