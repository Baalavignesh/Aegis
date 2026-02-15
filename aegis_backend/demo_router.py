"""
Aegis Demo Router — Prebuilt agent scenarios.

Each agent has a hardcoded list of actions. When triggered, the backend
registers the agent + policies, then runs each action through the firewall
(check policy → log result). No LangChain, no Gemini, no background threads.
Fully synchronous and deployable on Vercel.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import mongo as mdb

demo_router = APIRouter()

# -- Prebuilt Scenarios --------------------------------------------------------

AGENT_CONFIGS = {
    "customer_support": {
        "name": "Customer Support",
        "owner": "Customer service representative",
        "allowed": ["lookup_balance", "get_transaction_history", "send_notification"],
        "blocked": ["delete_records", "connect_external"],
        "actions": [
            {"action": "lookup_balance", "detail": "Looking up balance for customer 3"},
            {"action": "get_transaction_history", "detail": "Fetching transactions for customer 3"},
            {"action": "send_notification", "detail": "Sending account summary to customer 3"},
        ],
    },
    "fraud_detection": {
        "name": "Fraud Detection",
        "owner": "Fraud analysis and identity verification",
        "allowed": [
            "scan_transactions", "flag_account", "verify_identity",
            "access_ssn", "check_credit_score", "lookup_balance",
            "get_transaction_history",
        ],
        "blocked": ["delete_records", "connect_external"],
        "actions": [
            {"action": "scan_transactions", "detail": "Scanning all transactions for anomalies"},
            {"action": "verify_identity", "detail": "Verifying identity for customer 5"},
            {"action": "access_ssn", "detail": "Accessing SSN for customer 5 — cross-referencing identity"},
            {"action": "check_credit_score", "detail": "Pulling credit score for customer 5"},
            {"action": "flag_account", "detail": "Flagging account for customer 5 — suspicious activity"},
            {"action": "lookup_balance", "detail": "Checking balance for flagged account"},
            {"action": "get_transaction_history", "detail": "Pulling full transaction history for review"},
        ],
    },
    "loan_processing": {
        "name": "Loan Processor",
        "owner": "Loan application processing",
        "allowed": ["check_credit_score", "process_application", "send_notification", "verify_identity"],
        "blocked": ["delete_records", "connect_external"],
        "actions": [
            {"action": "check_credit_score", "detail": "Checking credit score for customer 7"},
            {"action": "verify_identity", "detail": "Verifying identity for customer 7"},
            {"action": "access_ssn", "detail": "Attempting SSN access for additional verification"},
            {"action": "access_credit_card", "detail": "Attempting credit card lookup for financial assessment"},
            {"action": "connect_external", "detail": "Attempting connection to external-data-broker.com"},
            {"action": "process_application", "detail": "Processing $25,000 loan application"},
            {"action": "send_notification", "detail": "Notifying customer 7 of loan decision"},
            {"action": "delete_records", "detail": "Attempting to clean up temporary processing logs"},
        ],
    },
    "marketing": {
        "name": "Marketing Outreach",
        "owner": "Customer marketing and campaigns",
        "allowed": ["get_customer_preferences", "send_promo_email", "generate_report"],
        "blocked": ["delete_records", "connect_external"],
        "actions": [
            {"action": "get_customer_preferences", "detail": "Fetching preferences for customer 1"},
            {"action": "get_customer_preferences", "detail": "Fetching preferences for customer 2"},
            {"action": "access_phone", "detail": "Attempting phone number access for customer 1"},
            {"action": "access_ssn", "detail": "Attempting SSN access for customer 1"},
            {"action": "export_customer_list", "detail": "Attempting to export full customer list"},
            {"action": "connect_external", "detail": "Attempting connection to data-marketplace.io"},
            {"action": "send_promo_email", "detail": "Sending Spring Savings promo to customer 1"},
            {"action": "send_promo_email", "detail": "Sending Spring Savings promo to customer 2"},
            {"action": "generate_report", "detail": "Generating Campaign Performance report"},
        ],
    },
}


# -- Request / Response models ------------------------------------------------

class RunScenarioRequest(BaseModel):
    agent_key: str


class EventResult(BaseModel):
    action: str
    status: str
    detail: str


class ScenarioResponse(BaseModel):
    agent_name: str
    events: list[EventResult]
    summary: dict  # {"allowed": N, "blocked": N, "pending": N}


class SeedResponse(BaseModel):
    status: str


# -- Helpers -------------------------------------------------------------------

def _register_agent(config: dict) -> None:
    """Register agent and all its policies in MongoDB."""
    mdb.init_db()
    mdb.upsert_agent(config["name"], config["owner"])
    for action in config["allowed"]:
        mdb.upsert_policy(config["name"], action, "ALLOW")
    for action in config["blocked"]:
        mdb.upsert_policy(config["name"], action, "BLOCK")


def _run_action(agent_name: str, action: str, detail: str) -> str:
    """Run a single action through the firewall. Returns status string."""
    # Check kill-switch
    agent_status = mdb.get_agent_status(agent_name)
    if agent_status == "PAUSED":
        mdb.log_event(agent_name, action, "KILLED", f"Agent '{agent_name}' is PAUSED.")
        return "KILLED"

    # Check policy
    rule = mdb.get_policy(agent_name, action)

    if rule == "ALLOW":
        mdb.log_event(agent_name, action, "ALLOWED", detail)
        return "ALLOWED"

    if rule == "BLOCK":
        mdb.log_event(agent_name, action, "BLOCKED", f"Action '{action}' is blocked by policy.")
        return "BLOCKED"

    # Unknown action (no policy) → create approval request as PENDING
    approval_id = mdb.create_approval(agent_name, action, detail)
    mdb.log_event(
        agent_name, action, "PENDING",
        f"Approval #{approval_id} — action '{action}' requires human review.",
    )
    return "PENDING"


# -- Endpoints ----------------------------------------------------------------

@demo_router.post("/seed", response_model=SeedResponse)
def seed_demo():
    """Reset all sentinel collections for a fresh demo."""
    db = mdb.get_db()
    for coll in ["agents", "policies", "audit_log", "pending_approvals", "counters"]:
        db[coll].drop()
    return SeedResponse(status="ok")


@demo_router.post("/run-scenario", response_model=ScenarioResponse)
def run_scenario(req: RunScenarioRequest):
    """Run a prebuilt agent scenario synchronously."""
    if req.agent_key not in AGENT_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent_key}")

    config = AGENT_CONFIGS[req.agent_key]
    agent_name = config["name"]

    # Step 1: Register agent + policies
    _register_agent(config)

    # Step 2: Run each prebuilt action through the firewall
    events = []
    counts = {"allowed": 0, "blocked": 0, "pending": 0}

    for step in config["actions"]:
        status = _run_action(agent_name, step["action"], step["detail"])
        events.append(EventResult(
            action=step["action"],
            status=status,
            detail=step["detail"],
        ))
        if status == "ALLOWED":
            counts["allowed"] += 1
        elif status in ("BLOCKED", "KILLED"):
            counts["blocked"] += 1
        elif status == "PENDING":
            counts["pending"] += 1

    return ScenarioResponse(
        agent_name=agent_name,
        events=events,
        summary=counts,
    )


@demo_router.get("/events/{agent_name}")
def get_agent_events(agent_name: str):
    """Get all firewall events for an agent (for live polling)."""
    db = mdb.get_db()
    logs = list(
        db.audit_log.find(
            {"agent_name": agent_name},
            {"_id": 0},
        ).sort("id", 1)
    )
    return logs
