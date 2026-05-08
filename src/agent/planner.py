
# -*- coding: utf-8 -*-
"""
任务规划器
负责制定执行计划和任务分解
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..core.llm_client import QwenClient

logger = logging.getLogger(__name__)

class TaskPlanner:
    """任务规划器"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.planning_strategies = {
            "sequential": self._create_sequential_plan,
            "parallel": self._create_parallel_plan,
            "conditional": self._create_conditional_plan,
            "iterative": self._create_iterative_plan
        }
    
    async def create_plan(
        self,
        goal: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建执行计划"""
        try:
            # 1. 分析目标复杂度
            complexity = await self._analyze_goal_complexity(goal)
            
            # 2. 选择规划策略
            strategy = self._select_planning_strategy(complexity, goal)
            
            # 3. 生成计划
            plan = await self.planning_strategies[strategy](goal, available_tools, constraints)
            
            # 4. 优化计划
            optimized_plan = await self._optimize_plan(plan, constraints)
            
            logger.info(f"创建计划成功，包含 {len(optimized_plan)} 个任务")
            return optimized_plan
            
        except Exception as e:
            logger.error(f"创建计划失败: {e}")
            return []
    
    async def _analyze_goal_complexity(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """分析目标复杂度"""
        prompt = f"""
        请分析以下目标的复杂度：
        
        目标: {goal.get('description', '')}
        类型: {goal.get('type', '')}
        上下文: {goal.get('context', {})}
        
        请从以下维度评估复杂度（1-10分）：
        1. 任务数量
        2. 依赖关系复杂度
        3. 所需工具数量
        4. 时间要求
        5. 资源需求
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个任务规划专家，擅长分析任务复杂度。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"complexity_score": 5, "strategy": "sequential"}
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                return {"complexity_score": 5, "strategy": "sequential"}
        except Exception as e:
            logger.error(f"解析复杂度分析失败: {e}")
            return {"complexity_score": 5, "strategy": "sequential"}
    
    def _select_planning_strategy(self, complexity: Dict[str, Any], goal: Dict[str, Any]) -> str:
        """选择规划策略"""
        complexity_score = complexity.get("complexity_score", 5)
        goal_type = goal.get("type", "general")
        
        if complexity_score <= 3:
            return "sequential"
        elif complexity_score <= 6:
            if goal_type in ["analysis", "monitoring"]:
                return "parallel"
            else:
                return "conditional"
        else:
            return "iterative"
    
    async def _create_sequential_plan(
        self,
        goal: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建顺序执行计划"""
        prompt = f"""
        请为以下目标创建一个顺序执行计划：
        
        目标: {goal.get('description', '')}
        可用工具: {[tool.get('name', '') for tool in available_tools]}
        
        请将目标分解为具体的执行步骤，每个步骤包含：
        1. 任务描述
        2. 所需工具
        3. 输入参数
        4. 预期输出
        5. 成功条件
        
        请以JSON数组格式返回计划。
        """
        
        messages = [
            {"role": "system", "content": "你是一个任务规划专家，擅长创建顺序执行计划。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return self._create_fallback_plan(goal)
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return self._format_plan_tasks(plan)
            else:
                return self._create_fallback_plan(goal)
        except Exception as e:
            logger.error(f"解析顺序计划失败: {e}")
            return self._create_fallback_plan(goal)
    
    async def _create_parallel_plan(
        self,
        goal: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建并行执行计划"""
        # 先创建基础任务
        base_tasks = await self._create_sequential_plan(goal, available_tools, constraints)
        
        # 分析任务间的依赖关系
        parallel_groups = self._group_parallel_tasks(base_tasks)
        
        return parallel_groups
    
    async def _create_conditional_plan(
        self,
        goal: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建条件执行计划"""
        prompt = f"""
        请为以下目标创建一个条件执行计划：
        
        目标: {goal.get('description', '')}
        上下文: {goal.get('context', {})}
        
        计划应该包含：
        1. 初始条件检查
        2. 分支逻辑
        3. 每个分支的具体任务
        4. 合并条件
        
        请以JSON格式返回计划。
        """
        
        messages = [
            {"role": "system", "content": "你是一个任务规划专家，擅长创建条件执行计划。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return await self._create_sequential_plan(goal, available_tools, constraints)
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return self._format_conditional_plan(plan)
            else:
                return await self._create_sequential_plan(goal, available_tools, constraints)
        except Exception as e:
            logger.error(f"解析条件计划失败: {e}")
            return await self._create_sequential_plan(goal, available_tools, constraints)
    
    async def _create_iterative_plan(
        self,
        goal: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建迭代执行计划"""
        # 创建基础计划
        base_plan = await self._create_sequential_plan(goal, available_tools, constraints)
        
        # 添加迭代控制任务
        iteration_control = {
            "id": "iteration_control",
            "type": "control",
            "description": "迭代控制",
            "max_iterations": constraints.get("max_iterations", 10),
            "convergence_criteria": goal.get("success_criteria", {}),
            "tasks": base_plan
        }
        
        return [iteration_control]
    
    def _group_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将任务分组为可并行执行的任务组"""
        groups = []
        current_group = []
        
        for task in tasks:
            # 简单的分组逻辑：相同类型的任务可以并行
            if not current_group or current_group[0].get("type") == task.get("type"):
                current_group.append(task)
            else:
                if current_group:
                    groups.append({
                        "type": "parallel_group",
                        "tasks": current_group,
                        "execution_mode": "parallel"
                    })
                current_group = [task]
        
        if current_group:
            groups.append({
                "type": "parallel_group",
                "tasks": current_group,
                "execution_mode": "parallel"
            })
        
        return groups
    
    def _format_plan_tasks(self, raw_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化计划任务"""
        formatted_tasks = []
        
        for i, task in enumerate(raw_plan):
            formatted_task = {
                "id": f"task_{i+1}",
                "type": task.get("type", "action"),
                "description": task.get("description", ""),
                "tool": task.get("tool", ""),
                "parameters": task.get("parameters", {}),
                "expected_output": task.get("expected_output", ""),
                "success_criteria": task.get("success_criteria", {}),
                "dependencies": task.get("dependencies", []),
                "priority": task.get("priority", 0.5),
                "timeout": task.get("timeout", 60)
            }
            formatted_tasks.append(formatted_task)
        
        return formatted_tasks
    
    def _format_conditional_plan(self, raw_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化条件计划"""
        formatted_tasks = []
        
        # 添加条件检查任务
        condition_task = {
            "id": "condition_check",
            "type": "condition",
            "description": "条件检查",
            "condition": raw_plan.get("condition", ""),
            "branches": raw_plan.get("branches", {})
        }
        formatted_tasks.append(condition_task)
        
        # 添加分支任务
        for branch_name, branch_tasks in raw_plan.get("branches", {}).items():
            branch_task = {
                "id": f"branch_{branch_name}",
                "type": "branch",
                "description": f"执行分支: {branch_name}",
                "condition": branch_name,
                "tasks": self._format_plan_tasks(branch_tasks)
            }
            formatted_tasks.append(branch_task)
        
        return formatted_tasks
    
    async def _optimize_plan(self, plan: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """优化计划"""
        optimized_plan = []
        
        for task in plan:
            # 检查时间约束
            if task.get("timeout", 60) > constraints.get("timeout", 300):
                task["timeout"] = constraints.get("timeout", 300)
            
            # 检查资源约束
            if task.get("resource_usage", 0) > constraints.get("memory_limit", 1000):
                # 分解大任务
                subtasks = await self._decompose_task(task)
                optimized_plan.extend(subtasks)
            else:
                optimized_plan.append(task)
        
        return optimized_plan
    
    async def _decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分解大任务为小任务"""
        prompt = f"""
        请将以下大任务分解为更小的子任务：
        
        任务: {task.get('description', '')}
        类型: {task.get('type', '')}
        参数: {task.get('parameters', {})}
        
        请返回分解后的子任务列表，每个子任务应该是独立的、可执行的。
        """
        
        messages = [
            {"role": "system", "content": "你是一个任务分解专家，擅长将复杂任务分解为简单任务。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return [task]  # 如果分解失败，返回原任务
        
        try:
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                subtasks = json.loads(json_match.group())
                return self._format_plan_tasks(subtasks)
            else:
                return [task]
        except Exception as e:
            logger.error(f"任务分解失败: {e}")
            return [task]
    
    def _create_fallback_plan(self, goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建备用计划"""
        return [{
            "id": "fallback_task",
            "type": "action",
            "description": goal.get("description", "执行目标"),
            "tool": "general_response",
            "parameters": {"goal": goal},
            "expected_output": "目标完成",
            "success_criteria": {"completion": True},
            "priority": 0.5,
            "timeout": 60
        }]
    
    def validate_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证计划的有效性"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        for task in plan:
            # 检查必要字段
            if not task.get("id"):
                validation_result["issues"].append("任务缺少ID")
                validation_result["valid"] = False
            
            if not task.get("description"):
                validation_result["warnings"].append(f"任务 {task.get('id', 'unknown')} 缺少描述")
            
            # 检查依赖关系
            dependencies = task.get("dependencies", [])
            task_ids = [t.get("id") for t in plan]
            for dep in dependencies:
                if dep not in task_ids:
                    validation_result["issues"].append(f"任务 {task.get('id')} 的依赖 {dep} 不存在")
                    validation_result["valid"] = False
        
        return validation_result
