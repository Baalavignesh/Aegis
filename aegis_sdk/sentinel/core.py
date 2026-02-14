"""Core polling engine for sentinel-guardrails.

Every call to ``validate_action`` queries the SQLite database,
ensuring the latest agent status and policy rules are always enforced.
No caching — true real-time polling.
"""

import json
import time
from typing import List, Optional

from sentinel import db
from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)

# How long the agent blocks waiting for a human decision (seconds)
APPROVAL_TIMEOUT = 120
APPROVAL_POLL_INTERVAL = 1


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
    db.init_db()
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
    4. If the action is REVIEW → create a pending approval, block
       until the human decides, then return accordingly.
    5. Default (unknown)     → return ``False``.
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
    """Create a pending approval and poll until the human decides.

    Returns ``True`` if approved, raises ``SentinelBlockedError`` if denied.
    Raises ``SentinelApprovalError`` on timeout.
    """
    approval_id = db.create_approval(agent_name, action_name, args_json)
    db.log_event(
        agent_name, action_name, "PENDING",
        f"Approval #{approval_id} — waiting for human decision.",
    )

    deadline = time.time() + APPROVAL_TIMEOUT

    while time.time() < deadline:
        decision = db.get_approval_status(approval_id)

        if decision == "APPROVED":
            db.log_event(
                agent_name, action_name, "APPROVED",
                f"Approval #{approval_id} — human approved.",
            )
            return True

        if decision == "DENIED":
            db.log_event(
                agent_name, action_name, "DENIED",
                f"Approval #{approval_id} — human denied.",
            )
            raise SentinelBlockedError(
                f"Action '{action_name}' was denied by human reviewer."
            )

        time.sleep(APPROVAL_POLL_INTERVAL)

    # Timeout — auto-deny
    db.decide_approval(approval_id, "DENIED")
    db.log_event(
        agent_name, action_name, "TIMEOUT",
        f"Approval #{approval_id} — timed out after {APPROVAL_TIMEOUT}s.",
    )
    raise SentinelApprovalError(
        f"Action '{action_name}' timed out waiting for approval."
    )
