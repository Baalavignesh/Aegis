"""sentinel-guardrails — Database Polling Security System."""

__version__ = "2.0.0"

from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)
from sentinel.decorators import agent, monitor, set_monitor_hook
from sentinel.core import wait_for_approval, request_approval
from sentinel.context import agent_context, set_agent_context, reset_agent_context
from sentinel.cli import kill_agent, revive_agent, show_audit_log

__all__ = [
    "agent",
    "monitor",
    "set_monitor_hook",
    "agent_context",
    "set_agent_context",
    "reset_agent_context",
    "wait_for_approval",
    "request_approval",
    "kill_agent",
    "revive_agent",
    "show_audit_log",
    "SentinelBlockedError",
    "SentinelKillSwitchError",
    "SentinelApprovalError",
]
