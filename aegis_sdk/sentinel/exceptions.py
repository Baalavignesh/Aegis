"""Custom exceptions for the sentinel-guardrails library."""


class SentinelBlockedError(Exception):
    """Raised when a monitored function call is blocked by policy."""

    def __init__(self, action: str, message: str = ""):
        self.action = action
        self.message = message or f"Action '{action}' is blocked by Sentinel policy."
        super().__init__(self.message)


class SentinelKillSwitchError(Exception):
    """Raised when an agent has been remotely PAUSED via the kill switch."""

    def __init__(self, agent_name: str, message: str = ""):
        self.agent_name = agent_name
        self.message = message or (
            f"Agent '{agent_name}' is PAUSED. All operations are suspended. "
            "Use 'sentinel revive' to reactivate."
        )
        super().__init__(self.message)


class SentinelApprovalError(Exception):
    """Raised when an action requires human approval before proceeding."""

    def __init__(self, action: str, approver: str = "", message: str = ""):
        self.action = action
        self.approver = approver
        self.message = message or (
            f"Action '{action}' requires approval from '{approver}'."
        )
        super().__init__(self.message)
