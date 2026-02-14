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
agent-sentinel/
├── backend/                    # FastAPI Server
│   ├── main.py                 # API endpoints + WebSocket
│   ├── models.py               # SQLModel database schemas
│   ├── firewall.py             # Policy enforcement engine
│   ├── governance.py           # Rule engine + manifest analyzer
│   ├── websocket.py            # Real-time event broadcasting
│   └── requirements.txt
│
├── sdk/                        # Python SDK (what developers integrate)
│   ├── sentinel.py             # AegisAgent class + @monitor decorator
│   ├── firewall.py             # Client-side policy checks
│   ├── manifest.py             # AgentBOM manifest generator
│   ├── adapters/
│   │   ├── langgraph.py        # LangGraph integration
│   │   ├── langchain.py        # LangChain integration
│   │   └── crewai.py           # CrewAI integration
│   ├── setup.py
│   └── README.md
│
├── frontend/                   # React Dashboard
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── api/client.js       # API + WebSocket client
│   │   ├── hooks/
│   │   │   ├── useAgents.js    # Agent state management
│   │   │   └── useWebSocket.js # Live event stream
│   │   └── components/
│   │       ├── AgentCard.jsx
│   │       ├── DecoratorPanel.jsx
│   │       ├── DecoratorEditor.jsx
│   │       ├── ActivityLog.jsx
│   │       ├── DependencyGraph.jsx
│   │       ├── GovernanceFlags.jsx
│   │       ├── ReviewQueue.jsx
│   │       ├── Analytics.jsx
│   │       ├── RegisterAgent.jsx
│   │       ├── AlertToast.jsx
│   │       └── StatsBar.jsx
│   └── package.json
│
├── governance/
│   └── rules.yaml              # Configurable governance rules
│
├── demo/
│   ├── good_agent.py           # Well-behaved demo agent
│   ├── rogue_agent.py          # Policy-violating demo agent
│   └── run_demo.sh             # One-command full demo
│
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip, npm

### 1. Clone and install

```bash
git clone https://github.com/yourname/agent-sentinel.git
cd agent-sentinel

# Backend
cd backend
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..

# SDK
cd sdk
pip install -e .
cd ..
```

### 2. Start the platform

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
# → Opens at http://localhost:5173

# Terminal 3 — Run demo agents
cd demo
python good_agent.py
python rogue_agent.py
```

### 3. Open dashboard
Navigate to `http://localhost:5173` — you'll see agents registering, events streaming in, and violations being caught in real time.

---

## SDK Usage Guide

### Basic Integration (Any Python Agent)

```python
from sentinel import AegisAgent

# 1. Create a sentinel-monitored agent
agent = AegisAgent(
    name="MyAgent",
    framework="custom",
    server_url="http://localhost:8000",
    decorator={
        "allowed_actions": ["read_database", "write_csv", "send_email"],
        "blocked_actions": ["delete_records", "access_credentials", "run_shell"],
        "allowed_data": ["sales_data", "public_analytics"],
        "blocked_data": ["PII", "passwords", "api_keys"],
        "allowed_servers": ["db.internal", "smtp.company.com"],
        "blocked_servers": ["*.darkweb.*", "pastebin.com"]
    }
)

# 2. Wrap your agent's tools with @agent.monitor
@agent.monitor
def read_database(query: str) -> dict:
    """This function is now monitored by Sentinel."""
    return db.execute(query)

@agent.monitor
def send_email(to: str, subject: str, body: str):
    """Sentinel checks this against decorator before execution."""
    smtp.send(to, subject, body)

# 3. (Optional) Log agent reasoning after actions for audit trail
agent.log_thought("User asked for Q4 report. I'll query the sales database.")
result = read_database("SELECT * FROM sales WHERE quarter = 'Q4'")

agent.log_thought("Data retrieved. Generating CSV report.")
# ... continues

# 4. If an agent tries a blocked action:
@agent.monitor
def access_credentials(key_name: str):
    return vault.get(key_name)

agent.log_thought("I need AWS keys to speed up the upload.")
access_credentials("aws_secret_key")
# → SentinelBlockedError raised
# → Event logged: status="blocked"
# → Dashboard alert fired
# → Function NEVER executes
```

### LangGraph Integration

```python
from langgraph.graph import StateGraph
from sentinel import AegisAgent
from sentinel.adapters.langgraph import wrap_tools

agent = AegisAgent(
    name="LangGraph-Research-Agent",
    framework="LangGraph",
    server_url="http://localhost:8000",
    decorator={...}
)

# Define your tools normally
def search_web(query: str) -> str:
    return google.search(query)

def read_file(path: str) -> str:
    return open(path).read()

# Wrap all tools with Sentinel monitoring
monitored_tools = wrap_tools(agent, [search_web, read_file])

# Build your graph as usual — tools are now monitored
graph = StateGraph(...)
```

### Generate Agent Manifest

```bash
# Generate AgentBOM manifest from all decorated agents in your project
sentinel manifest generate --output agent_manifest.json

# Run governance checks against the manifest
sentinel governance check --rules governance/rules.yaml --manifest agent_manifest.json
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

### MVP (Current Sprint)
- [ ] Dashboard with agent monitoring UI
- [ ] FastAPI backend with SQLite
- [ ] Python SDK with @monitor decorator
- [ ] Decorator policy engine (allow/block/review)
- [ ] Agent Manifest generation (AgentBOM)
- [ ] Governance rule engine with YAML config
- [ ] Multi-agent dependency graph visualization
- [ ] WebSocket real-time events
- [ ] Human-in-the-loop review queue
- [ ] Optional thought stream logging
- [ ] Export: manifest YAML + Markdown fact sheet
- [ ] Demo agents (good + rogue)

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
# Backend
SENTINEL_DB_URL=sqlite:///./sentinel.db    # Database path
SENTINEL_HOST=0.0.0.0                       # API host
SENTINEL_PORT=8000                          # API port
SENTINEL_CORS_ORIGINS=http://localhost:5173  # Allowed frontend origins
SENTINEL_LOG_LEVEL=info                     # Logging level

# SDK
SENTINEL_SERVER_URL=http://localhost:8000    # Backend URL
SENTINEL_AGENT_NAME=MyAgent                 # Default agent name
SENTINEL_AUTO_REGISTER=true                 # Auto-register on first use
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
