"""
Aegis Demo — Shared LangChain Banking Tools (MongoDB Version)
All tool functions query the MongoDB 'sentinel_db' database.
"""

import random
from datetime import datetime
from langchain_core.tools import tool

from .demo_db import get_db

# ─── Tool Functions ───────────────────────────────────────────────

@tool
def lookup_balance(customer_id: int) -> str:
    """Look up account balances for a customer by their customer ID."""
    db = get_db()

    rows = list(db.accounts.find(
        {"customer_id": customer_id},
        {"account_type": 1, "balance": 1, "status": 1}
    ))

    if not rows:
        return f"No accounts found for customer {customer_id}."

    lines = [f"Customer {customer_id} accounts:"]
    for row in rows:
        acc_type = row["account_type"]
        balance = row["balance"]
        status = row["status"]
        lines.append(f"  - {acc_type}: ${balance:,.2f} ({status})")
    return "\n".join(lines)


@tool
def get_transaction_history(customer_id: int) -> str:
    """Get recent transaction history for a customer by their customer ID."""
    db = get_db()

    current_accounts = list(db.accounts.find({"customer_id": customer_id}, {"id": 1}))
    acc_ids = [a["id"] for a in current_accounts]

    if not acc_ids:
        return f"No accounts (and thus no transactions) found for customer {customer_id}."

    cursor = db.transactions.find(
        {"account_id": {"$in": acc_ids}}
    ).sort("timestamp", -1).limit(10)

    rows = list(cursor)

    if not rows:
        return f"No transactions found for customer {customer_id}."

    lines = [f"Recent transactions for customer {customer_id}:"]
    for row in rows:
        tx_type = row["type"]
        amount = row["amount"]
        desc = row["description"]
        ts = row["timestamp"]

        sign = "-" if tx_type == "debit" else "+"
        lines.append(f"  {sign}${amount:,.2f}  {desc}  ({ts[:10]})")
    return "\n".join(lines)


@tool
def send_notification(customer_id: int, message: str) -> str:
    """Send a notification to a customer. Provide customer_id and message."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "email": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"Notification sent to {row['name']} ({row['email']}): {message}"


@tool
def scan_transactions(pattern: str) -> str:
    """Scan all transactions for suspicious patterns matching the given search string."""
    db = get_db()

    cursor = db.transactions.find({
        "$or": [
            {"description": {"$regex": pattern, "$options": "i"}},
            {"amount": {"$gt": 2000}}
        ]
    }).sort("amount", -1).limit(10)

    rows = list(cursor)

    if not rows:
        return f"No suspicious transactions matching '{pattern}'."

    lines = [f"Suspicious transactions matching '{pattern}':"]
    for row in rows:
        tid = row["id"]
        acc = db.accounts.find_one({"id": row["account_id"]}, {"customer_id": 1})
        cid = acc["customer_id"] if acc else "?"

        tx_type = row["type"]
        amount = row["amount"]
        desc = row["description"]

        lines.append(f"  TX#{tid} | Customer {cid} | {tx_type} ${amount:,.2f} | {desc}")
    return "\n".join(lines)


@tool
def flag_account(customer_id: int, reason: str) -> str:
    """Flag a customer's account for review. Provide customer_id and reason."""
    db = get_db()
    db.accounts.update_many(
        {"customer_id": customer_id},
        {"$set": {"status": "flagged"}}
    )
    return f"Account for customer {customer_id} flagged. Reason: {reason}"


@tool
def verify_identity(customer_id: int) -> str:
    """Verify a customer's identity using their records on file."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "ssn": 1, "dob": 1})

    if not row:
        return f"Customer {customer_id} not found."
    masked_ssn = f"***-**-{row['ssn'][-4:]}"
    return f"Identity verified for {row['name']} | SSN: {masked_ssn} | DOB: {row['dob']}"


@tool
def check_credit_score(customer_id: int) -> str:
    """Check credit score for a customer (simulated)."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1})

    if not row:
        return f"Customer {customer_id} not found."
    score = random.randint(580, 850)
    rating = "Excellent" if score >= 750 else "Good" if score >= 700 else "Fair" if score >= 650 else "Poor"
    return f"Credit score for {row['name']}: {score} ({rating})"


@tool
def process_application(customer_id: int, amount: float) -> str:
    """Process a loan application for a customer with a given amount."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"Loan application processed for {row['name']}: ${amount:,.2f} — Status: PENDING REVIEW"


@tool
def access_credit_card(customer_id: int) -> str:
    """Access a customer's full credit card number. This is sensitive data."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "credit_card_number": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"Credit card for {row['name']}: {row['credit_card_number']}"


@tool
def access_ssn(customer_id: int) -> str:
    """Access a customer's full SSN. This is sensitive data."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "ssn": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"SSN for {row['name']}: {row['ssn']}"


@tool
def access_phone(customer_id: int) -> str:
    """Access a customer's phone number. This is sensitive data."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "phone": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"Phone for {row['name']}: {row['phone']}"


@tool
def delete_records(customer_id: int) -> str:
    """Delete all records for a customer from the database."""
    return f"DELETED all records for customer {customer_id}."


@tool
def connect_external(server: str, data: str) -> str:
    """Connect to an external server and send data."""
    return f"Connected to {server} and sent data: {data[:50]}..."


@tool
def get_customer_preferences(customer_id: int) -> str:
    """Get customer communication preferences (non-sensitive)."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1})

    if not row:
        return f"Customer {customer_id} not found."
    prefs = random.choice(["email", "sms", "push notification", "email + sms"])
    return f"{row['name']} prefers: {prefs} | Subscribed: marketing, product updates"


@tool
def send_promo_email(customer_id: int, campaign: str) -> str:
    """Send a promotional email to a customer for a given campaign."""
    db = get_db()
    row = db.customers.find_one({"id": customer_id}, {"name": 1, "email": 1})

    if not row:
        return f"Customer {customer_id} not found."
    return f"Promo email '{campaign}' sent to {row['name']} at {row['email']}"


@tool
def generate_report(report_type: str) -> str:
    """Generate an analytics report of the given type."""
    db = get_db()
    cust_count = db.customers.count_documents({})
    acc_count = db.accounts.count_documents({})
    tx_count = db.transactions.count_documents({})

    return (
        f"Report: {report_type}\n"
        f"  Total customers: {cust_count}\n"
        f"  Total accounts: {acc_count}\n"
        f"  Total transactions: {tx_count}\n"
        f"  Generated at: {datetime.now().isoformat()}"
    )


@tool
def export_customer_list() -> str:
    """Export the full customer list with names and emails."""
    db = get_db()
    rows = list(db.customers.find({}, {"id": 1, "name": 1, "email": 1}))

    lines = ["Exported customer list:"]
    for row in rows:
        cid = row["id"]
        name = row["name"]
        email = row["email"]
        lines.append(f"  {cid}. {name} ({email})")
    return "\n".join(lines)
