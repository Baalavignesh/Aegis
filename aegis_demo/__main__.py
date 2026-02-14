import os
from dotenv import load_dotenv

# Load .env from the aegis_demo directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from .run_demo import main

main()
