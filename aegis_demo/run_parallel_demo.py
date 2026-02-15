"""
Aegis Demo — Concurrent Orchestrator
Runs all demo agents IN PARALLEL using threads.
"""

import threading
import time
import argparse
import os
import sys

# Ensure aegis_sdk is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "aegis_sdk"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from aegis_demo.run_demo import AGENTS, seed_via_backend, print_banner
from aegis_demo.core import C


def run_agent_wrapper(key, delay):
    """Run an agent after a delay."""
    module, display_name = AGENTS[key]

    if delay > 0:
        time.sleep(delay)

    print(f"\n{C.BOLD}Starting Thread: {display_name}{C.RESET}")
    try:
        module.run()
    except Exception as e:
        print(f"  {C.RED}Error in {display_name}: {e}{C.RESET}")
    print(f"{C.BOLD}Finished Thread: {display_name}{C.RESET}")


def main():
    parser = argparse.ArgumentParser(description="Aegis Concurrent Demo")
    parser.parse_args()

    print_banner()
    print(f"{C.YELLOW}{C.BOLD}  [CONCURRENT MODE] Running agents in parallel threads...{C.RESET}")

    # Seed via backend API
    print(f"  {C.DIM}Seeding database via backend...{C.RESET}", end=" ")
    try:
        result = seed_via_backend()
        print(f"{C.GREEN}{result['customers']} customers, {result['accounts']} accounts, {result['transactions']} transactions{C.RESET}\n")
    except Exception as e:
        print(f"{C.RED}Failed to seed: {e}{C.RESET}")
        print(f"  {C.YELLOW}Make sure the backend is running: uvicorn backend:app --port 8000{C.RESET}")
        return

    threads = []
    schedule = [
        ("customer_support", 0),
        ("fraud_detection", 3),
        ("loan_processing", 6),
        ("marketing", 9),
    ]

    for key, delay in schedule:
        t = threading.Thread(target=run_agent_wrapper, args=(key, delay), name=key)
        threads.append(t)
        t.start()

    print(f"\n{C.CYAN}  All agents started! Check the Dashboard.{C.RESET}")
    print(f"  {C.DIM}Marketing Agent will pause for approval around T+15s...{C.RESET}\n")

    for t in threads:
        t.join()

    print(f"\n{C.GREEN}{C.BOLD}  All parallel agents finished.{C.RESET}")


if __name__ == "__main__":
    main()
