# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aegis (Agent Sentinel) is an AI agent governance platform — a firewall and observability layer for autonomous AI agents. It intercepts agent actions, validates them against declared policies (decorators), and provides real-time monitoring, audit trails, and human-in-the-loop controls.

**Current state:** Documentation scaffold only. All four modules have READMEs with specifications but no source code yet. Implementation is the next step.

## Architecture

Three-tier system with four directories:

- **aegis_backend/** — FastAPI server (port 8000): agent registry, firewall/policy engine, governance rules, WebSocket events, review queue, analytics/exports. Uses SQLModel + SQLite (MVP). API docs at `/docs`.
- **aegis_frontend/** — React SPA via Vite (port 5173): agent dashboard, live activity feed, dependency graph visualization, governance flags, review queue UI, export controls.
- **aegis_sdk/** — Python library developers integrate into agents: `AegisAgent` class, `@monitor` decorator that wraps tool functions, client-side firewall, manifest generator CLI, framework adapters (LangGraph, LangChain, CrewAI).
- **aegis_demo/** — Two demo agents (`good_agent.py`, `rogue_agent.py`) and `run_demo.sh` for end-to-end showcase.

## Key Concepts

- **Digital Identity**: Each agent gets a unique ID (`AGT-0x{hash}`) tracked across its lifecycle
- **Decorator Policy**: Three-dimensional permissions — actions, data, and servers — each with allowed/blocked lists
- **Firewall Logic**: blocked → BLOCK; allowed → continue checks; unknown → REVIEW (human approval); then check servers and data
- **AgentBOM**: Auto-generated agent manifest (bill of materials) documenting identity, capabilities, tools, dependencies
- **Governance Rules**: YAML-defined policies scanned against manifests, with severity levels and LLM-enriched explanations

## Development Commands

```bash
# Backend
cd aegis_backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd aegis_frontend
npm install
npm run dev          # serves at http://localhost:5173

# SDK (editable install)
cd aegis_sdk
pip install -e .

# Demo (requires backend + frontend running)
cd aegis_demo
./run_demo.sh        # or run good_agent.py / rogue_agent.py individually
```

## Tech Stack

| Module | Stack |
|--------|-------|
| Backend | FastAPI, SQLModel, SQLite (MVP) → PostgreSQL, WebSocket |
| Frontend | React, Vite, WebSocket client, D3.js/React Flow, Recharts |
| SDK | Python 3.10+, httpx/requests, Click/argparse CLI |

## API Structure

Backend exposes REST endpoints under `/api/` for: agents (CRUD + status), activity/thought logging, manifests, governance checks/violations, review queue (approve/reject), analytics/exports, and a WebSocket at `WS /ws/events` for real-time event streaming. Full reference in `AGENT-SENTINEL-README.md`.

## Environment Variables

Backend: `SENTINEL_DB_URL`, `SENTINEL_HOST`, `SENTINEL_PORT`, `SENTINEL_CORS_ORIGINS`, `SENTINEL_LOG_LEVEL`
SDK: `SENTINEL_SERVER_URL`, `SENTINEL_AGENT_NAME`, `SENTINEL_AUTO_REGISTER`

## Important Files

- `AGENT-SENTINEL-README.md` — Comprehensive platform spec (580 lines): full API reference, SDK usage guide, decorator schema, firewall logic, governance rules format, WebSocket message format, roadmap
- `README.md` — High-level concept overview

## Architecture Note

The spec in `AGENT-SENTINEL-README.md` uses `backend/`, `sdk/`, `frontend/`, `demo/` as directory names, but the actual repo uses `aegis_backend/`, `aegis_frontend/`, `aegis_sdk/`, `aegis_demo/`. Align implementation with the actual directory names.
