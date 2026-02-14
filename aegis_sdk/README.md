# Aegis SDK

Python SDK that developers integrate into their AI agents to connect them to the Agent Sentinel platform.

## Responsibilities

- **`SentinelAgent` Class** — Main entry point for registering an agent, defining its decorator policy, and connecting to the backend
- **`@monitor` Decorator** — Wraps any agent tool/function to intercept calls and validate them against the decorator policy before execution
- **Client-side Firewall** — Local policy checks that block disallowed actions immediately, without a network round-trip
- **Thought Logging** — Optional API to log agent reasoning and chain-of-thought for auditing and debugging
- **Manifest Generator** — CLI tool (`sentinel manifest generate`) that scans decorated agents across a codebase and produces an `agent_manifest.json` (AgentBOM)
- **Framework Adapters** — Pre-built integrations for popular agent frameworks:
  - `adapters/langgraph.py` — LangGraph tool wrapping
  - `adapters/langchain.py` — LangChain tool wrapping
  - `adapters/crewai.py` — CrewAI tool wrapping

## Tech Stack

- **Language:** Python 3.10+
- **HTTP Client:** httpx / requests
- **Packaging:** setuptools (`setup.py`) / pyproject.toml
- **CLI:** Click or argparse (for manifest generation commands)

## Getting Started

```bash
cd aegis_sdk
pip install -e .
```

### Basic Usage

```python
from sentinel import SentinelAgent

agent = SentinelAgent(
    name="MyAgent",
    framework="custom",
    server_url="http://localhost:8000",
    decorator={
        "allowed_actions": ["read_database", "send_email"],
        "blocked_actions": ["delete_records", "access_credentials"],
        "allowed_data": ["sales_data"],
        "blocked_data": ["PII", "passwords"],
    }
)

@agent.monitor
def read_database(query: str) -> dict:
    return db.execute(query)
```

See the main [AGENT-SENTINEL-README.md](../AGENT-SENTINEL-README.md) for the full SDK usage guide.
