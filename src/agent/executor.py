
# -*- coding: utf-8 -*-
"""
任务执行器
负责执行计划中的具体任务
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.execution_strategies = {
            "sequential": self._execute_sequential,
            "parallel": self._execute_parallel,
            "conditional": self._execute_conditional,
            "iterative": self._execute_iterative
        }
        self.active_executions = {}
    
    async def execute_plan(
        self,
        plan: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行计划"""
        try:
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_executions[execution_id] = {
                "start_time": datetime.now(),
                "status": "running",
                "plan": plan
            }
            
            # 根据计划类型选择执行策略
            execution_strategy = self._determine_execution_strategy(plan)
            
            # 执行计划
            result = await self.execution_strategies[execution_strategy](
                plan=plan,
                tool_manager=tool_manager,
                context=context,
                execution_id=execution_id
            )
            
            # 更新执行状态
            self.active_executions[execution_id]["status"] = "completed"
            self.active_executions[execution_id]["end_time"] = datetime.now()
            self.active_executions[execution_id]["result"] = result
            
            logger.info(f"计划执行完成: {execution_id}")
            return result
            
        except Exception as e:
            logger.error(f"执行计划失败: {e}")
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = "failed"
                self.active_executions[execution_id]["error"] = str(e)
            
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id
            }
    
    def _determine_execution_strategy(self, plan: List[Dict[str, Any]]) -> str:
        """确定执行策略"""
        if not plan:
            return "sequential"
        
        # 检查计划类型
        plan_types = [task.get("type") for task in plan]
        
        if "parallel_group" in plan_types:
            return "parallel"
        elif "condition" in plan_types or "branch" in plan_types:
            return "conditional"
        elif "iteration_control" in plan_types:
            return "iterative"
        else:
            return "sequential"
    
    async def _execute_sequential(
        self,
        plan: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """顺序执行计划"""
        results = []
        execution_log = []
        
        for i, task in enumerate(plan):
            try:
                logger.info(f"执行任务 {i+1}/{len(plan)}: {task.get('id', 'unknown')}")
                
                # 检查任务依赖
                if not await self._check_dependencies(task, results):
                    logger.warning(f"任务 {task.get('id')} 的依赖未满足，跳过执行")
                    continue
                
                # 执行任务
                task_result = await self._execute_single_task(task, tool_manager, context)
                
                results.append({
                    "task_id": task.get("id"),
                    "result": task_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                execution_log.append({
                    "task_id": task.get("id"),
                    "status": "completed",
                    "duration": task_result.get("duration", 0)
                })
                
                # 检查是否满足成功条件
                if not self._check_success_criteria(task, task_result):
                    logger.warning(f"任务 {task.get('id')} 未满足成功条件")
                
            except Exception as e:
                logger.error(f"执行任务 {task.get('id')} 失败: {e}")
                execution_log.append({
                    "task_id": task.get("id"),
                    "status": "failed",
                    "error": str(e)
                })
                
                # 根据任务重要性决定是否继续
                if task.get("critical", False):
                    return {
                        "success": False,
                        "error": f"关键任务失败: {task.get('id')}",
                        "results": results,
                        "execution_log": execution_log
                    }
        
        return {
            "success": True,
            "results": results,
            "execution_log": execution_log,
            "execution_id": execution_id
        }
    
    async def _execute_parallel(
        self,
        plan: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """并行执行计划"""
        results = []
        execution_log = []
        
        # 将计划分组
        parallel_groups = self._group_tasks_for_parallel_execution(plan)
        
        for group in parallel_groups:
            if group["execution_mode"] == "parallel":
                # 并行执行组内任务
                group_results = await self._execute_tasks_parallel(
                    group["tasks"], tool_manager, context
                )
                results.extend(group_results)
            else:
                # 顺序执行组内任务
                for task in group["tasks"]:
                    task_result = await self._execute_single_task(task, tool_manager, context)
                    results.append({
                        "task_id": task.get("id"),
                        "result": task_result,
                        "timestamp": datetime.now().isoformat()
                    })
        
        return {
            "success": True,
            "results": results,
            "execution_log": execution_log,
            "execution_id": execution_id
        }
    
    async def _execute_conditional(
        self,
        plan: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """条件执行计划"""
        results = []
        execution_log = []
        
        # 找到条件检查任务
        condition_task = None
        branch_tasks = []
        
        for task in plan:
            if task.get("type") == "condition":
                condition_task = task
            elif task.get("type") == "branch":
                branch_tasks.append(task)
        
        if not condition_task:
            logger.error("条件计划中缺少条件检查任务")
            return {"success": False, "error": "缺少条件检查任务"}
        
        # 执行条件检查
        condition_result = await self._execute_single_task(condition_task, tool_manager, context)
        results.append({
            "task_id": condition_task.get("id"),
            "result": condition_result,
            "timestamp": datetime.now().isoformat()
        })
        
        # 根据条件结果选择分支
        selected_branch = self._select_branch(condition_result, branch_tasks)
        
        if selected_branch:
            # 执行选中的分支
            branch_result = await self._execute_sequential(
                selected_branch.get("tasks", []),
                tool_manager,
                context,
                execution_id
            )
            results.extend(branch_result.get("results", []))
            execution_log.extend(branch_result.get("execution_log", []))
        
        return {
            "success": True,
            "results": results,
            "execution_log": execution_log,
            "execution_id": execution_id,
            "selected_branch": selected_branch.get("id") if selected_branch else None
        }
    
    async def _execute_iterative(
        self,
        plan: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """迭代执行计划"""
        # 找到迭代控制任务
        iteration_task = None
        for task in plan:
            if task.get("type") == "iteration_control":
                iteration_task = task
                break
        
        if not iteration_task:
            logger.error("迭代计划中缺少迭代控制任务")
            return {"success": False, "error": "缺少迭代控制任务"}
        
        max_iterations = iteration_task.get("max_iterations", 10)
        convergence_criteria = iteration_task.get("convergence_criteria", {})
        tasks = iteration_task.get("tasks", [])
        
        results = []
        execution_log = []
        iteration_count = 0
        
        while iteration_count < max_iterations:
            iteration_count += 1
            logger.info(f"执行第 {iteration_count} 次迭代")
            
            # 执行迭代任务
            iteration_result = await self._execute_sequential(
                tasks, tool_manager, context, f"{execution_id}_iter_{iteration_count}"
            )
            
            results.append({
                "iteration": iteration_count,
                "result": iteration_result,
                "timestamp": datetime.now().isoformat()
            })
            
            # 检查收敛条件
            if self._check_convergence(iteration_result, convergence_criteria):
                logger.info(f"迭代在第 {iteration_count} 次收敛")
                break
        
        return {
            "success": True,
            "results": results,
            "execution_log": execution_log,
            "execution_id": execution_id,
            "iterations": iteration_count,
            "converged": iteration_count < max_iterations
        }
    
    async def _execute_single_task(
        self,
        task: Dict[str, Any],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个任务"""
        start_time = datetime.now()
        
        try:
            task_id = task.get("id", "unknown")
            task_type = task.get("type", "action")
            tool_name = task.get("tool", "")
            parameters = task.get("parameters", {})
            
            logger.info(f"执行任务: {task_id}, 类型: {task_type}, 工具: {tool_name}")
            
            # 根据任务类型执行
            if task_type == "action":
                result = await self._execute_action_task(task, tool_manager, context)
            elif task_type == "condition":
                result = await self._execute_condition_task(task, tool_manager, context)
            elif task_type == "control":
                result = await self._execute_control_task(task, tool_manager, context)
            else:
                result = await self._execute_general_task(task, tool_manager, context)
            
            duration = (datetime.now() - start_time).total_seconds()
            result["duration"] = duration
            
            logger.info(f"任务 {task_id} 执行完成，耗时: {duration:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_action_task(
        self,
        task: Dict[str, Any],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行动作任务"""
        tool_name = task.get("tool", "")
        parameters = task.get("parameters", {})
        
        # 合并上下文参数
        full_parameters = {**parameters, **context}
        
        # 调用工具
        result = await tool_manager.execute_tool(tool_name, full_parameters)
        
        return {
            "success": True,
            "tool": tool_name,
            "parameters": full_parameters,
            "result": result
        }
    
    async def _execute_condition_task(
        self,
        task: Dict[str, Any],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行条件任务"""
        condition = task.get("condition", "")
        branches = task.get("branches", {})
        
        # 评估条件
        condition_result = await self._evaluate_condition(condition, context)
        
        return {
            "success": True,
            "condition": condition,
            "result": condition_result,
            "available_branches": list(branches.keys())
        }
    
    async def _execute_control_task(
        self,
        task: Dict[str, Any],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行控制任务"""
        control_type = task.get("control_type", "general")
        
        if control_type == "iteration":
            return await self._execute_iteration_control(task, context)
        elif control_type == "loop":
            return await self._execute_loop_control(task, context)
        else:
            return {
                "success": True,
                "control_type": control_type,
                "message": "控制任务执行完成"
            }
    
    async def _execute_general_task(
        self,
        task: Dict[str, Any],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行通用任务"""
        description = task.get("description", "")
        
        # 这里可以实现通用的任务执行逻辑
        # 例如：调用LLM生成响应、执行数据库操作等
        
        return {
            "success": True,
            "description": description,
            "message": "通用任务执行完成"
        }
    
    async def _execute_tasks_parallel(
        self,
        tasks: List[Dict[str, Any]],
        tool_manager: Any,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """并行执行多个任务"""
        async def execute_task(task):
            return await self._execute_single_task(task, tool_manager, context)
        
        # 创建并行任务
        parallel_tasks = [execute_task(task) for task in tasks]
        
        # 等待所有任务完成
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": tasks[i].get("id"),
                    "result": {"success": False, "error": str(result)},
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append({
                    "task_id": tasks[i].get("id"),
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
        
        return processed_results
    
    def _group_tasks_for_parallel_execution(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将任务分组以便并行执行"""
        groups = []
        current_group = []
        
        for task in plan:
            if task.get("type") == "parallel_group":
                if current_group:
                    groups.append({
                        "execution_mode": "sequential",
                        "tasks": current_group
                    })
                    current_group = []
                groups.append(task)
            else:
                current_group.append(task)
        
        if current_group:
            groups.append({
                "execution_mode": "sequential",
                "tasks": current_group
            })
        
        return groups
    
    async def _check_dependencies(self, task: Dict[str, Any], results: List[Dict[str, Any]]) -> bool:
        """检查任务依赖是否满足"""
        dependencies = task.get("dependencies", [])
        
        if not dependencies:
            return True
        
        # 检查所有依赖是否已完成
        completed_task_ids = [r["task_id"] for r in results if r["result"].get("success", False)]
        
        for dep in dependencies:
            if dep not in completed_task_ids:
                return False
        
        return True
    
    def _check_success_criteria(self, task: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """检查任务是否满足成功条件"""
        success_criteria = task.get("success_criteria", {})
        
        if not success_criteria:
            return result.get("success", False)
        
        # 检查每个成功条件
        for criterion, expected_value in success_criteria.items():
            actual_value = result.get(criterion)
            if actual_value != expected_value:
                return False
        
        return True
    
    def _select_branch(self, condition_result: Dict[str, Any], branch_tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """根据条件结果选择分支"""
        condition_value = condition_result.get("result", "")
        
        for branch_task in branch_tasks:
            branch_condition = branch_task.get("condition", "")
            if branch_condition == condition_value:
                return branch_task
        
        return None
    
    def _check_convergence(self, iteration_result: Dict[str, Any], convergence_criteria: Dict[str, Any]) -> bool:
        """检查迭代是否收敛"""
        if not convergence_criteria:
            return False
        
        # 检查收敛条件
        for criterion, threshold in convergence_criteria.items():
            actual_value = iteration_result.get(criterion)
            if actual_value is None:
                continue
            
            # 这里可以实现更复杂的收敛判断逻辑
            if isinstance(threshold, dict):
                if threshold.get("type") == "less_than":
                    if actual_value >= threshold.get("value"):
                        return False
                elif threshold.get("type") == "greater_than":
                    if actual_value <= threshold.get("value"):
                        return False
        
        return True
    
    async def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> str:
        """评估条件表达式"""
        # 这里可以实现条件评估逻辑
        # 例如：解析条件表达式、查询上下文等
        
        # 简单的条件评估示例
        if "satisfaction" in condition:
            return "high" if context.get("satisfaction_score", 0) > 0.7 else "low"
        elif "priority" in condition:
            return context.get("priority", "medium")
        else:
            return "default"
    
    async def _execute_iteration_control(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行迭代控制"""
        max_iterations = task.get("max_iterations", 10)
        current_iteration = context.get("current_iteration", 0)
        
        return {
            "success": True,
            "max_iterations": max_iterations,
            "current_iteration": current_iteration,
            "continue": current_iteration < max_iterations
        }
    
    async def _execute_loop_control(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行循环控制"""
        loop_condition = task.get("loop_condition", "")
        
        return {
            "success": True,
            "loop_condition": loop_condition,
            "continue": True  # 这里应该根据实际条件判断
        }
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        return self.active_executions.get(execution_id)
    
    def get_all_executions(self) -> Dict[str, Any]:
        """获取所有执行记录"""
        return self.active_executions
