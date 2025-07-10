"""
汽车设计分析系统主程序入口
"""
import asyncio
from automotive_analyzer import AutomotiveDesignAnalyzer
from config import config


async def main():
    """主函数"""
    print("🚗 汽车设计需求分析系统启动")
    print("=" * 50)
    
    # 显示配置信息
    config.print_config()
    
    # 验证配置
    if not config.validate_config():
        print("\n❌ 配置验证失败！请检查API密钥配置。")
        print("请在config.py中配置正确的API密钥，或设置环境变量：")
        print("  export QWEN_API_KEY='your-qwen-api-key'")
        print("  export GOOGLE_API_KEY='your-google-api-key'")
        print("  export GOOGLE_CSE_ID='your-custom-search-engine-id'")
        return
    
    print("\n✅ 配置验证通过，系统准备就绪！")
    print("=" * 50)
    
    # 创建分析器
    print("\n🔧 正在初始化汽车设计分析系统...")
    analyzer = AutomotiveDesignAnalyzer()
    await analyzer.initialize()
    
    # 示例汽车设计需求
    design_requirements = [
        """
我想要一个运动点的SUV，希望外观看起来比较有攻击性，动力要强劲一些，
内饰要有科技感，最好是电动的，价格在30-50万之间。
        """,
        """
设计一款豪华轿车，外观要优雅大气，内饰要用高端材质，
配置要丰富，动力要平顺，适合商务人士使用，价格60-100万。
        """,
        """
我需要一款家用MPV，空间要大，座椅要舒适，安全配置要齐全，
油耗要低，价格在20-35万之间，外观不要太商务化。
        """
    ]
    
    print("📋 可选的设计需求:")
    for i, req in enumerate(design_requirements, 1):
        print(f"{i}. {req.strip()}")
    
    print("\n请选择一个需求进行分析，或者输入 'custom' 自定义需求:")
    choice = input("选择 (1-3 或 custom): ").strip()
    
    if choice == 'custom':
        design_requirement = input("请输入您的汽车设计需求: ").strip()
    elif choice in ['1', '2', '3']:
        design_requirement = design_requirements[int(choice) - 1].strip()
    else:
        print("无效选择，使用默认需求")
        design_requirement = design_requirements[0].strip()
    
    print(f"\n🎯 分析需求: {design_requirement}")
    print("\n" + "=" * 50)
    
    # 选择运行模式
    print("\n🔧 运行模式:")
    print("1. 自动分析模式 (完整分析后保存报告)")
    print("2. 交互式模式 (实时查看分析过程)")
    
    mode = input("选择模式 (1-2): ").strip()
    
    try:
        if mode == '2':
            print("\n🚀 启动交互式分析...")
            await analyzer.run_interactive(design_requirement)
        else:
            print("\n🚀 启动自动分析...")
            result = await analyzer.analyze_vehicle_design(design_requirement)
            print("\n✅ 分析完成!")
            
            # 显示结果摘要
            print(f"\n📊 分析结果摘要:")
            print(f"- 总消息数: {len(result.messages)}")
            print(f"- 输出目录: {analyzer.output_dir}")
            
            # 显示历史报告
            reports = analyzer.get_analysis_history()
            if reports:
                print(f"\n📁 历史分析报告 ({len(reports)} 份):")
                for i, report in enumerate(reports[:5], 1):  # 显示最近5份
                    print(f"  {i}. {report}")
                    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断分析")
    except Exception as e:
        print(f"\n❌ 分析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if 'analyzer' in locals():
            await analyzer.cleanup()


def run_example_analysis():
    """运行示例分析（用于测试）"""
    async def example():
        analyzer = AutomotiveDesignAnalyzer()
        await analyzer.initialize()
        
        design_requirement = """
我想要一个运动点的SUV，希望外观看起来比较有攻击性，动力要强劲一些，
内饰要有科技感，最好是电动的，价格在30-50万之间。
        """
        
        try:
            result = await analyzer.analyze_vehicle_design(design_requirement)
            return result
        finally:
            await analyzer.cleanup()
    
    return asyncio.run(example())


if __name__ == "__main__":
    asyncio.run(main())
1