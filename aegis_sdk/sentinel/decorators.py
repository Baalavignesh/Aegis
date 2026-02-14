"""Decorators for sentinel-guardrails.

Two decorators:
  @agent  — registers identity + policies at import time
  @monitor — wraps functions with the DB-polling firewall (context-based)
"""

import functools
from typing import List, Optional

from sentinel import db
from sentinel.context import get_current_agent
from sentinel.core import register_agent, validate_action
from sentinel.exceptions import SentinelBlockedError, SentinelKillSwitchError


# ---------------------------------------------------------------------------
# @agent — register identity & policies at import time
# ---------------------------------------------------------------------------

def agent(
    name: str,
    *,
    owner: str = "",
    allows: Optional[List[str]] = None,
    blocks: Optional[List[str]] = None,
):
    """Register an agent and seed its policies into the database.

    This runs at **import time** — the agent row and all policy rows
    are written to ``sentinel.db`` before any function is called.
    """

    def decorator(cls_or_fn):
        register_agent(name, owner=owner, allows=allows, blocks=blocks)
        return cls_or_fn

    return decorator


# ---------------------------------------------------------------------------
# @monitor — context-based DB-polling wrapper
# ---------------------------------------------------------------------------

def monitor(fn):
    """Wrap a function with the database-polling firewall.

    The agent is resolved from ``agent_context`` at **call time**, so the
    same decorated function can be shared across multiple agents::

        @monitor
        def lookup_balance(customer_id): ...

        with agent_context("SupportBot"):
            lookup_balance(123)     # checks SupportBot's policies

        with agent_context("FraudBot"):
            lookup_balance(123)     # checks FraudBot's policies

    On **every call** the wrapper:
    1. Reads the active agent from ``agent_context``.
    2. Calls ``core.validate_action`` → hits the DB for live status & policy.
    3. If valid → run the function, then log ``ALLOWED``.
    4. If blocked/killed → log the event, then re-raise the error.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        func_name = fn.__name__

        resolved = get_current_agent()
        if resolved is None:
            raise RuntimeError(
                f"@monitor on '{func_name}' could not resolve an agent name. "
                "Call this function inside a `with agent_context('AgentName'):` block."
            )

        try:
            validate_action(resolved, func_name)
        except SentinelKillSwitchError:
            db.log_event(resolved, func_name, "KILLED",
                         f"Agent '{resolved}' is PAUSED.")
            raise
        except SentinelBlockedError:
            db.log_event(resolved, func_name, "BLOCKED",
                         f"Action '{func_name}' is blocked by policy.")
            raise

        # Action is allowed — execute
        result = fn(*args, **kwargs)
        db.log_event(resolved, func_name, "ALLOWED",
                     f"Action '{func_name}' executed successfully.")
        return result

    return wrapper
