# Agent Sentinel

**AI Agent Governance Platform — Monitor, Control, and Secure Autonomous Agents**

Agent Sentinel is an open-source firewall and observability layer for AI agents. It gives developers and organizations full visibility into what agents do and what they access — with the power to stop them when they deviate.

> Think of it as **Cloudflare for AI Agents** — outbound policy enforcement, governance, and audit for any autonomous system.

---

## The Problem

AI agents (LangGraph, CrewAI, AutoGen, LangChain) are increasingly autonomous. They call APIs, access databases, read files, and make decisions — but there's no standardized way to:

- **See** what an agent is doing in real time
- **Control** what actions an agent is allowed to take
- **Stop** an agent when it deviates from expected behavior
- **Audit** every decision an agent made after the fact

Companies deploying agents today are essentially flying blind. Agent Sentinel fixes that.

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    DEVELOPER / COMPANY                    │
│                                                          │
│   1. Register Agent → Gets Digital ID (AGT-0x7A3F)      │
│   2. Define Decorator → What agent CAN and CANNOT do    │
│   3. Monitor Dashboard → Watch everything in real time   │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              SENTINEL FIREWALL (SDK + Backend)            │
│                                                          │
│  ┌──────────────┐   ┌────────────────────────────────┐   │
│  │   POLICY     │   │       OUTBOUND MONITOR         │   │
│  │   ENGINE     │──►│                                │   │
│  │  (Decorator) │   │  Every tool call is intercepted │   │
│  │              │   │  and checked against policy     │   │
│  │  ✓ Allowed   │   │  before execution               │   │
│  │  ✕ Blocked   │   │                                │   │
│  │  ? Review    │   │  SDK → HTTP → Backend → MongoDB │   │
│  └──────────────┘   └────────────────────────────────┘   │
│                        │                                  │
│              ┌─────────┴─────────┐                       │
│              │   AUDIT LOG       │                       │
│              │   (Every decision │                       │
│              │    persisted)     │                       │
│              └───────────────────┘                       │
└─────────────────────────┬────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
         ✓ ALLOWED               ✕ BLOCKED
         Action executes         Action stopped
         Event logged            Alert fired
                                 Human notified
                                 Agent paused/killed
```

---

## Architecture

```
┌────────────────────┐     HTTP (httpx)     ┌──────────────────────┐
│  AI Agent + SDK    │ ──────────────────►  │  Aegis Backend       │
│  (@agent, @monitor)│                      │  (FastAPI on Vercel) │
│                    │                      │                      │
│  aegis-sentinel    │                      │  /sdk/* endpoints    │
│  Python package    │                      │  /dashboard endpoints│
└────────────────────┘                      │  /demo/seed          │
                                            │                      │
┌────────────────────┐     REST API         │  mongo.py            │
│  React Dashboard   │ ──────────────────►  │  (single DB layer)   │
│  (Vite + Tailwind) │                      └──────────┬───────────┘
└────────────────────┘                                 │ pymongo
                                                       ▼
                                            ┌──────────────────────┐
                                            │  MongoDB Atlas        │
                                            │  agents, policies,    │
                                            │  audit_log, approvals │
                                            └──────────────────────┘
```

**Key principle:** The backend is the **single entry point** to the database. The SDK communicates via HTTP — no direct MongoDB connections.

### Project Structure

```
aegis/
├── aegis_sdk/                         # Python SDK (aegis-sentinel)
│   ├── sentinel/
│   │   ├── __init__.py                # Public API exports
│   │   ├── core.py                    # register_agent(), validate_action()
│   │   ├── decorators.py             # @agent, @monitor (context-based)
│   │   ├── context.py                # agent_context(), contextvars resolution
│   │   ├── db.py                     # HTTP client layer (httpx → backend API)
│   │   ├── cli.py                    # kill_agent(), revive_agent(), show_audit_log()
│   │   └── exceptions.py            # SentinelBlockedError, SentinelKillSwitchError
│   └── pyproject.toml
│
├── aegis_backend/                     # FastAPI Server (Vercel-deployed)
│   ├── backend.py                    # Dashboard + SDK + demo endpoints
│   ├── mongo.py                      # Direct MongoDB layer (ONLY DB module)
│   ├── demo_router.py               # /demo/seed endpoint
│   ├── api/
│   │   └── index.py                  # Vercel serverless entry point
│   ├── vercel.json                   # Vercel deployment config
│   └── requirements.txt
│
├── aegis_frontend/                    # React Dashboard
│   ├── src/
│   │   ├── api.js                    # API client functions
│   │   ├── App.jsx                   # Router setup (5 routes)
│   │   ├── index.css                 # Robinhood-style theme
│   │   ├── components/               # Reusable components
│   │   └── pages/                    # 5 page components
│   └── package.json
│
├── aegis_demo/                        # Demo — 4 LangChain agents
│   ├── __main__.py                    # Entry point
│   ├── run_demo.py                    # Orchestrator (seeds via backend API)
│   ├── core/
│   │   ├── mock_aegis.py             # SDK adapter (bridges SDK ↔ LangChain tools)
│   │   ├── tools.py                  # 17 shared banking tools
│   │   └── demo_db.py               # Direct MongoDB for banking data queries
│   ├── agents/                        # 4 agent definitions
│   └── data/
│       └── fake_data.py              # MongoDB seeder
│
├── AGENT-SENTINEL-README.md           # Full platform specification (this file)
└── README.md                          # Project overview
```

---

## Key Features

### 1. Digital Identity System
Every agent registered with Sentinel receives a unique Digital ID (`AGT-0x{hash}`). This ID tracks the agent across its entire lifecycle — registration, activity, policy changes, and termination. No agent operates anonymously.

### 2. Decorator Policy Engine
The Decorator is a developer-defined policy that specifies exactly what an agent is permitted to do. It covers three dimensions:

| Dimension | Allowed (Whitelist) | Blocked (Blacklist) |
|-----------|-------------------|-------------------|
| **Actions** | `read_database`, `send_email` | `delete_records`, `modify_schema` |
| **Data** | `sales_data`, `public_analytics` | `PII`, `credentials`, `employee_records` |
| **Servers** | `db-prod.internal`, `api.company.com` | `*.external.com`, `raw-internet` |

Any action not explicitly allowed or blocked enters a **"review" state** — paused and sent to a human for approval. This is the zero-trust principle: unknown = untrusted.

### 3. Outbound Firewall
Every tool call the agent attempts is intercepted and checked against the decorator policy before execution. Blocked actions never execute — the function is stopped before it runs. All actions (allowed and blocked) are logged for full audit trail.

### 4. Human-in-the-Loop Escalation
Three escalation modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Auto-block** | Action in blocked list | Immediately stopped, logged, alert fired |
| **Review queue** | Unknown action (not in any list) | Paused, sent to human review queue |
| **Kill switch** | Risk score > threshold OR manual | Agent process terminated, full audit logged |

### 5. HTTP-Based SDK Communication
The SDK communicates with the backend exclusively via HTTP (httpx). This makes the backend the single source of truth and the only entry point to the database. Policy changes, kill-switch commands, and audit logs all flow through the backend API.

### 6. Analytics & Audit Trail
- Complete, immutable log of every action
- Per-agent and aggregate statistics
- Risk score computation based on blocked/total action ratio

---

## Quick Start

### Prerequisites
- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))
- MongoDB Atlas cluster (or local MongoDB)

### 1. Install SDK and demo dependencies

```bash
git clone https://github.com/Baalavignesh/Aegis.git
cd Aegis

# Install SDK
cd aegis_sdk && pip install -e . && cd ..

# Install demo dependencies
cd aegis_demo && pip install -r requirements.txt && cd ..
```

### 2. Start the backend

```bash
cd aegis_backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set MONGO_URI

uvicorn backend:app --reload --port 8000
```

### 3. Configure and run the demo

```bash
# Set up environment
cp aegis_demo/.env.example aegis_demo/.env
# Edit .env — add GOOGLE_API_KEY, MONGO_URI, AEGIS_BACKEND_URL

# Run all 4 agents (backend must be running)
python -m aegis_demo

# Or run a specific agent
python -m aegis_demo --agent fraud_detection
```

### 4. What you'll see
Four agents run sequentially. Each tool call shows an AEGIS firewall decision (ALLOWED/BLOCKED/REVIEW). After all agents run, a summary dashboard shows totals, followed by a kill-switch demo and audit log dump.

---

## SDK Usage Guide

### Installation

```bash
cd aegis_sdk
pip install -e .
```

### Environment

```bash
# Required — URL of the Aegis backend API
AEGIS_BACKEND_URL=http://localhost:8000
```

### Basic Integration (Any Python Agent)

```python
from sentinel import agent, monitor, agent_context

# 1. Register an agent with policies (sent to backend API at import time)
@agent("MyAgent", owner="alice",
       allows=["read_database", "send_email"],
       blocks=["delete_records", "access_credentials"])
class MyAgent: pass

# 2. Decorate tools with @monitor — agent resolved from context at call time
@monitor
def read_database(query: str) -> dict:
    """This function is now monitored by Sentinel."""
    return db.execute(query)

@monitor
def send_email(to: str, subject: str, body: str):
    """Sentinel checks this against policy before execution."""
    smtp.send(to, subject, body)

@monitor
def access_credentials(key_name: str):
    return vault.get(key_name)

# 3. Use tools inside an agent context
with agent_context("MyAgent"):
    read_database("SELECT * FROM sales")
    # → ALLOWED — logged to audit_log via backend API

    access_credentials("aws_secret_key")
    # → SentinelBlockedError raised
    # → Event logged: status="BLOCKED"
    # → Function NEVER executes
```

### Shared Tools Across Multiple Agents

The same `@monitor`-decorated function works under different agents. The policy check depends on which agent is active in the context:

```python
from sentinel import monitor, agent_context
from sentinel.core import register_agent

register_agent("SupportBot", allows=["lookup_balance"], blocks=["delete_records"])
register_agent("AdminBot",   allows=["lookup_balance", "delete_records"])

@monitor
def lookup_balance(customer_id: int) -> str:
    return f"Balance: $5,000"

@monitor
def delete_records(table: str) -> str:
    return f"Deleted {table}"

with agent_context("SupportBot"):
    lookup_balance(42)    # ALLOWED
    delete_records("tmp") # BLOCKED

with agent_context("AdminBot"):
    lookup_balance(42)    # ALLOWED
    delete_records("tmp") # ALLOWED
```

### Kill Switch & Audit Log

```python
from sentinel import kill_agent, revive_agent, show_audit_log

kill_agent("MyAgent")       # Immediately PAUSES — all actions blocked
revive_agent("MyAgent")     # Reactivates agent
show_audit_log("MyAgent")   # Print last 10 audit log entries
```

### Framework Integration (LangChain / LangGraph)

For framework-specific tool wrapping (e.g., LangChain `StructuredTool`), see the demo adapter in `aegis_demo/core/mock_aegis.py` which bridges the SDK with LangChain's tool system using `validate_action()` directly.

### CLI Commands

```bash
sentinel kill <agent_name>     # Pause an agent (kill switch)
sentinel revive <agent_name>   # Reactivate an agent
sentinel log <agent_name>      # Show audit log
```

### Firewall Decision Logic

```
For every agent action:

1. Is action in blocked_actions?
   YES → BLOCK immediately. Log. Alert. Do not execute.

2. Is action in allowed_actions?
   YES → Continue to server/data check.

3. Action not in either list?
   → REVIEW mode. Pause. Send to human review queue.

4. Is target server in blocked_servers?
   YES → BLOCK. (Wildcard matching applies)

5. Is target server in allowed_servers?
   YES → ALLOW.

6. Does action reference blocked_data?
   YES → BLOCK.

7. All checks pass → EXECUTE and LOG.
```

---

## API Reference

### Production URL

`https://aegis-backend-eight.vercel.app`

### Local URL

`http://localhost:8000`

Full interactive docs: `http://localhost:8000/docs` (Swagger UI)

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats` | Aggregate platform stats |
| `GET` | `/agents` | List all registered agents |
| `GET` | `/agents/{name}/logs` | Activity log for an agent |
| `GET` | `/agents/{name}/policies` | Agent's policy rules |
| `POST` | `/agents/{name}/toggle` | Kill-switch toggle (ACTIVE/PAUSED) |
| `GET` | `/logs` | Global audit log |
| `GET` | `/approvals/pending` | Pending human approval requests |
| `POST` | `/approvals/{id}/decide` | Approve or deny a request |

### SDK Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sdk/init` | Initialize database indexes |
| `POST` | `/sdk/register-agent` | Register or update an agent |
| `POST` | `/sdk/register-policy` | Register a policy rule |
| `GET` | `/sdk/agent-status/{name}` | Get agent status |
| `GET` | `/sdk/policy/{agent_name}/{action}` | Get policy for agent+action |
| `GET` | `/sdk/policies/{agent_name}` | Get all policies for an agent |
| `POST` | `/sdk/log` | Write an audit log entry |
| `POST` | `/sdk/update-status` | Update agent status |
| `POST` | `/sdk/approval` | Create approval request |
| `GET` | `/sdk/approval-status/{id}` | Poll approval status |
| `POST` | `/sdk/decide-approval/{id}` | Decide on approval |
| `GET` | `/sdk/pending-approvals` | List pending approvals |
| `GET` | `/sdk/audit-log` | Get audit log entries |

### Demo Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/demo/seed` | Reset and seed demo banking data |

---

## Environment Variables

```bash
# Backend
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGO_DB_NAME=sentinel_db

# SDK / Demo
AEGIS_BACKEND_URL=http://localhost:8000    # Or production URL

# Demo only
GOOGLE_API_KEY=your-key-here               # Google Gemini API key
GEMINI_MODEL=gemini-2.5-flash-lite         # Optional — default model
MONGO_URI=mongodb+srv://...               # For banking tool queries

# Frontend (Vite — build-time env)
VITE_API_URL=http://localhost:8000         # Or production URL
```

---

## Use Cases

### For Developers
- Define strict boundaries for agents before deployment
- Get predictable agent behavior through decorator policies
- Debug agent behavior through audit logging
- Catch unexpected tool calls during development

### For Companies (Non-Technical)
- Monitor third-party AI agents operating in your infrastructure
- Set data access policies without modifying agent code
- Kill switch for any agent that deviates from expected behavior

### For Security Teams
- Analyze agent behavior patterns over time
- Identify high-risk agents via risk scores
- Block lateral movement (agent trying to access unauthorized tools)

---

## Roadmap

### MVP (Completed)
- [x] Python SDK with `@agent` and `@monitor` decorators
- [x] Context-based policy enforcement (`agent_context` via `contextvars`)
- [x] Decorator policy engine (allow/block/review)
- [x] HTTP-based SDK data layer (all DB ops go through backend API)
- [x] Kill switch (PAUSED/ACTIVE) with immediate enforcement
- [x] Demo agents (4 LangChain + Gemini agents with governed tool calls)
- [x] FastAPI backend as single DB gateway (dashboard + SDK endpoints)
- [x] Vercel deployment (backend + frontend)
- [x] React dashboard with agent monitoring UI (5 pages)
- [x] Human-in-the-loop review queue (approval/denial flow end-to-end)

### Future Improvements
- [ ] Agent Manifest Generation (AgentBOM)
- [ ] Governance Rule Engine (YAML-configurable)
- [ ] Multi-Agent Dependency Graph
- [ ] Analytics Timeline & Violation Breakdown
- [ ] Export & Compliance Reports (SOC2, GDPR, HIPAA)
- [ ] WebSocket Real-Time Events
- [ ] Content Inspection (DLP Layer)
- [ ] Multi-Language SDK Support (TypeScript, Go, Java)
- [ ] Rate limiting per agent
- [ ] Cost tracking (token usage)
- [ ] Role-based access control (RBAC)

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — use it however you want.
