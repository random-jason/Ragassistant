# -*- coding: utf-8 -*-
"""
Agent消息处理模块
处理Agent的消息处理和对话功能
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent_assistant_core import AgentAssistantCore
from .intelligent_agent import IntelligentAgent

logger = logging.getLogger(__name__)

class AgentMessageHandler:
    """Agent消息处理器"""
    
    def __init__(self, agent_core: AgentAssistantCore):
        self.agent_core = agent_core
        self.intelligent_agent = agent_core.intelligent_agent
        self.action_executor = agent_core.action_executor
    
    async def process_message_agent(self, message: str, user_id: str = "admin", 
                                  work_order_id: Optional[int] = None, 
                                  enable_proactive: bool = True) -> Dict[str, Any]:
        """使用Agent处理消息"""
        try:
            # 更新Agent状态
            self.agent_core.agent_state = self.agent_core.agent_core.AgentState.PROCESSING
            
            # 创建对话上下文
            context = {
                "message": message,
                "user_id": user_id,
                "work_order_id": work_order_id,
                "timestamp": datetime.now().isoformat(),
                "enable_proactive": enable_proactive
            }
            
            # 使用智能Agent处理消息
            agent_response = await self.intelligent_agent.process_message(context)
            
            # 执行建议的动作
            actions_taken = []
            if agent_response.get("recommended_actions"):
                for action in agent_response["recommended_actions"]:
                    action_result = self.action_executor.execute_action(action)
                    actions_taken.append(action_result)
            
            # 生成响应
            response = {
                "response": agent_response.get("response", "Agent已处理您的请求"),
                "actions": actions_taken,
                "status": "completed",
                "confidence": agent_response.get("confidence", 0.8),
                "context": context
            }
            
            # 记录执行历史
            self.agent_core._record_execution("message_processing", response)
            
            # 更新Agent状态
            self.agent_core.agent_state = self.agent_core.agent_core.AgentState.IDLE
            
            return response
            
        except Exception as e:
            logger.error(f"Agent消息处理失败: {e}")
            self.agent_core.agent_state = self.agent_core.agent_core.AgentState.ERROR
            
            return {
                "response": f"处理消息时发生错误: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    async def process_conversation_agent(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用Agent处理对话"""
        try:
            # 提取对话信息
            user_message = conversation_data.get("message", "")
            user_id = conversation_data.get("user_id", "anonymous")
            session_id = conversation_data.get("session_id")
            
            # 创建对话上下文
            context = {
                "message": user_message,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_history": conversation_data.get("history", []),
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用智能Agent处理对话
            agent_response = await self.intelligent_agent.process_conversation(context)
            
            # 执行建议的动作
            actions_taken = []
            if agent_response.get("recommended_actions"):
                for action in agent_response["recommended_actions"]:
                    action_result = self.action_executor.execute_action(action)
                    actions_taken.append(action_result)
            
            # 生成响应
            response = {
                "response": agent_response.get("response", "Agent已处理您的对话"),
                "actions": actions_taken,
                "status": "completed",
                "confidence": agent_response.get("confidence", 0.8),
                "context": context,
                "session_id": session_id
            }
            
            # 记录执行历史
            self.agent_core._record_execution("conversation_processing", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent对话处理失败: {e}")
            return {
                "response": f"处理对话时发生错误: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    async def process_workorder_agent(self, workorder_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用Agent处理工单"""
        try:
            # 提取工单信息
            workorder_id = workorder_data.get("workorder_id")
            action_type = workorder_data.get("action_type", "analyze")
            
            # 创建工单上下文
            context = {
                "workorder_id": workorder_id,
                "action_type": action_type,
                "workorder_data": workorder_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用智能Agent处理工单
            agent_response = await self.intelligent_agent.process_workorder(context)
            
            # 执行建议的动作
            actions_taken = []
            if agent_response.get("recommended_actions"):
                for action in agent_response["recommended_actions"]:
                    action_result = self.action_executor.execute_action(action)
                    actions_taken.append(action_result)
            
            # 生成响应
            response = {
                "response": agent_response.get("response", "Agent已处理工单"),
                "actions": actions_taken,
                "status": "completed",
                "confidence": agent_response.get("confidence", 0.8),
                "context": context
            }
            
            # 记录执行历史
            self.agent_core._record_execution("workorder_processing", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent工单处理失败: {e}")
            return {
                "response": f"处理工单时发生错误: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    async def process_alert_agent(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用Agent处理预警"""
        try:
            # 创建预警上下文
            context = {
                "alert_data": alert_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用智能Agent处理预警
            agent_response = await self.intelligent_agent.process_alert(context)
            
            # 执行建议的动作
            actions_taken = []
            if agent_response.get("recommended_actions"):
                for action in agent_response["recommended_actions"]:
                    action_result = self.action_executor.execute_action(action)
                    actions_taken.append(action_result)
            
            # 生成响应
            response = {
                "response": agent_response.get("response", "Agent已处理预警"),
                "actions": actions_taken,
                "status": "completed",
                "confidence": agent_response.get("confidence", 0.8),
                "context": context
            }
            
            # 记录执行历史
            self.agent_core._record_execution("alert_processing", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent预警处理失败: {e}")
            return {
                "response": f"处理预警时发生错误: {str(e)}",
                "actions": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_conversation_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """获取对话建议"""
        try:
            return self.intelligent_agent.get_conversation_suggestions(context)
        except Exception as e:
            logger.error(f"获取对话建议失败: {e}")
            return []
    
    def get_workorder_suggestions(self, workorder_data: Dict[str, Any]) -> List[str]:
        """获取工单建议"""
        try:
            return self.intelligent_agent.get_workorder_suggestions(workorder_data)
        except Exception as e:
            logger.error(f"获取工单建议失败: {e}")
            return []
    
    def get_alert_suggestions(self, alert_data: Dict[str, Any]) -> List[str]:
        """获取预警建议"""
        try:
            return self.intelligent_agent.get_alert_suggestions(alert_data)
        except Exception as e:
            logger.error(f"获取预警建议失败: {e}")
            return []
