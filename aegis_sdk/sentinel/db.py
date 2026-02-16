"""HTTP-based data layer for sentinel-guardrails SDK.

All operations go through the Aegis backend API.
The backend is the single source of truth and the only entry point to MongoDB.

Configure via environment variable:
    AEGIS_BACKEND_URL=https://your-aegis-backend.vercel.app
"""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("AEGIS_BACKEND_URL", "http://localhost:8000")

_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(base_url=BACKEND_URL, timeout=30.0)
    return _client


def _post(path: str, json: dict = None) -> dict:
    resp = _get_client().post(path, json=json or {})
    resp.raise_for_status()
    return resp.json()


def _get(path: str, params: dict = None) -> dict:
    resp = _get_client().get(path, params=params)
    resp.raise_for_status()
    return resp.json()


# -- Schema -------------------------------------------------------------------

def init_db() -> None:
    _post("/sdk/init")


# -- Queries ------------------------------------------------------------------

def get_agent_status(name: str) -> Optional[str]:
    data = _get(f"/sdk/agent-status/{name}")
    return data.get("status")


def get_policy(agent_name: str, action: str) -> Optional[str]:
    data = _get(f"/sdk/policy/{agent_name}/{action}")
    return data.get("rule_type")


def get_all_policies(agent_name: str) -> list:
    data = _get(f"/sdk/policies/{agent_name}")
    return data.get("policies", [])


# -- Writes -------------------------------------------------------------------

def log_event(agent_name: str, action: str, status: str, details: str = "") -> None:
    _post("/sdk/log", {
        "agent_name": agent_name,
        "action": action,
        "status": status,
        "details": details,
    })


def update_status(name: str, status: str) -> None:
    _post("/sdk/update-status", {"name": name, "status": status})


def upsert_agent(name: str, owner: str = "") -> None:
    _post("/sdk/register-agent", {"name": name, "owner": owner})


def upsert_policy(agent_name: str, action: str, rule_type: str) -> None:
    _post("/sdk/register-policy", {
        "agent_name": agent_name,
        "action": action,
        "rule_type": rule_type,
    })


# -- Approval helpers ---------------------------------------------------------

def create_approval(agent_name: str, action: str, args_json: str = "{}") -> int:
    data = _post("/sdk/approval", {
        "agent_name": agent_name,
        "action": action,
        "args_json": args_json,
    })
    return data["approval_id"]


def get_approval_status(approval_id: int) -> Optional[str]:
    data = _get(f"/sdk/approval-status/{approval_id}")
    return data.get("status")


def decide_approval(approval_id: int, decision: str) -> None:
    _post(f"/sdk/decide-approval/{approval_id}", {"decision": decision})


def find_approval(agent_name: str, action: str) -> Optional[dict]:
    data = _get(f"/sdk/find-approval/{agent_name}/{action}")
    return data.get("approval")


def get_pending_approvals() -> list:
    data = _get("/sdk/pending-approvals")
    return data.get("approvals", [])


# -- Read helpers --------------------------------------------------------------

def get_audit_log(agent_name: Optional[str] = None, limit: int = 10) -> list:
    params = {"limit": limit}
    if agent_name:
        params["agent_name"] = agent_name
    data = _get("/sdk/audit-log", params=params)
    return data.get("entries", [])
