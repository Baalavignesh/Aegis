# sentinel-guardrails

Python SDK for defining, enforcing, and auditing AI agent policies using decorators with SQLite persistence.

## Installation

```bash
cd aegis_sdk
pip install -e .
```

## Quick Start

```python
from sentinel import agent, monitor, agent_context

@agent("AegisBot", owner="alice", allows=["get_price"], blocks=["send_money"])
class AegisBot:
    pass

@monitor
def get_price(symbol: str) -> str:
    return f"{symbol}: $100"

@monitor
def send_money(to: str, amount: float) -> str:
    return f"Sent {amount} to {to}"

with agent_context("AegisBot"):
    get_price("BTC")      # ALLOWED — logged to audit_log
    send_money("Eve", 50) # raises SentinelBlockedError
```

### Shared Tools Across Agents

The same `@monitor`-decorated function works under different agents — the policy check depends on which agent is active in the context:

```python
from sentinel import monitor, agent_context
from sentinel.core import register_agent

register_agent("SupportBot", allows=["lookup_balance"], blocks=["delete_records"])
register_agent("AdminBot",   allows=["lookup_balance", "delete_records"])

@monitor
def lookup_balance(customer_id: int) -> str:
    return f"Balance: $5,000"

@monitor
def delete_records(table: str) -> str:
    return f"Deleted {table}"

with agent_context("SupportBot"):
    lookup_balance(42)    # ALLOWED
    delete_records("tmp") # BLOCKED

with agent_context("AdminBot"):
    lookup_balance(42)    # ALLOWED
    delete_records("tmp") # ALLOWED
```

## API Reference

### Decorators

**`@agent(name, *, owner="", allows=None, blocks=None)`**

Registers an agent and seeds its policies into the SQLite database at import time.

- `name` — unique agent identifier (also the DB primary key)
- `owner` — optional owner/role string
- `allows` — list of action names to ALLOW
- `blocks` — list of action names to BLOCK

**`@monitor`**

Wraps a function with the database-polling firewall. On every call it:

1. Reads the active agent from `agent_context`
2. Queries the DB for the agent's status (kill-switch check)
3. Queries the DB for the action's policy (ALLOW/BLOCK)
4. Logs the result to `audit_log`
5. Raises `SentinelBlockedError` or `SentinelKillSwitchError` if denied

### Context Management

```python
from sentinel import agent_context, set_agent_context, reset_agent_context
```

**`agent_context(name)`** — context manager that sets the active agent for a block:

```python
with agent_context("FraudBot"):
    scan_transactions()  # checks FraudBot's policies
```

**`set_agent_context(name)` / `reset_agent_context(token)`** — manual control for frameworks that can't use `with` blocks:

```python
token = set_agent_context("FraudBot")
try:
    scan_transactions()
finally:
    reset_agent_context(token)
```

### Core Functions

```python
from sentinel.core import register_agent, validate_action
```

- **`register_agent(name, owner="", allows=None, blocks=None)`** — upserts agent + policy rows
- **`validate_action(agent_name, action_name)`** — polls DB, returns `True` (ALLOW), `False` (unknown), or raises on BLOCK/KILLED

### CLI Helpers

```python
from sentinel import kill_agent, revive_agent, show_audit_log
```

- **`kill_agent(name)`** — sets agent status to PAUSED (kill switch)
- **`revive_agent(name)`** — sets agent status back to ACTIVE
- **`show_audit_log(name, limit=10)`** — prints the last N audit log entries

Also available as CLI commands: `sentinel kill <name>`, `sentinel revive <name>`, `sentinel log <name>`.

### Exceptions

- **`SentinelBlockedError(action)`** — raised when a BLOCK policy matches
- **`SentinelKillSwitchError(agent_name)`** — raised when the agent is PAUSED
- **`SentinelApprovalError(action)`** — raised when human approval is required

### Database Layer

```python
from sentinel import db

db.DB_PATH = "path/to/sentinel.db"  # set before any calls
db.init_db()                         # create tables
db.log_event(agent, action, status, details)
db.get_audit_log(agent, limit=10)
db.update_status(agent, "PAUSED")
db.get_agent_status(agent)
db.get_policy(agent, action)
```

## SQLite Schema

```sql
CREATE TABLE agents (
    name       TEXT PRIMARY KEY,
    status     TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','PAUSED')),
    owner      TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE policies (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    action     TEXT NOT NULL,
    rule_type  TEXT NOT NULL CHECK(rule_type IN ('ALLOW','BLOCK')),
    UNIQUE(agent_name, action)
);

CREATE TABLE audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT DEFAULT (datetime('now')),
    agent_name TEXT NOT NULL,
    action     TEXT NOT NULL,
    status     TEXT NOT NULL CHECK(status IN ('ALLOWED','BLOCKED','KILLED')),
    details    TEXT DEFAULT ''
);
```

## How It Works

1. **`@agent`** runs at import time — writes agent + policy rows to SQLite
2. **`@monitor`** wraps functions — on each call, reads the active agent from `agent_context`, then queries the DB for live status and policy
3. No caching — every call hits SQLite, so policy changes (including kill-switch) take effect immediately
4. All decisions are logged to `audit_log` for full traceability

## Architecture

```
Your Agent Code
    │
    ├── @agent("Bot", allows=[...], blocks=[...])
    │       └── writes to SQLite: agents + policies tables
    │
    └── @monitor
            └── on each call:
                 ├── read agent_context        (who is calling?)
                 ├── SELECT status FROM agents  (kill-switch)
                 ├── SELECT rule_type FROM policies (ALLOW/BLOCK)
                 ├── execute function or raise error
                 └── INSERT INTO audit_log
```
