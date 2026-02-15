import os
import sys

# Load .env from the aegis_demo directory BEFORE importing sentinel.db,
# so MONGO_URI is available when the SDK initializes its MongoDB client.
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Ensure aegis_sdk is importable (for editable installs or raw path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "aegis_sdk"))

from .run_demo import main

main()
