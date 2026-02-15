# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aegis (Agent Sentinel) is an AI agent governance platform — a firewall and observability layer for autonomous AI agents. It intercepts agent actions, validates them against declared policies (decorators), and provides real-time monitoring, audit trails, and human-in-the-loop controls.

**Current state:** All four modules are fully implemented and synced. The SDK, demo, backend, and frontend are working end-to-end.

## Architecture

Three-tier system with four directories:

- **aegis_backend/** — FastAPI server (port 8000): agent registry, firewall/policy engine, governance rules, review queue, analytics. Implemented with SQLModel + SQLite. API docs at `/docs`.
- **aegis_frontend/** — React SPA via Vite (port 5173): Robinhood-style dashboard with 5 pages (Dashboard, Agents, Agent Detail, Activity, Approvals), real-time polling, agent kill-switch toggle, HITL approval queue. Built with React Router, Tailwind CSS v4, and Lucide icons.
- **aegis_sdk/** — `sentinel-guardrails` Python library: `@agent` and `@monitor` decorators, `agent_context` for dynamic agent resolution, SQLite-backed policy enforcement, kill-switch (`PAUSED`/`ACTIVE`), audit logging, CLI helpers. No network dependency — all local via SQLite.
- **aegis_demo/** — Four LangChain + Gemini agents (Customer Support, Fraud Detection, Loan Processing, Marketing) demonstrating Aegis firewall governance over a personal finance scenario with a seeded SQLite bank database. Integrates with the real SDK via an adapter in `core/mock_aegis.py`.

## Key Concepts

- **Digital Identity**: Each agent gets a unique ID (`AGT-0x{hash}`) tracked across its lifecycle
- **Decorator Policy**: Three-dimensional permissions — actions, data, and servers — each with allowed/blocked lists
- **Firewall Logic**: blocked → BLOCK; allowed → continue checks; unknown → REVIEW (human approval); then check servers and data
- **Agent Context**: `agent_context("BotName")` sets the active agent via `contextvars` so `@monitor`-decorated shared tools resolve the correct policy at call time
- **Kill Switch**: Agent status can be set to PAUSED via `kill_agent()`, blocking all actions until `revive_agent()` is called
- **Audit Log**: Every firewall decision (ALLOWED/BLOCKED/KILLED) is persisted to `audit_log` table in SQLite

## Development Commands

```bash
# SDK (editable install)
cd aegis_sdk
pip install -e .

# Demo (requires SDK installed + GOOGLE_API_KEY in .env)
cd aegis_demo
pip install -r requirements.txt
python -m aegis_demo                     # run all 4 agents
python -m aegis_demo --agent fraud_detection  # run one agent

# Backend (implemented)
cd aegis_backend
pip install -r requirements.txt
uvicorn backend:app --reload --port 8000

# Frontend (Robinhood-style React dashboard)
cd aegis_frontend
npm install
npm run dev          # serves at http://localhost:5173
```

## Tech Stack

| Module | Stack |
|--------|-------|
| Backend | FastAPI, SQLite, raw SQL queries (no ORM) |
| Frontend | React 19, Vite, React Router v6, Tailwind CSS v4, Lucide icons |
| SDK | Python 3.10+, SQLite, `contextvars`, decorators (`@agent`, `@monitor`), Click CLI |
| Demo | LangChain, LangGraph, Gemini (google-genai), python-dotenv |

## API Structure

Backend exposes 8 REST endpoints (no `/api/` prefix): `GET /stats`, `GET /agents`, `GET /agents/{name}/logs`, `GET /agents/{name}/policies`, `POST /agents/{name}/toggle`, `GET /logs`, `GET /approvals/pending`, `POST /approvals/{id}/decide`. Interactive docs at `http://localhost:8000/docs`.

Additional APIs from the spec (manifests, governance rules, dependency graph, thought logging, analytics timeline, exports, WebSocket) are documented as future improvements in README.md.

## Environment Variables

Backend: `SENTINEL_DB_URL`, `SENTINEL_HOST`, `SENTINEL_PORT`, `SENTINEL_CORS_ORIGINS`, `SENTINEL_LOG_LEVEL`
SDK: `sentinel.db.DB_PATH` (Python variable, default `"sentinel.db"`)
Demo: `GOOGLE_API_KEY` (in `aegis_demo/.env`), `GEMINI_MODEL` (optional, default `gemini-2.5-flash-lite`)

## Important Files

- `AGENT-SENTINEL-README.md` — Comprehensive platform spec: full API reference, SDK usage guide, decorator schema, firewall logic, governance rules format, WebSocket message format, roadmap
- `README.md` — High-level project overview
- `aegis_sdk/sentinel/` — Implemented SDK:
  - `core.py` — `register_agent()`, `validate_action()` (DB-polling engine)
  - `decorators.py` — `@agent` (import-time registration), `@monitor` (context-based firewall wrapper)
  - `context.py` — `agent_context()`, `set_agent_context()`, `reset_agent_context()` (contextvars-based agent resolution)
  - `db.py` — SQLite layer (agents, policies, audit_log tables)
  - `cli.py` — `kill_agent()`, `revive_agent()`, `show_audit_log()`
  - `exceptions.py` — `SentinelBlockedError`, `SentinelKillSwitchError`, `SentinelApprovalError`
- `aegis_demo/core/mock_aegis.py` — SDK adapter that bridges `sentinel-guardrails` with LangChain tool wrapping and ANSI terminal output
- `aegis_frontend/src/` — Frontend source:
  - `api.js` — 8 API functions against localhost:8000
  - `components/Navbar.jsx` — Top navigation with active link underlines and approval badge
  - `components/AgentCard.jsx` — Agent card for grid view
  - `components/AgentProfile.jsx` — Agent detail header with kill-switch toggle
  - `components/ApprovalCard.jsx` — Individual approval with approve/deny buttons
  - `components/LiveFeed.jsx` — Real-time audit log feed component
  - `components/StatsCards.jsx` — Dashboard stat cards
  - `components/ToolsList.jsx` — Agent policy/tools display
  - `pages/DashboardPage.jsx` — Overview with stats, agents, activity, approval alerts
  - `pages/AgentsPage.jsx` — Grid of all registered agents
  - `pages/AgentDetailPage.jsx` — Single agent profile, tools, and live feed
  - `pages/ActivityPage.jsx` — Full audit log with agent filter
  - `pages/ApprovalsPage.jsx` — Pending HITL approval queue

## Architecture Note

The spec in `AGENT-SENTINEL-README.md` uses `backend/`, `sdk/`, `frontend/`, `demo/` as directory names, but the actual repo uses `aegis_backend/`, `aegis_frontend/`, `aegis_sdk/`, `aegis_demo/`. Align implementation with the actual directory names.
