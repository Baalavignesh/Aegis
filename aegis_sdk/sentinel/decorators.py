"""Decorators for sentinel-guardrails.

Two decorators:
  @agent  — registers identity + policies at import time
  @monitor — wraps functions with the DB-polling firewall
"""

import functools
import json
from typing import List, Optional

from sentinel import db
from sentinel.core import register_agent, validate_action
from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)


# ---------------------------------------------------------------------------
# @agent — register identity & policies at import time
# ---------------------------------------------------------------------------

def agent(
    name: str,
    *,
    owner: str = "",
    allows: Optional[List[str]] = None,
    blocks: Optional[List[str]] = None,
    requires_review: Optional[List[str]] = None,
):
    """Register an agent and seed its policies into the database.

    This runs at **import time** — the agent row and all policy rows
    are written to ``sentinel.db`` before any function is called.
    """

    def decorator(cls_or_fn):
        register_agent(
            name,
            owner=owner,
            allows=allows,
            blocks=blocks,
            requires_review=requires_review,
        )
        return cls_or_fn

    return decorator


# ---------------------------------------------------------------------------
# @monitor — DB-polling wrapper
# ---------------------------------------------------------------------------

def monitor(agent_name: str):
    """Wrap a function with the database-polling firewall.

    On **every call** the wrapper:
    1. Calls ``core.validate_action`` → hits the DB for live status & policy.
    2. If ALLOW → run the function, then log ``ALLOWED``.
    3. If REVIEW → blocks until human decides (handled inside validate_action).
    4. If blocked/killed → log the event, then re-raise the error.
    """

    def decorator(fn):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            func_name = fn.__name__

            # Serialize args for the approval request context
            try:
                args_json = json.dumps({"args": str(args), "kwargs": str(kwargs)})
            except (TypeError, ValueError):
                args_json = "{}"

            try:
                validate_action(agent_name, func_name, args_json=args_json)
            except SentinelKillSwitchError:
                db.log_event(agent_name, func_name, "KILLED",
                             f"Agent '{agent_name}' is PAUSED.")
                raise
            except SentinelBlockedError:
                db.log_event(agent_name, func_name, "BLOCKED",
                             f"Action '{func_name}' is blocked by policy.")
                raise
            except SentinelApprovalError:
                # Timeout — already logged by core.py
                raise

            # Action is allowed (directly or via approval) — execute
            result = fn(*args, **kwargs)
            db.log_event(agent_name, func_name, "ALLOWED",
                         f"Action '{func_name}' executed successfully.")
            return result

        return wrapper

    return decorator
