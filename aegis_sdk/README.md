# aegis-sentinel 🛡️

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
        "blocked_data": [],
        "blocked_servers": [],
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
| 🎯 **Policy Decorators** | Define allowed/blocked actions per agent |
| 📝 **Audit Logging** | Every tool call logged to MongoDB with timestamps |
| 🛑 **Kill Switch** | Instantly pause any agent |
| 👤 **Human-in-the-Loop** | Actions requiring approval wait for human decision |
| 🔌 **LangChain Native** | Works with LangChain tools out of the box |
| 🍃 **MongoDB Backend** | Scales with your infrastructure |

## Environment Variables

```bash
# Required
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGO_DB_NAME=sentinel_db   # optional, defaults to sentinel_db
```

## API Reference

### `AegisAgent(name, role, decorator)`
Create a governed agent with policy rules.

### `agent.wrap_langchain_tools(tools)`
Wrap LangChain tools with policy enforcement. Returns monitored tools.

### `agent.log_thought(message)`
Log agent reasoning to the audit trail.

### `kill_agent(name)` / `revive_agent(name)`
Emergency kill-switch to pause/resume an agent.

### `show_audit_log(name, limit=10)`
Retrieve recent audit log entries for an agent.

## Dashboard

Aegis includes a full React dashboard for monitoring agents in real-time. See the [main repo](https://github.com/Baalavignesh/Aegis) for details.

## License

MIT — see [LICENSE](LICENSE).
