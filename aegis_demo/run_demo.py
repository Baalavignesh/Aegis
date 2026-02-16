"""
Aegis Demo — Orchestrator
Runs all demo agents sequentially with a summary dashboard.
Usage:
    python -m aegis_demo                          # Run all agents
    python -m aegis_demo --agent fraud_detection   # Run one agent
"""

import argparse
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from .core import C, get_agent_stats

BACKEND_URL = os.getenv("AEGIS_BACKEND_URL", "http://localhost:8000")

# Agent module names — imported lazily AFTER seed so @agent registration
# happens on a clean database (seed drops all sentinel collections first).
AGENT_KEYS = {
    "customer_support": "Customer Support",
    "fraud_detection": "Fraud Detection",
    "loan_processing": "Loan Processor",
    "marketing": "Marketing Outreach",
}


def print_banner():
    print(f"\n{C.CYAN}{C.BOLD}")
    print("+" + "=" * 54 + "+")
    print("|  AEGIS GOVERNANCE PLATFORM — DEMO                    |")
    print("|  Personal Finance Multi-Agent System                 |")
    print("|  LangChain + Gemini                                  |")
    print("+" + "=" * 54 + "+")
    print(C.RESET)


def print_summary():
    stats = get_agent_stats()
    print(f"\n{C.CYAN}{C.BOLD}")
    print("+" + "=" * 54 + "+")
    print("|  DEMO SUMMARY                                        |")
    print("+" + "=" * 54 + "+")
    print(C.RESET)

    total_allowed = 0
    total_blocked = 0
    total_review = 0
    total_killed = 0

    for agent_id, data in stats.items():
        s = data["stats"]
        total = s["allowed"] + s["blocked"] + s["review"] + s["killed"]
        total_allowed += s["allowed"]
        total_blocked += s["blocked"]
        total_review += s["review"]
        total_killed += s["killed"]

        print(f"  {C.BOLD}{data['name']}{C.RESET} ({agent_id})")
        print(f"    Total actions: {total}")
        print(f"    {C.GREEN}Allowed: {s['allowed']}{C.RESET}  "
              f"{C.RED}Blocked: {s['blocked']}{C.RESET}  "
              f"{C.YELLOW}Review: {s['review']}{C.RESET}  "
              f"{C.BG_RED}{C.WHITE}Killed: {s['killed']}{C.RESET}")
        print()

    grand_total = total_allowed + total_blocked + total_review + total_killed
    print(f"  {C.BOLD}TOTALS:{C.RESET} {grand_total} actions across {len(stats)} agents")
    print(f"    {C.GREEN}Allowed: {total_allowed}{C.RESET}  "
          f"{C.RED}Blocked: {total_blocked}{C.RESET}  "
          f"{C.YELLOW}Review: {total_review}{C.RESET}  "
          f"{C.BG_RED}{C.WHITE}Killed: {total_killed}{C.RESET}")
    print()


def seed_via_backend():
    """Call the backend /demo/seed endpoint to reset and seed all data."""
    resp = httpx.post(f"{BACKEND_URL}/demo/seed", timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def demo_kill_switch():
    """Demonstrate the kill-switch and audit log features."""
    from sentinel import kill_agent, revive_agent, show_audit_log
    from sentinel import db as sdb

    print(f"\n{C.CYAN}{C.BOLD}")
    print("+" + "=" * 54 + "+")
    print("|  KILL-SWITCH & AUDIT LOG DEMO                        |")
    print("+" + "=" * 54 + "+")
    print(C.RESET)

    stats = get_agent_stats()
    if not stats:
        print(f"  {C.DIM}No agents ran — skipping kill-switch demo.{C.RESET}")
        return

    first_id = next(iter(stats))
    agent_name = stats[first_id]["name"]

    # Kill the agent
    print(f"  {C.BOLD}Activating kill-switch for '{agent_name}'...{C.RESET}")
    kill_agent(agent_name)

    # Show that it's paused
    status = sdb.get_agent_status(agent_name)
    print(f"  Agent status: {C.RED}{C.BOLD}{status}{C.RESET}")

    # Revive it
    print(f"\n  {C.BOLD}Reviving '{agent_name}'...{C.RESET}")
    revive_agent(agent_name)

    status = sdb.get_agent_status(agent_name)
    print(f"  Agent status: {C.GREEN}{C.BOLD}{status}{C.RESET}")

    # Show audit log
    print(f"\n  {C.BOLD}Audit log:{C.RESET}")
    show_audit_log(agent_name, limit=20)


def _import_agents():
    """Lazy-import agent modules so @agent decorators fire AFTER seed.

    Must be called after seed_via_backend() — the seed drops all sentinel
    collections, then these imports re-register agents on a clean DB.
    """
    from .agents import (
        customer_support_agent,
        fraud_detection_agent,
        loan_processing_agent,
        marketing_agent,
    )
    return {
        "customer_support": (customer_support_agent, "Customer Support"),
        "fraud_detection": (fraud_detection_agent, "Fraud Detection"),
        "loan_processing": (loan_processing_agent, "Loan Processor"),
        "marketing": (marketing_agent, "Marketing Outreach"),
    }


def run_agent(agents: dict, key: str):
    from sentinel import db as sdb

    module, display_name = agents[key]
    print(f"\n{C.BOLD}{'=' * 54}{C.RESET}")
    print(f" Running: {display_name}")
    print(f"{'=' * 54}")

    # Mark agent ACTIVE while its task runs
    sdb.update_status(display_name, "ACTIVE")
    try:
        module.run()
    except Exception as e:
        print(f"  {C.RED}Agent error: {e}{C.RESET}")
        traceback.print_exc()
    finally:
        # Mark agent COMPLETED when done (whether success or error)
        sdb.update_status(display_name, "COMPLETED")


def main():
    parser = argparse.ArgumentParser(description="Aegis Demo Orchestrator")
    parser.add_argument(
        "--agent",
        choices=list(AGENT_KEYS.keys()),
        help="Run a specific agent (default: all)",
    )
    args = parser.parse_args()

    print_banner()

    # 1. Seed database via backend API — drops all sentinel + banking collections
    print(f"  {C.DIM}Seeding database via backend...{C.RESET}", end=" ")
    try:
        result = seed_via_backend()
        print(f"{C.GREEN}{result['customers']} customers, {result['accounts']} accounts, {result['transactions']} transactions{C.RESET}\n")
    except Exception as e:
        print(f"{C.RED}Failed to seed: {e}{C.RESET}")
        print(f"  {C.YELLOW}Make sure the backend is running: uvicorn backend:app --port 8000{C.RESET}")
        return

    # 2. Import agent modules NOW — @agent decorators register on the clean DB
    agents = _import_agents()

    if args.agent:
        run_agent(agents, args.agent)
        print_summary()
        demo_kill_switch()
    else:
        # Run all agents in parallel threads.
        # Each agent blocks independently on its own approvals —
        # one agent waiting for human review doesn't freeze the others.
        print(f"  {C.DIM}Launching all agents in parallel...{C.RESET}\n")
        keys = list(agents.keys())
        with ThreadPoolExecutor(max_workers=len(keys)) as pool:
            futures = {
                pool.submit(run_agent, agents, key): key
                for key in keys
            }
            for future in as_completed(futures):
                future.result()  # propagate any unexpected errors

        print_summary()
        demo_kill_switch()


if __name__ == "__main__":
    main()
