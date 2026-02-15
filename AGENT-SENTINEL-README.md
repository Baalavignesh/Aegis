# 🛡️ Agent Sentinel

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
│                    DEVELOPER / COMPANY                   │
│                                                         │
│   1. Register Agent → Gets Digital ID (AGT-0x7A3F)     │
│   2. Define Decorator → What agent CAN and CANNOT do   │
│   3. Monitor Dashboard → Watch everything in real time  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   SENTINEL FIREWALL                      │
│                                                         │
│  ┌──────────────┐   ┌────────────────────────────────┐  │
│  │   POLICY     │   │       OUTBOUND MONITOR         │  │
│  │   ENGINE     │──►│                                │  │
│  │  (Decorator) │   │  Every tool call, API request, │  │
│  │              │   │  file write, and DB query is    │  │
│  │  ✓ Allowed   │   │  intercepted and checked        │  │
│  │  ✕ Blocked   │   │  against the decorator policy   │  │
│  │  ? Review    │   │  before execution               │  │
│  └──────────────┘   └────────────────────────────────┘  │
│                        │                                 │
│              ┌─────────┴─────────┐                      │
│              │  POST-ACTION LOG  │                      │
│              │  (Optional thought │                      │
│              │   & reasoning log) │                      │
│              └───────────────────┘                      │
└─────────────────────────┬───────────────────────────────┘
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
Every tool call, API request, file write, and database query the agent attempts is intercepted and checked against the decorator policy before execution. Blocked actions never execute — the function is stopped before it runs. All actions (allowed and blocked) are logged for full audit trail.

### 4. Agent Manifest Generation (AgentBOM)
Sentinel automatically generates an `agent_manifest.json` from decorator data across your entire codebase — an Agent Bill of Materials. The manifest documents every agent's identity, capabilities, tools, data access, permissions, dependencies on other agents, and human-in-the-loop requirements. This serves as a single source of truth for your agent ecosystem that can be exported as audit-ready documentation.

### 5. Governance Rule Engine
A configurable rule engine scans each agent's manifest against policies defined in YAML — such as "any agent accessing PII must have a human approval step" or "production write access requires an assigned owner." Violations surface on the dashboard with severity levels and suggested remediations. An LLM layer enriches each flag with a contextual, human-readable risk explanation.

### 6. Multi-Agent Dependency Graph
Sentinel automatically maps how agents depend on each other by reading the `dependencies` field in each agent's manifest. It builds a directed graph where agents are nodes, calls between them are edges, and tools and data sources branch off as connected endpoints. This renders as an interactive visualization on the dashboard — click any agent and instantly trace what it calls, what calls it, and what data flows through it.

### 7. Human-in-the-Loop Escalation
Three escalation modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Auto-block** | Action in blocked list | Immediately stopped, logged, alert fired |
| **Review queue** | Unknown action (not in any list) | Paused, sent to human review queue |
| **Kill switch** | Risk score > threshold OR manual | Agent process terminated, full audit logged |

### 8. Thought Stream Logging (Optional)
Developers can optionally log agent reasoning and chain-of-thought after actions complete. This is not real-time interception — it's a post-action log for debugging and auditing purposes. Useful for understanding *why* an agent made a decision, reviewing failed or blocked actions, and building audit trails that include agent reasoning.

### 9. Analytics & Audit Trail
- Complete, immutable log of every action
- Timeline charts showing agent behavior over time
- Violation breakdown across all agents
- One-click export: `agent_manifest.yaml`, Markdown/PDF "Agent Fact Sheet" for compliance (SOC2, GDPR, HIPAA)

---

## Architecture

```
aegis/
├── aegis_sdk/                         # Python SDK (sentinel-guardrails)
│   ├── sentinel/
│   │   ├── __init__.py                # Public API exports
│   │   ├── core.py                    # register_agent(), validate_action()
│   │   ├── decorators.py             # @agent, @monitor (context-based)
│   │   ├── context.py                # agent_context(), contextvars resolution
│   │   ├── db.py                     # SQLite layer (agents, policies, audit_log)
│   │   ├── cli.py                    # kill_agent(), revive_agent(), show_audit_log()
│   │   └── exceptions.py            # SentinelBlockedError, SentinelKillSwitchError
│   └── setup.py
│
├── aegis_demo/                        # Demo — 4 LangChain agents
│   ├── __main__.py                    # Entry point (sets DB path, loads .env)
│   ├── run_demo.py                    # Orchestrator with summary dashboard
│   ├── core/
│   │   ├── mock_aegis.py             # SDK adapter (bridges SDK ↔ LangChain tools)
│   │   └── tools.py                  # 17 shared banking tools
│   ├── agents/                        # 4 agent definitions
│   │   ├── customer_support_agent.py  # Well-behaved
│   │   ├── fraud_detection_agent.py   # High-privilege
│   │   ├── loan_processing_agent.py   # Rogue (blocked actions)
│   │   └── marketing_agent.py         # Rogue (undeclared actions)
│   └── data/
│       └── fake_data.py              # SQLite seeder (customers, accounts, transactions)
│
├── aegis_backend/                     # FastAPI Server (implemented)
│   ├── backend.py                    # 8 REST endpoints, SQLite queries
│   ├── requirements.txt
│   └── README.md
│
├── aegis_frontend/                    # React Dashboard (implemented)
│   ├── src/
│   │   ├── api.js                    # API client (8 functions)
│   │   ├── App.jsx                   # Router setup (5 routes)
│   │   ├── index.css                 # Robinhood-style theme
│   │   ├── components/               # 7 reusable components
│   │   │   ├── Navbar.jsx            # Top nav with active underlines
│   │   │   ├── AgentCard.jsx         # Agent grid card
│   │   │   ├── AgentProfile.jsx      # Agent header + kill-switch
│   │   │   ├── ApprovalCard.jsx      # Approve/deny controls
│   │   │   ├── LiveFeed.jsx          # Real-time audit feed
│   │   │   ├── StatsCards.jsx        # Dashboard stats
│   │   │   └── ToolsList.jsx         # Policy/tools display
│   │   └── pages/                    # 5 page components
│   │       ├── DashboardPage.jsx     # Overview + alerts
│   │       ├── AgentsPage.jsx        # Agent grid
│   │       ├── AgentDetailPage.jsx   # Single agent view
│   │       ├── ActivityPage.jsx      # Full audit log
│   │       └── ApprovalsPage.jsx     # HITL review queue
│   ├── package.json
│   └── README.md
│
├── AGENT-SENTINEL-README.md           # Full platform specification
└── README.md                          # Project overview
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Install SDK and demo dependencies

```bash
git clone https://github.com/yourname/aegis.git
cd aegis

# Install SDK
cd aegis_sdk && pip install -e . && cd ..

# Install demo dependencies
cd aegis_demo && pip install -r requirements.txt && cd ..
```

### 2. Configure and run the demo

```bash
# Set up API key
cp aegis_demo/.env.example aegis_demo/.env
# Edit .env and add your GOOGLE_API_KEY

# Run all 4 agents
python -m aegis_demo

# Or run a specific agent
python -m aegis_demo --agent fraud_detection
```

### 3. What you'll see
Four agents run sequentially. Each tool call shows an AEGIS firewall decision (ALLOWED/BLOCKED/REVIEW). After all agents run, a summary dashboard shows totals, followed by a kill-switch demo and audit log dump from SQLite.

---

## SDK Usage Guide

### Installation

```bash
cd aegis_sdk
pip install -e .
```

### Basic Integration (Any Python Agent)

```python
from sentinel import agent, monitor, agent_context

# 1. Register an agent with policies (persisted to SQLite at import time)
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
    # → ALLOWED — logged to audit_log

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
show_audit_log("MyAgent")   # Print last 10 audit log entries from SQLite
```

### Framework Integration (LangChain / LangGraph)

For framework-specific tool wrapping (e.g., LangChain `StructuredTool`), see the demo adapter in `aegis_demo/core/mock_aegis.py` which bridges the SDK with LangChain's tool system using `validate_action()` directly.

### CLI Commands

```bash
sentinel kill <agent_name>     # Pause an agent (kill switch)
sentinel revive <agent_name>   # Reactivate an agent
sentinel log <agent_name>      # Show audit log
```

### Decorator Schema Reference

```json
{
    "allowed_actions": [
        "string — function/tool names the agent CAN call"
    ],
    "blocked_actions": [
        "string — function/tool names the agent CANNOT call"
    ],
    "allowed_data": [
        "string — data categories the agent CAN access"
    ],
    "blocked_data": [
        "string — data categories the agent CANNOT access"
    ],
    "allowed_servers": [
        "string — hostnames/patterns the agent CAN connect to",
        "supports wildcards: *.company.com"
    ],
    "blocked_servers": [
        "string — hostnames/patterns the agent CANNOT connect to",
        "supports wildcards: *.darkweb.*"
    ]
}
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

## Governance Rules

Define governance policies in `governance/rules.yaml`:

```yaml
rules:
  - id: "PII_NO_APPROVAL"
    description: "Agent accesses PII but has no human approval step"
    condition:
      blocked_data_contains: "PII"
      has_approval_step: false
    severity: "critical"
    remediation: "Add a human-in-the-loop checkpoint before PII operations"

  - id: "PROD_WRITE_NO_OWNER"
    description: "Agent writes to production but has no assigned owner"
    condition:
      allowed_actions_contains: "write"
      allowed_servers_contains: "*.prod.*"
      owner: null
    severity: "high"
    remediation: "Assign an owner to this agent before deploying to production"

  - id: "NO_BLOCKED_LIST"
    description: "Agent has no blocked actions defined"
    condition:
      blocked_actions: []
    severity: "medium"
    remediation: "Define explicit blocked actions — open permissions are a security risk"
```

---

## API Reference

Base URL: `http://localhost:8000`

Full interactive docs: `http://localhost:8000/docs` (Swagger UI)

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents` | Register new agent, returns Digital ID |
| `GET` | `/api/agents` | List all registered agents |
| `GET` | `/api/agents/{id}` | Get agent details + decorator + recent logs |
| `PUT` | `/api/agents/{id}/decorator` | Update decorator policy |
| `PUT` | `/api/agents/{id}/status` | Change status: active, blocked, paused, review |
| `DELETE` | `/api/agents/{id}` | Deregister agent |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents/{id}/activity` | Log an activity event (used by SDK) |
| `GET` | `/api/agents/{id}/activity` | Get activity log (paginated) |
| `POST` | `/api/agents/{id}/thoughts` | Log a thought (used by SDK, optional) |
| `GET` | `/api/agents/{id}/thoughts` | Get thought log (paginated) |

### Manifests & Governance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/manifests` | Upload or register an agent manifest |
| `GET` | `/api/manifests` | List all manifests |
| `GET` | `/api/manifests/{id}` | Get manifest details + LLM summary |
| `POST` | `/api/governance/check` | Run governance rules against a manifest |
| `GET` | `/api/governance/violations` | Get all governance violations |
| `GET` | `/api/agents/{id}/dependencies` | Get agent dependency graph data |

### Review Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/review` | Get all pending review items |
| `POST` | `/api/review/{id}/approve` | Approve action, add to allowed list |
| `POST` | `/api/review/{id}/reject` | Reject action, add to blocked list |

### Analytics & Exports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Aggregate platform stats |
| `GET` | `/api/stats/timeline` | Activity timeline data |
| `GET` | `/api/stats/violations` | Violation breakdown |
| `GET` | `/api/export/manifest/{id}` | Export manifest as YAML |
| `GET` | `/api/export/factsheet/{id}` | Export agent fact sheet as Markdown/PDF |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/events` | Real-time stream of all agent events |

WebSocket message format:
```json
{
    "type": "activity | thought | alert | governance",
    "agent_id": "AGT-0x7A3F",
    "agent_name": "DataPipeline-Agent",
    "timestamp": "2025-02-14T14:32:08Z",
    "data": {
        "action": "access_credentials",
        "target": "aws_keys",
        "status": "blocked",
        "detail": "Attempted to read AWS secret key"
    }
}
```

---

## Use Cases

### For Developers
- Define strict boundaries for agents before deployment
- Get predictable agent behavior through decorator policies
- Auto-generate agent documentation from code
- Debug agent behavior through optional thought logging
- Catch unexpected tool calls during development

### For Companies (Non-Technical)
- Monitor third-party AI agents operating in your infrastructure
- Set data access policies without modifying agent code
- One-click audit trail exports for compliance (SOC2, GDPR, HIPAA)
- Kill switch for any agent that deviates from expected behavior

### For Security Teams
- Analyze agent behavior patterns over time
- Identify high-risk agents via governance rule engine
- Block lateral movement (agent trying to access unauthorized servers)
- Full dependency mapping of agent-to-agent communication

---

## Roadmap

### MVP (Completed)
- [x] Python SDK with `@agent` and `@monitor` decorators
- [x] Context-based policy enforcement (`agent_context` via `contextvars`)
- [x] Decorator policy engine (allow/block/review)
- [x] SQLite-backed audit logging
- [x] Kill switch (PAUSED/ACTIVE) with immediate enforcement
- [x] Demo agents (4 LangChain + Gemini agents with governed tool calls)
- [x] FastAPI backend with SQLite (8 REST endpoints)
- [x] React dashboard with agent monitoring UI (5 pages, Robinhood-style design)
- [x] Human-in-the-loop review queue (approval/denial flow end-to-end)

### Future Improvements

The following features are designed and spec'd but not yet implemented. Each adds a layer of governance, observability, or compliance capability to the platform.

#### Agent Manifest Generation (AgentBOM)
Automatically generate an `agent_manifest.json` from decorator data across the entire codebase — an Agent Bill of Materials. Documents every agent's identity, capabilities, tools, data access, permissions, dependencies on other agents, and human-in-the-loop requirements. This serves as a single source of truth for the agent ecosystem and can be exported as audit-ready documentation.

**Planned endpoints:** `POST /api/manifests` (upload/register), `GET /api/manifests` (list all), `GET /api/manifests/{id}` (details + LLM summary)

#### Governance Rule Engine
A configurable rule engine that scans each agent's manifest against policies defined in YAML — such as "any agent accessing PII must have a human approval step" or "production write access requires an assigned owner." Violations surface on the dashboard with severity levels (critical/high/medium) and suggested remediations. An LLM layer enriches each flag with a contextual, human-readable risk explanation.

**Planned endpoints:** `POST /api/governance/check` (run rules against a manifest), `GET /api/governance/violations` (list all violations)

#### Multi-Agent Dependency Graph
Automatically maps how agents depend on each other by reading the `dependencies` field in each agent's manifest. Builds a directed graph where agents are nodes, calls between them are edges, and tools/data sources branch off as connected endpoints. Renders as an interactive visualization (D3.js or React Flow) on the dashboard — click any agent and instantly trace what it calls, what calls it, and what data flows through it.

**Planned endpoint:** `GET /api/agents/{id}/dependencies`

#### Thought Stream Logging
Optional post-action logging of agent reasoning and chain-of-thought. Not real-time interception — it's a debug/audit log for understanding *why* an agent made a decision, reviewing failed or blocked actions, and building audit trails that include agent reasoning alongside firewall decisions.

**Planned endpoints:** `POST /api/agents/{id}/thoughts` (log a thought), `GET /api/agents/{id}/thoughts` (retrieve thought log, paginated)

#### Analytics Timeline & Violation Breakdown
Time-series data showing agent behavior over time (actions per hour/day, blocked vs. allowed trends) and violation breakdowns across all agents. Enables trend analysis, anomaly detection, and compliance reporting through charts on the dashboard.

**Planned endpoints:** `GET /api/stats/timeline` (activity timeline data), `GET /api/stats/violations` (violation breakdown)

#### Export & Compliance Reports
One-click export of agent manifests as YAML and agent fact sheets as Markdown/PDF for compliance frameworks (SOC2, GDPR, HIPAA). Provides audit-ready documentation without manual effort — every agent's identity, permissions, activity history, and governance status in a single downloadable report.

**Planned endpoints:** `GET /api/export/manifest/{id}` (YAML export), `GET /api/export/factsheet/{id}` (Markdown/PDF export)

#### WebSocket Real-Time Events
A persistent WebSocket connection that broadcasts agent events in real time — replacing the current 2-second polling interval with instant push updates. Streams activity events, thought logs, alerts, and governance violations as they happen.

**Planned endpoint:** `WS /ws/events`

### v0.2
- [ ] Framework adapters: LangGraph, CrewAI, AutoGen, LangChain
- [ ] LLM-powered manifest summarization and risk explanations
- [ ] Anomaly detection (ML-based soft deviation detection)
- [ ] Multi-tenant support (multiple teams/orgs)
- [ ] Decorator templates (pre-built policies for common use cases)
- [ ] Export audit reports (PDF)

### v0.3
- [ ] Agent-to-agent communication monitoring
- [ ] Rate limiting per agent (max N actions per minute)
- [ ] Cost tracking (token usage per agent)
- [ ] Integration with observability tools (Grafana, Datadog)
- [ ] Webhook notifications (Slack, Discord, PagerDuty)

### v1.0
- [ ] Production-grade deployment (Docker, Kubernetes)
- [ ] PostgreSQL support
- [ ] Role-based access control (RBAC)
- [ ] SDK for JavaScript/TypeScript agents
- [ ] Plugin system for custom firewall rules
- [ ] SaaS hosted version

---

## Environment Variables

```bash
# SDK (Python variable, not env var)
# sentinel.db.DB_PATH = "sentinel.db"       # Set in code before any SDK calls

# Demo
GOOGLE_API_KEY=your-key-here                # Required — Google Gemini API key
GEMINI_MODEL=gemini-2.5-flash-lite          # Optional — default model

# Backend
SENTINEL_DB_PATH=/path/to/sentinel.db   # Override default DB path
# Default: resolves to ../aegis_demo/data/sentinel.db relative to backend.py
```

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

---

**Built during a 14-hour sprint. Ship fast, govern responsibly.**
