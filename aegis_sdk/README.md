# aegis-sentinel

**Governance guardrails for AI agents** — drop-in policy decorators, real-time audit logging, kill-switch, and human-in-the-loop approval.

[![PyPI](https://img.shields.io/pypi/v/aegis-sentinel)](https://pypi.org/project/aegis-sentinel/)
[![Python](https://img.shields.io/pypi/pyversions/aegis-sentinel)](https://pypi.org/project/aegis-sentinel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Install

```bash
pip install aegis-sentinel
```

For LangChain integration:
```bash
pip install aegis-sentinel[langchain]
```

## How It Works

The SDK communicates with the **Aegis backend API** via HTTP. It does not connect to MongoDB directly — the backend is the single entry point to the database.

```
Your Agent Code
    ↓ uses SDK decorators
aegis-sentinel SDK
    ↓ HTTP (httpx)
Aegis Backend API (FastAPI)
    ↓ pymongo
MongoDB Atlas
```

## Quick Start

```python
from sentinel import AegisAgent

# 1. Define your agent with a policy decorator
agent = AegisAgent(
    name="Customer Support",
    role="Service representative",
    decorator={
        "allowed_actions": ["lookup_balance", "send_notification"],
        "blocked_actions": ["delete_records", "access_ssn"],
    },
)

# 2. Wrap your LangChain tools — Aegis enforces policies automatically
monitored_tools = agent.wrap_langchain_tools(your_tools)

# 3. Use with any LLM
from langgraph.prebuilt import create_react_agent
executor = create_react_agent(llm, monitored_tools)
result = executor.invoke({"messages": [("user", "Help this customer")]})
```

## Features

| Feature | Description |
|---|---|
| **Policy Decorators** | Define allowed/blocked actions per agent |
| **Audit Logging** | Every tool call logged via backend API with timestamps |
| **Kill Switch** | Instantly pause any agent |
| **Human-in-the-Loop** | Actions requiring approval wait for human decision |
| **LangChain Native** | Works with LangChain tools out of the box |
| **HTTP-Based** | All DB operations go through the backend API (no direct MongoDB) |

## Environment Variables

```bash
# Required — URL of the Aegis backend API
AEGIS_BACKEND_URL=http://localhost:8000

# For production:
# AEGIS_BACKEND_URL=https://aegis-backend-eight.vercel.app
```

The SDK uses `AEGIS_BACKEND_URL` to send all requests to the backend. Default: `http://localhost:8000`.

## API Reference

### `AegisAgent(name, role, decorator)`
Create a governed agent with policy rules. Registers the agent and policies via the backend API.

### `agent.wrap_langchain_tools(tools)`
Wrap LangChain tools with policy enforcement. Returns monitored tools.

### `agent.log_thought(message)`
Log agent reasoning to the audit trail.

### `kill_agent(name)` / `revive_agent(name)`
Emergency kill-switch to pause/resume an agent.

### `show_audit_log(name, limit=10)`
Retrieve recent audit log entries for an agent.

### Decorators

```python
from sentinel import agent, monitor, agent_context

@agent("MyAgent", owner="alice", allows=["read_db"], blocks=["delete_records"])
class MyAgent: pass

@monitor
def read_db(query: str) -> dict:
    return db.execute(query)

with agent_context("MyAgent"):
    read_db("SELECT * FROM sales")  # ALLOWED — logged via backend API
```

### CLI Commands

```bash
sentinel kill <agent_name>     # Pause an agent (kill switch)
sentinel revive <agent_name>   # Reactivate an agent
sentinel log <agent_name>      # Show audit log
```

## SDK Data Layer

The SDK's `sentinel/db.py` module is an HTTP client that routes all operations through the backend:

| SDK Function | Backend Endpoint | Purpose |
|---|---|---|
| `upsert_agent()` | `POST /sdk/register-agent` | Register/update an agent |
| `upsert_policy()` | `POST /sdk/register-policy` | Register/update a policy |
| `get_agent_status()` | `GET /sdk/agent-status/{name}` | Check agent status |
| `get_policy()` | `GET /sdk/policy/{agent}/{action}` | Get policy for action |
| `log_event()` | `POST /sdk/log` | Write audit log entry |
| `update_status()` | `POST /sdk/update-status` | Kill-switch |
| `create_approval()` | `POST /sdk/approval` | Create approval request |
| `get_approval_status()` | `GET /sdk/approval-status/{id}` | Poll approval |
| `decide_approval()` | `POST /sdk/decide-approval/{id}` | Approve/deny |
| `get_audit_log()` | `GET /sdk/audit-log` | Read audit log |

## Dashboard

Aegis includes a full React dashboard for monitoring agents in real-time. See the [main repo](https://github.com/Baalavignesh/Aegis) for details.

## License

MIT — see [LICENSE](LICENSE).
