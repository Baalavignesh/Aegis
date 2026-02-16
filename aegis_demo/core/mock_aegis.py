"""Terminal helpers for the Aegis demo.

Pure cosmetics — ANSI colors, banners, and a monitor hook that prints
firewall decisions to the terminal. No SDK logic lives here.
"""

import hashlib
from datetime import datetime
from typing import Optional

from sentinel.decorators import set_monitor_hook


# ---------------------------------------------------------------------------
# ANSI color constants
# ---------------------------------------------------------------------------

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"


# ---------------------------------------------------------------------------
# Per-agent stats (in-memory, for the terminal summary at the end)
# ---------------------------------------------------------------------------

_agent_stats: dict = {}


def generate_digital_id(name: str) -> str:
    """Generate a unique agent ID (AGT-0x{hash})."""
    h = hashlib.sha256(name.encode()).hexdigest()[:4].upper()
    return f"AGT-0x{h}"


def get_agent_stats() -> dict:
    """Return the stats dict: {digital_id: {"name": str, "stats": {...}}}."""
    return _agent_stats


# ---------------------------------------------------------------------------
# Banner + logging helpers
# ---------------------------------------------------------------------------

def print_agent_banner(name: str, role: str) -> str:
    """Print a registration banner and return the digital_id."""
    digital_id = generate_digital_id(name)
    _agent_stats[digital_id] = {
        "name": name,
        "stats": {"allowed": 0, "blocked": 0, "review": 0, "killed": 0},
    }
    print(f"\n{C.CYAN}{C.BOLD}{'━' * 50}{C.RESET}")
    print(f" {C.BOLD}Agent: {name} | {digital_id}{C.RESET}")
    print(f" {C.DIM}Role: {role}{C.RESET}")
    print(f" {C.DIM}Framework: LangChain + Gemini{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}{'━' * 50}{C.RESET}")
    return digital_id


def log_thought(message: str):
    """Print a timestamped thought to the terminal."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {C.DIM}[{ts}] [THOUGHT] {message}{C.RESET}")


# ---------------------------------------------------------------------------
# Monitor hook — prints colored firewall decisions to the terminal
# ---------------------------------------------------------------------------

def _terminal_hook(agent_name: str, action: str, decision: str) -> Optional[Exception]:
    """Print firewall decisions to the terminal and update in-memory stats."""
    digital_id = generate_digital_id(agent_name)
    if digital_id not in _agent_stats:
        return None

    stats = _agent_stats[digital_id]["stats"]
    ts = datetime.now().strftime("%H:%M:%S")

    if decision == "ALLOWED":
        stats["allowed"] += 1
        print(f"  {C.GREEN}[{ts}] [{digital_id}] ALLOWED → {action}{C.RESET}")
    elif decision == "BLOCKED":
        stats["blocked"] += 1
        print(f"  {C.RED}{C.BOLD}[{ts}] [{digital_id}] BLOCKED → {action}{C.RESET}")
    elif decision == "KILLED":
        stats["killed"] += 1
        print(f"  {C.BG_RED}{C.WHITE}[{ts}] [{digital_id}] KILLED → {action}{C.RESET}")
    elif decision == "PENDING":
        stats["review"] += 1
        print(f"  {C.YELLOW}[{ts}] [{digital_id}] PENDING APPROVAL → {action}{C.RESET}")

    return None


# Register the terminal hook at import time
set_monitor_hook(_terminal_hook)
