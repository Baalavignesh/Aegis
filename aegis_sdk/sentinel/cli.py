"""CLI helpers for sentinel-guardrails."""

from sentinel import db


def kill_agent(name: str) -> None:
    """Set agent status to PAUSED (kill switch)."""
    db.update_status(name, "PAUSED")
    print(f"🛑 Agent '{name}' has been PAUSED.")


def revive_agent(name: str) -> None:
    """Set agent status to ACTIVE."""
    db.update_status(name, "ACTIVE")
    print(f"✅ Agent '{name}' has been REVIVED.")


def show_audit_log(name: str, limit: int = 10) -> None:
    """Print the last *limit* audit-log entries for an agent."""
    rows = db.get_audit_log(name, limit)
    if not rows:
        print(f"No audit-log entries for '{name}'.")
        return

    print(f"\n{'─' * 80}")
    print(f"  Audit Log for '{name}' (last {len(rows)} entries)")
    print(f"{'─' * 80}")
    print(f"  {'ID':<5} {'Timestamp':<22} {'Action':<25} {'Status':<10} Details")
    print(f"  {'─'*4}  {'─'*20}  {'─'*23}  {'─'*8}  {'─'*20}")
    for r in rows:
        print(f"  {r['id']:<5} {r['timestamp']:<22} {r['action']:<25} "
              f"{r['status']:<10} {r['details']}")
    print()
