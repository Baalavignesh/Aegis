"""Vercel serverless entry point.

Vercel expects a handler at api/index.py. We import the FastAPI app
from backend.py and expose it as `app` for the @vercel/python runtime.
"""

import sys
import os

# Add the parent directory (aegis_backend/) to the Python path
# so that `import mongo`, `import demo_router`, etc. resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend import app  # noqa: F401, E402
