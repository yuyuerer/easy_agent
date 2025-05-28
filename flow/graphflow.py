from autogen_agentchat.agents import AssistantAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, SseServerParams

from google_search import google_search_tool
from fetch_webpage import fetch_webpage_tool


# Create an OpenAI model client
client = OpenAIChatCompletionClient(model="qwen-turbo-latest",
    api_key="sk-1d89e189fe624c3698a04a048c285069",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_info={
        "json_output": False,
        "function_calling": True,
        "vision": False,
        "family": "unknown",
        "structured_output": False,
    },
)

server_params = SseServerParams(
      url = "https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization=d25852aa856b47bfb43792e801f4e552.09cTV7pN93VAkjs3"
    )

mcp = McpWorkbench(server_params)

require_agent = AssistantAgent("require_agent", 
                        model_client=client, 
                        system_message="""
你是一名“汽车概念设计需求解析 Agent”。你的职责是：
1. 读取设计师提交的多模态需求：文字说明、手绘草图、竞品/灵感图片、硬性约束列表。
2. 将这些信息解析、抽取并映射到预定义的 JSON Schema（见下文），生成唯一的结构化设计 Brief。
3. 若发现必填槽位缺失、数据相互冲突或不合逻辑，必须在 `issues` 字段中列出问题，并给出所需补充字段名单。
4. 只允许输出 **合法 JSON**（UTF-8，换行、缩进不限），不得包含额外解释或 markdown。
5. 所有数值统一使用 *国际单位制*，小数保留 2 位；日期使用 `YYYY-MM-DD` 格式。

**JSON Schema**（字段顺序不可调整）  
```jsonc
{
  "brief_id": "string",             // 自动生成，格式：REQ-<YYYYMMDD>-<3 位流水号>
  "design_targets": {
    "Cd_target": "number|null",
    "lift_coeff_target": "number|null",
    "front_area": "number|null",
    "vehicle_dim": {
      "length": "number|null",
      "width": "number|null",
      "height": "number|null"
    }
  },
  "style_semantics": {
    "keywords": "string[]",         // 风格/形容词，最多 6 个
    "similar_refs": "string[]",     // 相似车型/概念，最多 5 个
    "excluded_motifs": "string[]"   // 需要排除的造型元素
  },
  "hard_constraints": "object",     // 原样拷贝或推理得到的硬性约束
  "priority_rank": "string[]",      // 从高到低
  "confidence": "number",           // 0.00‑1.00
  "issues": "string[]"              // 为空数组表示解析完全成功
}
""")

# web_surfer_agent = MultimodalWebSurfer(
#         name="MultimodalWebSurfer",
#         model_client=client
#     )

# Create the assistant agent
research_assistant = AssistantAgent(
    name="Research_Assistant",
    description="A research assistant that performsweb searches and analyzes information",
    model_client=client,
    workbench=mcp,
    reflect_on_tool_use=True,
    model_client_stream=True,
    system_message="""
    您是一名专注于汽车设计领域的技术研究助手。您的职责是：

1. 针对汽车设计需求中的具体技术参数缺失问题(issues)执行精准搜索
2. 为每个技术参数寻找行业标准数值或合理范围，特别关注：
   - 空气动力学参数(Cd值、升力系数)
   - 车身尺寸参数(长宽高、前投影面积)
   - 类似车型的设计参考数据

搜索策略：
- 使用专业术语进行搜索(如"sports SUV aerodynamic coefficient"而非简单的"car Cd")
- 优先寻找可信来源(如汽车制造商官方数据、工程文献、专业汽车评测)
- 对找到的数据进行分类整理(高性能SUV vs 普通SUV的参数范围)
- 报告数值时保留适当精度并注明数据来源

当找到相关信息时，清晰解释该数据如何解决原始issue，以及这些参数对车辆设计的实际影响。
    """)
# You are a research assistant focused on finding accurate information.
    # Use the google_search tool to find relevant information.
    # Break down complex queries into specific search terms.
    # Always verify information across multiple sources when possible.
    # When you find relevant information, explain why it's relevant and how it connects to the query. When you get feedback from the verifier agent, use your tools to act on the feedback and make progress.

# Create the Verifier agent
verifier = AssistantAgent(
    name="verifier",
    description="A verification specialist who ensures research quality and completeness",
    model_client=client,
    system_message="""
    您是一名汽车设计技术验证专家。您的角色是确保所有设计参数的准确性和完整性：

1. 验证research_assistant提供的数据是否:
   - 来源可靠(优先官方数据和专业测评)
   - 数值合理(在工程可行范围内)
   - 相互一致(无内部矛盾的参数组合)
   - 满足原始设计意图(如"运动型SUV"的特征)

2. 识别参数间的潜在冲突，如:
   - 流线型设计与内部空间需求间的权衡
   - 低风阻与运动型外观间的平衡点
   - 下压力设计与油耗表现的关系

3. 每次评估后明确指出:
   - 已解决的issues
   - 仍需补充的信息
   - 建议的下一步行动

对于未完成的research，在您的消息末尾添加"继续研究（CONTINUE RESEARCH）"。
对于已完成的research，在您的消息末尾添加"已批准（APPROVED）"。
    """
)
# You are a research verification specialist.
    # Your role is to:
    # 1. Verify that search queries are effective and suggest improvements if needed
    # 2. Explore drill downs where needed e.g, if the answer is likely in a link in the returned search results, suggest clicking on thlink
    # 3. Suggest additional angles or perspectives to explore. Be judicious in suggesting new paths to avoid scope creep or wastinresources, if the task appears to be addressed and we can provide a report, do this and respond with "TERMINATE".
    # 4. Track progress toward answering the original question
    # 5. When the research is complete, provide a detailed summary in markdown format
    
    # For incomplete research, end your message with "CONTINUE RESEARCH". 
    # For complete research, end your message with APPROVED.
    
    # Your responses should be structured as:
    # - Progress Assessment
    # - Gaps/Issues (if any)
    # - Suggestions (if needed)
    # - Next Steps or Final Summary

summary_agent = AssistantAgent(
    name="summary_agent",
    description="A summary agent that provides a detailed markdown summary of the research as a report to the user.",
    model_client=client,
    system_message="""
    您是一名设计简报总结专家。您的职责是整合研究过程中收集的所有参数和信息，生成最终的汽车设计简报。

    请分析整个对话历史，提取所有已解决的设计问题(issues)和相关参数，然后构建一个完整的、符合原始JSON Schema的设计简报。

    您必须：
    1. 仅输出有效的JSON格式数据，不包含任何额外说明或markdown标记
    2. 确保所有必填字段都有合理的值，未解决的字段保持为null
    3. 检查参数间的一致性，确保没有矛盾的设计元素
    4. 在design_targets中使用可靠来源支持的数值参数
    5. 在style_semantics中捕捉关键设计风格和参考车型
    6. 确保输出的JSON严格遵循原始Schema结构和字段顺序
    7. 如果所有issues都已解决，issues字段应为空数组[]

    输出仅限于标准JSON格式，以下是Schema参考：
    ```json
    {
      "brief_id": "string",
      "design_targets": {
        "Cd_target": "number|null",
        "lift_coeff_target": "number|null",
        "front_area": "number|null",
        "vehicle_dim": {
          "length": "number|null",
          "width": "number|null",
          "height": "number|null"
        }
      },
      "style_semantics": {
        "keywords": "string[]",
        "similar_refs": "string[]",
        "excluded_motifs": "string[]"
      },
      "hard_constraints": "object",
      "priority_rank": "string[]",
      "confidence": "number",
      "issues": "string[]"
    }
    ```

    完成JSON输出后，在最后一行单独添加"TERMINATE"一词。
    """
)
# You are a summary agent. Your role is to provide a detailed markdown summary of the research as a report to thuser. Your report should have a reasonable title that matches the research question and should summarize the key details in thresults found in natural an actionable manner. The main results/answer should be in the first paragraph.
    # Your report should end with the word "TERMINATE" to signal the end of the conversation.


# Set up termination conditions
text_termination = TextMentionTermination("TERMINATE")
max_messages = MaxMessageTermination(max_messages=30)
termination = text_termination | max_messages
# Create the selector prompt
selector_prompt = """
您正在协调一个高效的汽车设计需求分析与研究团队。根据当前对话状态，请智能选择下一个最适合发言的团队成员：
{roles}

**团队角色与职责：**
- require_agent：设计需求解析专家，将多模态设计需求转换为结构化JSON。始终作为工作流的第一步执行。
- research_assistant：信息检索专家，针对设计需求中的issues执行精准搜索，收集相关技术参数和行业标准。
- verifier：质量控制专家，验证收集的信息是否有效解决了issues，评估进度，确保数据准确性和完整性。
- summary_agent：总结专家，当所有issues都已解决时，提供全面的设计简报报告。

**智能工作流原则：**
1. 按顺序处理每个issue，完成一个再处理下一个
2. 每个issue的常规工作流：require_agent提出 → research_assistant搜索 → verifier评估 → (重复直到解决)
3. 解析-研究-验证的闭环：确保每个设计参数都有可靠来源支持
4. 仅在所有issues解决后选择summary_agent生成最终报告

**选择依据：**
- 当前处理的issue状态（未解决/部分解决/已解决）
- 上一发言者的角色和发现
- 收集的信息是否足够解决当前issue
- 是否需要额外验证或更具体的搜索

请分析以下对话，然后从{participants}中选择最适合的下一个发言者。只返回角色名称，不要额外解释。

{history}

请基于以上对话，从{participants}中仅返回下一个最佳角色名称。
"""
# You are coordinating a research team by selecting the team member to speak/act next. The following team memberroles are available:
# {roles}.
# The research_assistant performs searches and analyzes information.
# The verifier evaluates progress and ensures completeness.
# The summary_agent provides a detailed markdown summary of the research as a report to the user.
# Given the current context, select the most appropriate next speaker.
# The research_assistant should search and analyze.
# The verifier should evaluate progress and guide the research (select this role is there is a need to verify/evaluate progress). Youshould ONLY select the summary_agent role if the research is complete and it is time to generate a report.
# Base your selection on:
# 1. Current stage of research
# 2. Last speaker's findings or suggestions
# 3. Need for verification vs need for new information
    
# Read the following conversation. Then select the next role from {participants} to play. Only return the role.
# {history}
# Read the above conversation. Then select the next role from {participants} to play. ONLY RETURN THE ROLE.

team = SelectorGroupChat(
        participants=[require_agent,research_assistant, verifier, summary_agent],
        model_client=client,
        termination_condition=termination,
        selector_prompt=selector_prompt,
        allow_repeated_speaker=True
    )




# planning_agent = AssistantAgent(
#     "PlanningAgent",
#     description="An agent for planning tasks, this agent should be the first to engage when given a new task.",
#     model_client=client,
#     system_message="""
#     你是一个规划任务的助手。
#     你的工作是将require_agent的设计需求解析结果中的每一个issues解决一一解决，并分配解决的agent。
#     你有两个团队成员：
#         WebSearchAgent: 搜索信息
#         DataAnalystAgent: 执行计算

#     你只负责规划和分配任务 - 你不自己执行它们。
#     在分配任务时，请使用以下格式：
#     1. <agent> : <task>
#     2. <agent> : <task>

#     当所有任务完成后，总结结果并以“TERMINATE”结束。
#     """,
# )



# web_search_agent = AssistantAgent(
#     "WebSearchAgent",
#     description="An agent for searching information on the web.",
#     tools=[search_web_tool],
#     model_client=client,
#     system_message="""
#     You are a web search agent.
#     Your only tool is search_tool - use it to find information.
#     You make only one search call at a time.
#     Once you have the results, you never do calculations based on them.
#     """,
# )




# # Build the graph
# builder = DiGraphBuilder()
# builder.add_node(PM_agent).add_node(planning_agent).add_node(web_surfer_agent)
# builder.add_edge(PM_agent, planning_agent).add_edge(planning_agent, web_surfer_agent)

# # Build and validate the graph
# graph = builder.build()

# # Create the flow
# flow = GraphFlow([PM_agent, planning_agent, web_surfer_agent], graph=graph)

async def main() -> None:
    await Console(team.run_stream(task="设计一辆运动型 SUV，要求车身流线型优美，前脸具有攻击性，车顶线条平滑，车尾有一定的下压力。"))
    


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
