"""Agent context for sentinel-guardrails.

Tracks which agent is "currently running" so that @monitor (without a
static agent name) can resolve the agent at call time.

Two ways to set context:
    1. ``with agent_context("MyBot"): ...``   — context manager
    2. ``set_agent_context("MyBot")``         — manual (for frameworks)
"""

import contextvars
from contextlib import contextmanager
from typing import Optional

_current_agent: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "sentinel_current_agent", default=None
)


def get_current_agent() -> Optional[str]:
    """Return the agent name from the current context, or None."""
    return _current_agent.get()


def set_agent_context(agent_name: str) -> contextvars.Token:
    """Manually set the current agent. Returns a token for reset."""
    return _current_agent.set(agent_name)


def reset_agent_context(token: contextvars.Token) -> None:
    """Reset context to previous value using the token from set_agent_context."""
    _current_agent.reset(token)


@contextmanager
def agent_context(agent_name: str):
    """Context manager that sets the current agent for the duration of a block.

    Usage::

        with agent_context("FraudBot"):
            lookup_balance(123)   # @monitor resolves to "FraudBot"
    """
    token = _current_agent.set(agent_name)
    try:
        yield agent_name
    finally:
        _current_agent.reset(token)
