
# -*- coding: utf-8 -*-
"""
Agent核心模块
实现智能体的核心逻辑和决策机制
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import json

from ..core.database import db_manager
from ..core.llm_client import QwenClient
from .planner import TaskPlanner
from .executor import TaskExecutor
from .tool_manager import ToolManager
from .reasoning_engine import ReasoningEngine
from .goal_manager import GoalManager

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    LEARNING = "learning"
    ERROR = "error"

class AgentCore:
    """Agent核心类"""
    
    def __init__(self):
        self.state = AgentState.IDLE
        self.llm_client = QwenClient()
        self.planner = TaskPlanner()
        self.executor = TaskExecutor()
        self.tool_manager = ToolManager()
        self.reasoning_engine = ReasoningEngine()
        self.goal_manager = GoalManager()
        
        # Agent记忆和上下文
        self.memory = {}
        self.current_goal = None
        self.active_tasks = []
        self.execution_history = []
        
        # 配置参数
        self.max_iterations = 10
        self.confidence_threshold = 0.7
        
        logger.info("Agent核心初始化完成")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户请求的主入口"""
        try:
            self.state = AgentState.THINKING
            
            # 1. 理解用户意图
            intent = await self._understand_intent(request)
            
            # 2. 设定目标
            goal = await self._set_goal(intent, request)
            
            # 3. 制定计划
            plan = await self._create_plan(goal)
            
            # 4. 执行计划
            result = await self._execute_plan(plan)
            
            # 5. 学习和反思
            await self._learn_from_execution(result)
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            self.state = AgentState.ERROR
            return {"error": f"处理失败: {str(e)}"}
    
    async def _understand_intent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """理解用户意图"""
        user_message = request.get("message", "")
        context = request.get("context", {})
        
        # 使用推理引擎分析意图
        intent_analysis = await self.reasoning_engine.analyze_intent(
            message=user_message,
            context=context,
            history=self.execution_history[-5:]  # 最近5次执行历史
        )
        
        return intent_analysis
    
    async def _set_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """设定目标"""
        goal = await self.goal_manager.create_goal(
            intent=intent,
            request=request,
            current_state=self.state
        )
        
        self.current_goal = goal
        return goal
    
    async def _create_plan(self, goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制定执行计划"""
        self.state = AgentState.PLANNING
        
        plan = await self.planner.create_plan(
            goal=goal,
            available_tools=self.tool_manager.get_available_tools(),
            constraints=self._get_constraints()
        )
        
        return plan
    
    async def _execute_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行计划"""
        self.state = AgentState.EXECUTING
        
        execution_result = await self.executor.execute_plan(
            plan=plan,
            tool_manager=self.tool_manager,
            context=self.memory
        )
        
        # 记录执行历史
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "plan": plan,
            "result": execution_result
        })
        
        return execution_result
    
    async def _learn_from_execution(self, result: Dict[str, Any]):
        """从执行结果中学习"""
        self.state = AgentState.LEARNING
        
        # 分析执行效果
        learning_insights = await self.reasoning_engine.extract_insights(
            execution_result=result,
            goal=self.current_goal
        )
        
        # 更新记忆
        self._update_memory(learning_insights)
        
        # 更新工具使用统计
        self.tool_manager.update_usage_stats(result.get("tool_usage", []))
    
    def _get_constraints(self) -> Dict[str, Any]:
        """获取执行约束"""
        return {
            "max_iterations": self.max_iterations,
            "confidence_threshold": self.confidence_threshold,
            "timeout": 300,  # 5分钟超时
            "memory_limit": 1000  # 内存限制
        }
    
    def _update_memory(self, insights: Dict[str, Any]):
        """更新Agent记忆"""
        timestamp = datetime.now().isoformat()
        
        # 更新成功模式
        if insights.get("success_patterns"):
            if "success_patterns" not in self.memory:
                self.memory["success_patterns"] = []
            self.memory["success_patterns"].extend(insights["success_patterns"])
        
        # 更新失败模式
        if insights.get("failure_patterns"):
            if "failure_patterns" not in self.memory:
                self.memory["failure_patterns"] = []
            self.memory["failure_patterns"].extend(insights["failure_patterns"])
        
        # 更新知识
        if insights.get("new_knowledge"):
            if "knowledge" not in self.memory:
                self.memory["knowledge"] = []
            self.memory["knowledge"].extend(insights["new_knowledge"])
        
        # 限制记忆大小
        for key in self.memory:
            if isinstance(self.memory[key], list) and len(self.memory[key]) > 100:
                self.memory[key] = self.memory[key][-100:]
    
    async def proactive_action(self) -> Optional[Dict[str, Any]]:
        """主动行动 - Agent主动发起的行为"""
        try:
            # 检查是否有需要主动处理的任务
            proactive_tasks = await self._identify_proactive_tasks()
            
            if proactive_tasks:
                # 选择最重要的任务
                priority_task = max(proactive_tasks, key=lambda x: x.get("priority", 0))
                
                # 执行主动任务
                result = await self.process_request(priority_task)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"主动行动失败: {e}")
            return None
    
    async def _identify_proactive_tasks(self) -> List[Dict[str, Any]]:
        """识别需要主动处理的任务"""
        tasks = []
        
        # 检查预警系统
        alerts = await self._check_alerts()
        if alerts:
            tasks.extend([{
                "type": "alert_response",
                "message": f"处理预警: {alert['message']}",
                "priority": self._calculate_alert_priority(alert),
                "context": {"alert": alert}
            } for alert in alerts])
        
        # 检查知识库更新需求
        knowledge_gaps = await self._identify_knowledge_gaps()
        if knowledge_gaps:
            tasks.append({
                "type": "knowledge_update",
                "message": "更新知识库",
                "priority": 0.6,
                "context": {"gaps": knowledge_gaps}
            })
        
        # 检查系统健康状态
        health_issues = await self._check_system_health()
        if health_issues:
            tasks.append({
                "type": "system_maintenance",
                "message": "系统维护",
                "priority": 0.8,
                "context": {"issues": health_issues}
            })
        
        return tasks
    
    async def _check_alerts(self) -> List[Dict[str, Any]]:
        """检查预警"""
        # 这里可以调用现有的预警系统
        from ..analytics.alert_system import AlertSystem
        alert_system = AlertSystem()
        return alert_system.get_active_alerts()
    
    def _calculate_alert_priority(self, alert: Dict[str, Any]) -> float:
        """计算预警优先级"""
        severity_map = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 1.0
        }
        return severity_map.get(alert.get("severity", "medium"), 0.5)
    
    async def _identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """识别知识库缺口"""
        # 分析未解决的问题，识别知识缺口
        gaps = []
        
        # 这里可以实现具体的知识缺口识别逻辑
        # 例如：分析低置信度的回复、未解决的问题等
        
        return gaps
    
    async def _check_system_health(self) -> List[Dict[str, Any]]:
        """检查系统健康状态"""
        issues = []
        
        # 检查各个组件的健康状态
        if not self.llm_client.test_connection():
            issues.append({"component": "llm_client", "issue": "连接失败"})
        
        # 检查内存使用
        import psutil
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 80:
            issues.append({"component": "memory", "issue": f"内存使用率过高: {memory_percent}%"})
        
        return issues
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "state": self.state.value,
            "current_goal": self.current_goal,
            "active_tasks": len(self.active_tasks),
            "execution_history_count": len(self.execution_history),
            "memory_size": len(str(self.memory)),
            "available_tools": len(self.tool_manager.get_available_tools()),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset(self):
        """重置Agent状态"""
        self.state = AgentState.IDLE
        self.current_goal = None
        self.active_tasks = []
        self.execution_history = []
        self.memory = {}
        logger.info("Agent状态已重置")
