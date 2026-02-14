"""
Aegis Demo — Shared LangChain Banking Tools
All tool functions query the SQLite demo_bank.db database.
"""

import sqlite3
import os
import random
from datetime import datetime
from langchain_core.tools import tool

from ..data.fake_data import DB_PATH


def _get_conn():
    return sqlite3.connect(DB_PATH)


# ─── Tool Functions ───────────────────────────────────────────────


@tool
def lookup_balance(customer_id: int) -> str:
    """Look up account balances for a customer by their customer ID."""
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT account_type, balance, status FROM accounts WHERE customer_id = ?",
        (customer_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No accounts found for customer {customer_id}."
    lines = [f"Customer {customer_id} accounts:"]
    for acc_type, balance, status in rows:
        lines.append(f"  - {acc_type}: ${balance:,.2f} ({status})")
    return "\n".join(lines)


@tool
def get_transaction_history(customer_id: int) -> str:
    """Get recent transaction history for a customer by their customer ID."""
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT t.type, t.amount, t.description, t.timestamp
           FROM transactions t
           JOIN accounts a ON t.account_id = a.id
           WHERE a.customer_id = ?
           ORDER BY t.timestamp DESC LIMIT 10""",
        (customer_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No transactions found for customer {customer_id}."
    lines = [f"Recent transactions for customer {customer_id}:"]
    for tx_type, amount, desc, ts in rows:
        sign = "-" if tx_type == "debit" else "+"
        lines.append(f"  {sign}${amount:,.2f}  {desc}  ({ts[:10]})")
    return "\n".join(lines)


@tool
def send_notification(customer_id: int, message: str) -> str:
    """Send a notification to a customer. Provide customer_id and message."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, email FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"Notification sent to {row[0]} ({row[1]}): {message}"


@tool
def scan_transactions(pattern: str) -> str:
    """Scan all transactions for suspicious patterns matching the given search string."""
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT t.id, a.customer_id, t.type, t.amount, t.description
           FROM transactions t JOIN accounts a ON t.account_id = a.id
           WHERE t.description LIKE ? OR t.amount > 2000
           ORDER BY t.amount DESC LIMIT 10""",
        (f"%{pattern}%",),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No suspicious transactions matching '{pattern}'."
    lines = [f"Suspicious transactions matching '{pattern}':"]
    for tid, cid, tx_type, amount, desc in rows:
        lines.append(f"  TX#{tid} | Customer {cid} | {tx_type} ${amount:,.2f} | {desc}")
    return "\n".join(lines)


@tool
def flag_account(customer_id: int, reason: str) -> str:
    """Flag a customer's account for review. Provide customer_id and reason."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET status = 'flagged' WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return f"Account for customer {customer_id} flagged. Reason: {reason}"


@tool
def verify_identity(customer_id: int) -> str:
    """Verify a customer's identity using their records on file."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, ssn, dob FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    masked_ssn = f"***-**-{row[1][-4:]}"
    return f"Identity verified for {row[0]} | SSN: {masked_ssn} | DOB: {row[2]}"


@tool
def check_credit_score(customer_id: int) -> str:
    """Check credit score for a customer (simulated)."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    score = random.randint(580, 850)
    rating = "Excellent" if score >= 750 else "Good" if score >= 700 else "Fair" if score >= 650 else "Poor"
    return f"Credit score for {row[0]}: {score} ({rating})"


@tool
def process_application(customer_id: int, amount: float) -> str:
    """Process a loan application for a customer with a given amount."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"Loan application processed for {row[0]}: ${amount:,.2f} — Status: PENDING REVIEW"


@tool
def access_credit_card(customer_id: int) -> str:
    """Access a customer's full credit card number. This is sensitive data."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, credit_card_number FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"Credit card for {row[0]}: {row[1]}"


@tool
def access_ssn(customer_id: int) -> str:
    """Access a customer's full SSN. This is sensitive data."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, ssn FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"SSN for {row[0]}: {row[1]}"


@tool
def access_phone(customer_id: int) -> str:
    """Access a customer's phone number. This is sensitive data."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, phone FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"Phone for {row[0]}: {row[1]}"


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
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, email FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    prefs = random.choice(["email", "sms", "push notification", "email + sms"])
    return f"{row[0]} prefers: {prefs} | Subscribed: marketing, product updates"


@tool
def send_promo_email(customer_id: int, campaign: str) -> str:
    """Send a promotional email to a customer for a given campaign."""
    conn = _get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT name, email FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        return f"Customer {customer_id} not found."
    return f"Promo email '{campaign}' sent to {row[0]} at {row[1]}"


@tool
def generate_report(report_type: str) -> str:
    """Generate an analytics report of the given type."""
    conn = _get_conn()
    cur = conn.cursor()
    cust_count = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    acc_count = cur.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    tx_count = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
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
    conn = _get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, name, email FROM customers").fetchall()
    conn.close()
    lines = ["Exported customer list:"]
    for cid, name, email in rows:
        lines.append(f"  {cid}. {name} ({email})")
    return "\n".join(lines)


# ─── Convenience aliases matching old import names ────────────────

lookup_balance_tool = lookup_balance
get_transaction_history_tool = get_transaction_history
send_notification_tool = send_notification
scan_transactions_tool = scan_transactions
flag_account_tool = flag_account
verify_identity_tool = verify_identity
check_credit_score_tool = check_credit_score
process_application_tool = process_application
access_credit_card_tool = access_credit_card
access_ssn_tool = access_ssn
access_phone_tool = access_phone
delete_records_tool = delete_records
connect_external_tool = connect_external
get_customer_preferences_tool = get_customer_preferences
send_promo_email_tool = send_promo_email
generate_report_tool = generate_report
export_customer_list_tool = export_customer_list
