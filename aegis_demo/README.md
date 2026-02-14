# Aegis Demo

Pre-built demo agents and scripts to showcase the Agent Sentinel platform end-to-end.

## Purpose

This folder contains ready-to-run example agents that demonstrate every core feature of the platform — registration, decorator enforcement, real-time monitoring, governance violations, and the human-in-the-loop review queue. Run these against a live backend + frontend to see Agent Sentinel in action.

## Demo Agents

### `good_agent.py` — Well-Behaved Agent
A compliant agent that only performs actions within its declared decorator policy. Demonstrates:
- Agent registration and Digital ID assignment
- Allowed actions executing successfully (e.g., reading a database, sending an email)
- Activity events streaming to the dashboard in real time
- Optional thought logging for audit trail

### `rogue_agent.py` — Policy-Violating Agent
A deliberately misbehaving agent that attempts actions outside its permissions. Demonstrates:
- Blocked actions being caught and stopped before execution
- Alerts firing on the dashboard when violations occur
- Attempts to access restricted data (PII, credentials)
- Attempts to connect to unauthorized servers
- Actions landing in the review queue (unknown/undeclared actions)

### `run_demo.sh` — One-Command Full Demo
A convenience script that starts the backend, frontend, and both demo agents in sequence so you can see the full platform working with a single command.

## How to Run

### Option 1: Run everything at once

```bash
cd aegis_demo
chmod +x run_demo.sh
./run_demo.sh
```

### Option 2: Run agents individually

Make sure the backend and frontend are already running, then:

```bash
# Terminal — Run the good agent
cd aegis_demo
python good_agent.py

# Terminal — Run the rogue agent
cd aegis_demo
python rogue_agent.py
```

### What to Watch For

1. Open the dashboard at `http://localhost:5173`
2. Run `good_agent.py` — watch events stream in with green "allowed" badges
3. Run `rogue_agent.py` — watch red "blocked" alerts fire and actions land in the review queue
4. Check the dependency graph, governance flags, and analytics panels update live

## Prerequisites

- Backend running at `http://localhost:8000` (see `aegis_backend/`)
- Frontend running at `http://localhost:5173` (see `aegis_frontend/`)
- SDK installed (`pip install -e ../aegis_sdk`)
