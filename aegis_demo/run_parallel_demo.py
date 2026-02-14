"""
Aegis Demo — Concurrent Orchestrator
Runs all demo agents IN PARALLEL using threads.
This demonstrates the "Global Feed" capability where multiple agents
generate logs simultaneously, and one agent (Marketing) can wait for approval
while others continue working.
"""

import threading
import time
import argparse
import random
import threading
import time
import argparse
import random
import os
import sys

# Ensure aegis_sdk is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "aegis_sdk"))

# Point sentinel DB to aegis_demo/data/ BEFORE any demo imports
import sentinel.db as _sdb
_sdb.DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sentinel.db")

from dotenv import load_dotenv
# Load .env from the aegis_demo directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from aegis_demo.run_demo import AGENTS, clean_sentinel_db, seed_database, print_banner
from aegis_demo.core import C

def run_agent_wrapper(key, delay):
    """Run an agent after a delay."""
    module, display_name = AGENTS[key]
    
    if delay > 0:
        time.sleep(delay)
        
    print(f"\n{C.BOLD}🚀 Starting Thread: {display_name}{C.RESET}")
    try:
        # Run the agent's main logic
        # Note: module.run() is synchronous, so it blocks this thread
        module.run()
    except Exception as e:
        print(f"  {C.RED}Error in {display_name}: {e}{C.RESET}")
    print(f"{C.BOLD}✅ Finished Thread: {display_name}{C.RESET}")

def main():
    parser = argparse.ArgumentParser(description="Aegis Concurrent Demo")
    parser.parse_args()

    print_banner()
    print(f"{C.YELLOW}{C.BOLD}  [CONCURRENT MODE] Running agents in parallel threads...{C.RESET}")

    # Clean & Seed
    clean_sentinel_db()
    print(f"  {C.DIM}Seeding database...{C.RESET}", end=" ")
    c, a, t = seed_database()
    print(f"{C.GREEN}{c} customers, {a} accounts, {t} transactions{C.RESET}\n")

    threads = []
    
    # Staggered starts to avoid immediate rate limits and make logs readable
    # Order: Support (fast), Fraud (fast), Loan (rogue), Marketing (waits for approval)
    
    schedule = [
        ("customer_support", 0),    # Starts immediately
        ("fraud_detection", 3),     # Starts +3s
        ("loan_processing", 6),     # Starts +6s
        ("marketing", 9)            # Starts +9s (Trigger approval last)
    ]

    for key, delay in schedule:
        t = threading.Thread(target=run_agent_wrapper, args=(key, delay), name=key)
        threads.append(t)
        t.start()
    
    print(f"\n{C.CYAN}  All agents started! Check the Dashboard Global Feed.{C.RESET}")
    print(f"  {C.DIM}Marketing Agent will pause for approval around T+15s...{C.RESET}\n")

    for t in threads:
        t.join()

    print(f"\n{C.GREEN}{C.BOLD}  All parallel agents finished.{C.RESET}")

if __name__ == "__main__":
    main()
