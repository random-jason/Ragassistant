import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..config.unified_config import get_config

logger = logging.getLogger(__name__)

class QwenClient:
    """阿里云千问API客户端"""
    
    def __init__(self):
        config = get_config()
        self.base_url = config.llm.base_url
        self.api_key = config.llm.api_key
        self.model_name = config.llm.model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """发送聊天请求"""
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=get_config().llm.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("API请求成功")
                return result
            else:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return {"error": f"API请求失败: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return {"error": "请求超时"}
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {e}")
            return {"error": f"请求异常: {str(e)}"}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"error": f"未知错误: {str(e)}"}
    
    def generate_response(
        self,
        user_message: str,
        context: Optional[str] = None,
        knowledge_base: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成回复"""
        messages = []
        
        # 系统提示词
        system_prompt = "你是一个专业的客服助手，请根据用户问题提供准确、 helpful的回复。"
        if context:
            system_prompt += f"\n\n上下文信息: {context}"
        if knowledge_base:
            system_prompt += f"\n\n相关知识库: {' '.join(knowledge_base)}"
        
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        
        result = self.chat_completion(messages)
        
        if "error" in result:
            return result
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            return {
                "response": response_content,
                "usage": result.get("usage", {}),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
        except (KeyError, IndexError) as e:
            logger.error(f"解析API响应失败: {e}")
            return {"error": f"解析响应失败: {str(e)}"}
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """提取文本中的实体信息"""
        prompt = f"""
        请从以下文本中提取关键信息，包括：
        1. 问题类型/类别
        2. 优先级（高/中/低）
        3. 关键词
        4. 情感倾向（正面/负面/中性）
        
        文本: {text}
        
        请以JSON格式返回结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个信息提取专家，请准确提取文本中的关键信息。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return result
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            # 尝试解析JSON
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response_content}
        except Exception as e:
            logger.error(f"解析实体提取结果失败: {e}")
            return {"error": f"解析失败: {str(e)}"}
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            result = self.chat_completion([
                {"role": "user", "content": "你好"}
            ], max_tokens=10)
            return "error" not in result
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
