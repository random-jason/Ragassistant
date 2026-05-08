
# -*- coding: utf-8 -*-
"""
目标管理器
负责目标设定、跟踪和评估
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..core.llm_client import QwenClient

logger = logging.getLogger(__name__)

class GoalManager:
    """目标管理器"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.active_goals = {}
        self.goal_history = []
        self.goal_templates = {
            "problem_solving": self._create_problem_solving_goal,
            "information_gathering": self._create_information_gathering_goal,
            "task_execution": self._create_task_execution_goal,
            "analysis": self._create_analysis_goal,
            "communication": self._create_communication_goal
        }
    
    async def create_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建目标"""
        try:
            goal_type = self._determine_goal_type(intent, request)
            
            if goal_type in self.goal_templates:
                goal = await self.goal_templates[goal_type](intent, request, current_state)
            else:
                goal = await self._create_general_goal(intent, request, current_state)
            
            # 生成唯一目标ID
            goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            goal["id"] = goal_id
            goal["created_at"] = datetime.now().isoformat()
            goal["status"] = "active"
            
            # 添加到活跃目标
            self.active_goals[goal_id] = goal
            
            logger.info(f"创建目标: {goal_id}, 类型: {goal_type}")
            return goal
            
        except Exception as e:
            logger.error(f"创建目标失败: {e}")
            return self._create_fallback_goal(intent, request)
    
    def _determine_goal_type(self, intent: Dict[str, Any], request: Dict[str, Any]) -> str:
        """确定目标类型"""
        main_intent = intent.get("main_intent", "general_query")
        
        goal_type_mapping = {
            "problem_solving": ["problem_consultation", "issue_resolution", "troubleshooting"],
            "information_gathering": ["information_query", "data_collection", "research"],
            "task_execution": ["work_order_creation", "task_assignment", "action_request"],
            "analysis": ["data_analysis", "report_generation", "performance_review"],
            "communication": ["notification", "message_delivery", "user_interaction"]
        }
        
        for goal_type, intents in goal_type_mapping.items():
            if main_intent in intents:
                return goal_type
        
        return "general"
    
    async def _create_problem_solving_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建问题解决目标"""
        prompt = f"""
        请为以下问题解决请求创建目标：
        
        用户意图: {json.dumps(intent, ensure_ascii=False)}
        请求内容: {json.dumps(request, ensure_ascii=False)}
        
        请定义：
        1. 目标描述
        2. 成功标准
        3. 所需步骤
        4. 预期结果
        5. 时间限制
        6. 资源需求
        
        请以JSON格式返回目标定义。
        """
        
        messages = [
            {"role": "system", "content": "你是一个目标设定专家，擅长为问题解决任务设定清晰的目标。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_default_problem_solving_goal(intent, request)
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            goal_data = json.loads(json_match.group())
            goal_data["type"] = "problem_solving"
            return goal_data
        else:
            return self._create_default_problem_solving_goal(intent, request)
    
    async def _create_information_gathering_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建信息收集目标"""
        prompt = f"""
        请为以下信息收集请求创建目标：
        
        用户意图: {json.dumps(intent, ensure_ascii=False)}
        请求内容: {json.dumps(request, ensure_ascii=False)}
        
        请定义：
        1. 信息收集范围
        2. 信息质量要求
        3. 收集方法
        4. 验证标准
        5. 整理格式
        
        请以JSON格式返回目标定义。
        """
        
        messages = [
            {"role": "system", "content": "你是一个信息收集专家，擅长设定信息收集目标。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_default_information_goal(intent, request)
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            goal_data = json.loads(json_match.group())
            goal_data["type"] = "information_gathering"
            return goal_data
        else:
            return self._create_default_information_goal(intent, request)
    
    async def _create_task_execution_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建任务执行目标"""
        prompt = f"""
        请为以下任务执行请求创建目标：
        
        用户意图: {json.dumps(intent, ensure_ascii=False)}
        请求内容: {json.dumps(request, ensure_ascii=False)}
        
        请定义：
        1. 任务描述
        2. 执行步骤
        3. 完成标准
        4. 质量要求
        5. 时间安排
        
        请以JSON格式返回目标定义。
        """
        
        messages = [
            {"role": "system", "content": "你是一个任务执行专家，擅长设定任务执行目标。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_default_task_goal(intent, request)
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            goal_data = json.loads(json_match.group())
            goal_data["type"] = "task_execution"
            return goal_data
        else:
            return self._create_default_task_goal(intent, request)
    
    async def _create_analysis_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建分析目标"""
        prompt = f"""
        请为以下分析请求创建目标：
        
        用户意图: {json.dumps(intent, ensure_ascii=False)}
        请求内容: {json.dumps(request, ensure_ascii=False)}
        
        请定义：
        1. 分析范围
        2. 分析方法
        3. 分析深度
        4. 输出格式
        5. 质量指标
        
        请以JSON格式返回目标定义。
        """
        
        messages = [
            {"role": "system", "content": "你是一个分析专家，擅长设定分析目标。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_default_analysis_goal(intent, request)
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            goal_data = json.loads(json_match.group())
            goal_data["type"] = "analysis"
            return goal_data
        else:
            return self._create_default_analysis_goal(intent, request)
    
    async def _create_communication_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建沟通目标"""
        prompt = f"""
        请为以下沟通请求创建目标：
        
        用户意图: {json.dumps(intent, ensure_ascii=False)}
        请求内容: {json.dumps(request, ensure_ascii=False)}
        
        请定义：
        1. 沟通对象
        2. 沟通内容
        3. 沟通方式
        4. 预期效果
        5. 反馈机制
        
        请以JSON格式返回目标定义。
        """
        
        messages = [
            {"role": "system", "content": "你是一个沟通专家，擅长设定沟通目标。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_default_communication_goal(intent, request)
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            goal_data = json.loads(json_match.group())
            goal_data["type"] = "communication"
            return goal_data
        else:
            return self._create_default_communication_goal(intent, request)
    
    async def _create_general_goal(
        self,
        intent: Dict[str, Any],
        request: Dict[str, Any],
        current_state: Any
    ) -> Dict[str, Any]:
        """创建通用目标"""
        return {
            "type": "general",
            "description": intent.get("main_intent", "处理用户请求"),
            "success_criteria": {
                "completion": True,
                "user_satisfaction": 0.7
            },
            "steps": ["理解请求", "执行任务", "返回结果"],
            "expected_result": "用户需求得到满足",
            "time_limit": 300,  # 5分钟
            "resource_requirements": ["llm_client", "knowledge_base"]
        }
    
    def _create_default_problem_solving_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认问题解决目标"""
        return {
            "type": "problem_solving",
            "description": "解决用户问题",
            "success_criteria": {
                "problem_identified": True,
                "solution_provided": True,
                "user_satisfaction": 0.7
            },
            "steps": ["分析问题", "寻找解决方案", "提供建议", "验证效果"],
            "expected_result": "问题得到解决或提供有效建议",
            "time_limit": 300,
            "resource_requirements": ["knowledge_base", "llm_client"]
        }
    
    def _create_default_information_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认信息收集目标"""
        return {
            "type": "information_gathering",
            "description": "收集相关信息",
            "success_criteria": {
                "information_complete": True,
                "information_accurate": True,
                "information_relevant": True
            },
            "steps": ["确定信息需求", "搜索信息源", "收集信息", "整理信息"],
            "expected_result": "提供准确、完整、相关的信息",
            "time_limit": 180,
            "resource_requirements": ["knowledge_base", "search_tools"]
        }
    
    def _create_default_task_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认任务执行目标"""
        return {
            "type": "task_execution",
            "description": "执行指定任务",
            "success_criteria": {
                "task_completed": True,
                "quality_met": True,
                "time_met": True
            },
            "steps": ["理解任务", "制定计划", "执行任务", "验证结果"],
            "expected_result": "任务成功完成",
            "time_limit": 600,
            "resource_requirements": ["task_tools", "monitoring"]
        }
    
    def _create_default_analysis_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认分析目标"""
        return {
            "type": "analysis",
            "description": "执行数据分析",
            "success_criteria": {
                "analysis_complete": True,
                "insights_meaningful": True,
                "report_clear": True
            },
            "steps": ["收集数据", "分析数据", "提取洞察", "生成报告"],
            "expected_result": "提供有价值的分析报告",
            "time_limit": 900,
            "resource_requirements": ["analytics_tools", "data_sources"]
        }
    
    def _create_default_communication_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认沟通目标"""
        return {
            "type": "communication",
            "description": "与用户沟通",
            "success_criteria": {
                "message_delivered": True,
                "response_received": True,
                "understanding_achieved": True
            },
            "steps": ["准备消息", "发送消息", "等待响应", "确认理解"],
            "expected_result": "成功沟通并达成理解",
            "time_limit": 120,
            "resource_requirements": ["communication_tools"]
        }
    
    def _create_fallback_goal(self, intent: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用目标"""
        return {
            "type": "fallback",
            "description": "处理用户请求",
            "success_criteria": {"completion": True},
            "steps": ["处理请求"],
            "expected_result": "返回响应",
            "time_limit": 60,
            "resource_requirements": ["basic_tools"]
        }
    
    async def update_goal_progress(self, goal_id: str, progress_data: Dict[str, Any]) -> bool:
        """更新目标进度"""
        try:
            if goal_id not in self.active_goals:
                return False
            
            goal = self.active_goals[goal_id]
            goal["progress"] = progress_data
            goal["updated_at"] = datetime.now().isoformat()
            
            # 检查是否完成
            if self._check_goal_completion(goal):
                goal["status"] = "completed"
                goal["completed_at"] = datetime.now().isoformat()
                
                # 移动到历史记录
                self.goal_history.append(goal)
                del self.active_goals[goal_id]
                
                logger.info(f"目标 {goal_id} 已完成")
            
            return True
            
        except Exception as e:
            logger.error(f"更新目标进度失败: {e}")
            return False
    
    def _check_goal_completion(self, goal: Dict[str, Any]) -> bool:
        """检查目标是否完成"""
        success_criteria = goal.get("success_criteria", {})
        
        if not success_criteria:
            return True
        
        progress = goal.get("progress", {})
        
        # 检查每个成功标准
        for criterion, required_value in success_criteria.items():
            actual_value = progress.get(criterion)
            if actual_value != required_value:
                return False
        
        return True
    
    async def evaluate_goal_performance(self, goal_id: str) -> Dict[str, Any]:
        """评估目标性能"""
        try:
            if goal_id in self.active_goals:
                goal = self.active_goals[goal_id]
            elif goal_id in [g["id"] for g in self.goal_history]:
                goal = next(g for g in self.goal_history if g["id"] == goal_id)
            else:
                return {"error": "目标不存在"}
            
            evaluation = {
                "goal_id": goal_id,
                "type": goal.get("type"),
                "status": goal.get("status"),
                "created_at": goal.get("created_at"),
                "completed_at": goal.get("completed_at"),
                "duration": self._calculate_goal_duration(goal),
                "success_rate": self._calculate_success_rate(goal),
                "efficiency": self._calculate_efficiency(goal),
                "quality_score": self._calculate_quality_score(goal)
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"评估目标性能失败: {e}")
            return {"error": str(e)}
    
    def _calculate_goal_duration(self, goal: Dict[str, Any]) -> float:
        """计算目标持续时间"""
        created_at = datetime.fromisoformat(goal.get("created_at", datetime.now().isoformat()))
        
        if goal.get("completed_at"):
            completed_at = datetime.fromisoformat(goal["completed_at"])
            return (completed_at - created_at).total_seconds()
        else:
            return (datetime.now() - created_at).total_seconds()
    
    def _calculate_success_rate(self, goal: Dict[str, Any]) -> float:
        """计算成功率"""
        if goal.get("status") == "completed":
            return 1.0
        elif goal.get("status") == "failed":
            return 0.0
        else:
            # 根据进度计算部分成功率
            progress = goal.get("progress", {})
            success_criteria = goal.get("success_criteria", {})
            
            if not success_criteria:
                return 0.5
            
            completed_criteria = 0
            for criterion in success_criteria:
                if progress.get(criterion) == success_criteria[criterion]:
                    completed_criteria += 1
            
            return completed_criteria / len(success_criteria)
    
    def _calculate_efficiency(self, goal: Dict[str, Any]) -> float:
        """计算效率"""
        duration = self._calculate_goal_duration(goal)
        time_limit = goal.get("time_limit", 300)
        
        if duration <= time_limit:
            return 1.0
        else:
            # 超时惩罚
            return max(0.0, 1.0 - (duration - time_limit) / time_limit)
    
    def _calculate_quality_score(self, goal: Dict[str, Any]) -> float:
        """计算质量分数"""
        # 这里可以根据具体的目标类型和质量指标计算
        # 暂时返回一个基于成功率的简单计算
        success_rate = self._calculate_success_rate(goal)
        efficiency = self._calculate_efficiency(goal)
        
        return (success_rate + efficiency) / 2
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """获取活跃目标"""
        return list(self.active_goals.values())
    
    def get_goal_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取目标历史"""
        return self.goal_history[-limit:] if self.goal_history else []
    
    def get_goal_statistics(self) -> Dict[str, Any]:
        """获取目标统计"""
        total_goals = len(self.active_goals) + len(self.goal_history)
        completed_goals = len([g for g in self.goal_history if g.get("status") == "completed"])
        active_goals = len(self.active_goals)
        
        return {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "completion_rate": completed_goals / total_goals if total_goals > 0 else 0,
            "goal_types": self._get_goal_type_distribution()
        }
    
    def _get_goal_type_distribution(self) -> Dict[str, int]:
        """获取目标类型分布"""
        distribution = {}
        
        # 统计活跃目标
        for goal in self.active_goals.values():
            goal_type = goal.get("type", "unknown")
            distribution[goal_type] = distribution.get(goal_type, 0) + 1
        
        # 统计历史目标
        for goal in self.goal_history:
            goal_type = goal.get("type", "unknown")
            distribution[goal_type] = distribution.get(goal_type, 0) + 1
        
        return distribution
