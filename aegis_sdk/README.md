# aegis-secure

Governance guardrails for autonomous AI agents. Enforce per-agent policies through decorators, log every tool call to an audit trail, pause agents instantly with a kill switch, and route sensitive actions through human-in-the-loop approval — all without modifying your agent logic.

[![PyPI](https://img.shields.io/pypi/v/aegis)](https://pypi.org/project/aegis-secure/)
[![Python](https://img.shields.io/pypi/pyversions/aegis)](https://pypi.org/project/aegis-secure/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Usage Patterns](#usage-patterns)
  - [Pattern 1: @agent + wrap_tools (LangChain / CrewAI)](#pattern-1-agent--wrap_tools)
  - [Pattern 2: @monitor + agent_context (Shared Tools)](#pattern-2-monitor--agent_context)
  - [Pattern 3: @monitor with Explicit Agent Name](#pattern-3-monitor-with-explicit-agent-name)
- [Firewall Policy Logic](#firewall-policy-logic)
- [Human-in-the-Loop Approval](#human-in-the-loop-approval)
- [Kill Switch](#kill-switch)
- [Monitor Hook](#monitor-hook)
- [Error Handling](#error-handling)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Examples](#examples)
- [License](#license)

---

## Installation

```bash
pip install aegis-secure
```

If you are using LangChain or LangGraph:

```bash
pip install aegis-secure[langchain]
```

## Prerequisites

The SDK communicates with the Aegis backend over HTTP. The backend must be running before your agent code starts.

```bash
# Start the backend (requires MongoDB running on localhost:27017)
cd aegis_backend
pip install -r requirements.txt
uvicorn backend:app --port 8000
```

The SDK connects to `http://localhost:8000` by default. Set `AEGIS_BACKEND_URL` in a `.env` file or as an environment variable to point to a different host.

## Quick Start

This example registers a support agent that can look up balances and send notifications, but is blocked from deleting records. Any action not listed in `allows` or `blocks` is routed to a human reviewer on the dashboard.

```python
from sentinel import agent

@agent(
    "Customer Support",
    owner="support-team",
    allows=["lookup_balance", "get_transaction_history", "send_notification"],
    blocks=["delete_records", "connect_external"],
)
class CustomerSupport:
    pass
```

Wrap your tools and run the agent:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# wrap_tools copies each tool and injects the firewall check.
# The original tool list is not modified.
monitored_tools = CustomerSupport.wrap_tools(your_langchain_tools)

executor = create_react_agent(llm, monitored_tools)
result = executor.invoke({
    "messages": [("user", "Look up the balance for account 42 and notify them.")]
})
```

When the agent calls `lookup_balance`, the SDK queries the backend, confirms the policy is ALLOW, executes the tool, and logs the result. If the agent tries `delete_records`, the call is blocked before execution and the LLM receives an error message it can reason about.

---

## Architecture

```
Your Agent Code (LangChain, CrewAI, plain Python)
       |
       | @agent decorator registers policies at import time
       | @monitor / wrap_tools intercepts every tool call
       |
   aegis-secure SDK
       |
       | HTTP requests (httpx)
       |
   Aegis Backend (FastAPI, port 8000)
       |
       | pymongo
       |
   MongoDB (agents, policies, audit_log, pending_approvals)
       |
   Aegis Dashboard (React, port 5173)  <-- human reviewers approve/deny here
```

The SDK never connects to MongoDB directly. All reads and writes go through the backend API, which is the single source of truth.

---

## Usage Patterns

### Pattern 1: @agent + wrap_tools

Best for LangChain and CrewAI projects where each agent has its own tool set.

The `@agent` decorator runs at import time. It registers the agent name, owner, and all policy rules in the backend database. The decorated class receives a `wrap_tools()` static method.

```python
from sentinel import agent

@agent(
    "Fraud Detection",
    owner="security-team",
    allows=[
        "scan_transactions",
        "flag_account",
        "verify_identity",
        "access_ssn",
    ],
    blocks=["delete_records", "connect_external"],
    requires_review=["freeze_account"],
)
class FraudDetection:
    pass
```

`wrap_tools()` creates a shallow copy of each tool and wraps its callable with the firewall. The original tools are untouched.

```python
monitored_tools = FraudDetection.wrap_tools(all_tools)
executor = create_react_agent(llm, monitored_tools)
result = executor.invoke({
    "messages": [("user", "Scan recent transactions and flag anything suspicious.")]
})
```

For LangChain tools, SDK exceptions are automatically converted to `ToolException` so the LLM receives an error string instead of a crash. The agent can then reason about the refusal and move on.

### Pattern 2: @monitor + agent_context

Best when multiple agents share the same tool functions. Instead of binding an agent name at decoration time, the agent is resolved at call time from a context variable.

Define tools with `@monitor()` (no agent name):

```python
from sentinel import monitor

@monitor()
def lookup_balance(account_id: str) -> dict:
    """Look up account balance from the database."""
    return db.find_one({"account_id": account_id})

@monitor()
def send_notification(customer_id: int, message: str) -> str:
    """Send a notification to a customer."""
    return notifications.send(customer_id, message)
```

At runtime, set the agent context before calling the tools:

```python
from sentinel import agent_context

# All tool calls inside this block are validated against "Customer Support" policies.
with agent_context("Customer Support"):
    balance = lookup_balance("ACC-42")
    send_notification(3, "Your balance inquiry has been processed.")

# Same tools, different agent, different policies.
with agent_context("Fraud Detection"):
    balance = lookup_balance("ACC-42")  # validated against Fraud Detection policies
```

If you need to set the context manually (for example, inside a framework that does not support `with` blocks):

```python
from sentinel import set_agent_context, reset_agent_context

token = set_agent_context("Fraud Detection")
try:
    balance = lookup_balance("ACC-42")
finally:
    reset_agent_context(token)
```

### Pattern 3: @monitor with Explicit Agent Name

For tools that belong to exactly one agent:

```python
from sentinel import monitor

@monitor("Loan Processor")
def process_application(customer_id: int, amount: float) -> dict:
    """Process a loan application."""
    return loans.submit(customer_id, amount)
```

Every call to `process_application` is validated against the "Loan Processor" agent policies, regardless of any active `agent_context`.

---

## Firewall Policy Logic

On every tool call, the SDK queries the backend for the current agent status and action policy. The evaluation order is:

1. **Kill switch** -- If the agent status is `PAUSED`, raise `SentinelKillSwitchError`. No tool executes.
2. **BLOCK policy** -- If the action is in the `blocks` list, raise `SentinelBlockedError`. No tool executes.
3. **ALLOW policy** -- If the action is in the `allows` list, execute the tool and log `ALLOWED`.
4. **REVIEW policy** -- If the action is in the `requires_review` list, create a pending approval and block the thread until a human approves or denies on the dashboard.
5. **Unknown action** -- If the action is not in any list, it is treated the same as REVIEW: a pending approval is created and the thread blocks until a human decides.

There is no caching. Every call hits the backend, so policy changes and kill-switch activations take effect immediately.

---

## Human-in-the-Loop Approval

When an action is routed to REVIEW, the SDK creates a pending approval record and blocks the calling thread until a human makes a decision on the Aegis dashboard.

```
Agent calls access_ssn()
    --> SDK checks policy: REVIEW
    --> SDK creates pending approval in the backend
    --> SDK polls every 2 seconds: GET /sdk/approval-status/{id}
    --> Human clicks "Approve" on the dashboard
    --> SDK receives APPROVED, executes the tool, logs ALLOWED
```

The blocking only affects the calling thread. If you run multiple agents in separate threads, one agent waiting for approval does not block the others.

### Blocking vs. non-blocking

The default behavior (`wait_for_approval`) blocks the thread indefinitely until the human decides. For workflows that need non-blocking behavior:

```python
from sentinel import request_approval
from sentinel.exceptions import SentinelApprovalError

try:
    request_approval("Marketing", "export_customer_list", "{}")
except SentinelApprovalError:
    # Approval has been created but not yet decided.
    # The caller can move on to other work and retry later.
    print("Waiting for human approval. Will retry.")
```

`request_approval` raises `SentinelApprovalError` immediately if the approval is still pending, letting the caller decide how to handle the wait.

---

## Kill Switch

Any agent can be paused instantly from the CLI, the dashboard, or programmatically. A paused agent cannot execute any tool -- all calls raise `SentinelKillSwitchError` until the agent is revived.

From the CLI:

```bash
sentinel kill "Fraud Detection"
# Agent 'Fraud Detection' has been PAUSED.

sentinel revive "Fraud Detection"
# Agent 'Fraud Detection' has been REVIVED.
```

From Python:

```python
from sentinel import kill_agent, revive_agent

kill_agent("Fraud Detection")   # All tool calls now raise SentinelKillSwitchError
revive_agent("Fraud Detection") # Agent resumes normal operation
```

The kill switch takes effect on the next tool call. There is no delay -- the SDK checks the agent status on every single call.

---

## Monitor Hook

Register a global callback that fires on every firewall decision. This is useful for custom logging, metrics collection, or overriding the default exception behavior.

```python
from sentinel import set_monitor_hook

def on_decision(agent_name, action, decision):
    """
    Called after every @monitor decision.

    Parameters:
        agent_name (str): The agent that triggered the call.
        action (str): The tool/function name.
        decision (str): One of "ALLOWED", "BLOCKED", or "KILLED".

    Returns:
        None to keep default behavior.
        An Exception instance to raise that instead of the default SDK exception.
    """
    print(f"[{agent_name}] {action} -> {decision}")
    return None

set_monitor_hook(on_decision)
```

Pass `None` to clear the hook:

```python
set_monitor_hook(None)
```

---

## Error Handling

The SDK raises three exception types. All are importable from `sentinel`.

**`SentinelBlockedError`** -- Raised when an action is in the agent's `blocks` list, or when a human reviewer denies a pending approval.

```python
from sentinel.exceptions import SentinelBlockedError

try:
    delete_records(customer_id=5)
except SentinelBlockedError as e:
    print(f"Blocked: {e}")
    # "Action 'delete_records' is blocked by Sentinel policy."
```

**`SentinelKillSwitchError`** -- Raised when the agent is paused via the kill switch. All tool calls for that agent will raise this error until the agent is revived.

```python
from sentinel.exceptions import SentinelKillSwitchError

try:
    lookup_balance("ACC-42")
except SentinelKillSwitchError as e:
    print(f"Agent paused: {e}")
    # "Agent 'Fraud Detection' is PAUSED. All operations are suspended.
    #  Use 'sentinel revive' to reactivate."
```

**`SentinelApprovalError`** -- Raised by `request_approval` when an approval is pending and the caller requested non-blocking behavior.

```python
from sentinel.exceptions import SentinelApprovalError

try:
    request_approval("Marketing", "export_customer_list", "{}")
except SentinelApprovalError as e:
    print(f"Pending: {e}")
    # "Action 'export_customer_list' requires human approval
    #  (Approval #7). Retry after approval."
```

For LangChain tools wrapped via `wrap_tools()`, all three exceptions are automatically converted to `ToolException`, so the LLM receives an error string and can reason about it.

---

## CLI Reference

The `sentinel` command is installed automatically with the package.

```
sentinel kill <agent_name>              Pause an agent. All tool calls raise
                                        SentinelKillSwitchError until revived.

sentinel revive <agent_name>            Reactivate a paused agent.

sentinel logs <agent_name> [--limit N]  Print the last N audit log entries for
                                        the agent (default: 10).
```

Examples:

```bash
sentinel kill "Customer Support"
sentinel revive "Customer Support"
sentinel logs "Fraud Detection" --limit 20
```

---

## API Reference

### Decorators

#### `@agent(name, *, owner="", allows=None, blocks=None, requires_review=None)`

Class decorator. Registers the agent and its policy rules in the backend database at import time.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Unique agent identifier. |
| `owner` | `str` | Team or individual responsible for this agent. |
| `allows` | `list[str]` | Action names that are always permitted. |
| `blocks` | `list[str]` | Action names that are always denied. |
| `requires_review` | `list[str]` | Action names that require human approval. |

**Adds to the decorated class:**

| Attribute | Description |
|---|---|
| `wrap_tools(tools)` | Static method. Copies each tool and wraps it with the firewall. Supports LangChain `StructuredTool`, CrewAI `BaseTool`, and plain callables. |
| `__enter__` / `__exit__` | Context manager support. Sets `agent_context` for the duration of the block. |
| `_sentinel_agent_name` | The registered agent name string. |

#### `@monitor(agent_name=None)`

Function decorator. Wraps a callable with the firewall check.

- `@monitor("AgentName")` -- validates against the specified agent on every call.
- `@monitor()` -- resolves the agent at call time from `agent_context`. Raises `RuntimeError` if no context is set.

#### `agent_context(agent_name)`

Context manager. Sets the active agent for `@monitor()` calls within the block.

```python
with agent_context("Fraud Detection"):
    scan_transactions()  # validated against "Fraud Detection"
```

#### `set_agent_context(agent_name) -> Token`

Manually set the active agent. Returns a token that must be passed to `reset_agent_context` to restore the previous value. Use this in frameworks that do not support `with` blocks.

#### `reset_agent_context(token)`

Restore the agent context to its previous value.

#### `set_monitor_hook(callback)`

Register a global callback invoked on every `@monitor` decision. Pass `None` to clear. The callback signature is `callback(agent_name: str, action: str, decision: str)` where `decision` is `"ALLOWED"`, `"BLOCKED"`, or `"KILLED"`.

### Functions

| Function | Description |
|---|---|
| `kill_agent(name)` | Set the agent status to PAUSED. |
| `revive_agent(name)` | Set the agent status to ACTIVE. |
| `show_audit_log(name, limit=10)` | Print recent audit log entries to stdout. |
| `wait_for_approval(agent_name, action_name, args_json)` | Block until a human approves or denies. Returns `True` on approval, raises `SentinelBlockedError` on denial. |
| `request_approval(agent_name, action_name, args_json)` | Non-blocking. Returns `True` if already approved, raises `SentinelBlockedError` if denied, raises `SentinelApprovalError` if still pending. |

### Exceptions

| Exception | Raised When |
|---|---|
| `SentinelBlockedError` | Action is in the `blocks` list, or a human reviewer denied the approval. |
| `SentinelKillSwitchError` | Agent is PAUSED (kill switch is active). |
| `SentinelApprovalError` | Non-blocking approval check found a pending request (from `request_approval`). |

---

## Configuration

The SDK has no hardcoded values. All behavior is controlled by the user through decorators and environment variables.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AEGIS_BACKEND_URL` | `http://localhost:8000` | URL of the Aegis backend API that the SDK sends all requests to. |

Create a `.env` file in your project root:

```
AEGIS_BACKEND_URL=http://localhost:8000
```

The SDK loads `.env` automatically via `python-dotenv`. You can also set the variable directly in your shell:

```bash
export AEGIS_BACKEND_URL=https://your-aegis-backend.example.com
```

### Backend Requirement

The SDK does not connect to any database directly. It requires a running instance of the Aegis backend API, which handles all persistence (MongoDB), session management, and serves the monitoring dashboard.

For local development:

```bash
# Terminal 1: Start MongoDB (if not already running)
mongod

# Terminal 2: Start the Aegis backend
cd aegis_backend
pip install -r requirements.txt
uvicorn backend:app --port 8000

# Terminal 3: (Optional) Start the monitoring dashboard
cd aegis_frontend
npm install
npm run dev    # serves at http://localhost:5173
```

For production, deploy the backend to any hosting provider (Vercel, Railway, AWS, etc.) and point the SDK to it:

```
AEGIS_BACKEND_URL=https://aegis-backend-production.up.railway.app
```

### What the user defines (nothing is hardcoded in the SDK)

| Concern | Where you define it |
|---|---|
| Agent names and owners | `@agent` decorator in your code |
| Policy rules (allows, blocks, requires_review) | `@agent` decorator in your code |
| Tool functions | Your own codebase, wrapped via `wrap_tools()` or `@monitor` |
| Backend URL | `AEGIS_BACKEND_URL` environment variable |
| Monitor hook behavior | `set_monitor_hook()` in your code |

---

## Examples

### Multi-agent system with shared tools

Four agents share the same 17 tools. Each agent has different policies -- the Aegis firewall is the only enforcement layer.

```python
from sentinel import agent
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Agent definitions (policies registered at import time) ---

@agent(
    "Customer Support",
    owner="support-team",
    allows=["lookup_balance", "get_transaction_history", "send_notification"],
    blocks=["delete_records", "connect_external"],
)
class CustomerSupport:
    pass

@agent(
    "Fraud Detection",
    owner="security-team",
    allows=[
        "scan_transactions", "flag_account", "verify_identity",
        "access_ssn", "check_credit_score", "lookup_balance",
    ],
    blocks=["delete_records", "connect_external"],
)
class FraudDetection:
    pass

@agent(
    "Loan Processor",
    owner="lending-team",
    allows=["check_credit_score", "process_application", "send_notification"],
    blocks=["delete_records", "connect_external"],
)
class LoanProcessor:
    pass

@agent(
    "Marketing",
    owner="growth-team",
    allows=["get_customer_preferences", "send_promo_email", "generate_report"],
    blocks=["delete_records", "connect_external"],
)
class Marketing:
    pass


# --- Run each agent with its own wrapped tools ---

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# Customer Support can call lookup_balance (ALLOWED) but if it tries
# access_ssn, that action is not in any list, so it goes to REVIEW.
support_tools = CustomerSupport.wrap_tools(all_tools)
support_agent = create_react_agent(llm, support_tools)

# Fraud Detection can call access_ssn (ALLOWED) -- same tool, different policy.
fraud_tools = FraudDetection.wrap_tools(all_tools)
fraud_agent = create_react_agent(llm, fraud_tools)
```

### Running agents in parallel

When one agent is blocked waiting for human approval, other agents can continue if they run in separate threads.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_support():
    result = support_agent.invoke({
        "messages": [("user", "Look up balance for account 42.")]
    })
    return result["messages"][-1].content

def run_fraud():
    result = fraud_agent.invoke({
        "messages": [("user", "Scan transactions for suspicious activity.")]
    })
    return result["messages"][-1].content

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(run_support), pool.submit(run_fraud)]
    for future in as_completed(futures):
        print(future.result())
```

### Custom error handling with the monitor hook

Log every firewall decision to an external service and convert blocked actions into user-friendly messages:

```python
from sentinel import set_monitor_hook
from sentinel.exceptions import SentinelBlockedError

def audit_hook(agent_name, action, decision):
    # Log to your observability platform
    logger.info(f"agent={agent_name} action={action} decision={decision}")

    if decision == "BLOCKED":
        # Return a custom exception instead of the default SentinelBlockedError
        return SentinelBlockedError(
            f"The {agent_name} agent is not authorized to perform '{action}'. "
            f"Contact the security team if this action is required."
        )

    return None  # keep default behavior for ALLOWED and KILLED

set_monitor_hook(audit_hook)
```

---

## SDK Internal Endpoints

The SDK's data layer (`sentinel/db.py`) routes all operations through the backend API. These endpoints are called by the SDK automatically -- you do not need to call them directly.

| SDK Function | HTTP Method | Endpoint | Purpose |
|---|---|---|---|
| `init_db()` | POST | `/sdk/init` | Initialize session |
| `upsert_agent()` | POST | `/sdk/register-agent` | Register or update an agent |
| `upsert_policy()` | POST | `/sdk/register-policy` | Register or update a policy |
| `get_agent_status()` | GET | `/sdk/agent-status/{name}` | Check if agent is ACTIVE or PAUSED |
| `get_policy()` | GET | `/sdk/policy/{agent}/{action}` | Get the policy rule for an action |
| `log_event()` | POST | `/sdk/log` | Write an audit log entry |
| `update_status()` | POST | `/sdk/update-status` | Change agent status (kill switch) |
| `create_approval()` | POST | `/sdk/approval` | Create a pending approval |
| `get_approval_status()` | GET | `/sdk/approval-status/{id}` | Poll approval status |
| `decide_approval()` | POST | `/sdk/decide-approval/{id}` | Record approval decision |
| `find_approval()` | GET | `/sdk/find-approval/{agent}/{action}` | Find existing approval |
| `get_audit_log()` | GET | `/sdk/audit-log` | Read audit log entries |

---

## License

MIT. See [LICENSE](LICENSE).
