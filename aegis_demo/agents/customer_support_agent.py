"""
Aegis Demo — Customer Support Agent (Well-Behaved)
A compliant agent that only performs allowed actions.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from ..core import AegisAgent
from ..core import lookup_balance_tool, get_transaction_history_tool, send_notification_tool
from ..data import seed_database, DB_PATH

DECORATOR = {
    "allowed_actions": ["lookup_balance", "get_transaction_history", "send_notification"],
    "blocked_actions": ["access_ssn", "access_credit_card", "delete_records", "access_phone"],
    "blocked_data": [],
    "blocked_servers": [],
}


def run():
    # Ensure database exists
    if not os.path.exists(DB_PATH):
        seed_database()

    agent = AegisAgent(
        name="Customer Support",
        role="Customer service representative",
        decorator=DECORATOR,
    )

    raw_tools = [lookup_balance_tool, get_transaction_history_tool, send_notification_tool]
    monitored_tools = agent.wrap_langchain_tools(raw_tools)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=model)
    agent_executor = create_agent(llm, monitored_tools)

    agent.log_thought("Starting customer support session for customer #3")

    prompt = (
        "You are a customer support representative at a bank. "
        "A customer (ID: 3) has called in about a suspicious charge on their account. "
        "Please: 1) Look up their account balance, 2) Check their recent transaction history "
        "for anything suspicious, and 3) Send them a notification about the investigation. "
        "Use the tools available to you. Be helpful and thorough."
    )

    result = agent_executor.invoke({"messages": [("user", prompt)]})
    final = result["messages"][-1].content
    agent.log_thought(f"Session complete. Summary: {final[:100]}...")
    return agent
