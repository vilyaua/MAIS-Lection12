"""Planner Agent — decomposes a user request into a structured ResearchPlan.

Used inside the A2A server. Uses local @tool functions for searches.
System prompt loaded from Langfuse.
"""

from langchain.agents import create_agent

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import ResearchPlan
from tools import PLANNER_TOOLS

settings = Settings()


async def run_planner(request: str, tools: list | None = None) -> str:
    """Run the planner agent and return formatted plan."""
    prompt = get_system_prompt("planner-prompt")
    planner = create_agent(
        model=settings.model_powerful,
        tools=tools or PLANNER_TOOLS,
        system_prompt=prompt,
        response_format=ResearchPlan,
        name="planner",
    )
    result = await planner.ainvoke(
        {"messages": [{"role": "user", "content": request}]},
        {"recursion_limit": 30},
    )
    structured: ResearchPlan = result["structured_response"]
    return (
        f"RESEARCH PLAN:\n"
        f"Goal: {structured.goal}\n"
        f"Search queries: {', '.join(structured.search_queries)}\n"
        f"Sources: {', '.join(structured.sources_to_check)}\n"
        f"Output format: {structured.output_format}"
    )
