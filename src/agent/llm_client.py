
# -*- coding: utf-8 -*-
"""
大模型客户端 - 统一的LLM接口
支持多种大模型提供商
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str  # openai, anthropic, local, etc.
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000

class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI客户端 - 支持OpenAI和兼容OpenAI API的模型（如千问）"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        except ImportError:
            logger.warning("OpenAI库未安装，将使用模拟客户端")
            self.client = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.client:
            return self._simulate_response(prompt)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return self._simulate_response(prompt)
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        if not self.client:
            return self._simulate_chat(messages)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Chat API调用失败: {e}")
            return self._simulate_chat(messages)
    
    def _simulate_response(self, prompt: str) -> str:
        """模拟响应"""
        if "千问" in self.config.model or "qwen" in self.config.model.lower():
            return f"【千问模型模拟响应】根据您的问题，我建议采取以下措施：{prompt[:50]}... 这是一个智能化的解决方案。"
        return f"模拟LLM响应: {prompt[:100]}..."
    
    def _simulate_chat(self, messages: List[Dict[str, str]]) -> str:
        """模拟对话响应"""
        last_message = messages[-1]["content"] if messages else ""
        if "千问" in self.config.model or "qwen" in self.config.model.lower():
            return f"【千问模型模拟对话】我理解您的问题：{last_message[:50]}... 让我为您提供专业的建议。"
        return f"模拟对话响应: {last_message[:100]}..."

class AnthropicClient(BaseLLMClient):
    """Anthropic客户端"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key
            )
        except ImportError:
            logger.warning("Anthropic库未安装，将使用模拟客户端")
            self.client = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.client:
            return self._simulate_response(prompt)
        
        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {e}")
            return self._simulate_response(prompt)
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        if not self.client:
            return self._simulate_chat(messages)
        
        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic Chat API调用失败: {e}")
            return self._simulate_chat(messages)
    
    def _simulate_response(self, prompt: str) -> str:
        """模拟响应"""
        return f"模拟Anthropic响应: {prompt[:100]}..."
    
    def _simulate_chat(self, messages: List[Dict[str, str]]) -> str:
        """模拟对话响应"""
        last_message = messages[-1]["content"] if messages else ""
        return f"模拟Anthropic对话: {last_message[:100]}..."

class LocalLLMClient(BaseLLMClient):
    """本地LLM客户端"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化本地客户端"""
        try:
            # 这里可以集成Ollama、vLLM等本地LLM服务
            logger.info("本地LLM客户端初始化")
        except Exception as e:
            logger.warning(f"本地LLM客户端初始化失败: {e}")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        # 实现本地LLM调用
        return f"本地LLM响应: {prompt[:100]}..."
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        last_message = messages[-1]["content"] if messages else ""
        return f"本地LLM对话: {last_message[:100]}..."

class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """创建LLM客户端"""
        if config.provider.lower() == "openai":
            return OpenAIClient(config)
        elif config.provider.lower() == "anthropic":
            return AnthropicClient(config)
        elif config.provider.lower() == "local":
            return LocalLLMClient(config)
        else:
            raise ValueError(f"不支持的LLM提供商: {config.provider}")

class LLMManager:
    """LLM管理器"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = LLMClientFactory.create_client(config)
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "error_count": 0
        }
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            self.usage_stats["total_requests"] += 1
            response = await self.client.generate(prompt, **kwargs)
            self.usage_stats["total_tokens"] += len(response)
            return response
        except Exception as e:
            self.usage_stats["error_count"] += 1
            logger.error(f"LLM生成失败: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        try:
            self.usage_stats["total_requests"] += 1
            response = await self.client.chat(messages, **kwargs)
            self.usage_stats["total_tokens"] += len(response)
            return response
        except Exception as e:
            self.usage_stats["error_count"] += 1
            logger.error(f"LLM对话失败: {e}")
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.usage_stats.copy()
