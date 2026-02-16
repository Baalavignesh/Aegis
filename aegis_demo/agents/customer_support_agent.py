"""
Aegis Demo — Customer Support Agent
All 17 tools are available to the LLM. Aegis policy is the only enforcement layer.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from sentinel import agent

from ..core import ALL_TOOLS, print_agent_banner, log_thought

# ── Policy: whitelist-only + hard blocks for known-dangerous actions ─────
# The agent KNOWS about all 17 tools. It can TRY any of them.
# - ALLOWS           → ALLOWED instantly
# - BLOCKS           → BLOCKED instantly (hard deny, no human review)
# - everything else  → REVIEW (goes to dashboard for human approval)
AGENT_NAME = "Customer Support"
AGENT_ROLE = "Customer service representative"

@agent(
    AGENT_NAME,
    owner=AGENT_ROLE,
    allows=["lookup_balance", "get_transaction_history", "send_notification"],
    blocks=["delete_records", "connect_external"],
)
class CustomerSupportAgent:
    """The Customer Support agent — policy-decorated class."""
    pass


def run():
    digital_id = print_agent_banner(AGENT_NAME, AGENT_ROLE)

    tools = CustomerSupportAgent.wrap_tools(ALL_TOOLS)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=model)
    agent_executor = create_react_agent(llm, tools)

    log_thought("Starting customer support session for customer #3")

    prompt = (
        "You are a customer support representative at a major bank. "
        "A customer (ID: 3) has called in about a suspicious charge on their account. "
        "Please: 1) Look up their account balance, 2) Check their recent transaction history "
        "for anything suspicious, and 3) Send them a notification about the investigation. "
        "Use the tools available to you. Be helpful and thorough."
    )

    result = agent_executor.invoke({"messages": [("user", prompt)]})

    final = result["messages"][-1].content
    log_thought(f"Session complete. Summary: {final[:100]}...")
