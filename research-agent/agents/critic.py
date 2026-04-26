"""Critic Agent — evaluates research quality via independent verification.

Used inside the A2A server. Uses local @tool functions for fact-checking.
System prompt loaded from Langfuse.
"""

from datetime import datetime

from langchain.agents import create_agent
from langfuse.langchain import CallbackHandler

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import CritiqueResult
from tools import CRITIC_TOOLS

settings = Settings()


async def run_critic(findings: str, tools: list | None = None) -> str:
    """Run the critic agent and return structured critique."""
    prompt = get_system_prompt(
        "critic-prompt",
        current_date=datetime.now().strftime("%Y-%m-%d"),
    )
    handler = CallbackHandler()
    critic = create_agent(
        model=settings.model_powerful,
        tools=tools or CRITIC_TOOLS,
        system_prompt=prompt,
        response_format=CritiqueResult,
        name="critic",
    )
    result = await critic.ainvoke(
        {"messages": [{"role": "user", "content": findings}]},
        {
            "recursion_limit": 15,
            "callbacks": [handler],
            "metadata": {"langfuse_tags": ["research-agent", "critic"]},
        },
    )
    structured: CritiqueResult = result["structured_response"]
    parts = [
        f"VERDICT: {structured.verdict}",
        f"Fresh: {structured.is_fresh} | Complete: {structured.is_complete} | "
        f"Well-structured: {structured.is_well_structured}",
    ]
    if structured.strengths:
        parts.append(f"Strengths: {'; '.join(structured.strengths)}")
    if structured.gaps:
        parts.append(f"Gaps: {'; '.join(structured.gaps)}")
    if structured.revision_requests:
        parts.append(f"Revision requests: {'; '.join(structured.revision_requests)}")
    return "\n".join(parts)
