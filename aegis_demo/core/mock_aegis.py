"""
Aegis Demo — SDK Adapter
Bridges sentinel-guardrails SDK with LangChain tool wrapping and ANSI terminal output.
Delegates agent registration, action validation, and audit logging to the real SDK.
Retains local logic for: data/server keyword checks, REVIEW state, LangChain wrapping, ANSI output.
"""

import hashlib
import copy
from datetime import datetime
from functools import wraps
from langchain_core.tools.base import ToolException

from sentinel.core import register_agent, validate_action, wait_for_approval
from sentinel import db as sentinel_db
from sentinel.exceptions import SentinelBlockedError, SentinelKillSwitchError, SentinelApprovalError


# --- ANSI Colors ---
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


class AegisBlockedError(Exception):
    """Raised when the Aegis firewall blocks an action."""
    pass


class AegisReviewError(Exception):
    """Raised when an action requires human review."""
    pass


# Tracking stats per agent
_agent_stats = {}


def get_agent_stats():
    return _agent_stats


class AegisAgent:
    def __init__(self, name: str, role: str, decorator: dict):
        self.name = name
        self.role = role
        self.decorator = decorator
        self.digital_id = self._generate_id(name)
        self.stats = {"allowed": 0, "blocked": 0, "review": 0, "killed": 0}
        _agent_stats[self.digital_id] = {"name": name, "stats": self.stats}

        # Register agent + policies in SDK's MongoDB database
        register_agent(
            name,
            owner=role,
            allows=decorator.get("allowed_actions", []),
            blocks=decorator.get("blocked_actions", []),
            requires_review=decorator.get("requires_review_actions", []),
        )

        self._print_registration()

    def _generate_id(self, name: str) -> str:
        h = hashlib.sha256(name.encode()).hexdigest()[:4].upper()
        return f"AGT-0x{h}"

    def _print_registration(self):
        print(f"\n{C.CYAN}{C.BOLD}{'━' * 50}{C.RESET}")
        print(f" {C.BOLD}Agent: {self.name} | {self.digital_id}{C.RESET}")
        print(f" {C.DIM}Role: {self.role}{C.RESET}")
        print(f" {C.DIM}Framework: LangChain + Gemini{C.RESET}")
        print(f"{C.CYAN}{C.BOLD}{'━' * 50}{C.RESET}")

    def _check_firewall(self, action: str, args_str: str = "") -> str:
        """
        Firewall decision logic — delegates steps 1-3 to SDK, keeps local data/server checks.
        1. Kill-switch check (SDK) -> KILLED
        2. Action in blocked_actions (SDK) -> BLOCKED
        3. Action in allowed_actions (SDK) -> continue
        4. Unknown action (SDK returns False) -> REVIEW
        5. Check blocked_data keywords in args -> BLOCKED
        6. Check blocked_servers in args -> BLOCKED
        7. All pass -> ALLOWED
        """
        # Steps 1-3: delegate to SDK (queries MongoDB on every call)
        try:
            result = validate_action(self.name, action)
        except SentinelKillSwitchError:
            return "KILLED"
        except SentinelBlockedError:
            return "BLOCKED"

        # Step 4: unknown action -> REVIEW (ask for approval)
        if not result:
            print(f"  {C.YELLOW}{C.BOLD}[AEGIS]{C.RESET} Action '{action}' requires approval. Waiting for human decision... (120s timeout)")
            try:
                # args_str contains the arguments for context
                approved = wait_for_approval(self.name, action, args_str)
                if approved:
                     # If approved, we return ALLOWED so execution continues
                     return "ALLOWED"
            except (SentinelBlockedError, SentinelApprovalError):
                return "BLOCKED"

        # Step 5: check blocked_data keywords in args
        blocked_data = self.decorator.get("blocked_data", [])
        args_lower = args_str.lower()
        for keyword in blocked_data:
            if keyword.lower() in args_lower:
                return "BLOCKED"

        # Step 6: check blocked_servers in args
        blocked_servers = self.decorator.get("blocked_servers", [])
        for server in blocked_servers:
            if server.lower() in args_lower:
                return "BLOCKED"

        # Step 7: all pass
        return "ALLOWED"

    def _print_decision(self, action: str, decision: str, detail: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        if decision == "ALLOWED":
            badge = f"{C.GREEN}{C.BOLD}ALLOWED{C.RESET}"
            icon = "+"
            self.stats["allowed"] += 1
        elif decision == "BLOCKED":
            badge = f"{C.RED}{C.BOLD}BLOCKED{C.RESET}"
            icon = "x"
            self.stats["blocked"] += 1
        elif decision == "KILLED":
            badge = f"{C.BG_RED}{C.WHITE}{C.BOLD} KILLED {C.RESET}"
            icon = "!"
            self.stats["killed"] += 1
        else:
            badge = f"{C.YELLOW}{C.BOLD}REVIEW{C.RESET}"
            icon = "?"
            self.stats["review"] += 1

        prefix = f"{C.DIM}[{ts}]{C.RESET} {C.MAGENTA}[AEGIS]{C.RESET}"
        print(f"  {prefix} {action} -> [{icon}] {badge}  {C.DIM}{detail}{C.RESET}")

    def _log_to_sdk(self, action: str, decision: str):
        """Log the decision to the SDK's audit_log table."""
        # Map REVIEW -> BLOCKED for SDK (CHECK constraint only allows ALLOWED/BLOCKED/KILLED)
        sdk_status = "BLOCKED" if decision == "REVIEW" else decision
        detail = f"REVIEW: undeclared action" if decision == "REVIEW" else ""
        sentinel_db.log_event(self.name, action, sdk_status, detail)

    def log_thought(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {C.DIM}[{ts}] [THOUGHT] {message}{C.RESET}")

    def wrap_tool(self, func, tool_name: str):
        """Wrap a function with Aegis firewall checks."""
        agent = self

        @wraps(func)
        def wrapper(*args, **kwargs):
            args_str = " ".join(str(a) for a in args) + " " + " ".join(str(v) for v in kwargs.values())
            decision = agent._check_firewall(tool_name, args_str)
            agent._print_decision(tool_name, decision)
            agent._log_to_sdk(tool_name, decision)

            if decision == "KILLED":
                raise ToolException(
                    f"AEGIS FIREWALL: Agent {agent.name} ({agent.digital_id}) is KILLED (paused). "
                    f"All operations suspended. Do NOT retry any actions."
                )
            elif decision == "BLOCKED":
                raise ToolException(
                    f"AEGIS FIREWALL: Action '{tool_name}' is BLOCKED by policy for agent {agent.name} ({agent.digital_id}). "
                    f"This action violates the agent's decorator policy. Do NOT retry this action."
                )
            elif decision == "REVIEW":
                raise ToolException(
                    f"AEGIS FIREWALL: Action '{tool_name}' requires HUMAN REVIEW for agent {agent.name} ({agent.digital_id}). "
                    f"This action is not declared in the agent's policy. Awaiting approval. Do NOT retry this action."
                )

            return func(*args, **kwargs)

        return wrapper

    def wrap_langchain_tools(self, tools: list) -> list:
        """Wrap a list of LangChain Tool objects with Aegis firewall logic.
        Preserves StructuredTool schemas so multi-arg tools work correctly."""
        wrapped = []
        for tool in tools:
            cloned = copy.copy(tool)
            cloned.func = self.wrap_tool(tool.func, tool.name)
            cloned.handle_tool_error = True
            if hasattr(tool, 'coroutine'):
                cloned.coroutine = None
            wrapped.append(cloned)
        return wrapped
