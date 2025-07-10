"""
汽车设计分析智能体定义
"""
import os
import asyncio
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config import config
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, mcp_server_tools
from utils.fetch_webpage import fetch_webpage_tool
from utils.google_search import google_search_tool





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


def create_design_analyst(client, tools=None):
    """创建汽车设计需求分析智能体"""
    return AssistantAgent(
        name="DesignAnalyst",
        description="汽车设计需求分析专家，负责细化汽车设计要素",
        model_client=client,
        tools=tools or [],
        system_message="""您的目标是生成复杂多样的网络搜索查询。这些查询旨在用于高级自动化网络研究工具，该工具能够分析复杂结果、跟踪链接和综合信息。

指示：
- 始终优先选择单个搜索查询，只有当原始问题要求多个方面或元素且一个查询不足时才添加另一个查询。
- 每个查询应专注于原始问题的一个特定方面，例如汽车外观设计、运动型SUV的特点等。
- 不要生成超过10个查询。
- 查询应当多样化，如果主题范围广泛，生成多于1个查询。
- 不要生成多个相似的查询，1个就足够了。
- 查询应确保收集最新信息。

格式：
- 将您的回复格式化为一个JSON对象，包含这两个精确的键：
   - "rationale"：为什么这些查询相关的简要解释
   - "query"：搜索查询列表

示例：

Context：我想要一个运动型的SUV，希望外观看起来比较有攻击性
```json
{{
    "rationale": "为了找到符合用户需求的运动型SUV，我们需要针对汽车外观设计、运动型特点以及市场上流行的SUV车型进行搜索。这些查询旨在收集关于外观设计趋势、运动型SUV的市场评价以及具体车型的相关信息。",
    "query": ["运动型SUV外观设计趋势", "攻击性外观的SUV推荐", "2025年运动型SUV市场评价"],
}}
 ```

 """
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
    img_mcp = await initialize_image_tools()
    # web_mcp = await initialize_web_tools()
    
    agents = {
        'design_analyst': create_design_analyst(client),
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
    output_dir = config.get_output_dir()
    
    return StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(output_dir),
        ],
        read_timeout_seconds=30,
    )

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

async def initialize_file_tools():
    file_system_params = _get_file_system_params()
    file_server_tools = await mcp_server_tools(file_system_params)
    return file_server_tools

async def initialize_image_tools():
    """初始化图片工具，带有超时处理"""
    img_save_params = _get_img_save_params()
    img_server_tools = await mcp_server_tools(img_save_params)
    return img_server_tools
    