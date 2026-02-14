"""Custom exceptions for sentinel-guardrails."""


class SentinelBlockedError(Exception):
    """Raised when an action is blocked by policy."""

    def __init__(self, action_name: str):
        self.action_name = action_name
        super().__init__(
            f"Action '{action_name}' is blocked by Sentinel policy."
        )


class SentinelKillSwitchError(Exception):
    """Raised when the agent is PAUSED (kill switch active)."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(
            f"Agent '{agent_name}' is PAUSED. All operations are suspended. "
            f"Use 'sentinel revive' to reactivate."
        )


class SentinelApprovalError(Exception):
    """Raised when a REVIEW action times out waiting for human approval."""

    def __init__(self, message: str = "Approval timed out."):
        super().__init__(message)
