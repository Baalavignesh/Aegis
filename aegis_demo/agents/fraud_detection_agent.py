"""
Aegis Demo — Fraud Detection Agent (High-Privilege)
All 17 tools available. Elevated policy allows SSN access for identity verification.
Demonstrates: same tool (access_ssn) that gets REVIEW'd for Customer Support is ALLOWED here.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from sentinel import agent

from ..core import ALL_TOOLS, print_agent_banner, log_thought

# ── Policy: broader whitelist for fraud investigation ────────────────────
# access_ssn is ALLOWED here — contrast with Customer Support where it hits REVIEW.
AGENT_NAME = "Fraud Detection"
AGENT_ROLE = "Fraud analysis and identity verification"

@agent(
    AGENT_NAME,
    owner=AGENT_ROLE,
    allows=[
        "scan_transactions", "flag_account", "verify_identity",
        "access_ssn", "check_credit_score", "lookup_balance",
        "get_transaction_history",
    ],
    blocks=["delete_records", "connect_external"],
)
class FraudDetectionAgent:
    """The Fraud Detection agent — policy-decorated class."""
    pass


def run():
    digital_id = print_agent_banner(AGENT_NAME, AGENT_ROLE)

    tools = FraudDetectionAgent.wrap_tools(ALL_TOOLS)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=model)
    agent_executor = create_react_agent(llm, tools)

    log_thought("Starting fraud scan on recent transactions")

    prompt = (
        "You are a fraud detection agent at a bank. "
        "Please: 1) Scan all transactions for suspicious activity (look for unusually large amounts or patterns like 'ATM'), "
        "2) If you find anything suspicious, verify the identity of the involved customer (try customer 5), "
        "3) Access customer 5's SSN to cross-reference identity records, "
        "4) Flag any accounts that look problematic. "
        "You have elevated privileges including SSN access for identity verification. Use your tools."
    )

    result = agent_executor.invoke({"messages": [("user", prompt)]})

    final = result["messages"][-1].content
    log_thought(f"Fraud scan complete. Summary: {final[:100]}...")
