"""
配置文件
"""
import os
from pathlib import Path


class Config:
    """系统配置类"""
    
    # 模型配置
    MODEL_NAME = "qwen-turbo-latest"
    MODEL_API_KEY = os.getenv("QWEN_API_KEY", "sk-1d89e189fe624c3698a04a048c285069")
    MODEL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # Google搜索配置
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCW1l_7sV8nkOTURfA_BQEuov9AE_edowY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "e79552a91bdd54278")
    
    # 输出配置
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/Users/jinxinyu/Desktop/资料/easy_agent/analy/automotive_output"))
  
    
    # 搜索配置
    MAX_SEARCH_RESULTS = 10
    MAX_IMAGES_PER_VEHICLE = 8
    
    # 网络请求配置
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 2
    
    # 团队配置
    MAX_MESSAGES = 35
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """获取输出目录"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR
    
    @classmethod
    def get_images_dir(cls) -> Path:
        """获取图片输出目录"""
        images_dir = cls.get_output_dir() / "vehicle_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否有效"""
        required_keys = [
            cls.MODEL_API_KEY,
            cls.GOOGLE_API_KEY,
            cls.GOOGLE_CSE_ID
        ]
        
        for key in required_keys:
            if not key or key.startswith("your-") or key == "":
                return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """打印当前配置（隐敏感信息）"""
        print("🔧 当前系统配置:")
        print(f"  模型: {cls.MODEL_NAME}")
        print(f"  模型API: {cls.MODEL_BASE_URL}")
        print(f"  模型密钥: {'✅ 已配置' if cls.MODEL_API_KEY else '❌ 未配置'}")
        print(f"  谷歌API密钥: {'✅ 已配置' if cls.GOOGLE_API_KEY else '❌ 未配置'}")
        print(f"  搜索引擎ID: {'✅ 已配置' if cls.GOOGLE_CSE_ID else '❌ 未配置'}")
        print(f"  输出目录: {cls.OUTPUT_DIR}")
        print(f"  最大消息数: {cls.MAX_MESSAGES}")
        print(f"  配置有效性: {'✅ 有效' if cls.validate_config() else '❌ 无效'}")


# 创建默认配置实例
config = Config()
