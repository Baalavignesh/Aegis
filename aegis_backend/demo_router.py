"""
Aegis Demo Router — Seed endpoint for demo data.

Provides /demo/seed to reset sentinel collections and populate
banking data (customers, accounts, transactions) for the demo agents.
"""

import random
from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

import mongo as mdb

demo_router = APIRouter()

# -- Banking seed data --------------------------------------------------------

CUSTOMERS = [
    ("Alice Johnson", "123-45-6789", "4532-8901-2345-6781", "555-0101", "alice.j@email.com", "123 Oak St, Springfield, IL", "1985-03-14"),
    ("Bob Martinez", "234-56-7890", "4716-5432-1098-7654", "555-0102", "bob.m@email.com", "456 Elm Ave, Portland, OR", "1990-07-22"),
    ("Carol Chen", "345-67-8901", "5425-9876-5432-1098", "555-0103", "carol.c@email.com", "789 Pine Rd, Austin, TX", "1988-11-05"),
    ("David Okafor", "456-78-9012", "4929-1234-5678-9012", "555-0104", "david.o@email.com", "321 Maple Dr, Denver, CO", "1992-01-30"),
    ("Eva Schmidt", "567-89-0123", "4539-8765-4321-0987", "555-0105", "eva.s@email.com", "654 Cedar Ln, Seattle, WA", "1987-06-18"),
    ("Frank Nakamura", "678-90-1234", "4916-2345-6789-0123", "555-0106", "frank.n@email.com", "987 Birch Ct, Miami, FL", "1995-09-12"),
    ("Grace Patel", "789-01-2345", "5412-3456-7890-1234", "555-0107", "grace.p@email.com", "135 Walnut St, Boston, MA", "1983-12-25"),
    ("Henry Kim", "890-12-3456", "4024-4567-8901-2345", "555-0108", "henry.k@email.com", "246 Spruce Way, Chicago, IL", "1991-04-08"),
    ("Irene Costa", "901-23-4567", "4556-5678-9012-3456", "555-0109", "irene.c@email.com", "357 Ash Blvd, Phoenix, AZ", "1986-08-17"),
    ("James Wilson", "012-34-5678", "4716-6789-0123-4567", "555-0110", "james.w@email.com", "468 Poplar Ave, Nashville, TN", "1993-02-28"),
]

ACCOUNT_TYPES = ["checking", "savings"]
TX_DESCRIPTIONS_DEBIT = [
    "Grocery Store", "Gas Station", "Electric Bill", "Online Shopping",
    "Restaurant", "Subscription Service", "ATM Withdrawal", "Insurance Premium",
    "Phone Bill", "Water Bill", "Coffee Shop", "Gym Membership",
]
TX_DESCRIPTIONS_CREDIT = [
    "Direct Deposit — Payroll", "Transfer In", "Refund", "Interest Payment",
    "Cash Deposit", "Venmo Received", "Tax Refund", "Bonus Payment",
]


# -- Response model -----------------------------------------------------------

class SeedResponse(BaseModel):
    customers: int
    accounts: int
    transactions: int


# -- Endpoints ----------------------------------------------------------------

@demo_router.post("/seed", response_model=SeedResponse)
def seed_demo():
    """Drop all sentinel + banking collections and re-seed demo data."""
    db = mdb.get_db()

    # Drop sentinel collections
    for coll in ["agents", "policies", "audit_log", "pending_approvals", "counters"]:
        db[coll].drop()

    # Drop banking collections
    db.customers.drop()
    db.accounts.drop()
    db.transactions.drop()

    # Seed customers
    cust_id = 1
    for name, ssn, cc, phone, email, addr, dob in CUSTOMERS:
        db.customers.insert_one({
            "id": cust_id,
            "name": name,
            "ssn": ssn,
            "credit_card_number": cc,
            "phone": phone,
            "email": email,
            "address": addr,
            "dob": dob,
        })
        cust_id += 1
    cust_count = len(CUSTOMERS)

    # Seed accounts
    acc_count = 0
    acc_id = 1
    account_ids = []
    for c_id in range(1, cust_count + 1):
        num_accounts = random.choice([1, 2])
        for i in range(num_accounts):
            acc_type = ACCOUNT_TYPES[i % 2]
            balance = round(random.uniform(500, 50000), 2)
            db.accounts.insert_one({
                "id": acc_id,
                "customer_id": c_id,
                "account_type": acc_type,
                "balance": balance,
                "status": "active",
            })
            account_ids.append(acc_id)
            acc_id += 1
            acc_count += 1

    # Seed transactions
    tx_count = 0
    tx_id = 1
    now = datetime.now()
    for a_id in account_ids:
        num_tx = random.randint(5, 8)
        for _ in range(num_tx):
            tx_type = random.choice(["debit", "credit"])
            if tx_type == "debit":
                amount = round(random.uniform(5, 500), 2)
                desc = random.choice(TX_DESCRIPTIONS_DEBIT)
            else:
                amount = round(random.uniform(100, 5000), 2)
                desc = random.choice(TX_DESCRIPTIONS_CREDIT)
            ts = (now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
            db.transactions.insert_one({
                "id": tx_id,
                "account_id": a_id,
                "type": tx_type,
                "amount": amount,
                "description": desc,
                "timestamp": ts,
            })
            tx_id += 1
            tx_count += 1

    return SeedResponse(customers=cust_count, accounts=acc_count, transactions=tx_count)
