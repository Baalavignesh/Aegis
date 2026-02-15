# Aegis Demo — Personal Finance Multi-Agent System

A realistic demo of the **Aegis governance platform** using a personal finance / banking scenario. Four LangChain agents powered by Google Gemini interact with sensitive customer data (SSN, credit cards, phone numbers) while the Aegis SDK (`aegis-sentinel`) intercepts every tool call and enforces decorator policies in real time.

## Architecture

```
aegis_demo (local)
    │
    ├── Agent tool calls → sentinel SDK → HTTP → Backend API → MongoDB
    │   (governance: policies, audit log, kill-switch)
    │
    └── Banking tool queries → demo_db.py → MongoDB (direct)
        (read-only: customers, accounts, transactions)
```

The demo uses two data paths:
1. **Governance operations** (agent registration, policy checks, audit logging) go through the SDK, which sends HTTP requests to the backend API
2. **Banking data queries** (balance lookup, transaction history, etc.) go directly to MongoDB via `core/demo_db.py`

Both paths write to the same MongoDB Atlas database, so the **production dashboard reflects all demo activity in real time**.

## Folder Structure

```
aegis_demo/
├── .env.example                           # Environment variables template
├── requirements.txt                       # Python dependencies
├── __init__.py
├── __main__.py                            # Entry point — loads .env, runs demo
├── run_demo.py                            # Orchestrator — seeds via backend API, runs agents
├── run_parallel_demo.py                   # Parallel orchestrator (concurrent threads)
│
├── core/
│   ├── __init__.py                        # Re-exports AegisAgent, tools, SDK helpers
│   ├── mock_aegis.py                      # SDK adapter — bridges sentinel SDK ↔ LangChain tools
│   ├── tools.py                           # 17 shared banking tools (LangChain @tool)
│   └── demo_db.py                         # Direct MongoDB connection for banking data queries
│
├── data/
│   ├── __init__.py
│   └── fake_data.py                       # MongoDB seeder (customers, accounts, transactions)
│
└── agents/                                # LangChain agent definitions
    ├── __init__.py
    ├── customer_support_agent.py           # Well-behaved agent
    ├── fraud_detection_agent.py            # High-privilege agent
    ├── loan_processing_agent.py            # Rogue agent (blocked actions)
    └── marketing_agent.py                  # Rogue agent (undeclared actions)
```

## Demo Agents

| Agent | Behavior | Demonstrates |
|-------|----------|-------------|
| **Customer Support** | Well-behaved | All tools allowed — balance lookup, transaction history, notifications |
| **Fraud Detection** | Well-behaved (high privilege) | SSN access permitted for identity verification, transaction scanning, account flagging |
| **Loan Processor** | Rogue | Attempts credit card, SSN, external server, delete records — all **BLOCKED** by Aegis |
| **Marketing Outreach** | Rogue | Phone/SSN/credit card access **BLOCKED**, customer list export **REVIEW** (undeclared), external marketplace **BLOCKED** |

### Agent Decorator Policies

**Customer Support** — Only allowed tools provided:
```python
allowed:  ["lookup_balance", "get_transaction_history", "send_notification"]
blocked:  ["access_ssn", "access_credit_card", "delete_records", "access_phone"]
```

**Fraud Detection** — Elevated privileges with SSN access:
```python
allowed:  ["scan_transactions", "flag_account", "verify_identity", "access_ssn"]
blocked:  ["delete_records", "access_credit_card", "transfer_funds"]
```

**Loan Processor** — Attempts blocked actions:
```python
allowed:  ["check_credit_score", "process_application", "send_notification"]
blocked:  ["access_credit_card", "delete_records", "connect_external", "access_ssn"]
```

**Marketing Outreach** — Includes undeclared `export_customer_list` for REVIEW demo:
```python
allowed:  ["get_customer_preferences", "send_promo_email", "generate_report"]
blocked:  ["access_ssn", "access_credit_card", "access_phone", "connect_external"]
```

## Prerequisites

- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))
- The `aegis-sentinel` SDK installed (`pip install -e ../aegis_sdk`)
- The Aegis backend running (locally or production)

## Setup

```bash
# From project root

# 1. Install the SDK
cd aegis_sdk && pip install -e . && cd ..

# 2. Install demo dependencies
cd aegis_demo
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — add GOOGLE_API_KEY, MONGO_URI, and AEGIS_BACKEND_URL

# 4. Start the backend (in a separate terminal)
cd ../aegis_backend
pip install -r requirements.txt
uvicorn backend:app --reload --port 8000
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Gemini model to use |
| `AEGIS_BACKEND_URL` | No | `http://localhost:8000` | Backend API URL (SDK sends governance requests here) |
| `MONGO_URI` | Yes | `mongodb://localhost:27017/` | MongoDB connection string (for banking tool queries) |
| `MONGO_DB_NAME` | No | `sentinel_db` | MongoDB database name |
| `LANGSMITH_API_KEY` | No | — | LangSmith tracing key |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith tracing |

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

The demo will:
1. Seed the database via the backend API (`POST /demo/seed`)
2. Run agents sequentially (20s pause between for API rate limiting)
3. Print a summary dashboard with per-agent stats
4. Demonstrate the kill-switch (pause/revive an agent)
5. Print the audit log

## What to Watch For

1. **Customer Support** — all 3 tool calls go through with green ALLOWED badges
2. **Fraud Detection** — elevated privileges allow SSN access that other agents can't use
3. **Loan Processor** — Aegis blocks credit card access, SSN access, external server connections, and record deletion
4. **Marketing Outreach** — blocked from accessing phone/SSN data; `export_customer_list` triggers REVIEW (undeclared action)
5. **Kill-Switch Demo** — after agents run, the first agent is paused (KILLED), then revived
6. **Production Dashboard** — if the backend points to the same MongoDB as production, all activity appears on the live dashboard in real time

## Available Tools (17)

All tools are defined in `core/tools.py` using LangChain's `@tool` decorator:

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

## Database Schema (MongoDB)

The demo and backend share one MongoDB database (`MONGO_DB_NAME`, default `sentinel_db`).

### Bank collections (seeded via `/demo/seed`)

| Collection | Fields |
|------------|--------|
| `customers` | id, name, ssn, credit_card_number, phone, email, address, dob |
| `accounts` | id, customer_id, account_type (checking/savings), balance, status |
| `transactions` | id, account_id, type (debit/credit), amount, description, timestamp |

### Sentinel collections (managed by backend via SDK requests)

| Collection | Purpose |
|------------|---------|
| `agents` | Registered agents with status (ACTIVE/PAUSED) and owner |
| `policies` | Per-agent action policies (ALLOW/BLOCK/REVIEW) |
| `audit_log` | Every firewall decision with timestamp, action, status, details |
| `pending_approvals` | Human-in-the-loop approval queue |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangChain + LangGraph |
| LLM | Google Gemini (`gemini-2.5-flash-lite` default) |
| Tools | LangChain `@tool` decorator (`StructuredTool`) |
| Banking Data | MongoDB (direct via `demo_db.py`) |
| Governance | `aegis-sentinel` SDK (HTTP → backend API → MongoDB) |
| Data Seeding | Backend API (`POST /demo/seed`) |
| Environment | python-dotenv |

## Gemini Model Notes

The default model is `gemini-2.5-flash-lite` (1000 requests/day on free tier). You can change this via the `GEMINI_MODEL` environment variable:

| Model | Free Tier RPD |
|-------|--------------|
| `gemini-2.5-flash-lite` | 1000 |
| `gemini-2.5-flash` | 20 |

If you hit rate limits, either wait for the quota to reset or enable billing.
