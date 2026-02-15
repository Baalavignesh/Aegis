"""Direct MongoDB layer for the Aegis backend.

This is the ONLY module that talks to MongoDB directly.
The SDK no longer connects to MongoDB — it calls the backend API instead.
"""

import os
from typing import Optional
from datetime import datetime

import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "sentinel_db")

_CLIENT = None


def get_db():
    """Get the MongoDB database object. Reuses the client."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = MongoClient(MONGO_URI)
    return _CLIENT[DB_NAME]


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
    """Initialize indexes."""
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
        }
    )


def update_status(name: str, status: str) -> None:
    get_db().agents.update_one({"name": name}, {"$set": {"status": status}})


def upsert_agent(name: str, owner: str = "") -> None:
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    result = db.agents.find_one({"name": name})
    if result:
        db.agents.update_one({"name": name}, {"$set": {"owner": owner}})
    else:
        db.agents.insert_one(
            {"name": name, "status": "ACTIVE", "owner": owner, "created_at": now}
        )


def upsert_policy(agent_name: str, action: str, rule_type: str) -> None:
    get_db().policies.update_one(
        {"agent_name": agent_name, "action": action},
        {"$set": {"rule_type": rule_type}},
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
        }
    )
    return new_id


def get_approval_status(approval_id: int) -> Optional[str]:
    doc = get_db().pending_approvals.find_one({"id": approval_id}, {"status": 1})
    return doc["status"] if doc else None


def decide_approval(approval_id: int, decision: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    get_db().pending_approvals.update_one(
        {"id": approval_id},
        {"$set": {"status": decision, "decided_at": now}},
    )


def get_pending_approvals() -> list:
    cursor = get_db().pending_approvals.find({"status": "PENDING"}).sort("id", -1)
    results = []
    for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results


def get_audit_log(agent_name: Optional[str] = None, limit: int = 10) -> list:
    db = get_db()
    query = {"agent_name": agent_name} if agent_name else {}
    cursor = db.audit_log.find(query).sort("id", -1).limit(limit)
    rows = []
    for doc in cursor:
        doc.pop("_id", None)
        rows.append(doc)
    return list(reversed(rows))
