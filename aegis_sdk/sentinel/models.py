"""Data models for sentinel-guardrails (Database Polling edition)."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Agent:
    """Represents a registered AI agent."""

    name: str = ""
    status: str = "ACTIVE"  # ACTIVE or PAUSED
    owner: str = ""


@dataclass
class Policy:
    """A single policy rule for an agent action."""

    agent_name: str = ""
    action: str = ""
    rule_type: str = ""  # ALLOW or BLOCK


@dataclass
class LogEntry:
    """A single audit-log record."""

    timestamp: str = ""
    agent: str = ""
    action: str = ""
    status: str = ""  # ALLOWED, BLOCKED, KILLED
