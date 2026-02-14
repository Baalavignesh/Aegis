"""SQLite database layer for sentinel-guardrails.

Every public function opens and closes its own connection via
contextlib for thread safety — no shared state.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

DB_PATH = "sentinel.db"


@contextmanager
def _connect(db_path: str = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Yield a short-lived SQLite connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ──────────────────────────────────────────────────────────────────

def init_db(db_path: str = DB_PATH) -> None:
    """Create the core tables if they don't already exist."""
    with _connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                name       TEXT PRIMARY KEY,
                status     TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','PAUSED')),
                owner      TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS policies (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                action     TEXT NOT NULL,
                rule_type  TEXT NOT NULL CHECK(rule_type IN ('ALLOW','BLOCK','REVIEW')),
                UNIQUE(agent_name, action)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT DEFAULT (datetime('now')),
                agent_name TEXT NOT NULL,
                action     TEXT NOT NULL,
                status     TEXT NOT NULL CHECK(
                    status IN ('ALLOWED','BLOCKED','KILLED','PENDING','APPROVED','DENIED','TIMEOUT')
                ),
                details    TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS pending_approvals (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                action     TEXT NOT NULL,
                args_json  TEXT DEFAULT '{}',
                status     TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING','APPROVED','DENIED')),
                created_at TEXT DEFAULT (datetime('now')),
                decided_at TEXT
            );
        """)


# ── Queries (called on every function invocation — the "poll") ──────────

def get_agent_status(name: str, db_path: str = DB_PATH) -> Optional[str]:
    """Return ``'ACTIVE'``, ``'PAUSED'``, or ``None`` if not found."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT status FROM agents WHERE name = ?", (name,)
        ).fetchone()
    return row["status"] if row else None


def get_policy(agent_name: str, action: str, db_path: str = DB_PATH) -> Optional[str]:
    """Return ``'ALLOW'``, ``'BLOCK'``, ``'REVIEW'``, or ``None``."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT rule_type FROM policies WHERE agent_name = ? AND action = ?",
            (agent_name, action),
        ).fetchone()
    return row["rule_type"] if row else None


def get_all_policies(agent_name: str, db_path: str = DB_PATH) -> list:
    """Return all policy rows for an agent."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT action, rule_type FROM policies WHERE agent_name = ?",
            (agent_name,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Writes ──────────────────────────────────────────────────────────────────

def log_event(
    agent_name: str,
    action: str,
    status: str,
    details: str = "",
    db_path: str = DB_PATH,
) -> None:
    """Append one row to the ``audit_log`` table."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_log (agent_name, action, status, details) "
            "VALUES (?, ?, ?, ?)",
            (agent_name, action, status, details),
        )


def update_status(name: str, status: str, db_path: str = DB_PATH) -> None:
    """Set an agent's status to ``'ACTIVE'`` or ``'PAUSED'``."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE agents SET status = ? WHERE name = ?", (status, name)
        )


def upsert_agent(name: str, owner: str = "", db_path: str = DB_PATH) -> None:
    """Insert the agent or update the owner if it already exists."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO agents (name, owner) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET owner = excluded.owner",
            (name, owner),
        )


def upsert_policy(
    agent_name: str, action: str, rule_type: str, db_path: str = DB_PATH
) -> None:
    """Insert or replace a single policy row."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO policies (agent_name, action, rule_type) VALUES (?, ?, ?) "
            "ON CONFLICT(agent_name, action) DO UPDATE SET rule_type = excluded.rule_type",
            (agent_name, action, rule_type),
        )


# ── Approval helpers ────────────────────────────────────────────────────────

def create_approval(
    agent_name: str, action: str, args_json: str = "{}", db_path: str = DB_PATH
) -> int:
    """Create a PENDING approval row. Returns the approval ID."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO pending_approvals (agent_name, action, args_json) "
            "VALUES (?, ?, ?)",
            (agent_name, action, args_json),
        )
        return cursor.lastrowid


def get_approval_status(approval_id: int, db_path: str = DB_PATH) -> Optional[str]:
    """Return the status of an approval: 'PENDING', 'APPROVED', or 'DENIED'."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT status FROM pending_approvals WHERE id = ?", (approval_id,)
        ).fetchone()
    return row["status"] if row else None


def decide_approval(
    approval_id: int, decision: str, db_path: str = DB_PATH
) -> None:
    """Set approval to 'APPROVED' or 'DENIED'."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE pending_approvals SET status = ?, decided_at = datetime('now') "
            "WHERE id = ?",
            (decision, approval_id),
        )


def get_pending_approvals(db_path: str = DB_PATH) -> list:
    """Return all PENDING approval rows."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, agent_name, action, args_json, status, created_at "
            "FROM pending_approvals WHERE status = 'PENDING' "
            "ORDER BY id DESC",
        ).fetchall()
    return [dict(r) for r in rows]


# ── Read helpers (for CLI / manifest) ───────────────────────────────────────

def get_audit_log(agent_name: str, limit: int = 10, db_path: str = DB_PATH) -> list:
    """Return the last *limit* audit-log rows for *agent_name*."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, timestamp, agent_name, action, status, details "
            "FROM audit_log WHERE agent_name = ? ORDER BY id DESC LIMIT ?",
            (agent_name, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
