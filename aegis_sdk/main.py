"""
CryptoBot — Usage proof for sentinel-guardrails (Human-in-the-Loop edition).

Demonstrates:
  Test 1: Allowed action → executes, audit log: ALLOWED
  Test 2: Blocked action → SentinelBlockedError, audit log: BLOCKED
  Test 3: Kill switch — same allowed action fails when PAUSED
  Test 4: REVIEW action — agent blocks until human clicks Allow/Deny
          on the dashboard (or until the API call is made)

Run the backend alongside:
    uvicorn backend:app --reload

Then run this script:
    python main.py
"""

import os
import sys
import threading
import time

# Clean slate for reproducible demo
if os.path.exists("sentinel.db"):
    os.remove("sentinel.db")

from sentinel import (
    agent,
    monitor,
    kill_agent,
    revive_agent,
    show_audit_log,
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)


# ── Agent definition (registers in DB at import time) ───────────────────────

@agent(
    "CryptoBot",
    owner="trading-team@example.com",
    allows=["check_balance", "get_market_price"],
    blocks=["withdraw_funds", "delete_wallet"],
    requires_review=["transfer_funds"],
)
class CryptoBotAgent:
    """The CryptoBot agent — policy-decorated class."""
    pass


# ── Monitored tool functions ───────────────────────────────────────────────

@monitor("CryptoBot")
def check_balance(wallet_id: str) -> dict:
    """Check the balance of a crypto wallet."""
    return {"wallet_id": wallet_id, "balance": "3.42 BTC", "usd_value": "$215,460"}


@monitor("CryptoBot")
def get_market_price(symbol: str) -> dict:
    """Get the current market price for a crypto symbol."""
    return {"symbol": symbol, "price": "$62,990", "change_24h": "+2.4%"}


@monitor("CryptoBot")
def withdraw_funds(wallet_id: str, amount: str) -> dict:
    """Withdraw funds from a wallet (BLOCKED by policy)."""
    return {"wallet_id": wallet_id, "withdrawn": amount}


@monitor("CryptoBot")
def delete_wallet(wallet_id: str) -> dict:
    """Delete a wallet entirely (BLOCKED by policy)."""
    return {"deleted": wallet_id}


@monitor("CryptoBot")
def transfer_funds(wallet_from: str, wallet_to: str, amount: str) -> dict:
    """Transfer funds between wallets (REQUIRES HUMAN APPROVAL)."""
    return {"from": wallet_from, "to": wallet_to, "amount": amount, "status": "completed"}


# ── Demo ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Sentinel Guardrails — CryptoBot (Human-in-the-Loop Demo)")
    print("=" * 70)

    # ── Test 1: Allowed action ──
    print("\n── Test 1: Allowed action — check_balance ──")
    result = check_balance("WALLET-001")
    print(f"   ✅ Result: {result}")

    # ── Test 2: Blocked action ──
    print("\n── Test 2: Blocked action — withdraw_funds ──")
    try:
        withdraw_funds("WALLET-001", "1.0 BTC")
    except SentinelBlockedError as e:
        print(f"   🚫 Caught SentinelBlockedError: {e}")

    # ── Test 3: The Kill Switch ──
    print("\n── Test 3: Kill Switch ──")
    print("   3a. Running get_market_price (should succeed)...")
    result = get_market_price("BTC")
    print(f"       ✅ Result: {result}")

    print("\n   3b. Admin activates the kill switch...")
    kill_agent("CryptoBot")

    print("\n   3c. Running get_market_price AGAIN (should FAIL)...")
    try:
        get_market_price("BTC")
    except SentinelKillSwitchError as e:
        print(f"       💀 Caught SentinelKillSwitchError: {e}")

    print("\n   3d. Admin revives the agent...")
    revive_agent("CryptoBot")
    result = get_market_price("BTC")
    print(f"       ✅ Result: {result}")

    # ── Test 4: Human-in-the-Loop Approval ──
    print("\n── Test 4: Human-in-the-Loop — transfer_funds ──")
    print("   ⏳ Calling transfer_funds() — this will BLOCK until you")
    print("      approve/deny on the dashboard or via the API.")
    print()
    print("   To approve via API, run:")
    print("     curl -X POST http://localhost:8000/approvals/1/decide \\")
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"decision": "APPROVED"}\'')
    print()
    print("   Or open http://localhost:5173 and click the ALLOW button.")
    print()

    # Run in a thread so the demo doesn't hang indefinitely
    result_holder = {"result": None, "error": None}

    def run_transfer():
        try:
            result_holder["result"] = transfer_funds("WALLET-001", "WALLET-002", "0.5 BTC")
        except (SentinelBlockedError, SentinelApprovalError) as e:
            result_holder["error"] = e

    thread = threading.Thread(target=run_transfer)
    thread.start()

    # Wait for the thread, but with a timeout
    thread.join(timeout=30)

    if thread.is_alive():
        print("   ⏰ Still waiting for approval (thread still running).")
        print("   The agent is blocked — go approve/deny on the dashboard!")
        print("   (Exiting demo, but the thread continues in background)")
    elif result_holder["error"]:
        print(f"   🚫 Transfer denied/timed out: {result_holder['error']}")
    else:
        print(f"   ✅ Transfer approved! Result: {result_holder['result']}")

    # ── Audit Log ──
    print("\n── Full Audit Log ──")
    show_audit_log("CryptoBot", limit=20)


if __name__ == "__main__":
    main()
