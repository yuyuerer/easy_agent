"""
汽车设计需求分析多智能体系统主类
"""
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from agents import create_all_agents
from config import config



class AutomotiveDesignAnalyzer:
    """汽车设计需求分析多智能体系统"""
    
    def __init__(self):
        # 创建智能体和客户端
        self.agents = None
        self.client = None
        
        # 创建输出目录
        self.output_dir = config.get_output_dir()
        self.images_dir = config.get_images_dir()
        
        # 设置终止条件
        text_termination = TextMentionTermination("TERMINATE")
        max_messages = MaxMessageTermination(max_messages=config.MAX_MESSAGES)
        self.termination = text_termination | max_messages
        
        # 初始化标志
        self.initialized = False
    
    async def initialize(self):
        """异步初始化系统"""
        if self.initialized:
            return
        
        print("🚀 初始化汽车设计分析系统...")
        
        
        # 创建智能体
        print("🤖 正在创建智能体团队...")
        self.agents, self.client = await create_all_agents()
        
        # 创建团队
        self._create_team()
        
        self.initialized = True
        print("✅ 系统初始化完成！")
    
   
    
    def _create_team(self):
        """创建汽车设计分析团队"""
        
        selector_prompt = """
你正在协调一个汽车设计需求分析研究团队。根据当前对话状态和已完成的工作，选择下一个最适合发言的团队成员。

{roles}

团队角色职责：
- DesignAnalyst: 分析汽车设计需求，生成多样化的网络搜索查询，专注于设计要素和技术指标
- MarketResearcher: 执行网络搜索，收集最新可信的汽车市场信息、车型数据和竞品信息
- ReflectAnalyst: 评估收集的信息是否充分，识别知识缺口，决定是否需要进一步研究
- ReportGenerator: 基于所有收集的信息生成最终的汽车设计开发指导报告

工作流程逻辑：
1. 任务开始时，选择 DesignAnalyst 分析需求并生成搜索查询
2. 当有搜索查询需要执行时，选择 MarketResearcher 进行信息收集
3. 当收集到信息后，选择 ReflectAnalyst 评估信息充分性：
   - 如果ReflectAnalyst输出包含"APPROVE"，表示信息充分，选择 ReportGenerator
   - 如果ReflectAnalyst输出包含"REJECT"，表示需要更多信息，选择 MarketResearcher 继续搜索
4. ReportGenerator 生成最终报告后，任务结束

选择规则：
- 如果对话刚开始或需要分析新需求 → 选择 DesignAnalyst
- 如果有JSON格式的搜索查询待执行 → 选择 MarketResearcher  
- 如果刚完成信息收集且未进行评估 → 选择 ReflectAnalyst
- 如果ReflectAnalyst说"APPROVE"或信息已充分 → 选择 ReportGenerator
- 如果ReflectAnalyst说"REJECT"或需要更多信息 → 选择 MarketResearcher
- 如果已有完整报告且包含"TERMINATE" → 任务结束，不选择任何人

注意事项：
- 避免重复选择同一个角色，除非明确需要
- ReportGenerator只在最后阶段选择一次
- 关注最近的消息内容来判断工作进展

{history}

从 {participants} 中选择下一个最适合的角色（只返回角色名称）：
    """
        
        self.team = SelectorGroupChat(
            participants=[
                self.agents['design_analyst'],
                self.agents['market_researcher'],
                self.agents['reflect_analyst'],
                self.agents['design_report_generator'],
                #self.agents['image_saver']
            ],
            model_client=self.client,
            termination_condition=self.termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=True
        )
    
    async def analyze_vehicle_design(self, design_requirement: str):
        """
        执行汽车设计需求分析
        
        Args:
            design_requirement: 用户的设计需求描述
            
        Returns:
            分析结果
        """
        # 确保系统已初始化
        if not self.initialized:
            await self.initialize()
        
        print(f"开始分析汽车设计需求: {design_requirement}")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # 运行多智能体分析
        result = await self.team.run(
            task=f"请分析以下汽车设计需求并进行竞品分析：{design_requirement}",
        )
        
        # 保存分析报告
        await self._save_analysis_report(design_requirement, result)
        
        # 打印图片收集摘要
        self.print_image_summary()
        
        return result
    
    async def _save_analysis_report(self, design_requirement: str, result):
        """保存分析报告到文件"""
        report_path = self.output_dir / f"automotive_design_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 提取最终报告内容
        final_report = ""
        
        def extract_content(content):
            """统一处理content内容，确保返回字符串"""
            if content is None:
                return ""
            elif isinstance(content, str):
                return content
            elif isinstance(content, list):
                # 过滤掉函数调用，只保留文本内容
                text_items = []
                for item in content:
                    if isinstance(item, str):
                        text_items.append(item)
                    elif hasattr(item, '__str__') and not str(item).startswith('FunctionCall'):
                        text_items.append(str(item))
                return "\n".join(text_items)
            elif isinstance(content, dict):
                return str(content)
            else:
                return str(content)
        
        if hasattr(result, 'messages'):
            # 优先查找DesignReportGenerator的消息
            for message in result.messages:
                if hasattr(message, 'source') and message.source == "DesignReportGenerator":
                    content = extract_content(message.content)
                    # 过滤掉空内容和纯函数调用内容
                    if content and not content.startswith('FunctionCall') and len(content.strip()) > 10:
                        final_report = content
                        break
            
            # 如果没有找到DesignReportGenerator的有效内容，查找所有智能体的文本消息
            if not final_report:
                for message in result.messages:
                    content = extract_content(message.content)
                    if content and not content.startswith('FunctionCall') and len(content.strip()) > 50:
                        source = getattr(message, 'source', 'Unknown')
                        if final_report:
                            final_report += f"\n\n## {source}\n\n{content}"
                        else:
                            final_report = f"## {source}\n\n{content}"
        
        # 如果仍然没有找到有效内容，使用所有消息的备用方案
        if not final_report and hasattr(result, 'messages'):
            final_report = "# 分析过程记录\n\n"
            for message in result.messages:
                source = getattr(message, 'source', 'Unknown')
                content = extract_content(message.content)
                if content and len(content.strip()) > 5:
                    final_report += f"## {source}\n\n{content}\n\n---\n\n"
        
        # 检查是否有保存的竞品图片
        saved_vehicles = []
        if self.images_dir.exists():
            saved_vehicles = [d.name for d in self.images_dir.iterdir() if d.is_dir()]
        
        # 保存报告到文件
        async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
            await f.write(f"# 汽车设计开发分析报告\n\n")
            await f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            await f.write(f"**设计需求**: {design_requirement}\n\n")
            
            if saved_vehicles:
                await f.write(f"**收集的竞品车型图片**: {len(saved_vehicles)} 个车型\n")
                for vehicle in saved_vehicles:
                    await f.write(f"- {vehicle.replace('_', ' ')}\n")
                await f.write(f"**图片保存位置**: {self.images_dir}\n\n")
            
            await f.write("---\n\n")
            
            # 最终安全检查，确保final_report是字符串
            if isinstance(final_report, str):
                await f.write(final_report)
            else:
                await f.write(str(final_report))
        
        print(f"汽车设计分析报告已保存到: {report_path}")
    
    def get_saved_vehicle_images(self) -> Dict[str, List[str]]:
        """
        获取已保存的车型图片信息
        
        Returns:
            车型图片信息字典
        """
        vehicle_images = {}
        
        if self.images_dir.exists():
            for vehicle_dir in self.images_dir.iterdir():
                if vehicle_dir.is_dir():
                    vehicle_name = vehicle_dir.name.replace('_', ' ')
                    images = []
                    for img_file in vehicle_dir.iterdir():
                        if img_file.is_file() and img_file.suffix.lower() in config.SUPPORTED_IMAGE_FORMATS:
                            images.append(str(img_file))
                    vehicle_images[vehicle_name] = images
        
        return vehicle_images
    
    def print_image_summary(self):
        """打印图片收集摘要"""
        vehicle_images = self.get_saved_vehicle_images()
        
        if not vehicle_images:
            print("📷 还没有收集到竞品车型图片")
            return
        
        print(f"\n📷 竞品车型图片收集摘要:")
        print("=" * 50)
        
        total_images = 0
        for vehicle_name, images in vehicle_images.items():
            image_count = len(images)
            total_images += image_count
            print(f"🚗 {vehicle_name}: {image_count} 张图片")
            
        print(f"\n📊 总计: {len(vehicle_images)} 个车型, {total_images} 张图片")
        print(f"📁 图片保存位置: {self.images_dir}")
    
    async def run_interactive(self, design_requirement: str):
        """
        运行交互式分析（使用Console界面）
        
        Args:
            design_requirement: 设计需求
        """
        # 确保系统已初始化
        if not self.initialized:
            await self.initialize()
        
        from autogen_agentchat.ui import Console
        
        task = f"请分析以下汽车设计需求并进行竞品分析：{design_requirement}"
        await Console(self.team.run_stream(task=task))
    
    def get_analysis_history(self) -> List[str]:
        """获取历史分析报告列表"""
        if not self.output_dir.exists():
            return []
        
        reports = []
        for file_path in self.output_dir.glob("automotive_design_analysis_*.md"):
            reports.append(str(file_path))
        
        return sorted(reports, reverse=True)  # 按时间倒序

    async def cleanup(self):
        """清理资源"""
        print("🧹 清理系统资源...")
        # 这里可以添加任何需要在系统关闭时执行的清理工作
        # 例如关闭所有打开的文件、断开网络连接等
        
        # 如果MCP工具有自己的清理方法，可以在这里调用
        # 如果存在client实例且有close方法
        if hasattr(self, 'client') and self.client and hasattr(self.client, 'close'):
            await self.client.close()
            
        self.initialized = False
        print("✅ 资源清理完成")
