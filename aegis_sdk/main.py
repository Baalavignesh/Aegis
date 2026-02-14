"""
CryptoBot — Usage proof for sentinel-guardrails (Database Polling edition).

Demonstrates:
  Test 1: Allowed action → executes, audit log: ALLOWED
  Test 2: Blocked action → SentinelBlockedError, audit log: BLOCKED
  Test 3: Kill switch polling proof
          — kill the agent via CLI
          — re-run the *same allowed action*
          — it MUST now fail with SentinelKillSwitchError
          — proves the code checked the DB in real-time
"""

import os

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
)


# ── Agent definition (registers in DB at import time) ───────────────────────

@agent(
    "CryptoBot",
    owner="trading-team@example.com",
    allows=["check_balance", "get_market_price"],
    blocks=["withdraw_funds", "delete_wallet"],
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


# ── Demo ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Sentinel Guardrails — CryptoBot DB Polling Demo")
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

    # ── Test 3: The Polling Proof ──
    print("\n── Test 3: Kill Switch — Real-Time DB Polling Proof ──")

    # 3a. First, prove the action works right now
    print("   3a. Running get_market_price (should succeed)...")
    result = get_market_price("BTC")
    print(f"       ✅ Result: {result}")

    # 3b. Admin kills the agent
    print("\n   3b. Admin activates the kill switch...")
    kill_agent("CryptoBot")

    # 3c. Same action, same function — but now the DB says PAUSED
    print("\n   3c. Running get_market_price AGAIN (should FAIL)...")
    try:
        get_market_price("BTC")
    except SentinelKillSwitchError as e:
        print(f"       💀 Caught SentinelKillSwitchError: {e}")
        print("       ✅ PROOF: The wrapper polled the DB and saw PAUSED!")

    # 3d. Revive and retry
    print("\n   3d. Admin revives the agent...")
    revive_agent("CryptoBot")

    print("       Running get_market_price after revive...")
    result = get_market_price("BTC")
    print(f"       ✅ Result: {result}")

    # ── Audit Log ──
    print("\n── Full Audit Log ──")
    show_audit_log("CryptoBot")


if __name__ == "__main__":
    main()
