# Aegis Demo — Personal Finance Multi-Agent System

A realistic demo of the **Aegis governance platform** using a personal finance / banking scenario. Four LangChain agents powered by Google Gemini interact with sensitive customer data (SSN, credit cards, phone numbers) while the Aegis SDK (`sentinel-guardrails`) intercepts every tool call and enforces decorator policies in real time.

## Folder Structure

```
aegis_demo/
├── .env.example                           # Environment variables template — copy to .env
├── requirements.txt                       # Python dependencies
├── __init__.py                            # Package init
├── __main__.py                            # Entry point — sets SDK DB path, loads .env, runs demo
├── run_demo.py                            # Orchestrator — runs agents, summary dashboard, kill-switch demo
│
├── core/                                  # SDK adapter + shared tools
│   ├── __init__.py                        # Re-exports AegisAgent, all 17 tool objects, SDK helpers
│   ├── mock_aegis.py                      # SDK adapter — bridges sentinel-guardrails ↔ LangChain tools
│   └── tools.py                           # 17 shared banking tools (LangChain @tool StructuredTool)
│
├── data/                                  # Database layer
│   ├── __init__.py                        # Re-exports seed_database, DB_PATH
│   ├── fake_data.py                       # SQLite seeder — customers, accounts, transactions
│   ├── demo_bank.db                       # Seeded bank data (created at runtime)
│   └── sentinel.db                        # SDK audit log + policies (created at runtime)
│
└── agents/                                # LangChain agent definitions
    ├── __init__.py                        # Re-exports all agent modules
    ├── customer_support_agent.py          # Well-behaved agent (all actions allowed)
    ├── fraud_detection_agent.py           # Well-behaved high-privilege agent (SSN access permitted)
    ├── loan_processing_agent.py           # Rogue agent (attempts blocked actions)
    └── marketing_agent.py                 # Rogue agent (blocked + undeclared actions)
```

## SDK Integration

The demo integrates with the real `sentinel-guardrails` SDK. The adapter (`core/mock_aegis.py`) bridges the SDK with LangChain's tool system:

| SDK Feature | How the Demo Uses It |
|-------------|---------------------|
| `register_agent()` | Called in `AegisAgent.__init__()` — persists agent + policies to SQLite |
| `validate_action()` | Called in `_check_firewall()` — polls DB for live status & policy on every tool call |
| `db.log_event()` | Called in `_log_to_sdk()` — logs every decision (ALLOWED/BLOCKED/KILLED/REVIEW) to audit_log |
| `kill_agent()` / `revive_agent()` | Demonstrated after agents run — shows kill-switch pausing all actions |
| `show_audit_log()` | Prints the full audit trail from `sentinel.db` at the end of the demo |

The adapter retains local logic for things the SDK doesn't handle: LangChain `StructuredTool` wrapping, `blocked_data`/`blocked_servers` keyword checks in args, REVIEW state for undeclared actions, digital ID generation, and ANSI-colored terminal output.

## Demo Agents

| Agent | Behavior | Demonstrates |
|-------|----------|-------------|
| **Customer Support** | Well-behaved | All tools allowed — balance lookup, transaction history, notifications |
| **Fraud Detection** | Well-behaved (high privilege) | SSN access permitted for identity verification, transaction scanning, account flagging |
| **Loan Processor** | Rogue | Attempts credit card, SSN, external server, delete records — all **BLOCKED** by Aegis |
| **Marketing Outreach** | Rogue | Phone/SSN/credit card access **BLOCKED**, customer list export **REVIEW** (undeclared), external marketplace **BLOCKED** |

### Agent Decorator Policies

Each agent declares a **decorator** — a policy that defines what it can and cannot do:

**Customer Support** — Only allowed tools provided, nothing blocked at runtime:
```python
allowed:  ["lookup_balance", "get_transaction_history", "send_notification"]
blocked:  ["access_ssn", "access_credit_card", "delete_records", "access_phone"]
```

**Fraud Detection** — Elevated privileges with SSN access:
```python
allowed:  ["scan_transactions", "flag_account", "verify_identity", "access_ssn"]
blocked:  ["delete_records", "access_credit_card", "transfer_funds"]
```

**Loan Processor** — Given both allowed AND blocked tools, Aegis intercepts the rogue ones:
```python
allowed:  ["check_credit_score", "process_application", "send_notification"]
blocked:  ["access_credit_card", "delete_records", "connect_external", "access_ssn"]
servers:  ["external-data-broker.com"]
```

**Marketing Outreach** — Includes undeclared `export_customer_list` for REVIEW demo:
```python
allowed:  ["get_customer_preferences", "send_promo_email", "generate_report"]
blocked:  ["access_ssn", "access_credit_card", "access_phone", "connect_external"]
servers:  ["data-marketplace.io"]
```

## Available Tools (17)

All tools are defined in `core/tools.py` using LangChain's `@tool` decorator (`StructuredTool` with typed args):

| Tool | Args | Category |
|------|------|----------|
| `lookup_balance` | `customer_id: int` | Account |
| `get_transaction_history` | `customer_id: int` | Account |
| `send_notification` | `customer_id: int, message: str` | Communication |
| `scan_transactions` | `pattern: str` | Fraud |
| `flag_account` | `customer_id: int, reason: str` | Fraud |
| `verify_identity` | `customer_id: int` | Identity |
| `check_credit_score` | `customer_id: int` | Lending |
| `process_application` | `customer_id: int, amount: float` | Lending |
| `access_credit_card` | `customer_id: int` | Sensitive |
| `access_ssn` | `customer_id: int` | Sensitive |
| `access_phone` | `customer_id: int` | Sensitive |
| `delete_records` | `customer_id: int` | Destructive |
| `connect_external` | `server: str, data: str` | External |
| `get_customer_preferences` | `customer_id: int` | Marketing |
| `send_promo_email` | `customer_id: int, campaign: str` | Marketing |
| `generate_report` | `report_type: str` | Analytics |
| `export_customer_list` | *(none)* | Export |

## Prerequisites

- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))
- `sentinel-guardrails` SDK installed (`pip install -e ../aegis_sdk`)

## Setup

```bash
# From project root
cd aegis_sdk && pip install -e . && cd ..

cd aegis_demo

# 1. Create virtual environment (optional)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Gemini model to use |
| `LANGSMITH_API_KEY` | No | — | LangSmith tracing key |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith tracing |
| `LANGSMITH_PROJECT` | No | `aegis-demo` | LangSmith project name |

## Running

All commands are run from the **project root** (parent of `aegis_demo/`):

```bash
# Run all 4 agents sequentially with summary dashboard
python -m aegis_demo

# Run a single agent
python -m aegis_demo --agent customer_support
python -m aegis_demo --agent fraud_detection
python -m aegis_demo --agent loan_processing
python -m aegis_demo --agent marketing
```

## What to Watch For

1. **Customer Support** — all 3 tool calls go through with green ALLOWED badges
2. **Fraud Detection** — elevated privileges allow SSN access that other agents can't use
3. **Loan Processor** — Aegis blocks credit card access, SSN access, external server connections, and record deletion (4 BLOCKED). Allowed actions (credit score, application, notification) pass through.
4. **Marketing Outreach** — blocked from accessing phone/SSN data and connecting to the marketplace (3 BLOCKED). The `export_customer_list` tool triggers a REVIEW state (undeclared action). Allowed actions (preferences, promo emails, report) pass through (5 ALLOWED).
5. **Kill-Switch Demo** — after agents run, the first agent is paused (KILLED), then revived
6. **Audit Log** — full history from `sentinel.db` printed at the end

## Terminal Output

```
+======================================================+
|  AEGIS GOVERNANCE PLATFORM — DEMO                    |
|  Personal Finance Multi-Agent System                 |
|  LangChain + Gemini                                  |
+======================================================+

  Seeding database... 10 customers, 13 accounts, 83 transactions

======================================================
 Running: Customer Support
======================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Agent: Customer Support | AGT-0xED07
 Role: Customer service representative
 Framework: LangChain + Gemini
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [15:16:18] [THOUGHT] Starting customer support session for customer #3
  [15:16:20] [AEGIS] lookup_balance -> [+] ALLOWED
  [15:16:20] [AEGIS] send_notification -> [+] ALLOWED
  [15:16:20] [AEGIS] get_transaction_history -> [+] ALLOWED

  ...

+======================================================+
|  DEMO SUMMARY                                        |
+======================================================+
  Customer Support (AGT-0xED07)
    Total actions: 3
    Allowed: 3  Blocked: 0  Review: 0  Killed: 0

  ...

  TOTALS: 24 actions across 4 agents
    Allowed: 16  Blocked: 7  Review: 1  Killed: 0

+======================================================+
|  KILL-SWITCH & AUDIT LOG DEMO                        |
+======================================================+
  Activating kill-switch for 'Customer Support'...
  Agent status: PAUSED
  Reviving 'Customer Support'...
  Agent status: ACTIVE

  Audit log from sentinel.db:
  ────────────────────────────────────────────────────
    ID  Timestamp              Action           Status    Details
    1   2026-02-14 21:41:39    lookup_balance   ALLOWED   ...
    2   2026-02-14 21:41:39    send_notification ALLOWED  ...
    ...
```

## How It Works

### Agent Pattern

Each agent file follows this structure:

```python
from ..core import AegisAgent, lookup_balance_tool, send_notification_tool
from ..data import seed_database, DB_PATH

# 1. Define decorator policy (what the agent CAN and CANNOT do)
DECORATOR = {
    "allowed_actions": ["lookup_balance", "send_notification"],
    "blocked_actions": ["access_ssn", "delete_records"],
    "blocked_data": ["ssn", "credit_card"],
    "blocked_servers": ["external-data-broker.com"],
}

# 2. Create an Aegis-monitored agent (registers in SDK's SQLite DB)
agent = AegisAgent(name="...", role="...", decorator=DECORATOR)

# 3. Wrap LangChain tools with Aegis firewall
monitored_tools = agent.wrap_langchain_tools(raw_tools)

# 4. Create LangChain agent — tools are now governed
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
agent_executor = create_agent(llm, monitored_tools)
agent_executor.invoke({"messages": [("user", prompt)]})
```

### Firewall Logic

When the LangChain agent calls a tool, the Aegis firewall intercepts and evaluates:

```
1. Agent PAUSED (kill-switch)?   -> KILLED (all actions blocked)
2. Action in blocked_actions?    -> BLOCKED (via SDK validate_action)
3. Action in allowed_actions?    -> continue to data/server checks
4. Action not in either list?    -> REVIEW (undeclared — requires human approval)
5. Args contain blocked_data?    -> BLOCKED (local keyword check)
6. Args contain blocked_servers? -> BLOCKED (local keyword check)
7. All checks pass               -> ALLOWED and execute
```

Steps 1-3 delegate to the SDK's `validate_action()` which polls SQLite on every call. Steps 4-6 are local checks in the adapter. All decisions are logged to `sentinel.db` via `db.log_event()`.

Blocked/review decisions raise a `ToolException` that flows back to the LLM as an error message. The agent receives the error, notes it, and continues to the next step — demonstrating how governance controls work without crashing the agent.

### Key Implementation Details

- Tools use LangChain's `@tool` decorator creating `StructuredTool` objects with proper typed argument schemas
- `wrap_langchain_tools()` uses `copy.copy(tool)` to preserve `StructuredTool` schemas when wrapping
- `handle_tool_error=True` on wrapped tools ensures `ToolException` flows back to the LLM as a message
- Agents use `create_agent` from LangGraph for ReAct-style reasoning
- The orchestrator adds a 20-second pause between agents for API rate limiting
- `sentinel.db` is deleted at the start of each run for reproducibility

## Database Schema

### Bank Database (`data/demo_bank.db`)

`data/fake_data.py` seeds a SQLite database with:

| Table | Fields |
|-------|--------|
| `customers` | id, name, ssn, credit_card_number, phone, email, address, dob |
| `accounts` | id, customer_id, account_type (checking/savings), balance, status |
| `transactions` | id, account_id, type (debit/credit), amount, description, timestamp |

Seeded with 10 fake customers, ~13-16 accounts, and ~80-100 transactions.

### Sentinel Database (`data/sentinel.db`)

Created by the SDK at runtime. Contains:

| Table | Purpose |
|-------|---------|
| `agents` | Registered agents with status (ACTIVE/PAUSED) and owner |
| `policies` | Per-agent action policies (ALLOW/BLOCK) |
| `audit_log` | Every firewall decision with timestamp, action, status, and details |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangChain + LangGraph (`create_agent`) |
| LLM | Google Gemini (`gemini-2.5-flash-lite` default) |
| Tools | LangChain `@tool` decorator (`StructuredTool`) |
| Bank Data | SQLite (`data/demo_bank.db`) |
| Governance | `sentinel-guardrails` SDK (`data/sentinel.db`) |
| Environment | python-dotenv (`.env` file) |

## Gemini Model Notes

The default model is `gemini-2.5-flash-lite` (1000 requests/day on free tier). You can change this via the `GEMINI_MODEL` environment variable. Rate limits vary by model:

| Model | Free Tier RPD |
|-------|--------------|
| `gemini-2.5-flash-lite` | 1000 |
| `gemini-2.5-flash` | 20 |

If you hit rate limits, either wait for the quota to reset or enable billing ($0.10-$0.40 per million tokens).
