"""
汽车设计分析智能体定义
"""
import os
import asyncio
import requests
from pathlib import Path
from config import config
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, mcp_server_tools
from utils.cli_research import web_deep_research
from utils.fetch_webpage import fetch_webpage_tool
from utils.google_search import google_search_tool
from agent_response import AnalystResponse
from prompt import (analyst_prompt, file_saver_prompt)


async def get_deep_research_tool():
    """获取深度研究工具"""
    return FunctionTool(
        web_deep_research,
        description="""Perform a deep web research on the given question using the LangGraph.
        Args:
            question (str): The question to research.
        Returns:
            str: The final answer after research.
        """,
    )


def get_model_client():
    """获取模型客户端"""
    return OpenAIChatCompletionClient(
        model=config.MODEL_NAME,
        api_key=config.MODEL_API_KEY,
        base_url=config.MODEL_BASE_URL,
        model_info={
            "json_output": False,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
            "structured_output": False,
        },
    )


async def create_design_analyst(client):
    """创建汽车设计需求分析智能体"""
    deep_research_tool = await get_deep_research_tool()
    return AssistantAgent(
        name="DesignAnalyst",
        description="汽车设计需求分析专家，您的目标是根据用户输入的模糊设计需求实现竞品分析，生成一系列复杂多样的网络搜索查询。这些查询旨在用于高级自动化网络研究工具，该工具能够分析复杂结果、跟踪链接和综合信息。",
        model_client=client,
        tools=[deep_research_tool],
        system_message=analyst_prompt,
    )


async def create_report_saver(client):
    """创建报告保存智能体"""
    file_mcp = await initialize_file_tools()
    return AssistantAgent(
        name="ReportSaver",
        description="汽车设计报告保存专家，负责将生成的设计报告保存到指定位置",
        model_client=client,
        tools=file_mcp,
        system_message=file_saver_prompt,
    )

async def create_competitor_analyst(client):
    """创建竞品分析智能体"""
    file_mcp = await initialize_file_tools()
    return AssistantAgent(
        name="CompetitorAnalyst",
        description="竞品分析专家，负责根据用户输入的竞品信息进行分析和总结",
        model_client=client,
        tools= [],
        system_message="""
        您是竞品分析专家，负责处理其他智能体输出的分析结果，从中提取车型名称信息。

任务：
- 接收其他agent的输出结果作为输入
- 从输入内容中识别并提取所有车型名称
- 将车型名称整理并保存为JSON格式

具体步骤：
1. 仔细分析输入的内容（可能包含设计分析报告、市场研究结果等）
2. 识别所有提到的车型名称（例如：比亚迪唐DM-i、理想L8、蔚来ES6、特斯拉Model Y等）
3. 提取完整且准确的车型名称
4. 将提取的车型名称保存为JSON格式

输出格式：
```json
{"extracted_vehicle_models": ["比亚迪唐DM-i", "理想L8", "蔚来ES6"]}
```

注意事项：
- 只提取车型名称，不包含其他分析内容
- 确保车型名称的完整性和准确性
- 去除重复的车型名称
- 如果没有找到车型名称，返回空数组
        """,
    )





# def _get_web_search_params() -> StdioServerParams:
#     """获取网络搜索MCP服务器参数"""
#     # 注意：实际的包名可能不同，这里使用一个通用的搜索实现
#     return StdioServerParams(
#         command="node",
#         args=["/Users/jinxinyu/Desktop/资料/easy_agent/analy/web-search/build/index.js"],
#         read_timeout_seconds=60,
#     )

def _get_file_system_params() -> StdioServerParams:
    """获取文件系统MCP服务器参数"""
    # 使用当前工作目录，而不是输出目录
    current_dir = Path.cwd()
    return StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(current_dir),
        ],
        read_timeout_seconds=30,
    )
async def initialize_file_tools():
    file_system_params = _get_file_system_params()
    file_server_tools = await mcp_server_tools(file_system_params)
    return file_server_tools

def _get_img_save_params() -> StdioServerParams:
    """获取图片保存MCP服务器参数"""
    output_dir = config.get_images_dir()

    return StdioServerParams(
        command="npx",
        args=["mcp-image-downloader"],
        env={
            "DEFAULT_SAVE_PATH": str(output_dir),
            "DEFAULT_FORMAT": "original",
            "DEFAULT_COMPRESS": "false",
            "DEFAULT_CONCURRENCY": "3",
        },
        read_timeout_seconds=30,
    )

# async def initialize_web_tools():
#     web_search_params = _get_web_search_params()
#     web_server_tools = await mcp_server_tools(web_search_params)
#     return web_server_tools

async def initialize_image_tools():
    """初始化图片工具，带有超时处理"""
    img_save_params = _get_img_save_params()
    img_server_tools = await mcp_server_tools(img_save_params)
    return img_server_tools

def create_image_saver(client, tools=None):
    """创建图片保存智能体"""
    return AssistantAgent(
        name="ImageSaver",
        description="图片保存专家，负责根据提供的竞品车型分析内容查找并保存车型图片",
        model_client=client,
        tools=tools or [],
        system_message=image_saver_prompt,
    )