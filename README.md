# Aegis — AI Agent Governance Platform

**Monitor, control, and secure autonomous AI agents.**

Aegis is a firewall and observability layer for AI agents. It gives developers and organizations full visibility into what agents do and what they access — with the power to stop them when they deviate.

> Think of it as **Cloudflare for AI Agents** — outbound policy enforcement, governance, and audit for any autonomous system.

## The Problem

AI agents (LangGraph, CrewAI, AutoGen, LangChain) are increasingly autonomous. They call APIs, access databases, read files, and make decisions — but there's no standardized way to:

- **See** what an agent is doing in real time
- **Control** what actions an agent is allowed to take
- **Stop** an agent when it deviates from expected behavior
- **Audit** every decision an agent made after the fact


## How It Works

```
Developer defines policy          Sentinel enforces it
─────────────────────────         ──────────────────────────────
@agent("SupportBot",              Every tool call is intercepted:
  allows=["lookup_balance"],        1. Check agent status (kill-switch)
  blocks=["delete_records"])        2. Check action policy (ALLOW/BLOCK)
                                    3. Check data & server restrictions
@monitor                            4. Log decision to audit_log
def lookup_balance(cid): ...        5. Execute or raise error

with agent_context("SupportBot"):
    lookup_balance(42)   # ALLOWED
    delete_records("x")  # BLOCKED
```

### Key Feature: Context-Based Policy Enforcement

Tools are shared — the same `lookup_balance` function might be called by a Support agent, a Fraud agent, and an Admin agent. Aegis uses Python's `contextvars` to resolve which agent is calling at runtime:

```python
@monitor
def lookup_balance(customer_id): ...

with agent_context("SupportBot"):
    lookup_balance(42)     # checks SupportBot's policies

with agent_context("FraudBot"):
    lookup_balance(42)     # checks FraudBot's policies
```

## Project Structure

| Module | Description | Status |
|--------|------------|--------|
| **aegis_sdk/** | `sentinel-guardrails` — Python SDK with `@agent`, `@monitor`, `agent_context`, SQLite policy engine, kill-switch, audit log | Implemented |
| **aegis_demo/** | 4 LangChain + Gemini agents (banking scenario) demonstrating firewall governance | Implemented |
| **aegis_backend/** | FastAPI server — agent registry, policy engine, review queue, analytics, kill-switch toggle | Implemented |
| **aegis_frontend/** | React dashboard — live monitoring, agent management, review queue, activity feed | Implemented |

## Quick Start

```bash
# 1. Install the SDK
cd aegis_sdk && pip install -e . && cd ..

# 2. Install demo dependencies
cd aegis_demo && pip install -r requirements.txt && cd ..

# 3. Configure API key
cp aegis_demo/.env.example aegis_demo/.env
# Edit .env and add your GOOGLE_API_KEY

# 4. Run the demo (generates governance data in sentinel.db)
python -m aegis_demo

# 5. Start the backend API
cd aegis_backend && pip install -r requirements.txt
uvicorn backend:app --reload --port 8000

# 6. Start the frontend dashboard
cd aegis_frontend && npm install
npm run dev    # serves at http://localhost:5173
```

## SDK At a Glance

```python
from sentinel import agent, monitor, agent_context, kill_agent, revive_agent

# Register agent with policies (persisted to SQLite)
@agent("MyBot", owner="alice", allows=["read_data"], blocks=["delete_data"])
class MyBot: pass

# Decorate shared tools — agent resolved from context at call time
@monitor
def read_data(query: str) -> str:
    return db.execute(query)

# Use tools under an agent's context
with agent_context("MyBot"):
    read_data("SELECT * FROM users")  # ALLOWED — logged to audit_log

# Kill switch — immediately blocks all actions
kill_agent("MyBot")
# ... later ...
revive_agent("MyBot")
```

## Core Concepts

- **Digital Identity** — Each agent gets a unique ID (`AGT-0x{hash}`) tracked across its lifecycle
- **Decorator Policy** — Three-dimensional permissions: actions, data, and servers with allowed/blocked lists
- **Firewall Logic** — blocked → BLOCK; allowed → continue checks; unknown → REVIEW; then check data and servers
- **Agent Context** — `contextvars`-based resolution so shared tools enforce the correct agent's policy at call time
- **Kill Switch** — Set any agent to PAUSED instantly; all actions blocked until revived
- **Audit Log** — Every decision (ALLOWED/BLOCKED/KILLED) persisted to SQLite with timestamps

## Dashboard

The React frontend provides a real-time governance dashboard with five views:

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | Overview with aggregate stats, agent list, recent activity, and pending approval alerts |
| **Agents** | `/agents` | Grid of all registered agents with status, action counts, and risk scores |
| **Agent Detail** | `/agents/:name` | Individual agent profile with kill-switch toggle, policy/tools list, and live activity feed |
| **Activity** | `/activity` | Full audit log with agent filter dropdown and real-time polling |
| **Approvals** | `/approvals` | Human-in-the-loop review queue with approve/deny controls |

### Implemented Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats` | Aggregate platform stats (total agents, actions, blocked, risk) |
| `GET` | `/agents` | List all registered agents with status and action counts |
| `GET` | `/agents/{name}/logs` | Get activity log for a specific agent |
| `GET` | `/agents/{name}/policies` | Get an agent's allowed/blocked policy rules |
| `POST` | `/agents/{name}/toggle` | Toggle agent status between ACTIVE and PAUSED (kill-switch) |
| `GET` | `/logs` | Get all activity logs across all agents |
| `GET` | `/approvals/pending` | Get all pending human-in-the-loop approval requests |
| `POST` | `/approvals/{id}/decide` | Approve or deny a pending approval request |

## Future Improvements

The following features are designed and spec'd in [AGENT-SENTINEL-README.md](AGENT-SENTINEL-README.md) but not yet implemented:

### Agent Manifest Generation (AgentBOM)
Automatically generate an `agent_manifest.json` from decorator data across the entire codebase — an Agent Bill of Materials. Documents every agent's identity, capabilities, tools, data access, permissions, dependencies, and human-in-the-loop requirements. Serves as audit-ready documentation and a single source of truth for the agent ecosystem.

**Planned endpoints:** `POST /api/manifests`, `GET /api/manifests`, `GET /api/manifests/{id}`

### Governance Rule Engine
A configurable YAML-based rule engine that scans agent manifests against organizational policies (e.g., "any agent accessing PII must have human approval" or "production write access requires an assigned owner"). Violations surface on the dashboard with severity levels and suggested remediations. An LLM layer enriches each flag with contextual, human-readable risk explanations.

**Planned endpoints:** `POST /api/governance/check`, `GET /api/governance/violations`

### Multi-Agent Dependency Graph
Automatically maps how agents depend on each other by reading the `dependencies` field in each agent's manifest. Builds a directed graph (agents as nodes, calls as edges, tools/data as connected endpoints) rendered as an interactive visualization on the dashboard.

**Planned endpoints:** `GET /api/agents/{id}/dependencies`

### Thought Stream Logging
Optional post-action logging of agent reasoning and chain-of-thought. Not real-time interception — a debug/audit log for understanding *why* an agent made a decision, reviewing failed or blocked actions, and building audit trails that include agent reasoning.

**Planned endpoints:** `POST /api/agents/{id}/thoughts`, `GET /api/agents/{id}/thoughts`

### Analytics Timeline & Violation Breakdown
Time-series charts showing agent behavior over time and violation breakdowns across all agents. Enables trend analysis, anomaly detection, and compliance reporting.

**Planned endpoints:** `GET /api/stats/timeline`, `GET /api/stats/violations`

### Export & Compliance Reports
One-click export of agent manifests as YAML and agent fact sheets as Markdown/PDF for compliance (SOC2, GDPR, HIPAA). Provides audit-ready documentation without manual effort.

**Planned endpoints:** `GET /api/export/manifest/{id}`, `GET /api/export/factsheet/{id}`

### WebSocket Real-Time Events
A persistent WebSocket connection (`WS /ws/events`) that broadcasts agent events in real time — replacing the current 2-second polling with instant push updates for activity, thought logs, alerts, and governance violations.

**Planned endpoint:** `WS /ws/events`

## Full Documentation

- **[AGENT-SENTINEL-README.md](AGENT-SENTINEL-README.md)** — Comprehensive platform spec: API reference, SDK usage guide, governance rules, roadmap
- **[aegis_sdk/README.md](aegis_sdk/README.md)** — SDK API reference and usage examples
- **[aegis_demo/README.md](aegis_demo/README.md)** — Demo setup, agent policies, and expected output

## License

MIT License
