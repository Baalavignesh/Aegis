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

from .core import C, get_agent_stats
from .data import seed_database
from .agents import (
    customer_support_agent,
    fraud_detection_agent,
    loan_processing_agent,
    marketing_agent,
)

AGENTS = {
    "customer_support": (customer_support_agent, "Customer Support"),
    "fraud_detection": (fraud_detection_agent, "Fraud Detection"),
    "loan_processing": (loan_processing_agent, "Loan Processor"),
    "marketing": (marketing_agent, "Marketing Outreach"),
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


def clean_sentinel_db():
    """Remove sentinel.db for a fresh run."""
    import sentinel.db as sdb
    db_path = sdb.DB_PATH
    if os.path.exists(db_path):
        os.remove(db_path)


def demo_kill_switch():
    """Demonstrate the kill-switch and audit log features."""
    from sentinel import kill_agent, revive_agent, show_audit_log
    import sentinel.db as sdb

    print(f"\n{C.CYAN}{C.BOLD}")
    print("+" + "=" * 54 + "+")
    print("|  KILL-SWITCH & AUDIT LOG DEMO                        |")
    print("+" + "=" * 54 + "+")
    print(C.RESET)

    # Pick the first agent that ran
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
    print(f"\n  {C.BOLD}Audit log from sentinel.db:{C.RESET}")
    show_audit_log(agent_name, limit=20)


def run_agent(key: str):
    module, display_name = AGENTS[key]
    print(f"\n{C.BOLD}{'=' * 54}{C.RESET}")
    print(f" Running: {display_name}")
    print(f"{'=' * 54}")
    try:
        module.run()
    except Exception as e:
        print(f"  {C.RED}Agent error: {e}{C.RESET}")
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Aegis Demo Orchestrator")
    parser.add_argument(
        "--agent",
        choices=list(AGENTS.keys()),
        help="Run a specific agent (default: all)",
    )
    args = parser.parse_args()

    print_banner()

    # Clean slate — remove sentinel.db so each run is reproducible
    clean_sentinel_db()

    # Seed database
    print(f"  {C.DIM}Seeding database...{C.RESET}", end=" ")
    c, a, t = seed_database()
    print(f"{C.GREEN}{c} customers, {a} accounts, {t} transactions{C.RESET}\n")

    if args.agent:
        run_agent(args.agent)
    else:
        keys = list(AGENTS.keys())
        for i, key in enumerate(keys):
            run_agent(key)
            if i < len(keys) - 1:
                wait = 20  # Stay under 5 RPM for strict models; 2.5 Flash Lite allows 10 RPM
                print(f"\n  {C.DIM}Waiting {wait}s for API rate limit...{C.RESET}", flush=True)
                time.sleep(wait)

    print_summary()

    # Demo kill-switch and audit log
    demo_kill_switch()


if __name__ == "__main__":
    main()
