"""Direct MongoDB connection for demo banking tools.

The sentinel SDK no longer connects to MongoDB directly (it uses HTTP).
But the demo's banking tools (lookup_balance, etc.) need to query
customer/account/transaction data. This module provides that connection.
"""

import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "sentinel_db")

_CLIENT = None


def get_db():
    """Get the MongoDB database for banking data queries."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = MongoClient(MONGO_URI)
    return _CLIENT[DB_NAME]
