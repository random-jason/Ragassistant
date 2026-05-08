# -*- coding: utf-8 -*-
"""
Agent助手核心模块
包含Agent助手的核心功能和基础类
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from src.main import Assistant
from src.agent import AgentCore, AgentState
from src.agent.auto_monitor import AutoMonitorService
from src.agent.intelligent_agent import IntelligentAgent, AlertContext, KnowledgeContext
from src.agent.llm_client import LLMManager, LLMConfig
from src.agent.action_executor import ActionExecutor

logger = logging.getLogger(__name__)

class AgentAssistantCore(Assistant):
    """Agent助手核心 - 基础功能"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        # 初始化基础
        super().__init__()
        
        # 初始化Agent核心
        self.agent_core = AgentCore()
        
        # 初始化自动监控服务
        self.auto_monitor = AutoMonitorService(self)
        
        # 初始化LLM客户端
        self._init_llm_manager(llm_config)
        
        # 初始化智能Agent
        self.intelligent_agent = IntelligentAgent(
            llm_client=self.llm_manager
        )
        
        # 初始化动作执行器
        self.action_executor = ActionExecutor(self)
        
        # Agent状态
        self.agent_state = AgentState.IDLE
        self.is_agent_mode = True
        self.proactive_monitoring_enabled = False
        
        # 执行历史
        self.execution_history = []
        self.max_history_size = 1000
        
        logger.info("Agent助手核心初始化完成")
    
    def _init_llm_manager(self, llm_config: Optional[LLMConfig] = None):
        """初始化LLM管理器"""
        if llm_config:
            self.llm_manager = LLMManager(llm_config)
        else:
            # 从统一配置管理器获取LLM配置
            try:
                from src.config.unified_config import get_config
                unified_llm = get_config().llm
                # 将统一配置的LLMConfig转换为agent需要的LLMConfig
                agent_llm_config = LLMConfig(
                    provider=unified_llm.provider,
                    api_key=unified_llm.api_key,
                    base_url=unified_llm.base_url,
                    model=unified_llm.model,
                    temperature=unified_llm.temperature,
                    max_tokens=unified_llm.max_tokens
                )
                self.llm_manager = LLMManager(agent_llm_config)
            except Exception as e:
                logger.warning(f"无法从统一配置加载LLM配置，使用config/llm_config.py: {e}")
                try:
                    from config.llm_config import DEFAULT_CONFIG
                    self.llm_manager = LLMManager(DEFAULT_CONFIG)
                except ImportError:
                    # 最后的fallback
                    default_config = LLMConfig(
                        provider="qwen",
                        api_key="",
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        model="qwen-turbo",
                        temperature=0.7,
                        max_tokens=2000
                    )
                    self.llm_manager = LLMManager(default_config)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_state": self.agent_state.value,
            "is_agent_mode": self.is_agent_mode,
            "proactive_monitoring": self.proactive_monitoring_enabled,
            "execution_count": len(self.execution_history),
            "llm_status": self.llm_manager.get_status(),
            "agent_core_status": self.agent_core.get_status(),
            "last_activity": self.execution_history[-1]["timestamp"] if self.execution_history else None
        }
    
    def toggle_agent_mode(self, enabled: bool) -> bool:
        """切换Agent模式"""
        try:
            self.is_agent_mode = enabled
            if enabled:
                self.agent_state = AgentState.IDLE
                logger.info("Agent模式已启用")
            else:
                self.agent_state = AgentState.DISABLED
                logger.info("Agent模式已禁用")
            return True
        except Exception as e:
            logger.error(f"切换Agent模式失败: {e}")
            return False
    
    def start_proactive_monitoring(self) -> bool:
        """启动主动监控"""
        try:
            if not self.proactive_monitoring_enabled:
                self.proactive_monitoring_enabled = True
                self.auto_monitor.start_monitoring()
                logger.info("主动监控已启动")
                return True
            return False
        except Exception as e:
            logger.error(f"启动主动监控失败: {e}")
            return False
    
    def stop_proactive_monitoring(self) -> bool:
        """停止主动监控"""
        try:
            if self.proactive_monitoring_enabled:
                self.proactive_monitoring_enabled = False
                self.auto_monitor.stop_monitoring()
                logger.info("主动监控已停止")
                return True
            return False
        except Exception as e:
            logger.error(f"停止主动监控失败: {e}")
            return False
    
    def run_proactive_monitoring(self) -> Dict[str, Any]:
        """运行主动监控检查"""
        try:
            if not self.proactive_monitoring_enabled:
                return {"success": False, "message": "主动监控未启用"}
            
            # 获取系统状态
            system_health = self.get_system_health()
            
            # 检查预警
            alerts = self.check_alerts()
            
            # 检查工单状态
            workorders_status = self._check_workorders_status()
            
            # 运行智能分析
            analysis = self.intelligent_agent.analyze_system_state(
                system_health=system_health,
                alerts=alerts,
                workorders=workorders_status
            )
            
            # 执行建议的动作
            actions_taken = []
            if analysis.get("recommended_actions"):
                for action in analysis["recommended_actions"]:
                    result = self.action_executor.execute_action(action)
                    actions_taken.append(result)
            
            return {
                "success": True,
                "analysis": analysis,
                "actions_taken": actions_taken,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"主动监控检查失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_workorders_status(self) -> Dict[str, Any]:
        """检查工单状态"""
        try:
            from src.core.database import db_manager
            from src.core.models import WorkOrder
            
            with db_manager.get_session() as session:
                total_workorders = session.query(WorkOrder).count()
                open_workorders = session.query(WorkOrder).filter(WorkOrder.status == 'open').count()
                resolved_workorders = session.query(WorkOrder).filter(WorkOrder.status == 'resolved').count()
                
                return {
                    "total": total_workorders,
                    "open": open_workorders,
                    "resolved": resolved_workorders,
                    "resolution_rate": resolved_workorders / total_workorders if total_workorders > 0 else 0
                }
        except Exception as e:
            logger.error(f"检查工单状态失败: {e}")
            return {"error": str(e)}
    
    def run_intelligent_analysis(self) -> Dict[str, Any]:
        """运行智能分析"""
        try:
            # 获取系统数据
            system_health = self.get_system_health()
            alerts = self.check_alerts()
            workorders = self._check_workorders_status()
            
            # 创建分析上下文
            context = {
                "system_health": system_health,
                "alerts": alerts,
                "workorders": workorders,
                "timestamp": datetime.now().isoformat()
            }
            
            # 运行智能分析
            analysis = self.intelligent_agent.comprehensive_analysis(context)
            
            # 记录分析结果
            self._record_execution("intelligent_analysis", analysis)
            
            return analysis
        except Exception as e:
            logger.error(f"智能分析失败: {e}")
            return {"error": str(e)}
    
    def _record_execution(self, action_type: str, result: Any):
        """记录执行历史"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "result": result,
            "agent_state": self.agent_state.value
        }
        
        self.execution_history.append(execution_record)
        
        # 保持历史记录大小限制
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
    
    def get_action_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取动作执行历史"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def clear_execution_history(self) -> Dict[str, Any]:
        """清空执行历史"""
        try:
            self.execution_history.clear()
            logger.info("执行历史已清空")
            return {"success": True, "message": "执行历史已清空"}
        except Exception as e:
            logger.error(f"清空执行历史失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_llm_usage_stats(self) -> Dict[str, Any]:
        """获取LLM使用统计"""
        try:
            return self.llm_manager.get_usage_stats()
        except Exception as e:
            logger.error(f"获取LLM使用统计失败: {e}")
            return {"error": str(e)}
