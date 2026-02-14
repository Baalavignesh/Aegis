"""Core polling engine for sentinel-guardrails.

Every call to ``validate_action`` queries the SQLite database,
ensuring the latest agent status and policy rules are always enforced.
No caching — true real-time polling.
"""

from typing import List

from sentinel import db
from sentinel.exceptions import SentinelBlockedError, SentinelKillSwitchError


def register_agent(
    name: str,
    owner: str = "",
    allows: List[str] | None = None,
    blocks: List[str] | None = None,
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


def validate_action(agent_name: str, action_name: str) -> bool:
    """The polling check — queries the DB on every call.

    1. If the agent is PAUSED → raise ``SentinelKillSwitchError``.
    2. If the action is BLOCK → raise ``SentinelBlockedError``.
    3. If the action is ALLOW → return ``True``.
    4. Default (unknown)     → return ``False``.
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

    # Default: unknown action
    return False
