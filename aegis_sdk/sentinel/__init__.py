"""sentinel-guardrails — Database Polling Security System."""

__version__ = "0.1.0"

from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)
from sentinel.decorators import agent, monitor
from sentinel.core import wait_for_approval
from sentinel.cli import kill_agent, revive_agent, show_audit_log

__all__ = [
    "agent",
    "monitor",
    "wait_for_approval",
    "kill_agent",
    "revive_agent",
    "show_audit_log",
    "SentinelBlockedError",
    "SentinelKillSwitchError",
    "SentinelApprovalError",
]
