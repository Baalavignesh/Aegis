# Aegis — AI Agent Governance Platform

**A firewall and observability layer for autonomous AI agents.**

Aegis intercepts every tool call an AI agent makes, validates it against a developer-defined policy, and logs the decision — before the action ever executes. If the action is unauthorized, it's blocked. If it's unknown, it's held for human review. If the agent goes rogue, a kill-switch shuts it down instantly.

> Think of it as **Cloudflare for AI Agents** — outbound policy enforcement, governance, and real-time audit for any autonomous system.

---

## The Problem

AI agents (LangChain, LangGraph, CrewAI, AutoGen) are increasingly autonomous. They call APIs, access databases, read files, and make decisions on their own. But there's no standardized way to:

- **See** what an agent is doing in real time
- **Control** what actions an agent is allowed to take
- **Stop** an agent when it deviates from expected behavior
- **Audit** every decision an agent made after the fact

LLMs are unpredictable. An agent given access to 17 banking tools will try to use whichever ones it thinks are helpful — including accessing SSNs, deleting records, or connecting to external servers — if nothing stops it. Prompt injection attacks can trick agents into calling tools they shouldn't. Autonomous reasoning can lead agents to escalate their own privileges ("I should verify the SSN to be thorough").

Companies deploying agents today are essentially flying blind. Aegis fixes that.

---

## How Aegis Works

### The Three-Tier Security Model

Every agent action is evaluated against a policy with three possible outcomes:

| Tier | Who decides? | Can it execute? | Use case |
|------|-------------|-----------------|----------|
| **ALLOW** | Pre-approved by developer | Always | Vetted, safe actions |
| **REVIEW** | Human reviewer (dashboard) | Only if approved | Unknown/undeclared actions |
| **BLOCK** | Pre-denied by developer | Never | Known-dangerous actions |

The developer defines a **whitelist** of allowed actions. Everything not on the list goes to **REVIEW** (human approval on the dashboard). Known-dangerous actions like `delete_records` are hard-**BLOCKED** — no human can accidentally approve them.

```
Agent tries to call a tool
        │
   In allowed_actions? ──── YES ──→ ALLOWED (execute + log)
        │ NO
   In blocked_actions? ──── YES ──→ BLOCKED (hard deny, logged, alert)
        │ NO
   Unknown action ─────────────────→ REVIEW (held for human approval on dashboard)
```

### Key Design: All Tools, Policy as Gatekeeper

Every agent receives access to **all tools** in the platform. The LLM knows they exist and can attempt to call any of them. **Aegis policy is the only enforcement layer** — not tool availability.

This mirrors real-world security: an employee can see all the doors in the building, but company policy controls which rooms they can enter. The tool registry and the security policy are separate concerns managed by different teams.

```python
# Customer Support agent — knows about all 17 tools, allowed to use 3
DECORATOR = {
    "allowed_actions": ["lookup_balance", "get_transaction_history", "send_notification"],
    "blocked_actions": ["delete_records", "connect_external"],
}
# access_ssn, access_credit_card, export_customer_list, etc. → REVIEW
```

### Context-Based Policy Enforcement

The same tool behaves differently depending on which agent calls it:

```python
# Same tool, different agents, different outcomes
access_ssn(customer_id=3)

# Under Customer Support → REVIEW (not in allowed list)
# Under Fraud Detection  → ALLOWED (SSN access is in its allowed list)
```

This is powered by Python's `contextvars` — shared tools resolve the correct agent's policy at call time.

---

## Approach: SDK-First Integration

Aegis is designed as a **Python SDK** (`sentinel-guardrails`) that integrates into existing agent code with two decorators and a context manager. No infrastructure changes, no proxy servers, no config files — just `pip install` and annotate.

```python
from sentinel import agent, monitor, agent_context

# 1. Register agent with policy (persisted to MongoDB)
@agent("SupportBot", owner="alice", allows=["lookup_balance"], blocks=["delete_records"])
class SupportBot: pass

# 2. Wrap any tool with firewall enforcement
@monitor
def lookup_balance(customer_id: int) -> str:
    return db.query(f"SELECT balance FROM accounts WHERE customer_id = {customer_id}")

# 3. Use tools under an agent's identity
with agent_context("SupportBot"):
    lookup_balance(42)      # ALLOWED — logged
    delete_records("tmp")   # BLOCKED — logged, alert fired, function never executes
```

The SDK polls MongoDB on every call — no caching. Policy changes (including kill-switch) take effect immediately. Every decision is logged to an audit trail.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **SDK** | Python 3.10+, pymongo, `contextvars` | `@agent` and `@monitor` decorators, policy enforcement, audit logging |
| **Backend** | FastAPI, pymongo | REST API for dashboard (8 endpoints), reads from shared MongoDB |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Lucide icons, Motion | Real-time governance dashboard with 5 pages |
| **Database** | MongoDB Atlas | Agents, policies, audit log, pending approvals, demo bank data |
| **Demo Agents** | LangChain, LangGraph, Google Gemini | 4 banking agents demonstrating firewall governance |
| **Infra** | Docker, Docker Compose | Containerized deployment of backend + frontend |

---

## Work Completed

### SDK (`aegis_sdk/`) — `sentinel-guardrails`
- `@agent` decorator — registers agent + policies to MongoDB at import time
- `@monitor` decorator — wraps any function with the firewall; queries MongoDB on every call
- `agent_context()` — `contextvars`-based context manager for multi-agent shared tools
- Three-tier firewall logic: ALLOW → BLOCK → REVIEW with human-in-the-loop approval flow
- Kill-switch: `kill_agent()` / `revive_agent()` — instantly pauses/resumes all agent actions
- Full audit logging — every decision (ALLOWED/BLOCKED/KILLED/REVIEW) persisted with timestamps
- CLI commands: `sentinel kill <name>`, `sentinel revive <name>`, `sentinel log <name>`
- Approval system — `create_approval()`, `wait_for_approval()`, `decide_approval()` with timeout

### Backend (`aegis_backend/`) — FastAPI API
- 8 REST endpoints powering the dashboard (no `/api/` prefix)
- `GET /stats` — aggregate platform stats (agents, blocks in 24h, pending approvals, risk level)
- `GET /agents` — all agents with computed risk scores, action counts, status
- `GET /agents/{name}/logs` — per-agent audit log (last 50 entries)
- `GET /agents/{name}/policies` — agent's allowed/blocked/review action lists
- `POST /agents/{name}/toggle` — kill-switch toggle (ACTIVE ↔ PAUSED)
- `GET /logs` — global audit log across all agents
- `GET /approvals/pending` — pending human approval requests
- `POST /approvals/{id}/decide` — approve or deny with APPROVED/DENIED
- CORS enabled for frontend communication
- Shared MongoDB with SDK — reads the same collections the agents write to

### Frontend (`aegis_frontend/`) — React Dashboard
- **Dashboard** (`/`) — overview with stats cards, agent list, recent activity feed, approval alerts
- **Agents** (`/agents`) — responsive grid of all agents with status badges, risk scores, action counts
- **Agent Detail** (`/agents/:name`) — profile header with kill-switch toggle, policy/tools display, live feed
- **Activity** (`/activity`) — full audit log with agent filter dropdown, real-time 2s polling
- **Approvals** (`/approvals`) — human-in-the-loop queue with approve/deny buttons per pending action
- Robinhood-inspired design: clean white backgrounds, Inter font, green/red status colors
- Configurable API URL via `VITE_API_URL` environment variable

### Demo (`aegis_demo/`) — 4 LangChain Agents
- **Customer Support** — well-behaved agent; 3 allowed actions out of 17 tools
- **Fraud Detection** — elevated privileges; SSN access allowed (contrast with Customer Support)
- **Loan Processor** — over-reaching; LLM autonomously attempts tools beyond its policy
- **Marketing Outreach** — over-reaching; undeclared `export_customer_list` triggers REVIEW
- All agents receive **all 17 tools** — Aegis policy is the only enforcement layer
- 17 shared banking tools querying MongoDB (balances, transactions, SSN, credit cards, notifications, reports)
- Seeded bank database: 10 customers, ~13 accounts, ~80 transactions with realistic fake data
- Kill-switch demo: pauses and revives an agent, shows audit trail
- Summary dashboard: per-agent and aggregate stats (allowed/blocked/review/killed counts)

### Database (MongoDB)
- **agents** — name (unique), status (ACTIVE/PAUSED), owner, created_at
- **policies** — agent_name, action, rule_type (ALLOW/BLOCK/REVIEW); unique on (agent_name, action)
- **audit_log** — sequential ID, timestamp, agent_name, action, status, details
- **pending_approvals** — approval queue with status tracking and timestamps
- **counters** — auto-increment ID generation
- **customers, accounts, transactions** — demo bank data

---

## Quick Start

```bash
# 1. Install the SDK
cd aegis_sdk && pip install -e . && cd ..

# 2. Install demo dependencies
cd aegis_demo && pip install -r requirements.txt && cd ..

# 3. Configure environment
cp aegis_demo/.env.example aegis_demo/.env
# Edit .env — add GOOGLE_API_KEY and MONGO_URI (or use defaults for local MongoDB)

# 4. Run the demo (registers agents, runs 4 scenarios, seeds governance data in MongoDB)
python -m aegis_demo

# 5. Start the backend API
cd aegis_backend && pip install -r requirements.txt
uvicorn backend:app --reload --port 8000

# 6. Start the frontend dashboard
cd aegis_frontend && npm install
npm run dev    # http://localhost:5173
```

### Environment Variables

| Variable | Where | Default | Description |
|----------|-------|---------|-------------|
| `GOOGLE_API_KEY` | Demo `.env` | — | Google Gemini API key (required for demo) |
| `GEMINI_MODEL` | Demo `.env` | `gemini-2.5-flash-lite` | Gemini model to use |
| `MONGO_URI` | SDK/Backend/Demo | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | SDK/Backend/Demo | `sentinel_db` | MongoDB database name |
| `VITE_API_URL` | Frontend `.env` | `http://localhost:8000` | Backend API base URL |

---

## Future Improvements

### Agent Manifest Generation (AgentBOM)
Auto-generate an `agent_manifest.json` from decorator data across the codebase — an Agent Bill of Materials. Documents every agent's identity, capabilities, tools, data access, permissions, and dependencies. Serves as audit-ready documentation and a single source of truth.

### Governance Rule Engine
YAML-configurable rules scanned against agent manifests (e.g., "any agent accessing PII must have human approval"). Violations surface on the dashboard with severity levels. An LLM layer enriches each flag with contextual risk explanations.

### Policy Learning from REVIEW Events
"Promote to BLOCK" / "Promote to ALLOW" buttons on the approval queue. Over time, the REVIEW tier shrinks as the security team confirms which actions are safe and which are dangerous. The policy evolves from incident data, not guesswork.

### Multi-Agent Dependency Graph
Interactive visualization mapping agent-to-agent dependencies, shared tools, and data flows. Click any agent to trace what it calls, what calls it, and what data flows through it.

### Analytics Timeline & Violation Breakdown
Time-series charts showing agent behavior trends, violation breakdowns, and anomaly detection. Enables compliance reporting and historical analysis.

### Content Inspection (DLP Layer)
Current enforcement is at the **tool level** — which function is called. A future DLP layer would inspect **arguments and return values** for sensitive data patterns (SSN, credit card numbers) even through allowed tools. This catches data exfiltration through legitimate channels.

### WebSocket Real-Time Events
Replace 2-second polling with persistent WebSocket connections for instant push updates on activity, alerts, and governance violations.

### Export & Compliance Reports
One-click export of audit trails, agent manifests, and fact sheets as YAML/Markdown/PDF for SOC2, GDPR, and HIPAA compliance.

### Multi-Language SDK Support
Current SDK is Python-only. Future versions would add TypeScript/JavaScript, Go, and Java SDKs, plus a language-agnostic HTTP proxy mode for any runtime.

---

## Project Structure

```
aegis/
├── aegis_sdk/                  # Python SDK (sentinel-guardrails)
│   ├── sentinel/
│   │   ├── core.py             # register_agent(), validate_action(), wait_for_approval()
│   │   ├── decorators.py       # @agent, @monitor
│   │   ├── context.py          # agent_context() via contextvars
│   │   ├── db.py               # MongoDB layer (agents, policies, audit_log, approvals)
│   │   ├── cli.py              # kill_agent(), revive_agent(), show_audit_log()
│   │   └── exceptions.py       # SentinelBlockedError, SentinelKillSwitchError
│   └── setup.py
│
├── aegis_backend/              # FastAPI server (8 REST endpoints)
│   ├── backend.py
│   └── requirements.txt
│
├── aegis_frontend/             # React dashboard (5 pages)
│   ├── src/
│   │   ├── api.js              # 8 API functions
│   │   ├── App.jsx             # Router (5 routes)
│   │   ├── index.css           # Robinhood-style theme
│   │   ├── components/         # 7 reusable components
│   │   └── pages/              # Dashboard, Agents, AgentDetail, Activity, Approvals
│   └── package.json
│
├── aegis_demo/                 # 4 LangChain + Gemini agents
│   ├── run_demo.py             # Orchestrator
│   ├── core/
│   │   ├── mock_aegis.py       # SDK ↔ LangChain adapter
│   │   └── tools.py            # 17 shared banking tools
│   ├── agents/                 # 4 agent definitions
│   └── data/
│       └── fake_data.py        # MongoDB seeder
│
├── AGENT-SENTINEL-README.md    # Full platform spec
└── README.md                   # This file
```

## Documentation

- **[AGENT-SENTINEL-README.md](AGENT-SENTINEL-README.md)** — Comprehensive platform spec: full API reference, SDK usage guide, decorator schema, firewall logic, governance rules format
- **[aegis_sdk/README.md](aegis_sdk/README.md)** — SDK API reference and usage examples
- **[aegis_demo/README.md](aegis_demo/README.md)** — Demo setup, agent policies, and expected output
- **[aegis_backend/README.md](aegis_backend/README.md)** — Backend endpoints and configuration
- **[aegis_frontend/README.md](aegis_frontend/README.md)** — Dashboard pages, design system, and API functions

## License

MIT License
