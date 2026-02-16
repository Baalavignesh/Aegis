"""Core polling engine for sentinel-guardrails.

Every call to ``validate_action`` queries the backend API,
ensuring the latest agent status and policy rules are always enforced.
No caching — true real-time polling.
"""

import time
from typing import List, Optional

from sentinel import db
from sentinel.exceptions import (
    SentinelApprovalError,
    SentinelBlockedError,
    SentinelKillSwitchError,
)

APPROVAL_POLL_INTERVAL = 2

_db_initialized = False


def register_agent(
    name: str,
    owner: str = "",
    allows: Optional[List[str]] = None,
    blocks: Optional[List[str]] = None,
    requires_review: Optional[List[str]] = None,
) -> None:
    """Upsert the agent and seed its policies into the DB.

    Called at import time by the ``@agent`` decorator.
    """
    global _db_initialized
    if not _db_initialized:
        db.init_db()
        _db_initialized = True
    db.upsert_agent(name, owner)

    for action in (allows or []):
        db.upsert_policy(name, action, "ALLOW")

    for action in (blocks or []):
        db.upsert_policy(name, action, "BLOCK")

    for action in (requires_review or []):
        db.upsert_policy(name, action, "REVIEW")


def validate_action(
    agent_name: str,
    action_name: str,
    args_json: str = "{}",
) -> bool:
    """The polling check — queries the DB on every call.

    1. If the agent is PAUSED → raise ``SentinelKillSwitchError``.
    2. If the action is BLOCK → raise ``SentinelBlockedError``.
    3. If the action is ALLOW → return ``True``.
    4. If the action is REVIEW → block until human decides (thread-safe).
    5. Default (unknown)     → return ``False``.

    Blocking only affects the calling thread. Run agents in separate
    threads so one agent waiting for approval doesn't block others.
    """
    # Step 1: Kill-switch check
    status = db.get_agent_status(agent_name)
    if status == "PAUSED":
        raise SentinelKillSwitchError(agent_name)

    # Step 2: Policy check
    rule = db.get_policy(agent_name, action_name)

    if rule == "BLOCK":
        raise SentinelBlockedError(action_name)

    if rule == "ALLOW":
        return True

    if rule == "REVIEW":
        return wait_for_approval(agent_name, action_name, args_json)

    # Default: unknown action
    return False


def wait_for_approval(
    agent_name: str, action_name: str, args_json: str
) -> bool:
    """Create a pending approval and block until the human decides.

    Blocks **forever** until a human approves or denies on the dashboard.
    This only blocks the calling thread — other agents running in
    separate threads are not affected.

    If there's already an approval for this agent+action in the current
    session, it resumes from that instead of creating a duplicate.

    Returns ``True`` if approved, raises ``SentinelBlockedError`` if denied.
    """
    # Check for existing approval first (e.g. retry after earlier attempt)
    existing = db.find_approval(agent_name, action_name)

    if existing:
        existing_status = existing["status"]
        aid = existing["id"]

        if existing_status == "APPROVED":
            return True

        if existing_status == "DENIED":
            raise SentinelBlockedError(
                f"Action '{action_name}' was denied by human reviewer "
                f"(Approval #{aid})."
            )

        # Still PENDING from a previous attempt — poll this one
        approval_id = aid
    else:
        # Create new approval
        approval_id = db.create_approval(agent_name, action_name, args_json)
        db.log_event(
            agent_name, action_name, "PENDING",
            f"Approval #{approval_id} — waiting for human decision.",
        )

    # Poll forever until the human decides
    while True:
        decision = db.get_approval_status(approval_id)

        if decision == "APPROVED":
            return True

        if decision == "DENIED":
            raise SentinelBlockedError(
                f"Action '{action_name}' was denied by human reviewer "
                f"(Approval #{approval_id})."
            )

        time.sleep(APPROVAL_POLL_INTERVAL)


def request_approval(
    agent_name: str, action_name: str, args_json: str
) -> bool:
    """Non-blocking approval request (alternative to wait_for_approval).

    Use this when the caller can handle deferred execution — e.g. an LLM
    that can move on to independent tasks and retry later.

    Checks if there's already an approval for this agent+action:
      - APPROVED → return True (tool executes)
      - DENIED   → raise SentinelBlockedError
      - PENDING  → raise SentinelApprovalError (caller retries later)
      - None     → create new approval + raise SentinelApprovalError
    """
    existing = db.find_approval(agent_name, action_name)

    if existing:
        status = existing["status"]
        aid = existing["id"]

        if status == "APPROVED":
            return True

        if status == "DENIED":
            raise SentinelBlockedError(
                f"Action '{action_name}' was denied by human reviewer "
                f"(Approval #{aid})."
            )

        raise SentinelApprovalError(
            f"Action '{action_name}' is awaiting human approval "
            f"(Approval #{aid}). Retry later."
        )

    approval_id = db.create_approval(agent_name, action_name, args_json)
    db.log_event(
        agent_name, action_name, "PENDING",
        f"Approval #{approval_id} — waiting for human decision.",
    )
    raise SentinelApprovalError(
        f"Action '{action_name}' requires human approval "
        f"(Approval #{approval_id}). Retry after approval."
    )
