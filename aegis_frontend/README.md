# Aegis Frontend

React dashboard that provides real-time visibility and control over all registered AI agents.

## Responsibilities

- **Agent Overview** — Display all registered agents with their Digital IDs, status, and risk badges
- **Decorator Panel** — View and edit each agent's policy (allowed/blocked actions, data, servers)
- **Live Activity Feed** — Stream agent events in real time via WebSocket connection
- **Dependency Graph** — Interactive visualization of agent-to-agent relationships and data flows
- **Governance Flags** — Surface policy violations with severity levels and suggested remediations
- **Review Queue** — Human-in-the-loop interface to approve or reject unknown agent actions
- **Analytics Dashboard** — Timeline charts, violation breakdowns, and aggregate stats
- **Export Controls** — One-click export of manifests (YAML) and fact sheets (Markdown/PDF)

## Tech Stack

- **Framework:** React (Vite)
- **Styling:** TBD (Tailwind CSS / shadcn recommended)
- **State:** React hooks + context
- **Real-time:** WebSocket client
- **Graphing:** TBD (D3.js / React Flow for dependency graph, Recharts for analytics)

## Getting Started

```bash
cd aegis_frontend
npm install
npm run dev
```

Dashboard will be available at `http://localhost:5173`.
