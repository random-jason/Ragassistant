# -*- coding: utf-8 -*-
"""
服务管理器
统一管理各种服务的懒加载实例
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ServiceManager:
    """服务管理器 - 统一管理各种服务的懒加载实例"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
    
    def get_service(self, service_name: str, factory_func):
        """获取服务实例（懒加载）"""
        if service_name not in self._services:
            try:
                self._services[service_name] = factory_func()
                logger.info(f"服务 {service_name} 已初始化")
            except Exception as e:
                logger.error(f"初始化服务 {service_name} 失败: {e}")
                raise
        return self._services[service_name]
    
    def get_assistant(self):
        """获取实例"""
        def factory():
            from src.main import Assistant
            return Assistant()
        return self.get_service('assistant', factory)
    
    def get_agent_assistant(self):
        """获取Agent助手实例"""
        def factory():
            from src.agent_assistant import AgentAssistant
            return AgentAssistant()
        return self.get_service('agent_assistant', factory)
    
    def get_chat_manager(self):
        """获取聊天管理器实例"""
        def factory():
            from src.dialogue.realtime_chat import RealtimeChatManager
            return RealtimeChatManager()
        return self.get_service('chat_manager', factory)
    
    def clear_service(self, service_name: str):
        """清除指定服务实例"""
        if service_name in self._services:
            del self._services[service_name]
            logger.info(f"服务 {service_name} 已清除")
    
    def clear_all_services(self):
        """清除所有服务实例"""
        self._services.clear()
        logger.info("所有服务实例已清除")


# 全局服务管理器实例
service_manager = ServiceManager()
