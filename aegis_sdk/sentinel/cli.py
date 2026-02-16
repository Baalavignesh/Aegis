"""CLI for sentinel-guardrails.

Usage:
    sentinel kill <agent_name>
    sentinel revive <agent_name>
    sentinel logs <agent_name> [--limit N]
"""

import argparse
import sys

from sentinel import db


def kill_agent(name: str) -> None:
    """Set agent status to PAUSED (kill switch)."""
    db.update_status(name, "PAUSED")
    print(f"Agent '{name}' has been PAUSED.")


def revive_agent(name: str) -> None:
    """Set agent status to ACTIVE."""
    db.update_status(name, "ACTIVE")
    print(f"Agent '{name}' has been REVIVED.")


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


def main():
    """Entry point for the ``sentinel`` CLI command."""
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="sentinel-guardrails — manage AI agent policies from the terminal.",
    )
    sub = parser.add_subparsers(dest="command")

    # sentinel kill <name>
    p_kill = sub.add_parser("kill", help="Pause an agent (kill switch)")
    p_kill.add_argument("name", help="Agent name to pause")

    # sentinel revive <name>
    p_revive = sub.add_parser("revive", help="Reactivate a paused agent")
    p_revive.add_argument("name", help="Agent name to revive")

    # sentinel logs <name> [--limit N]
    p_logs = sub.add_parser("logs", help="Show audit log for an agent")
    p_logs.add_argument("name", help="Agent name")
    p_logs.add_argument("--limit", type=int, default=10, help="Number of entries (default: 10)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "kill":
        kill_agent(args.name)
    elif args.command == "revive":
        revive_agent(args.name)
    elif args.command == "logs":
        show_audit_log(args.name, args.limit)


if __name__ == "__main__":
    main()
