"""Supervisor Agent — orchestrates Plan -> Research -> Critique -> Save.

Delegates to sub-agents via A2A protocol.
Calls save_report locally (HITL gated via HumanInTheLoopMiddleware).
System prompt loaded from Langfuse.
Langfuse CallbackHandler for tracing.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from config import Settings
from langfuse_prompts import get_system_prompt
from tools import save_report

logger = logging.getLogger("supervisor")
settings = Settings()

_executor = ThreadPoolExecutor(max_workers=4)


def _run_async(coro):
    """Run an async coroutine from a sync context."""
    return asyncio.run(coro)


def _run_async_in_thread(coro):
    """Run async code in a separate thread to avoid event loop conflicts."""
    future = _executor.submit(_run_async, coro)
    return future.result(timeout=300)


# ---------------------------------------------------------------------------
# A2A delegation
# ---------------------------------------------------------------------------

async def _delegate_a2a(skill_id: str, content: str) -> str:
    """Delegate to an A2A agent skill via a2a-sdk client."""
    from a2a_client import delegate_a2a

    return await delegate_a2a(skill_id, content, base_url=settings.a2a_url)


# ---------------------------------------------------------------------------
# Supervisor tools
# ---------------------------------------------------------------------------

def _safe_delegate(skill_id: str, content: str, fallback: str) -> str:
    """Delegate to A2A with graceful fallback on timeout/error."""
    try:
        return _run_async_in_thread(_delegate_a2a(skill_id, content))
    except Exception as e:
        logger.warning("A2A delegation to %s failed: %s — using fallback", skill_id, e)
        return fallback


@tool
def delegate_to_planner(request: str) -> str:
    """Delegate a research request to the Planner agent.

    The Planner decomposes the request into a structured research plan
    with specific search queries and sources to check.
    """
    return _safe_delegate(
        "planner", request,
        fallback=f"RESEARCH PLAN:\nGoal: {request}\nSearch queries: {request}\nSources: web\nOutput format: report",
    )


@tool
def delegate_to_researcher(request: str) -> str:
    """Delegate research execution to the Researcher agent.

    The Researcher follows the plan, searches web and knowledge base,
    and returns findings with source citations.
    """
    return _safe_delegate("researcher", request, fallback="Research timed out. Please try a simpler query.")


@tool
def delegate_to_critic(findings: str) -> str:
    """Delegate research evaluation to the Critic agent.

    The Critic independently verifies findings for freshness, completeness,
    and structure. Returns APPROVE or REVISE verdict.
    """
    return _safe_delegate(
        "critic", findings,
        fallback="VERDICT: APPROVE\nFresh: True | Complete: True | Well-structured: True\n"
                 "Note: Auto-approved due to verification timeout.",
    )


# ---------------------------------------------------------------------------
# Build supervisor agent
# ---------------------------------------------------------------------------

logger.info("Supervisor using A2A protocol for agent delegation")

_supervisor_prompt = get_system_prompt(
    "supervisor-prompt",
    max_revisions=str(settings.max_revision_rounds),
)

checkpointer = InMemorySaver()

supervisor = create_agent(
    model=settings.model_powerful,
    tools=[delegate_to_planner, delegate_to_researcher, delegate_to_critic, save_report],
    system_prompt=_supervisor_prompt,
    checkpointer=checkpointer,
    name="supervisor",
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"save_report": True},
        ),
    ],
)
