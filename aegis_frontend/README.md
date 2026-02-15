# Aegis Frontend — Governance Dashboard

React SPA providing a real-time monitoring dashboard for the Aegis AI agent governance platform. Built with a Robinhood-inspired design language — clean white backgrounds, Inter font, green/red status colors, and minimal borders. The dashboard talks to the **Aegis backend API**, which reads from **MongoDB** (agents, policies, audit log, approvals).

## Tech Stack

- **Framework:** React 19 + Vite
- **Routing:** React Router v6
- **Styling:** Tailwind CSS v4 with custom theme variables
- **Icons:** Lucide React
- **Data:** REST API polling (2-second intervals) against the FastAPI backend (MongoDB-backed)

## Getting Started

```bash
cd aegis_frontend
npm install
npm run dev    # serves at http://localhost:5173
```

Requires the backend running (default `http://localhost:8000`). The backend uses MongoDB; configure `MONGO_URI` and `MONGO_DB_NAME` in the backend environment (see `aegis_backend/`).

### API base URL (MongoDB integration)

The frontend uses the backend API as the single source of truth; all dashboard data (agents, logs, approvals) comes from the backend, which reads from MongoDB. Set the API base URL via environment:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL (used at build time) |

Create a `.env` file in `aegis_frontend/` to override, e.g.:

```bash
VITE_API_URL=http://localhost:8000
```

For a different host/port (e.g. deployed backend), set `VITE_API_URL` and run `npm run build` / `npm run dev` again.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Overview with aggregate stats, agent list, recent activity feed, and pending approval alert banner |
| `/agents` | Agents | Responsive grid of all registered agents showing status, action counts, and risk scores |
| `/agents/:name` | Agent Detail | Individual agent profile with kill-switch toggle, policy/tools list, and live activity feed |
| `/activity` | Activity | Full audit log with agent filter dropdown and real-time updates |
| `/approvals` | Approvals | Human-in-the-loop review queue with approve/deny controls for each pending action |

## Folder Structure

```
src/
├── api.js                  # 8 API functions (stats, agents, logs, policies, toggle, approvals)
├── App.jsx                 # BrowserRouter with 5 routes + Navbar layout
├── index.css               # Tailwind v4 @theme with Robinhood color palette
├── main.jsx                # Entry point
├── components/
│   ├── Navbar.jsx          # Top nav — active link underlines, approval count badge
│   ├── AgentCard.jsx       # Card component for agents grid
│   ├── AgentProfile.jsx    # Agent header with name, ID, status, kill-switch toggle
│   ├── ApprovalCard.jsx    # Individual approval with action details + approve/deny buttons
│   ├── LiveFeed.jsx        # Scrollable audit log feed with status color coding
│   ├── StatsCards.jsx      # Dashboard stat cards (agents, actions, blocked, reviews, risk)
│   └── ToolsList.jsx       # Agent policy display (allowed/blocked action lists)
└── pages/
    ├── DashboardPage.jsx   # Stats + two-column layout (agents left, activity right)
    ├── AgentsPage.jsx      # Responsive grid (1/2/3 columns) of AgentCard components
    ├── AgentDetailPage.jsx # Profile + tools (left 3/5) + sticky live feed (right 2/5)
    ├── ActivityPage.jsx    # Full-height LiveFeed with agent filter dropdown
    └── ApprovalsPage.jsx   # ApprovalCard list with empty state
```

## Design System

Robinhood-inspired theme defined in `index.css`:

| Token | Value | Usage |
|-------|-------|-------|
| `--color-surface` | `#FFFFFF` | Page and card backgrounds |
| `--color-surface-alt` | `#F7F7F8` | Alternating row backgrounds |
| `--color-divider` | `#E3E5E8` | Borders and separators |
| `--color-positive` | `#00C805` | Allowed actions, active status, success |
| `--color-negative` | `#FF5000` | Blocked actions, paused status, errors |
| `--color-caution` | `#FFAB00` | Pending approvals, review states |
| `--color-ink` | `#1B1B1B` | Primary text |
| `--color-ink-secondary` | `#6F7177` | Secondary text |
| `--color-ink-faint` | `#9B9BA3` | Muted text, timestamps |
| `--font-sans` | `Inter` | All typography |

## API Functions

All functions in `api.js` call the backend at `VITE_API_URL` (default `http://localhost:8000`). The backend serves data from MongoDB.

| Function | Endpoint | Used By |
|----------|----------|---------|
| `fetchStats()` | `GET /stats` | DashboardPage |
| `fetchAgents()` | `GET /agents` | DashboardPage, AgentsPage, AgentDetailPage, ActivityPage, Navbar |
| `fetchAgentLogs(name)` | `GET /agents/{name}/logs` | AgentDetailPage |
| `fetchAgentPolicies(name)` | `GET /agents/{name}/policies` | AgentDetailPage |
| `toggleAgent(name, status)` | `POST /agents/{name}/toggle` | AgentDetailPage |
| `fetchAllLogs()` | `GET /logs` | DashboardPage, ActivityPage |
| `fetchPendingApprovals()` | `GET /approvals/pending` | DashboardPage, ApprovalsPage, Navbar |
| `decideApproval(id, decision)` | `POST /approvals/{id}/decide` | ApprovalsPage |
