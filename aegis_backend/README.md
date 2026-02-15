# Aegis Backend

FastAPI server that powers the Aegis governance dashboard and serves as the **single entry point to MongoDB**. Both the dashboard frontend and the SDK communicate with the database exclusively through this API.

## Architecture

```
SDK (httpx) ──→ /sdk/* endpoints ──→ mongo.py ──→ MongoDB Atlas
Frontend    ──→ /dashboard endpoints ──→ mongo.py ──→ MongoDB Atlas
Demo        ──→ /demo/seed ──→ mongo.py ──→ MongoDB Atlas
```

- `mongo.py` — the **only module** that connects to MongoDB directly
- `backend.py` — FastAPI app with dashboard + SDK + demo endpoints
- `demo_router.py` — `/demo/seed` endpoint for resetting and seeding demo data

## Tech Stack

- **Framework:** FastAPI
- **Database:** MongoDB Atlas (via pymongo)
- **Deployment:** Vercel (serverless via `api/index.py`)
- **Auth:** None (RBAC planned for v1.0)

## Getting Started

### Local Development

```bash
cd aegis_backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set MONGO_URI and MONGO_DB_NAME

uvicorn backend:app --reload --port 8000
```

API docs at `http://localhost:8000/docs` (Swagger UI).

### Vercel Deployment

The backend is deployed on Vercel as a serverless function:

```
aegis_backend/
├── api/
│   └── index.py        # Vercel entry point — imports FastAPI app from backend.py
├── vercel.json         # Routes all requests to api/index.py
├── backend.py          # FastAPI application
├── mongo.py            # MongoDB layer
├── demo_router.py      # Demo seed endpoint
└── requirements.txt    # Python dependencies
```

Set `MONGO_URI` and `MONGO_DB_NAME` as Vercel environment variables.

Production URL: `https://aegis-backend-eight.vercel.app`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | `sentinel_db` | MongoDB database name |

Create a `.env` file:

```bash
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?appName=Aegis
MONGO_DB_NAME=sentinel_db
```

## Dashboard Endpoints

Consumed by the React frontend:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats` | Aggregate platform stats — registered agents, active agents, blocks in 24h, pending approvals, risk level |
| `GET` | `/agents` | List all agents with status, owner, action counts, computed risk scores |
| `GET` | `/agents/{name}/logs` | Activity log for a specific agent (last 50 entries, newest first) |
| `GET` | `/agents/{name}/policies` | Agent's allowed/blocked/review action lists |
| `POST` | `/agents/{name}/toggle` | Kill-switch toggle (ACTIVE ↔ PAUSED). Body: `{"status": "PAUSED"}` |
| `GET` | `/logs` | Global audit log across all agents (last 50 entries) |
| `GET` | `/approvals/pending` | Pending human-in-the-loop approval requests |
| `POST` | `/approvals/{id}/decide` | Approve or deny a request. Body: `{"decision": "APPROVED"}` |

## SDK Endpoints

Consumed by the `aegis-sentinel` SDK via HTTP (httpx). The SDK no longer connects to MongoDB directly — all operations go through these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sdk/init` | Initialize database indexes |
| `POST` | `/sdk/register-agent` | Register or update an agent. Body: `{"name": "...", "owner": "..."}` |
| `POST` | `/sdk/register-policy` | Register a policy rule. Body: `{"agent_name": "...", "action": "...", "rule_type": "ALLOW"}` |
| `GET` | `/sdk/agent-status/{name}` | Get agent status (ACTIVE/PAUSED) |
| `GET` | `/sdk/policy/{agent_name}/{action}` | Get policy rule_type for a specific agent+action |
| `GET` | `/sdk/policies/{agent_name}` | Get all policy rules for an agent |
| `POST` | `/sdk/log` | Write an audit log entry. Body: `{"agent_name": "...", "action": "...", "status": "...", "details": "..."}` |
| `POST` | `/sdk/update-status` | Update agent status (kill-switch). Body: `{"name": "...", "status": "PAUSED"}` |
| `POST` | `/sdk/approval` | Create a pending approval request. Returns `{"approval_id": N}` |
| `GET` | `/sdk/approval-status/{approval_id}` | Poll approval status |
| `POST` | `/sdk/decide-approval/{approval_id}` | Decide on an approval. Body: `{"decision": "APPROVED"}` |
| `GET` | `/sdk/pending-approvals` | List all pending approval requests |
| `GET` | `/sdk/audit-log` | Get audit log entries. Query params: `agent_name`, `limit` |

## Demo Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/demo/seed` | Drop all sentinel + banking collections and re-seed demo data (10 customers, ~13 accounts, ~80 transactions) |

## Future Improvements

The following APIs are designed in the platform spec ([AGENT-SENTINEL-README.md](../AGENT-SENTINEL-README.md)) but not yet implemented:

- **Agent Manifests** — Auto-generated Agent Bill of Materials (AgentBOM)
- **Governance Rule Engine** — YAML-configurable rules scanned against agent manifests
- **Dependency Graph** — Directed graph mapping agent-to-agent dependencies
- **Analytics Timeline** — Time-series data for agent behavior trends
- **Export & Compliance** — One-click export for SOC2, GDPR, HIPAA
- **WebSocket Events** — Real-time event streaming replacing polling
