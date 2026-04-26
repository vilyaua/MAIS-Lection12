"""Research Agent — executes the research plan using web + knowledge base.

Used inside the A2A server. Uses local @tool functions for searches.
System prompt loaded from Langfuse.
"""

from langchain.agents import create_agent
from langfuse.langchain import CallbackHandler

from config import Settings
from langfuse_prompts import get_system_prompt
from tools import RESEARCH_TOOLS

settings = Settings()


async def run_researcher(request: str, tools: list | None = None) -> str:
    """Run the research agent and return findings."""
    prompt = get_system_prompt("researcher-prompt")
    handler = CallbackHandler()
    researcher = create_agent(
        model=settings.model_fast,
        tools=tools or RESEARCH_TOOLS,
        system_prompt=prompt,
        name="researcher",
    )
    result = await researcher.ainvoke(
        {"messages": [{"role": "user", "content": request}]},
        {
            "recursion_limit": 30,
            "callbacks": [handler],
            "metadata": {"langfuse_tags": ["research-agent", "researcher"]},
        },
    )
    return result["messages"][-1].content
