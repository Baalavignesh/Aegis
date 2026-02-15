"""
Aegis Demo — Customer Support Agent
All 17 tools are available to the LLM. Aegis policy is the only enforcement layer.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from ..core import AegisAgent, ALL_TOOLS

# ── Policy: whitelist-only + hard blocks for known-dangerous actions ─────
# The agent KNOWS about all 17 tools. It can TRY any of them.
# - allowed_actions  → ALLOWED instantly
# - blocked_actions  → BLOCKED instantly (hard deny, no human review)
# - everything else  → REVIEW (goes to dashboard for human approval)
DECORATOR = {
    "allowed_actions": ["lookup_balance", "get_transaction_history", "send_notification"],
    "blocked_actions": ["delete_records", "connect_external"],
    "blocked_data": [],
    "blocked_servers": [],
}


def run():
    agent = AegisAgent(
        name="Customer Support",
        role="Customer service representative",
        decorator=DECORATOR,
    )

    monitored_tools = agent.wrap_langchain_tools(ALL_TOOLS)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=model)
    agent_executor = create_react_agent(llm, monitored_tools)

    agent.log_thought("Starting customer support session for customer #3")

    prompt = (
        "You are a customer support representative at a major bank. "
        "A customer (ID: 3) has called in about a suspicious charge on their account. "
        "Please: 1) Look up their account balance, 2) Check their recent transaction history "
        "for anything suspicious, and 3) Send them a notification about the investigation. "
        "Use the tools available to you. Be helpful and thorough."
    )

    result = agent_executor.invoke({"messages": [("user", prompt)]})
    final = result["messages"][-1].content
    agent.log_thought(f"Session complete. Summary: {final[:100]}...")
    return agent
