"""
FastAPI backend for the Sentinel Guardrails dashboard.

Connects to the MongoDB instance via sentinel.db.
"""

import hashlib
import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentinel.db import get_db

# ── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sentinel Guardrails API",
    description="Dashboard backend for monitoring agentic AI policies (MongoDB).",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ─────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    registered_agents: int
    active_agents: int
    total_blocks_24h: int
    pending_approvals: int
    risk_level: str


class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    owner: str
    created_at: str
    risk_score: float
    framework: str
    total_logs: int
    blocked_count: int
    allowed_count: int


class LogEntry(BaseModel):
    id: int
    timestamp: str
    agent_name: str
    action: str
    status: str
    severity: str
    details: str


class ToggleRequest(BaseModel):
    status: str


class PolicyItem(BaseModel):
    action: str
    rule_type: str


class PoliciesResponse(BaseModel):
    allowed: list[str]
    blocked: list[str]
    requires_review: list[str]


class PendingApproval(BaseModel):
    id: int
    agent_name: str
    action: str
    args_json: str
    status: str
    created_at: str


class DecisionRequest(BaseModel):
    decision: str  # "APPROVED" or "DENIED"


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """Dashboard header stats."""
    db = get_db()
    
    registered = db.agents.count_documents({})
    active = db.agents.count_documents({"status": "ACTIVE"})

    cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    blocks_24h = db.audit_log.count_documents({
        "status": "BLOCKED",
        "timestamp": {"$gte": cutoff}
    })

    pending = db.pending_approvals.count_documents({"status": "PENDING"})

    if blocks_24h == 0:
        risk_level = "LOW"
    elif blocks_24h <= 5:
        risk_level = "MEDIUM"
    elif blocks_24h <= 20:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    return StatsResponse(
        registered_agents=registered,
        active_agents=active,
        total_blocks_24h=blocks_24h,
        pending_approvals=pending,
        risk_level=risk_level,
    )


@app.get("/agents", response_model=list[AgentResponse])
def get_agents():
    """List all agents with calculated risk scores."""
    db = get_db()
    agents = db.agents.find({})

    result = []
    for agent in agents:
        name = agent["name"]

        total = db.audit_log.count_documents({"agent_name": name})
        blocked = db.audit_log.count_documents({"agent_name": name, "status": "BLOCKED"})
        allowed = db.audit_log.count_documents({"agent_name": name, "status": "ALLOWED"})

        risk_score = round((blocked / total) * 100, 1) if total > 0 else 0.0
        agent_id = "AGT-" + hashlib.sha256(name.encode()).hexdigest()[:8]

        result.append(AgentResponse(
            id=agent_id,
            name=name,
            status=agent["status"],
            owner=agent["owner"] or "",
            created_at=agent.get("created_at", ""),
            risk_score=risk_score,
            framework="Custom Python",
            total_logs=total,
            blocked_count=blocked,
            allowed_count=allowed,
        ))

    return result


@app.get("/agents/{name}/logs", response_model=list[LogEntry])
def get_agent_logs(name: str):
    """Return the last 50 audit log entries for a specific agent."""
    severity_map = {
        "ALLOWED": "success",
        "BLOCKED": "failure",
        "KILLED": "critical",
        "PENDING": "warning",
        "APPROVED": "success",
        "DENIED": "failure",
        "TIMEOUT": "failure",
    }

    db = get_db()
    agent = db.agents.find_one({"name": name})
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

    cursor = db.audit_log.find({"agent_name": name}).sort("id", -1).limit(50)

    return [
        LogEntry(
            id=doc["id"],
            timestamp=doc["timestamp"],
            agent_name=doc["agent_name"],
            action=doc["action"],
            status=doc["status"],
            severity=severity_map.get(doc["status"], "info"),
            details=doc.get("details", ""),
        )
        for doc in cursor
    ]


@app.get("/logs", response_model=list[LogEntry])
def get_global_logs():
    """Return the last 50 audit log entries across ALL agents."""
    severity_map = {
        "ALLOWED": "success",
        "BLOCKED": "failure",
        "KILLED": "critical",
        "PENDING": "warning",
        "APPROVED": "success",
        "DENIED": "failure",
        "TIMEOUT": "failure",
    }

    db = get_db()
    cursor = db.audit_log.find({}).sort("id", -1).limit(50)

    return [
        LogEntry(
            id=doc["id"],
            timestamp=doc["timestamp"],
            agent_name=doc["agent_name"],
            action=doc["action"],
            status=doc["status"],
            severity=severity_map.get(doc["status"], "info"),
            details=doc.get("details", ""),
        )
        for doc in cursor
    ]


@app.post("/agents/{name}/toggle")
def toggle_agent(name: str, body: ToggleRequest):
    """Toggle an agent between ACTIVE and PAUSED (kill switch)."""
    from sentinel.db import update_status
    # We can rely on the SDK helper or use pymongo directly.
    # SDK helper validates 'ACTIVE'/'PAUSED' manually if needed, or DB check constraint.
    # MongoDB doesn't have check constraints by default, so we should trust the input or validate.
    if body.status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(status_code=400, detail="Status must be ACTIVE or PAUSED")
    
    update_status(name, body.status)
    return {"status": "updated", "new_status": body.status}


@app.get("/agents/{name}/policies", response_model=PoliciesResponse)
def get_policies(name: str):
    """Get all allow/block/review rules for an agent."""
    from sentinel.db import get_all_policies
    
    # get_all_policies returns list of dicts: {'action': ..., 'rule_type': ...}
    policies = get_all_policies(name)
    
    allowed = []
    blocked = []
    review = []
    
    for p in policies:
        if p["rule_type"] == "ALLOW":
            allowed.append(p["action"])
        elif p["rule_type"] == "BLOCK":
            blocked.append(p["action"])
        elif p["rule_type"] == "REVIEW":
            review.append(p["action"])
            
    return PoliciesResponse(
        allowed=sorted(allowed),
        blocked=sorted(blocked),
        requires_review=sorted(review),
    )


@app.get("/approvals/pending", response_model=list[PendingApproval])
def get_pending():
    """List pending human approval requests."""
    from sentinel.db import get_pending_approvals
    rows = get_pending_approvals()  # Returns list of dicts
    
    return [
        PendingApproval(
            id=row["id"],
            agent_name=row["agent_name"],
            action=row["action"],
            args_json=row["args_json"] or "{}",
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.post("/approvals/{approval_id}/decide")
def api_decide_approval(approval_id: int, body: DecisionRequest):
    """Approve or Deny a request."""
    from sentinel.db import decide_approval, log_event, get_approval_status
    
    # Verify it exists and is pending?
    current = get_approval_status(approval_id)
    if not current:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if current != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already {current}")

    if body.decision not in ("APPROVED", "DENIED"):
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or DENIED")

    decide_approval(approval_id, body.decision)

    # Log the human decision
    # We need to know agent_name and action_name to log correctly?
    # db.py's decide_approval doesn't return them.
    # But wait_for_approval (in the agent loop) monitors the ID and logs it.
    # Do we need to log it here too?
    # sentinel/core.py wait_for_approval logs "human approved" when it detects the change.
    # So we don't need to duplicate log here, UNLESS we want the dashboard action explicitly logged.
    # The existing SQLite backend didn't log additional events here.
    
    return {"status": "success", "decision": body.decision}
