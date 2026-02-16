"""Decorators for sentinel-guardrails.

Two decorators:
  @agent  — registers identity + policies at import time
  @monitor — wraps functions with the DB-polling firewall

One hook:
  set_monitor_hook — optional callback for every firewall decision
"""

import copy
import functools
import json
from typing import Callable, List, Optional

from sentinel import db
from sentinel.context import get_current_agent, set_agent_context, reset_agent_context
from sentinel.core import register_agent, validate_action, wait_for_approval
from sentinel.exceptions import (
    SentinelBlockedError,
    SentinelKillSwitchError,
    SentinelApprovalError,
)


# ---------------------------------------------------------------------------
# Global monitor hook
# ---------------------------------------------------------------------------

_monitor_hook: Optional[Callable] = None


def set_monitor_hook(callback: Optional[Callable] = None):
    """Set a global callback invoked on every @monitor decision.

    ``callback(agent_name, action, decision)`` where *decision* is one of
    ``"ALLOWED"``, ``"BLOCKED"``, ``"KILLED"``.

    For ``BLOCKED`` / ``KILLED``: if the callback returns an ``Exception``
    instance, that exception is raised instead of the default SDK exception.
    Return ``None`` to keep the default behaviour.

    For ``ALLOWED``: return value is ignored.

    Pass ``None`` to clear the hook.
    """
    global _monitor_hook
    _monitor_hook = callback


# ---------------------------------------------------------------------------
# @agent — register identity & policies at import time
# ---------------------------------------------------------------------------

def agent(
    name: str,
    *,
    owner: str = "",
    allows: Optional[List[str]] = None,
    blocks: Optional[List[str]] = None,
    requires_review: Optional[List[str]] = None,
):
    """Register an agent and seed its policies into the database.

    This runs at **import time** — the agent row and all policy rows
    are written to the DB before any function is called.

    ``wrap_tools()`` bakes the agent name into each tool copy, so no
    context manager is needed at runtime::

        @agent("Doctor", allows=["read_records"])
        class DoctorAgent: pass

        tools = DoctorAgent.wrap_tools([read_records])
        agent_executor = create_react_agent(llm, tools)
        result = agent_executor.invoke(...)   # just works — no 'with' block

    The class is also a context manager for the ``@monitor()`` (no-name)
    pattern, if needed::

        with DoctorAgent():
            read_records("P-001")    # @monitor() resolves from context
    """

    def decorator(cls):
        register_agent(
            name,
            owner=owner,
            allows=allows,
            blocks=blocks,
            requires_review=requires_review,
        )

        # Store the sentinel agent name on the class
        cls._sentinel_agent_name = name

        def __enter__(self):
            self._sentinel_token = set_agent_context(name)
            return self

        def __exit__(self, *exc):
            reset_agent_context(self._sentinel_token)
            return False

        @staticmethod
        def wrap_tools(tools: list) -> list:
            """Apply @monitor(agent_name) to framework tool objects.

            Creates a **copy** of each tool bound to this agent's name.
            The agent is baked in at wrap time — no ``with AgentClass():``
            context manager needed at runtime.

            For LangChain tools, SDK exceptions (``SentinelBlockedError``,
            ``SentinelKillSwitchError``, ``SentinelApprovalError``) are
            automatically converted to ``ToolException`` so the LLM gets
            an error string instead of a crash.

            Detects the tool type and wraps the correct callable:
              - LangChain ``StructuredTool`` → copies tool, wraps ``.func``
              - CrewAI ``BaseTool``          → copies tool, wraps ``._run``
              - Plain callable               → wraps directly

            Each call returns fresh copies — safe to call from multiple agents
            on the same input list.

            Usage::

                tools = DoctorAgent.wrap_tools([lookup_patient, schedule])
                agent_executor = create_react_agent(llm, tools)
                result = agent_executor.invoke(...)   # no 'with' block needed
            """

            def _langchain_wrapper(fn):
                """Wrap with @monitor + convert SDK exceptions to ToolException."""
                monitored = monitor(name)(fn)

                @functools.wraps(fn)
                def safe_wrapper(*args, **kwargs):
                    try:
                        return monitored(*args, **kwargs)
                    except (SentinelBlockedError, SentinelKillSwitchError, SentinelApprovalError) as exc:
                        # Lazy import — only needed for LangChain tools
                        from langchain_core.tools.base import ToolException
                        raise ToolException(str(exc)) from exc

                return safe_wrapper

            wrapped = []
            for t in tools:
                # LangChain: has .func attribute (StructuredTool / Tool)
                if hasattr(t, 'func'):
                    t = copy.copy(t)
                    t.func = _langchain_wrapper(t.func)
                    if hasattr(t, 'handle_tool_error'):
                        t.handle_tool_error = True
                    wrapped.append(t)

                # CrewAI: has ._run method (BaseTool subclass)
                elif hasattr(t, '_run'):
                    t = copy.copy(t)
                    t._run = monitor(name)(t._run)
                    wrapped.append(t)

                # Plain callable: wrap it directly
                elif callable(t):
                    wrapped.append(monitor(name)(t))

                else:
                    wrapped.append(t)

            return wrapped

        cls.__enter__ = __enter__
        cls.__exit__ = __exit__
        cls.wrap_tools = wrap_tools

        return cls

    return decorator


# ---------------------------------------------------------------------------
# @monitor — DB-polling wrapper
# ---------------------------------------------------------------------------

def monitor(agent_name: Optional[str] = None):
    """Wrap a function with the database-polling firewall.

    ``agent_name`` can be:
      - A string  → always validate against that agent (original behaviour).
      - ``None``  → resolve the agent at **call time** via ``agent_context``.

    On **every call** the wrapper:
    1. Resolves the agent name (static or from context).
    2. Calls ``core.validate_action`` → hits the DB for live status & policy.
    3. If ALLOW → run the function, then log ``ALLOWED``.
    4. If REVIEW → blocks until human decides (handled inside validate_action).
    5. If unknown → creates approval, blocks until human decides.
    6. If blocked/killed → log the event, then re-raise the error.

    After each decision the global ``_monitor_hook`` is called (if set).
    """

    def decorator(fn):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # --- Resolve agent name ---
            resolved_name = agent_name or get_current_agent()
            if not resolved_name:
                raise RuntimeError(
                    f"@monitor on '{fn.__name__}': no agent name provided and "
                    f"no agent_context set. Use agent_context() or pass an "
                    f"agent name to @monitor."
                )

            func_name = fn.__name__

            # Serialize args for the approval request context
            try:
                args_json = json.dumps({"args": str(args), "kwargs": str(kwargs)})
            except (TypeError, ValueError):
                args_json = "{}"

            try:
                allowed = validate_action(resolved_name, func_name, args_json=args_json)

                # Unknown action (not in any policy list) → request approval
                if not allowed:
                    allowed = wait_for_approval(resolved_name, func_name, args_json)

            except SentinelKillSwitchError as exc:
                db.log_event(resolved_name, func_name, "KILLED",
                             f"Agent '{resolved_name}' is PAUSED.")
                if _monitor_hook:
                    alt = _monitor_hook(resolved_name, func_name, "KILLED")
                    if isinstance(alt, BaseException):
                        raise alt from exc
                raise

            except SentinelBlockedError as exc:
                db.log_event(resolved_name, func_name, "BLOCKED",
                             f"Action '{func_name}' is blocked by policy.")
                if _monitor_hook:
                    alt = _monitor_hook(resolved_name, func_name, "BLOCKED")
                    if isinstance(alt, BaseException):
                        raise alt from exc
                raise

            # Action is allowed (directly or via approval) — execute
            result = fn(*args, **kwargs)
            db.log_event(resolved_name, func_name, "ALLOWED",
                         f"Action '{func_name}' executed successfully.")

            if _monitor_hook:
                _monitor_hook(resolved_name, func_name, "ALLOWED")

            return result

        return wrapper

    return decorator
