# -*- coding: utf-8 -*-
"""
Agent示例动作模块
包含Agent的示例动作和测试功能
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .agent_assistant_core import AgentAssistantCore

logger = logging.getLogger(__name__)

class AgentSampleActions:
    """Agent示例动作处理器"""
    
    def __init__(self, agent_core: AgentAssistantCore):
        self.agent_core = agent_core
    
    async def trigger_sample_actions(self) -> Dict[str, Any]:
        """触发示例动作"""
        try:
            logger.info("开始执行示例动作")
            
            # 执行多个示例动作
            actions_results = []
            
            # 1. 系统健康检查
            health_result = await self._sample_health_check()
            actions_results.append(health_result)
            
            # 2. 预警分析
            alert_result = await self._sample_alert_analysis()
            actions_results.append(alert_result)
            
            # 3. 工单处理
            workorder_result = await self._sample_workorder_processing()
            actions_results.append(workorder_result)
            
            # 4. 知识库更新
            knowledge_result = await self._sample_knowledge_update()
            actions_results.append(knowledge_result)
            
            # 5. 性能优化
            optimization_result = await self._sample_performance_optimization()
            actions_results.append(optimization_result)
            
            # 记录执行历史
            self.agent_core._record_execution("sample_actions", {
                "actions_count": len(actions_results),
                "results": actions_results
            })
            
            return {
                "success": True,
                "message": f"成功执行 {len(actions_results)} 个示例动作",
                "actions_results": actions_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行示例动作失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _sample_health_check(self) -> Dict[str, Any]:
        """示例：系统健康检查"""
        try:
            # 获取系统健康状态
            health_data = self.agent_core.get_system_health()
            
            # 模拟健康检查逻辑
            health_score = health_data.get("health_score", 0)
            
            if health_score > 80:
                status = "excellent"
                message = "系统运行状态良好"
            elif health_score > 60:
                status = "good"
                message = "系统运行状态正常"
            elif health_score > 40:
                status = "fair"
                message = "系统运行状态一般，建议关注"
            else:
                status = "poor"
                message = "系统运行状态较差，需要优化"
            
            return {
                "action_type": "health_check",
                "status": status,
                "message": message,
                "health_score": health_score,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "action_type": "health_check",
                "status": "error",
                "error": str(e)
            }
    
    async def _sample_alert_analysis(self) -> Dict[str, Any]:
        """示例：预警分析"""
        try:
            # 获取预警数据
            alerts = self.agent_core.check_alerts()
            
            # 分析预警
            alert_count = len(alerts)
            critical_alerts = [a for a in alerts if a.get("level") == "critical"]
            warning_alerts = [a for a in alerts if a.get("level") == "warning"]
            
            # 生成分析结果
            if alert_count == 0:
                status = "no_alerts"
                message = "当前无活跃预警"
            elif len(critical_alerts) > 0:
                status = "critical"
                message = f"发现 {len(critical_alerts)} 个严重预警，需要立即处理"
            elif len(warning_alerts) > 0:
                status = "warning"
                message = f"发现 {len(warning_alerts)} 个警告预警，建议关注"
            else:
                status = "info"
                message = f"发现 {alert_count} 个信息预警"
            
            return {
                "action_type": "alert_analysis",
                "status": status,
                "message": message,
                "alert_count": alert_count,
                "critical_count": len(critical_alerts),
                "warning_count": len(warning_alerts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"预警分析失败: {e}")
            return {
                "action_type": "alert_analysis",
                "status": "error",
                "error": str(e)
            }
    
    async def _sample_workorder_processing(self) -> Dict[str, Any]:
        """示例：工单处理"""
        try:
            # 获取工单状态
            workorders_status = self.agent_core._check_workorders_status()
            
            total = workorders_status.get("total", 0)
            open_count = workorders_status.get("open", 0)
            resolved_count = workorders_status.get("resolved", 0)
            resolution_rate = workorders_status.get("resolution_rate", 0)
            
            # 分析工单状态
            if total == 0:
                status = "no_workorders"
                message = "当前无工单"
            elif open_count > 10:
                status = "high_backlog"
                message = f"工单积压严重，有 {open_count} 个待处理工单"
            elif resolution_rate > 0.8:
                status = "good_resolution"
                message = f"工单处理效率良好，解决率 {resolution_rate:.1%}"
            else:
                status = "normal"
                message = f"工单处理状态正常，待处理 {open_count} 个"
            
            return {
                "action_type": "workorder_processing",
                "status": status,
                "message": message,
                "total_workorders": total,
                "open_workorders": open_count,
                "resolved_workorders": resolved_count,
                "resolution_rate": resolution_rate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"工单处理分析失败: {e}")
            return {
                "action_type": "workorder_processing",
                "status": "error",
                "error": str(e)
            }
    
    async def _sample_knowledge_update(self) -> Dict[str, Any]:
        """示例：知识库更新"""
        try:
            from src.core.database import db_manager
            from src.core.models import KnowledgeEntry
            
            with db_manager.get_session() as session:
                # 获取知识库统计
                total_knowledge = session.query(KnowledgeEntry).count()
                verified_knowledge = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_verified == True
                ).count()
                unverified_knowledge = total_knowledge - verified_knowledge
                
                # 分析知识库状态
                if total_knowledge == 0:
                    status = "empty"
                    message = "知识库为空，建议添加知识条目"
                elif unverified_knowledge > 0:
                    status = "needs_verification"
                    message = f"有 {unverified_knowledge} 个知识条目需要验证"
                else:
                    status = "up_to_date"
                    message = "知识库状态良好，所有条目已验证"
                
                return {
                    "action_type": "knowledge_update",
                    "status": status,
                    "message": message,
                    "total_knowledge": total_knowledge,
                    "verified_knowledge": verified_knowledge,
                    "unverified_knowledge": unverified_knowledge,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"知识库更新分析失败: {e}")
            return {
                "action_type": "knowledge_update",
                "status": "error",
                "error": str(e)
            }
    
    async def _sample_performance_optimization(self) -> Dict[str, Any]:
        """示例：性能优化"""
        try:
            # 获取系统性能数据
            system_health = self.agent_core.get_system_health()
            
            # 分析性能指标
            cpu_usage = system_health.get("cpu_usage", 0)
            memory_usage = system_health.get("memory_usage", 0)
            disk_usage = system_health.get("disk_usage", 0)
            
            # 生成优化建议
            optimization_suggestions = []
            
            if cpu_usage > 80:
                optimization_suggestions.append("CPU使用率过高，建议优化计算密集型任务")
            if memory_usage > 80:
                optimization_suggestions.append("内存使用率过高，建议清理缓存或增加内存")
            if disk_usage > 90:
                optimization_suggestions.append("磁盘空间不足，建议清理日志文件或扩容")
            
            if not optimization_suggestions:
                status = "optimal"
                message = "系统性能良好，无需优化"
            else:
                status = "needs_optimization"
                message = f"发现 {len(optimization_suggestions)} 个性能优化点"
            
            return {
                "action_type": "performance_optimization",
                "status": status,
                "message": message,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "optimization_suggestions": optimization_suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"性能优化分析失败: {e}")
            return {
                "action_type": "performance_optimization",
                "status": "error",
                "error": str(e)
            }
    
    async def run_performance_test(self) -> Dict[str, Any]:
        """运行性能测试"""
        try:
            start_time = datetime.now()
            
            # 执行多个测试
            test_results = []
            
            # 1. 响应时间测试
            response_time = await self._test_response_time()
            test_results.append(response_time)
            
            # 2. 并发处理测试
            concurrency_test = await self._test_concurrency()
            test_results.append(concurrency_test)
            
            # 3. 内存使用测试
            memory_test = await self._test_memory_usage()
            test_results.append(memory_test)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "message": "性能测试完成",
                "total_time": total_time,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _test_response_time(self) -> Dict[str, Any]:
        """测试响应时间"""
        start_time = datetime.now()
        
        # 模拟处理任务
        await asyncio.sleep(0.1)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        return {
            "test_type": "response_time",
            "response_time": response_time,
            "status": "good" if response_time < 0.5 else "slow"
        }
    
    async def _test_concurrency(self) -> Dict[str, Any]:
        """测试并发处理"""
        try:
            # 创建多个并发任务
            tasks = []
            for i in range(5):
                task = asyncio.create_task(self._simulate_task(i))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)
            
            return {
                "test_type": "concurrency",
                "concurrent_tasks": len(tasks),
                "successful_tasks": len([r for r in results if r.get("success")]),
                "status": "good"
            }
            
        except Exception as e:
            return {
                "test_type": "concurrency",
                "status": "error",
                "error": str(e)
            }
    
    async def _simulate_task(self, task_id: int) -> Dict[str, Any]:
        """模拟任务"""
        try:
            await asyncio.sleep(0.05)  # 模拟处理时间
            return {
                "task_id": task_id,
                "success": True,
                "result": f"Task {task_id} completed"
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }
    
    async def _test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        try:
            import psutil
            
            # 获取当前内存使用情况
            memory_info = psutil.virtual_memory()
            
            return {
                "test_type": "memory_usage",
                "total_memory": memory_info.total,
                "available_memory": memory_info.available,
                "used_memory": memory_info.used,
                "memory_percentage": memory_info.percent,
                "status": "good" if memory_info.percent < 80 else "high"
            }
            
        except Exception as e:
            return {
                "test_type": "memory_usage",
                "status": "error",
                "error": str(e)
            }
