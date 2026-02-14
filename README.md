A governance for AI Agents to know what each agent is meant to do and make sure no AI will hallucinate. 

The idea is to create a package that act as a decorator which we add above each Agent created. The user manually types what the agent is supposed to do and wihch data it can handle. 

Once we run a command, it will create a config.json file which can be used to display the information in a neat format in a website.

If the user makes a mistake/ if the user didn't write a decorator. We will have a custom agent that will use certain tools to write the decorator for the user.

If the Agent is trying to do an operation that it is not meant to do, such as accessing certain information by trying to bypass, we hold it and make sure it won't move forward.

Each agent gets a unique identity with declared capabilities, permissions, and ownership, similar to how IAM works for human users in cloud platforms.

dashboard and visualization — the web UI that shows the agent list, risk badges, dependency graph.

So the decorator isn't just metadata anymore, it's a guardrail wrapper. Think of it like a middleware that intercepts every action the agent takes and validates it against the declared permissions before letting it through.

AgentBOM's governance rule engine automatically scans each agent's manifest against a set of configurable rules defined in YAML — such as "any agent accessing PII must have a human approval step" or "production write access requires an assigned owner." When violations are detected, they surface on the dashboard with severity levels and suggested fixes. An LLM layer enriches each flag with a contextual, human-readable risk explanation. This turns governance from a manual audit process into an automated, continuous check that runs alongside development — catching policy gaps the moment they appear rather than weeks later during a compliance review.

LLM-powered summarization — auto-generating human-readable descriptions and risk assessments from the manifest. 

Exports — the audit-ready Markdown/PDF fact sheets.  

AgentBOM automatically maps how agents depend on each other by reading the dependencies field in each agent's manifest. It builds a directed graph where agents are nodes, calls between them are edges, and tools and data sources branch off as connected endpoints. This renders as an interactive visualization on the dashboard — click any agent and instantly trace what it calls, what calls it, and what data flows through it. When something breaks or access gets revoked, teams can immediately see the blast radius instead of manually tracing through code across multiple repos. (MultiAgent)