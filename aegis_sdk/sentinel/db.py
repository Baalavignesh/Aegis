"""MongoDB database layer for sentinel-guardrails.

Attempts to maintain the same function signatures as the SQLite version,
but interacts with MongoDB collections.
"""

import os
import time
from typing import Optional, Any
from datetime import datetime

import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env to get MONGO_URI if present
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
        return_document=pymongo.ReturnDocument.AFTER
    )
    return ret["seq"]


# ── Schema ──────────────────────────────────────────────────────────────────

def init_db(db_path: Optional[str] = None) -> None:
    """Initialize indexes."""
    db = get_db()
    
    # agents: name is unique
    db.agents.create_index("name", unique=True)
    
    # policies: unique(agent_name, action)
    db.policies.create_index([("agent_name", 1), ("action", 1)], unique=True)
    
    # audit_log: index on id (desc)
    db.audit_log.create_index("id", unique=True)
    db.audit_log.create_index([("id", -1)])
    
    # approvals
    db.pending_approvals.create_index("id", unique=True)


# ── Queries ─────────────────────────────────────────────────────────────────

def get_agent_status(name: str, db_path: Optional[str] = None) -> Optional[str]:
    db = get_db()
    doc = db.agents.find_one({"name": name}, {"status": 1})
    return doc["status"] if doc else None


def get_policy(agent_name: str, action: str, db_path: Optional[str] = None) -> Optional[str]:
    db = get_db()
    doc = db.policies.find_one(
        {"agent_name": agent_name, "action": action},
        {"rule_type": 1}
    )
    return doc["rule_type"] if doc else None


def get_all_policies(agent_name: str, db_path: Optional[str] = None) -> list:
    db = get_db()
    cursor = db.policies.find({"agent_name": agent_name}, {"action": 1, "rule_type": 1, "_id": 0})
    return list(cursor)


# ── Writes ──────────────────────────────────────────────────────────────────

def log_event(
    agent_name: str,
    action: str,
    status: str,
    details: str = "",
    db_path: Optional[str] = None,
) -> None:
    db = get_db()
    new_id = _get_next_sequence("audit_log")
    
    doc = {
        "id": new_id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_name": agent_name,
        "action": action,
        "status": status,
        "details": details
    }
    db.audit_log.insert_one(doc)


def update_status(name: str, status: str, db_path: Optional[str] = None) -> None:
    db = get_db()
    db.agents.update_one(
        {"name": name},
        {"$set": {"status": status}}
    )


def upsert_agent(name: str, owner: str = "", db_path: Optional[str] = None) -> None:
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Attempt update, if not exists insert.
    # Note: SQLite logic was ON CONFLICT(name) DO UPDATE SET owner...
    # We want to preserve status if it exists.
    
    result = db.agents.find_one({"name": name})
    if result:
        # Update owner only
        db.agents.update_one({"name": name}, {"$set": {"owner": owner}})
    else:
        # Insert new
        db.agents.insert_one({
            "name": name,
            "status": "ACTIVE",
            "owner": owner,
            "created_at": now
        })


def upsert_policy(
    agent_name: str, action: str, rule_type: str, db_path: Optional[str] = None
) -> None:
    db = get_db()
    # Unique index on (agent_name, action)
    db.policies.update_one(
        {"agent_name": agent_name, "action": action},
        {"$set": {"rule_type": rule_type}},
        upsert=True
    )


# ── Approval helpers ────────────────────────────────────────────────────────

def create_approval(
    agent_name: str, action: str, args_json: str = "{}", db_path: Optional[str] = None
) -> int:
    db = get_db()
    new_id = _get_next_sequence("pending_approvals")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    doc = {
        "id": new_id,
        "agent_name": agent_name,
        "action": action,
        "args_json": args_json,
        "status": "PENDING",
        "created_at": now,
        "decided_at": None
    }
    db.pending_approvals.insert_one(doc)
    return new_id


def get_approval_status(approval_id: int, db_path: Optional[str] = None) -> Optional[str]:
    db = get_db()
    doc = db.pending_approvals.find_one({"id": approval_id}, {"status": 1})
    return doc["status"] if doc else None


def decide_approval(
    approval_id: int, decision: str, db_path: Optional[str] = None
) -> None:
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.pending_approvals.update_one(
        {"id": approval_id},
        {"$set": {"status": decision, "decided_at": now}}
    )


def get_pending_approvals(db_path: Optional[str] = None) -> list:
    db = get_db()
    cursor = db.pending_approvals.find({"status": "PENDING"}).sort("id", -1)
    
    results = []
    for doc in cursor:
        doc.pop("_id", None) # Remove ObjectId
        results.append(doc)
    return results


# ── Read helpers (for CLI / manifest) ───────────────────────────────────────

def get_audit_log(agent_name: Optional[str] = None, limit: int = 10, db_path: Optional[str] = None) -> list:
    db = get_db()
    
    if agent_name:
        cursor = db.audit_log.find({"agent_name": agent_name})
    else:
        cursor = db.audit_log.find({})
        
    cursor = cursor.sort("id", -1).limit(limit)
    
    # Return reversed list to match SQLite behavior (older to newer)?
    # Wait, SQLite query was ORDER BY id DESC LIMIT ?. Then reversed(rows).
    # So SQLite returned [oldest ... newest] of the last N.
    # We fetch DESC (newest first). So [newest ... oldest].
    # We should reverse it to return [oldest ... newest].
    
    rows = []
    for doc in cursor:
        doc.pop("_id", None)
        rows.append(doc)
        
    return list(reversed(rows))
