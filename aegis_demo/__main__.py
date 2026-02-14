import os
import sys

# Ensure aegis_sdk is importable (for editable installs or raw path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "aegis_sdk"))

# Point sentinel DB to aegis_demo/data/ before any demo imports
import sentinel.db as _sdb
_sdb.DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sentinel.db")

from dotenv import load_dotenv

# Load .env from the aegis_demo directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from .run_demo import main

main()
