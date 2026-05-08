# -*- coding: utf-8 -*-
"""
LLM配置文件 - 千问模型配置
"""

from src.agent.llm_client import LLMConfig

# 千问模型配置
QWEN_CONFIG = LLMConfig(
    provider="qwen",
    api_key="",  # 请在 .env 中配置 LLM_API_KEY
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus-latest",  # 可选: qwen-turbo, qwen-plus, qwen-max
    temperature=0.7,
    max_tokens=2000
)

# 其他模型配置示例
OPENAI_CONFIG = LLMConfig(
    provider="openai",
    api_key="sk-your-openai-api-key-here",
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=2000
)

ANTHROPIC_CONFIG = LLMConfig(
    provider="anthropic",
    api_key="sk-ant-your-anthropic-api-key-here",
    model="claude-3-sonnet-20240229",
    temperature=0.7,
    max_tokens=2000
)

# 默认使用千问模型
DEFAULT_CONFIG = QWEN_CONFIG


def get_default_llm_config() -> LLMConfig:
    """
    获取默认的LLM配置
    优先从统一配置管理器获取，如果失败则使用本地配置
    """
    try:
        from src.config.unified_config import get_config
        config = get_config()
        llm_dict = config.get_llm_config()
        
        # 创建LLMConfig对象
        return LLMConfig(
            provider=llm_dict.get("provider", "qwen"),
            api_key=llm_dict.get("api_key", ""),
            base_url=llm_dict.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model=llm_dict.get("model", "qwen-plus-latest"),
            temperature=llm_dict.get("temperature", 0.7),
            max_tokens=llm_dict.get("max_tokens", 2000)
        )
    except Exception:
        # 如果统一配置不可用，使用本地配置
        return DEFAULT_CONFIG
