"""
FastAPI backend for the Sentinel Guardrails dashboard.

This is the SINGLE entry point to MongoDB. Both the dashboard frontend
and the SDK communicate with the database exclusively through this API.
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mongo as mdb

# -- App Setup ----------------------------------------------------------------

app = FastAPI(
    title="Sentinel Guardrails API",
    description="Dashboard backend + SDK gateway for monitoring agentic AI policies.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from demo_router import demo_router
app.include_router(demo_router, prefix="/demo")


# -- Pydantic Models (Dashboard) ----------------------------------------------

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


# -- Pydantic Models (SDK) ----------------------------------------------------

class SDKRegisterAgentRequest(BaseModel):
    name: str
    owner: str = ""


class SDKRegisterPolicyRequest(BaseModel):
    agent_name: str
    action: str
    rule_type: str


class SDKLogEventRequest(BaseModel):
    agent_name: str
    action: str
    status: str
    details: str = ""


class SDKCreateApprovalRequest(BaseModel):
    agent_name: str
    action: str
    args_json: str = "{}"


class SDKDecideApprovalRequest(BaseModel):
    decision: str


class SDKUpdateStatusRequest(BaseModel):
    name: str
    status: str


# ==============================================================================
# Dashboard Endpoints (consumed by React frontend)
# ==============================================================================

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """Dashboard header stats."""
    db = mdb.get_db()

    registered = db.agents.count_documents({})
    active = db.agents.count_documents({"status": "ACTIVE"})

    cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    blocks_24h = db.audit_log.count_documents({
        "status": "BLOCKED",
        "timestamp": {"$gte": cutoff},
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
    db = mdb.get_db()
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

    db = mdb.get_db()
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

    db = mdb.get_db()
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
    if body.status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(status_code=400, detail="Status must be ACTIVE or PAUSED")
    mdb.update_status(name, body.status)
    return {"status": "updated", "new_status": body.status}


@app.get("/agents/{name}/policies", response_model=PoliciesResponse)
def get_policies(name: str):
    """Get all allow/block/review rules for an agent."""
    policies = mdb.get_all_policies(name)

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
    rows = mdb.get_pending_approvals()

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
    current = mdb.get_approval_status(approval_id)
    if not current:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if current != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already {current}")
    if body.decision not in ("APPROVED", "DENIED"):
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or DENIED")

    mdb.decide_approval(approval_id, body.decision)
    return {"status": "success", "decision": body.decision}


# ==============================================================================
# SDK Endpoints (consumed by aegis-sentinel SDK via HTTP)
# ==============================================================================

@app.post("/sdk/init")
def sdk_init():
    """Initialize database indexes. Called once on SDK startup."""
    mdb.init_db()
    return {"status": "ok"}


@app.post("/sdk/register-agent")
def sdk_register_agent(body: SDKRegisterAgentRequest):
    """Register or update an agent."""
    mdb.upsert_agent(body.name, body.owner)
    return {"status": "ok"}


@app.post("/sdk/register-policy")
def sdk_register_policy(body: SDKRegisterPolicyRequest):
    """Register or update a policy rule."""
    mdb.upsert_policy(body.agent_name, body.action, body.rule_type)
    return {"status": "ok"}


@app.get("/sdk/agent-status/{name}")
def sdk_agent_status(name: str):
    """Get the current status of an agent (ACTIVE / PAUSED)."""
    status = mdb.get_agent_status(name)
    return {"status": status}


@app.get("/sdk/policy/{agent_name}/{action}")
def sdk_get_policy(agent_name: str, action: str):
    """Get the policy rule_type for a specific agent+action."""
    rule = mdb.get_policy(agent_name, action)
    return {"rule_type": rule}


@app.post("/sdk/log")
def sdk_log_event(body: SDKLogEventRequest):
    """Write an audit log entry."""
    mdb.log_event(body.agent_name, body.action, body.status, body.details)
    return {"status": "ok"}


@app.post("/sdk/update-status")
def sdk_update_status(body: SDKUpdateStatusRequest):
    """Update agent status (kill-switch)."""
    mdb.update_status(body.name, body.status)
    return {"status": "ok"}


@app.post("/sdk/approval")
def sdk_create_approval(body: SDKCreateApprovalRequest):
    """Create a pending approval request. Returns the approval ID."""
    approval_id = mdb.create_approval(body.agent_name, body.action, body.args_json)
    return {"approval_id": approval_id}


@app.get("/sdk/approval-status/{approval_id}")
def sdk_approval_status(approval_id: int):
    """Poll the status of an approval request."""
    status = mdb.get_approval_status(approval_id)
    return {"status": status}


@app.post("/sdk/decide-approval/{approval_id}")
def sdk_decide_approval(approval_id: int, body: SDKDecideApprovalRequest):
    """Decide on an approval request."""
    mdb.decide_approval(approval_id, body.decision)
    return {"status": "ok"}


@app.get("/sdk/policies/{agent_name}")
def sdk_get_all_policies(agent_name: str):
    """Get all policy rules for an agent."""
    policies = mdb.get_all_policies(agent_name)
    return {"policies": policies}


@app.get("/sdk/pending-approvals")
def sdk_pending_approvals():
    """List pending approval requests."""
    rows = mdb.get_pending_approvals()
    return {"approvals": rows}


@app.get("/sdk/audit-log")
def sdk_audit_log(agent_name: Optional[str] = None, limit: int = 10):
    """Get audit log entries."""
    rows = mdb.get_audit_log(agent_name, limit)
    return {"entries": rows}
