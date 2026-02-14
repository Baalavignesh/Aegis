# Aegis — AI Agent Governance Platform

**Monitor, control, and secure autonomous AI agents.**

Aegis is a firewall and observability layer for AI agents. It gives developers and organizations full visibility into what agents do and what they access — with the power to stop them when they deviate.

> Think of it as **Cloudflare for AI Agents** — outbound policy enforcement, governance, and audit for any autonomous system.

## The Problem

AI agents (LangGraph, CrewAI, AutoGen, LangChain) are increasingly autonomous. They call APIs, access databases, read files, and make decisions — but there's no standardized way to:

- **See** what an agent is doing in real time
- **Control** what actions an agent is allowed to take
- **Stop** an agent when it deviates from expected behavior
- **Audit** every decision an agent made after the fact

## How It Works

```
Developer defines policy          Sentinel enforces it
─────────────────────────         ──────────────────────────────
@agent("SupportBot",              Every tool call is intercepted:
  allows=["lookup_balance"],        1. Check agent status (kill-switch)
  blocks=["delete_records"])        2. Check action policy (ALLOW/BLOCK)
                                    3. Check data & server restrictions
@monitor                            4. Log decision to audit_log
def lookup_balance(cid): ...        5. Execute or raise error

with agent_context("SupportBot"):
    lookup_balance(42)   # ALLOWED
    delete_records("x")  # BLOCKED
```

### Key Feature: Context-Based Policy Enforcement

Tools are shared — the same `lookup_balance` function might be called by a Support agent, a Fraud agent, and an Admin agent. Aegis uses Python's `contextvars` to resolve which agent is calling at runtime:

```python
@monitor
def lookup_balance(customer_id): ...

with agent_context("SupportBot"):
    lookup_balance(42)     # checks SupportBot's policies

with agent_context("FraudBot"):
    lookup_balance(42)     # checks FraudBot's policies
```

## Project Structure

| Module | Description | Status |
|--------|------------|--------|
| **aegis_sdk/** | `sentinel-guardrails` — Python SDK with `@agent`, `@monitor`, `agent_context`, SQLite policy engine, kill-switch, audit log | Implemented |
| **aegis_demo/** | 4 LangChain + Gemini agents (banking scenario) demonstrating firewall governance | Implemented |
| **aegis_backend/** | FastAPI server — agent registry, policy engine, governance rules, WebSocket events | Spec only |
| **aegis_frontend/** | React dashboard — live monitoring, dependency graph, review queue, analytics | Spec only |

## Quick Start

```bash
# 1. Install the SDK
cd aegis_sdk && pip install -e . && cd ..

# 2. Install demo dependencies
cd aegis_demo && pip install -r requirements.txt && cd ..

# 3. Configure API key
cp aegis_demo/.env.example aegis_demo/.env
# Edit .env and add your GOOGLE_API_KEY

# 4. Run the demo
python -m aegis_demo
```

## SDK At a Glance

```python
from sentinel import agent, monitor, agent_context, kill_agent, revive_agent

# Register agent with policies (persisted to SQLite)
@agent("MyBot", owner="alice", allows=["read_data"], blocks=["delete_data"])
class MyBot: pass

# Decorate shared tools — agent resolved from context at call time
@monitor
def read_data(query: str) -> str:
    return db.execute(query)

# Use tools under an agent's context
with agent_context("MyBot"):
    read_data("SELECT * FROM users")  # ALLOWED — logged to audit_log

# Kill switch — immediately blocks all actions
kill_agent("MyBot")
# ... later ...
revive_agent("MyBot")
```

## Core Concepts

- **Digital Identity** — Each agent gets a unique ID (`AGT-0x{hash}`) tracked across its lifecycle
- **Decorator Policy** — Three-dimensional permissions: actions, data, and servers with allowed/blocked lists
- **Firewall Logic** — blocked → BLOCK; allowed → continue checks; unknown → REVIEW; then check data and servers
- **Agent Context** — `contextvars`-based resolution so shared tools enforce the correct agent's policy at call time
- **Kill Switch** — Set any agent to PAUSED instantly; all actions blocked until revived
- **Audit Log** — Every decision (ALLOWED/BLOCKED/KILLED) persisted to SQLite with timestamps

## Full Documentation

- **[AGENT-SENTINEL-README.md](AGENT-SENTINEL-README.md)** — Comprehensive platform spec: API reference, SDK usage guide, governance rules, roadmap
- **[aegis_sdk/README.md](aegis_sdk/README.md)** — SDK API reference and usage examples
- **[aegis_demo/README.md](aegis_demo/README.md)** — Demo setup, agent policies, and expected output

## License

MIT License
