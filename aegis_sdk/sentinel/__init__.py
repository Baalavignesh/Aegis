"""sentinel-guardrails — Database Polling Security System."""

__version__ = "0.1.0"

from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
)
from sentinel.decorators import agent, monitor
from sentinel.context import agent_context, set_agent_context, reset_agent_context
from sentinel.cli import kill_agent, revive_agent, show_audit_log

__all__ = [
    "agent",
    "monitor",
    "agent_context",
    "set_agent_context",
    "reset_agent_context",
    "kill_agent",
    "revive_agent",
    "show_audit_log",
    "SentinelBlockedError",
    "SentinelKillSwitchError",
]
