"""Direct MongoDB layer for the Aegis backend.

This is the ONLY module that talks to MongoDB directly.
The SDK no longer connects to MongoDB — it calls the backend API instead.

Session tracking: each SDK init creates a new session_id. All writes are
tagged with it. Dashboard endpoints filter by the current session so only
fresh data is displayed — old sessions stay in the DB for history.
"""

import os
import uuid
from typing import Optional
from datetime import datetime

import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "sentinel_db")

_CLIENT = None
_current_session_id: Optional[str] = None


def get_db():
    """Get the MongoDB database object. Reuses the client."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = MongoClient(MONGO_URI)
    return _CLIENT[DB_NAME]


def get_current_session_id() -> Optional[str]:
    """Return the active session_id (None until first SDK init)."""
    return _current_session_id


def _get_next_sequence(collection_name: str) -> int:
    """Simulate AUTOINCREMENT for IDs using a counters collection."""
    db = get_db()
    ret = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER,
    )
    return ret["seq"]


# -- Schema ------------------------------------------------------------------

def init_db() -> None:
    """Initialize indexes and start a new session.

    Every call creates a fresh session_id. All subsequent writes are
    tagged with it, and dashboard endpoints filter by it.
    """
    global _current_session_id
    _current_session_id = uuid.uuid4().hex[:12]
    db = get_db()
    db.agents.create_index("name", unique=True)
    db.policies.create_index([("agent_name", 1), ("action", 1)], unique=True)
    db.audit_log.create_index("id", unique=True)
    db.audit_log.create_index([("id", -1)])
    db.pending_approvals.create_index("id", unique=True)


# -- Queries ------------------------------------------------------------------

def get_agent_status(name: str) -> Optional[str]:
    doc = get_db().agents.find_one({"name": name}, {"status": 1})
    return doc["status"] if doc else None


def get_policy(agent_name: str, action: str) -> Optional[str]:
    doc = get_db().policies.find_one(
        {"agent_name": agent_name, "action": action},
        {"rule_type": 1},
    )
    return doc["rule_type"] if doc else None


def get_all_policies(agent_name: str) -> list:
    cursor = get_db().policies.find(
        {"agent_name": agent_name}, {"action": 1, "rule_type": 1, "_id": 0}
    )
    return list(cursor)


# -- Writes -------------------------------------------------------------------

def log_event(
    agent_name: str,
    action: str,
    status: str,
    details: str = "",
) -> None:
    db = get_db()
    new_id = _get_next_sequence("audit_log")
    db.audit_log.insert_one(
        {
            "id": new_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_name": agent_name,
            "action": action,
            "status": status,
            "details": details,
            "session_id": _current_session_id,
        }
    )


def update_status(name: str, status: str) -> None:
    get_db().agents.update_one({"name": name}, {"$set": {"status": status}})


def upsert_agent(name: str, owner: str = "") -> None:
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.agents.update_one(
        {"name": name},
        {
            "$set": {
                "owner": owner,
                "status": "REGISTERED",
                "session_id": _current_session_id,
                "registered_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


def upsert_policy(agent_name: str, action: str, rule_type: str) -> None:
    get_db().policies.update_one(
        {"agent_name": agent_name, "action": action},
        {"$set": {"rule_type": rule_type, "session_id": _current_session_id}},
        upsert=True,
    )


# -- Approval helpers ---------------------------------------------------------

def create_approval(
    agent_name: str, action: str, args_json: str = "{}"
) -> int:
    db = get_db()
    new_id = _get_next_sequence("pending_approvals")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.pending_approvals.insert_one(
        {
            "id": new_id,
            "agent_name": agent_name,
            "action": action,
            "args_json": args_json,
            "status": "PENDING",
            "created_at": now,
            "decided_at": None,
            "session_id": _current_session_id,
        }
    )
    return new_id


def get_approval_status(approval_id: int) -> Optional[str]:
    doc = get_db().pending_approvals.find_one({"id": approval_id}, {"status": 1})
    return doc["status"] if doc else None


def decide_approval(approval_id: int, decision: str) -> None:
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Look up the approval to get agent_name + action before updating
    approval = db.pending_approvals.find_one({"id": approval_id})

    # Update the pending_approvals record
    db.pending_approvals.update_one(
        {"id": approval_id},
        {"$set": {"status": decision, "decided_at": now}},
    )

    # Update the original PENDING audit_log entry so the firewall decision
    # graph reflects the resolved status, not a stale "PENDING".
    if approval:
        db.audit_log.update_one(
            {
                "agent_name": approval["agent_name"],
                "action": approval["action"],
                "status": "PENDING",
                "details": {"$regex": f"Approval #{approval_id}"},
            },
            {"$set": {
                "status": decision,
                "details": f"Approval #{approval_id} — {decision.lower()} by human reviewer.",
            }},
        )


def find_approval(agent_name: str, action: str) -> Optional[dict]:
    """Find the most recent approval for agent+action in current session."""
    query = {"agent_name": agent_name, "action": action}
    if _current_session_id:
        query["session_id"] = _current_session_id
    doc = get_db().pending_approvals.find_one(query, sort=[("id", -1)])
    if doc:
        doc.pop("_id", None)
    return doc


def get_pending_approvals() -> list:
    query = {"status": "PENDING"}
    if _current_session_id:
        query["session_id"] = _current_session_id
    cursor = get_db().pending_approvals.find(query).sort("id", -1)
    results = []
    for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results


def get_audit_log(agent_name: Optional[str] = None, limit: int = 10) -> list:
    db = get_db()
    query = {}
    if _current_session_id:
        query["session_id"] = _current_session_id
    if agent_name:
        query["agent_name"] = agent_name
    cursor = db.audit_log.find(query).sort("id", -1).limit(limit)
    rows = []
    for doc in cursor:
        doc.pop("_id", None)
        rows.append(doc)
    return list(reversed(rows))
