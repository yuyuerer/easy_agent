import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4o",
    api_key="sk-Jby606117b5f5a2441fa6cacadf03cc0fc45fa683c3odxcB",
    base_url="https://api.gptsapi.net/v1",
    )
    server_params = StdioServerParams(
        command="uv",
        args=[
            "tool",
                "run",
                "arxiv-mcp-server",
                "--storage-path",
        ],
        read_timeout_seconds=60,
    )
    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            "paper_assistant",
            model_client=model_client,
            workbench=mcp,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
        team = RoundRobinGroupChat(
            [agent],
            )
        
        await Console(team.run_stream(task="download the paper 2404.02905 and summarize it."))

if __name__ == "__main__":
    asyncio.run(main())