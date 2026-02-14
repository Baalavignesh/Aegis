"""
FastAPI backend for the Sentinel Guardrails dashboard.

Connects to the existing sentinel.db managed by db.py.
Uses raw SQL queries — no ORM table redefinition.

Run with:
    uvicorn backend:app --reload
"""

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sentinel Guardrails API",
    description="Dashboard backend for monitoring agentic AI policies.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default: resolve to the demo's sentinel.db relative to this file's location.
# Override with SENTINEL_DB_PATH env var if needed.
DB_PATH = os.environ.get(
    "SENTINEL_DB_PATH",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "aegis_demo", "data", "sentinel.db",
    ),
)


# ── Database Helper ─────────────────────────────────────────────────────────

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a short-lived SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


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
    with get_db() as conn:
        registered = conn.execute("SELECT COUNT(*) as cnt FROM agents").fetchone()["cnt"]
        active = conn.execute(
            "SELECT COUNT(*) as cnt FROM agents WHERE status = 'ACTIVE'"
        ).fetchone()["cnt"]

        cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        blocks_24h = conn.execute(
            "SELECT COUNT(*) as cnt FROM audit_log "
            "WHERE status = 'BLOCKED' AND timestamp >= ?",
            (cutoff,),
        ).fetchone()["cnt"]

        pending = conn.execute(
            "SELECT COUNT(*) as cnt FROM pending_approvals WHERE status = 'PENDING'"
        ).fetchone()["cnt"]

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
    with get_db() as conn:
        agents = conn.execute("SELECT * FROM agents").fetchall()

        result = []
        for agent in agents:
            name = agent["name"]

            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM audit_log WHERE agent_name = ?",
                (name,),
            ).fetchone()["cnt"]

            blocked = conn.execute(
                "SELECT COUNT(*) as cnt FROM audit_log "
                "WHERE agent_name = ? AND status = 'BLOCKED'",
                (name,),
            ).fetchone()["cnt"]

            allowed = conn.execute(
                "SELECT COUNT(*) as cnt FROM audit_log "
                "WHERE agent_name = ? AND status = 'ALLOWED'",
                (name,),
            ).fetchone()["cnt"]

            risk_score = round((blocked / total) * 100, 1) if total > 0 else 0.0
            agent_id = "AGT-" + hashlib.sha256(name.encode()).hexdigest()[:8]

            result.append(AgentResponse(
                id=agent_id,
                name=name,
                status=agent["status"],
                owner=agent["owner"] or "",
                created_at=agent["created_at"] or "",
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

    with get_db() as conn:
        agent = conn.execute(
            "SELECT name FROM agents WHERE name = ?", (name,)
        ).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")
        
        # Use existing query logic
        rows = conn.execute(
            "SELECT id, timestamp, agent_name, action, status, details "
            "FROM audit_log WHERE agent_name = ? "
            "ORDER BY id DESC LIMIT 50",
            (name,),
        ).fetchall()

    return [
        LogEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            agent_name=row["agent_name"],
            action=row["action"],
            status=row["status"],
            severity=severity_map.get(row["status"], "info"),
            details=row["details"] or "",
        )
        for row in rows
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

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, agent_name, action, status, details "
            "FROM audit_log ORDER BY id DESC LIMIT 50"
        ).fetchall()

    return [
        LogEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            agent_name=row["agent_name"],
            action=row["action"],
            status=row["status"],
            severity=severity_map.get(row["status"], "info"),
            details=row["details"] or "",
        )
        for row in rows
    ]


@app.post("/agents/{name}/toggle")
def toggle_agent(name: str, body: ToggleRequest):
    """Toggle an agent between ACTIVE and PAUSED (kill switch)."""
    if body.status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(
            status_code=400,
            detail="Status must be 'ACTIVE' or 'PAUSED'.",
        )

    with get_db() as conn:
        agent = conn.execute(
            "SELECT name FROM agents WHERE name = ?", (name,)
        ).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

        conn.execute(
            "UPDATE agents SET status = ? WHERE name = ?",
            (body.status, name),
        )

    action = "PAUSED" if body.status == "PAUSED" else "ACTIVATED"
    return {"message": f"Agent '{name}' has been {action}.", "status": body.status}


# ── NEW: Policies endpoint ──────────────────────────────────────────────────

@app.get("/agents/{name}/policies", response_model=PoliciesResponse)
def get_agent_policies(name: str):
    """Return the allowed, blocked, and review-required tools for an agent."""
    with get_db() as conn:
        agent = conn.execute(
            "SELECT name FROM agents WHERE name = ?", (name,)
        ).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

        rows = conn.execute(
            "SELECT action, rule_type FROM policies WHERE agent_name = ?",
            (name,),
        ).fetchall()

    allowed = [r["action"] for r in rows if r["rule_type"] == "ALLOW"]
    blocked = [r["action"] for r in rows if r["rule_type"] == "BLOCK"]
    requires_review = [r["action"] for r in rows if r["rule_type"] == "REVIEW"]

    return PoliciesResponse(
        allowed=allowed,
        blocked=blocked,
        requires_review=requires_review,
    )


# ── NEW: Approvals endpoints ───────────────────────────────────────────────

@app.get("/approvals/pending", response_model=list[PendingApproval])
def get_pending_approvals():
    """Return all PENDING approval requests."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, agent_name, action, args_json, status, created_at "
            "FROM pending_approvals WHERE status = 'PENDING' "
            "ORDER BY id DESC",
        ).fetchall()

    return [
        PendingApproval(
            id=row["id"],
            agent_name=row["agent_name"],
            action=row["action"],
            args_json=row["args_json"] or "{}",
            status=row["status"],
            created_at=row["created_at"] or "",
        )
        for row in rows
    ]


@app.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: int, body: DecisionRequest):
    """Approve or deny a pending approval request."""
    if body.decision not in ("APPROVED", "DENIED"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'APPROVED' or 'DENIED'.",
        )

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, status FROM pending_approvals WHERE id = ?",
            (approval_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Approval #{approval_id} not found.")

        if row["status"] != "PENDING":
            raise HTTPException(
                status_code=400,
                detail=f"Approval #{approval_id} has already been decided: {row['status']}.",
            )

        conn.execute(
            "UPDATE pending_approvals SET status = ?, decided_at = datetime('now') "
            "WHERE id = ?",
            (body.decision, approval_id),
        )

    return {
        "message": f"Approval #{approval_id} has been {body.decision}.",
        "approval_id": approval_id,
        "decision": body.decision,
    }


# ── Run command (for reference) ─────────────────────────────────────────────
# uvicorn backend:app --reload
