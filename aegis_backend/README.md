# Aegis Backend

FastAPI server that powers the Agent Sentinel platform.

## Responsibilities

- **Agent Registry** — Register, update, and manage AI agents with unique Digital IDs (`AGT-0x{hash}`)
- **Firewall / Policy Engine** — Intercept and validate every agent action against its decorator policy (allow / block / review)
- **Activity & Thought Logging** — Store and serve the full audit trail of agent actions and optional reasoning logs
- **Governance Engine** — Run configurable YAML-based rules against agent manifests and surface violations
- **Manifest Management** — Generate and store Agent Bill of Materials (AgentBOM) for every registered agent
- **Review Queue** — Hold unknown actions for human approval and process approve/reject decisions
- **WebSocket Events** — Broadcast real-time agent activity to the frontend dashboard
- **Analytics & Exports** — Aggregate stats, timelines, and export audit-ready Markdown/YAML/PDF reports

## Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite (MVP) → PostgreSQL (production)
- **ORM:** SQLModel
- **Real-time:** WebSocket via FastAPI
- **Auth:** None for MVP (RBAC planned for v1.0)

## Getting Started

```bash
cd aegis_backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs will be available at `http://localhost:8000/docs`.
