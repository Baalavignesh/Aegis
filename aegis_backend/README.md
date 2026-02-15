# Aegis Backend

FastAPI server that powers the Aegis governance dashboard. Uses MongoDB via the SDK's `sentinel.db` module — same database as the SDK (agents, policies, audit_log, pending_approvals).

## Tech Stack

- **Framework:** FastAPI
- **Database:** MongoDB (shared with `sentinel-guardrails` SDK via `sentinel.db`)
- **Driver:** pymongo
- **Auth:** None (RBAC planned for v1.0)

## Getting Started

```bash
cd aegis_backend
pip install -r requirements.txt
uvicorn backend:app --reload --port 8000
```

API docs at `http://localhost:8000/docs` (Swagger UI).

### MongoDB Configuration

The backend uses the same MongoDB as the SDK. Set these environment variables (optional — defaults shown):

```bash
MONGO_URI=mongodb://localhost:27017/   # MongoDB connection string
MONGO_DB_NAME=sentinel_db              # Database name
```

Ensure the SDK's `sentinel.db` module can connect (e.g. same `MONGO_URI` / `MONGO_DB_NAME` in the environment when running the backend).

## Implemented Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats` | Aggregate platform stats — total agents, total actions, blocked count, review count, overall risk score |
| `GET` | `/agents` | List all registered agents with status (ACTIVE/PAUSED), owner, action counts, and computed risk score |
| `GET` | `/agents/{name}/logs` | Get the full activity log for a specific agent (sorted newest first) |
| `GET` | `/agents/{name}/policies` | Get an agent's policy rules — lists of allowed and blocked actions |
| `POST` | `/agents/{name}/toggle` | Toggle agent status between ACTIVE and PAUSED (kill-switch). Body: `{"status": "PAUSED"}` |
| `GET` | `/logs` | Get all activity logs across all agents (sorted newest first) |
| `GET` | `/approvals/pending` | Get all pending human-in-the-loop approval requests |
| `POST` | `/approvals/{id}/decide` | Approve or deny a pending approval. Body: `{"decision": "APPROVED"}` or `{"decision": "DENIED"}` |

## Future Improvements

The following APIs are designed in the platform spec ([AGENT-SENTINEL-README.md](../AGENT-SENTINEL-README.md)) but not yet implemented:

### Agent Manifests
Auto-generated Agent Bill of Materials (AgentBOM) documenting every agent's identity, capabilities, tools, data access, and permissions. Serves as audit-ready documentation.

`POST /api/manifests` | `GET /api/manifests` | `GET /api/manifests/{id}`

### Governance Rule Engine
YAML-configurable rules scanned against agent manifests (e.g., "PII access requires human approval"). Surfaces violations with severity levels and LLM-enriched risk explanations.

`POST /api/governance/check` | `GET /api/governance/violations`

### Dependency Graph
Directed graph mapping agent-to-agent dependencies, tools, and data flows for interactive visualization.

`GET /api/agents/{id}/dependencies`

### Thought Stream Logging
Optional post-action logging of agent reasoning and chain-of-thought for debugging and compliance audits.

`POST /api/agents/{id}/thoughts` | `GET /api/agents/{id}/thoughts`

### Analytics Timeline
Time-series data for agent behavior trends (actions per hour/day, blocked vs. allowed) and violation breakdowns.

`GET /api/stats/timeline` | `GET /api/stats/violations`

### Export & Compliance
One-click export of agent manifests (YAML) and fact sheets (Markdown/PDF) for SOC2, GDPR, and HIPAA compliance.

`GET /api/export/manifest/{id}` | `GET /api/export/factsheet/{id}`

### WebSocket Events
Real-time event streaming replacing 2-second polling with instant push updates for activity, alerts, and governance violations.

`WS /ws/events`
