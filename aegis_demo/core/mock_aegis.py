"""
Aegis Demo — Mock Aegis SDK
Provides AegisAgent with firewall logic and LangChain tool wrapping.
"""

import hashlib
import copy
import time
from datetime import datetime
from functools import wraps
from langchain_core.tools.base import ToolException


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
        self.stats = {"allowed": 0, "blocked": 0, "review": 0}
        _agent_stats[self.digital_id] = {"name": name, "stats": self.stats}
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
        Firewall decision logic (matches the Aegis spec):
        1. Action in blocked_actions? -> BLOCK
        2. Action in allowed_actions? -> continue checks
        3. Unknown action? -> REVIEW
        4. Check blocked_data keywords in args -> BLOCK
        5. Check blocked_servers in args -> BLOCK
        6. All pass -> ALLOW
        """
        blocked_actions = self.decorator.get("blocked_actions", [])
        allowed_actions = self.decorator.get("allowed_actions", [])
        blocked_data = self.decorator.get("blocked_data", [])
        blocked_servers = self.decorator.get("blocked_servers", [])

        # Step 1: blocked action?
        if action in blocked_actions:
            return "BLOCKED"

        # Step 2: allowed action? continue to data/server checks
        # Step 3: unknown action -> review
        if action not in allowed_actions:
            return "REVIEW"

        # Step 4: check blocked_data keywords in args
        args_lower = args_str.lower()
        for keyword in blocked_data:
            if keyword.lower() in args_lower:
                return "BLOCKED"

        # Step 5: check blocked_servers in args
        for server in blocked_servers:
            if server.lower() in args_lower:
                return "BLOCKED"

        # Step 6: all pass
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
        else:
            badge = f"{C.YELLOW}{C.BOLD}REVIEW{C.RESET}"
            icon = "?"
            self.stats["review"] += 1

        prefix = f"{C.DIM}[{ts}]{C.RESET} {C.MAGENTA}[AEGIS]{C.RESET}"
        print(f"  {prefix} {action} -> [{icon}] {badge}  {C.DIM}{detail}{C.RESET}")

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

            if decision == "BLOCKED":
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
