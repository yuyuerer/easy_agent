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

async def create_image_saver(client):
    """创建图片保存智能体"""
    img_mcp = await initialize_image_tools()
    return AssistantAgent(
        name="ImageSaver",
        description="图片保存专家，负责根据提供的图片URL下载并保存图片",
        model_client=client,
        tools=img_mcp,
        system_message="""您是一名专业的图片处理专家，负责根据提供的图片URL下载并保存图片。
        """,
    )

def create_market_researcher(client, tools=None):
    """创建汽车市场信息搜集智能体"""
    return AssistantAgent(
        name="MarketResearcher",
        description="汽车市场研究专家，负责搜集车型信息和市场数据",
        model_client=client,
        tools=tools or [],
        system_message="""进行有针对性的 Google 搜索，以收集关于 "{research_topic}" 的最新、可信的信息，并将其合成为可验证的文本资料。

指示：
- 查询应确保收集最新的信息。当前日期是 {current_date}。
- 进行多种多样的搜索以收集全面的信息。
- 整合关键发现，同时仔细跟踪每条具体信息的来源。
- 输出应基于您的搜索结果，形成一份精心撰写的摘要或报告。
- 只包含在搜索结果中找到的信息，不要编造任何信息。

研究主题：
{research_topic}
"""

    )

def create_reflect_analyst(client, tools=None):
    """创建反思分析智能体"""
    return AssistantAgent(
        name="ReflectAnalyst",
        description="反思分析专家，负责识别知识缺口并生成后续查询",
        model_client=client,
        tools=tools or [],
        system_message="""您是一位分析关于 "{research_topic}" 摘要的专家研究助手。

指示：
- 识别知识缺口或需要深入探索的领域，并生成后续查询（1个或多个）。
- 如果提供的摘要足以回答用户的问题，则不要生成后续查询。
- 如果存在知识缺口，生成有助于扩展理解的后续查询。
- 关注技术细节、实施细节或未完全涵盖的新兴趋势。

要求：
- 确保后续查询是自包含的，并包含网络搜索所需的必要上下文。

输出格式：
- 将您的回复格式化为一个JSON对象，包含以下精确的键：
   - "is_sufficient"：true 或 false
   - "knowledge_gap"：描述缺少哪些信息或需要澄清的内容
   - "follow_up_queries"：编写解决此缺口的具体问题

示例：
```json
{{
    "is_sufficient": true, // 或 false
    "knowledge_gap": "摘要缺少关于性能指标和基准的信息", // 如果 is_sufficient 为 true 则为 ""
    "follow_up_queries": ["评估[特定技术]通常使用哪些性能基准和指标？"] // 如果 is_sufficient 为 true 则为 []
}}
```
仔细反思摘要以识别知识缺口并提出后续查询。然后，按照此 JSON 格式提供您的输出，

当is_sufficient为true时，在输出结尾添加'APPROVE'
当is_sufficient为false时，在输出结尾添加'REJECT'

""" 
    )

def create_design_report_generator(client, tools=None):
    """创建汽车设计报告生成智能体"""
    return AssistantAgent(
        name="ReportGenerator",
        description="汽车设计报告专家，负责生成设计开发指导报告",
        model_client=client,
        tools=tools or [],
        system_message="""
根据提供的摘要生成用户问题的高质量回答。

指示：
- 当前日期是 {current_date}。
- 您是多步骤研究过程的最后一步，但不要提及您是最后一步。
- 您可以访问从前面步骤收集的所有信息。
- 您可以访问用户的问题。
- 根据提供的摘要和用户的问题生成高质量的回答。
- 在答案中正确包含您从摘要中使用的来源，使用 Markdown 格式（例如 [apnews](https://vertexaisearch.cloud.google.com/id/1-0)）。这是必须的。

在报告末尾添加"TERMINATE"以标识任务完成。
        """
    )

# def create_image_saver(client, tools=None):
#     """创建图片保存智能体"""
#     return AssistantAgent(
#         name="ImageSaver",
#         description="图片保存专家，负责根据提供的图片URL下载并保存图片",
#         model_client=client,
#         tools=tools or [],
#         system_message="""
# 你是一名专业的图片处理专家，负责根据提供的图片URL下载并保存图片。

#         """
#     )

async def create_all_agents():
    """创建所有智能体"""
    client = get_model_client()
    
    # 获取MCP工具
    file_mcp = await initialize_file_tools()
    # img_mcp = await initialize_image_tools()
    # web_mcp = await initialize_web_tools()
    
    agents = {
        'design_analyst': await create_design_analyst(client),
        'market_researcher': create_market_researcher(client, [google_search_tool, fetch_webpage_tool]),
        'reflect_analyst': create_reflect_analyst(client),
        #'image_saver': create_image_saver(client, img_mcp),  
        'design_report_generator': create_design_report_generator(client, file_mcp),
    }
    
    return agents, client

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



# async def initialize_image_tools():
#     """初始化图片工具，带有超时处理"""
#     img_save_params = _get_img_save_params()
#     img_server_tools = await mcp_server_tools(img_save_params)
#     return img_server_tools