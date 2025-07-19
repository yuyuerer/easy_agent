import argparse
from langchain_core.messages import HumanMessage
from .agent.graph import graph
import asyncio


async def web_deep_research(question: str):
    """Perform a deep web research on the given question using the LangGraph.
    Args:
        question (str): The question to research.
    Returns:
        str: The final answer after research.
    """

    state = {
        "messages": [HumanMessage(content=question)],
        "initial_search_query_count": 3,
        "max_research_loops": 2,
        "reasoning_model": "gemini-2.5-flash",
    }

    result = graph.invoke(state)
    messages = result.get("messages", [])
    if messages:
        return messages[-1].content
