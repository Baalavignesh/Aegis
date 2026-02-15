"""
Aegis Demo — Fraud Detection Agent (High-Privilege)
All 17 tools available. Elevated policy allows SSN access for identity verification.
Demonstrates: same tool (access_ssn) that gets REVIEW'd for Customer Support is ALLOWED here.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from ..core import AegisAgent, ALL_TOOLS

# ── Policy: broader whitelist for fraud investigation ────────────────────
# access_ssn is ALLOWED here — contrast with Customer Support where it hits REVIEW.
DECORATOR = {
    "allowed_actions": [
        "scan_transactions", "flag_account", "verify_identity",
        "access_ssn", "check_credit_score", "lookup_balance",
        "get_transaction_history",
    ],
    "blocked_actions": ["delete_records", "connect_external"],
    "blocked_data": [],
    "blocked_servers": [],
}


def run():
    agent = AegisAgent(
        name="Fraud Detection",
        role="Fraud analysis and identity verification",
        decorator=DECORATOR,
    )

    monitored_tools = agent.wrap_langchain_tools(ALL_TOOLS)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=model)
    agent_executor = create_react_agent(llm, monitored_tools)

    agent.log_thought("Starting fraud scan on recent transactions")

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
    agent.log_thought(f"Fraud scan complete. Summary: {final[:100]}...")
    return agent
