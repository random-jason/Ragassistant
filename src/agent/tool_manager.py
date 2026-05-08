
# -*- coding: utf-8 -*-
"""
工具管理器
负责管理和执行各种工具
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools = {}
        self.tool_usage_stats = {}
        self.tool_performance = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 注册基础工具
        self.register_tool("search_knowledge", self._search_knowledge_tool)
        self.register_tool("create_work_order", self._create_work_order_tool)
        self.register_tool("update_work_order", self._update_work_order_tool)
        self.register_tool("generate_response", self._generate_response_tool)
        self.register_tool("analyze_data", self._analyze_data_tool)
        self.register_tool("send_notification", self._send_notification_tool)
        self.register_tool("schedule_task", self._schedule_task_tool)
        self.register_tool("web_search", self._web_search_tool)
        self.register_tool("file_operation", self._file_operation_tool)
        self.register_tool("database_query", self._database_query_tool)
        
        logger.info(f"已注册 {len(self.tools)} 个默认工具")
    
    def register_tool(self, name: str, func: Callable, metadata: Optional[Dict[str, Any]] = None):
        """注册工具"""
        self.tools[name] = {
            "function": func,
            "metadata": metadata or {},
            "usage_count": 0,
            "last_used": None,
            "success_rate": 0.0
        }
        
        logger.info(f"注册工具: {name}")
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"注销工具: {name}")
            return True
        return False
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"工具 '{tool_name}' 不存在"
            }
        
        tool = self.tools[tool_name]
        start_time = datetime.now()
        
        try:
            # 更新使用统计
            tool["usage_count"] += 1
            tool["last_used"] = start_time
            
            # 执行工具
            if asyncio.iscoroutinefunction(tool["function"]):
                result = await tool["function"](**parameters)
            else:
                result = tool["function"](**parameters)
            
            # 更新性能统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_tool_performance(tool_name, True, execution_time)
            
            logger.info(f"工具 '{tool_name}' 执行成功，耗时: {execution_time:.2f}秒")
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tool": tool_name
            }
            
        except Exception as e:
            logger.error(f"工具 '{tool_name}' 执行失败: {e}")
            
            # 更新性能统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_tool_performance(tool_name, False, execution_time)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "tool": tool_name
            }
    
    def _update_tool_performance(self, tool_name: str, success: bool, execution_time: float):
        """更新工具性能统计"""
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "total_time": 0.0,
                "avg_execution_time": 0.0,
                "success_rate": 0.0
            }
        
        perf = self.tool_performance[tool_name]
        perf["total_executions"] += 1
        perf["total_time"] += execution_time
        perf["avg_execution_time"] = perf["total_time"] / perf["total_executions"]
        
        if success:
            perf["successful_executions"] += 1
        
        perf["success_rate"] = perf["successful_executions"] / perf["total_executions"]
        
        # 更新工具的成功率
        self.tools[tool_name]["success_rate"] = perf["success_rate"]
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools_info = []
        
        for name, tool in self.tools.items():
            tool_info = {
                "name": name,
                "metadata": tool["metadata"],
                "usage_count": tool["usage_count"],
                "last_used": tool["last_used"].isoformat() if tool["last_used"] else None,
                "success_rate": tool["success_rate"]
            }
            
            # 添加性能信息
            if name in self.tool_performance:
                perf = self.tool_performance[name]
                tool_info.update({
                    "avg_execution_time": perf["avg_execution_time"],
                    "total_executions": perf["total_executions"]
                })
            
            tools_info.append(tool_info)
        
        return tools_info
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        info = {
            "name": tool_name,
            "metadata": tool["metadata"],
            "usage_count": tool["usage_count"],
            "last_used": tool["last_used"].isoformat() if tool["last_used"] else None,
            "success_rate": tool["success_rate"]
        }
        
        if tool_name in self.tool_performance:
            info.update(self.tool_performance[tool_name])
        
        return info
    
    def update_usage_stats(self, tool_usage: List[Dict[str, Any]]):
        """更新工具使用统计"""
        for usage in tool_usage:
            tool_name = usage.get("tool")
            if tool_name in self.tools:
                self.tools[tool_name]["usage_count"] += usage.get("count", 1)
    
    # 默认工具实现
    
    async def _search_knowledge_tool(self, query: str, top_k: int = 3, **kwargs) -> Dict[str, Any]:
        """搜索知识库工具"""
        try:
            from ..knowledge_base.knowledge_manager import KnowledgeManager
            knowledge_manager = KnowledgeManager()
            
            results = knowledge_manager.search_knowledge(query, top_k)
            
            return {
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {"error": str(e)}
    
    async def _create_work_order_tool(self, title: str, description: str, category: str, priority: str = "medium", **kwargs) -> Dict[str, Any]:
        """创建工单工具"""
        try:
            from ..dialogue.dialogue_manager import DialogueManager
            dialogue_manager = DialogueManager()
            
            result = dialogue_manager.create_work_order(title, description, category, priority)
            
            return result
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            return {"error": str(e)}
    
    async def _update_work_order_tool(self, work_order_id: int, **kwargs) -> Dict[str, Any]:
        """更新工单工具"""
        try:
            from ..dialogue.dialogue_manager import DialogueManager
            dialogue_manager = DialogueManager()
            
            success = dialogue_manager.update_work_order(work_order_id, **kwargs)
            
            return {
                "success": success,
                "work_order_id": work_order_id,
                "updated_fields": list(kwargs.keys())
            }
        except Exception as e:
            logger.error(f"更新工单失败: {e}")
            return {"error": str(e)}
    
    async def _generate_response_tool(self, message: str, context: str = "", **kwargs) -> Dict[str, Any]:
        """生成回复工具"""
        try:
            from ..core.llm_client import QwenClient
            llm_client = QwenClient()
            
            result = llm_client.generate_response(message, context)
            
            return result
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return {"error": str(e)}
    
    async def _analyze_data_tool(self, data_type: str, date_range: str = "last_7_days", **kwargs) -> Dict[str, Any]:
        """数据分析工具"""
        try:
            from ..analytics.analytics_manager import AnalyticsManager
            analytics_manager = AnalyticsManager()
            
            if data_type == "daily_analytics":
                result = analytics_manager.generate_daily_analytics()
            elif data_type == "summary":
                result = analytics_manager.get_analytics_summary()
            elif data_type == "category_performance":
                result = analytics_manager.get_category_performance()
            else:
                result = {"error": f"不支持的数据类型: {data_type}"}
            
            return result
        except Exception as e:
            logger.error(f"数据分析失败: {e}")
            return {"error": str(e)}
    
    async def _send_notification_tool(self, message: str, recipients: List[str], notification_type: str = "info", **kwargs) -> Dict[str, Any]:
        """发送通知工具"""
        try:
            # 这里可以实现具体的通知逻辑
            # 例如：发送邮件、短信、推送通知等
            
            notification_data = {
                "message": message,
                "recipients": recipients,
                "type": notification_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # 模拟发送通知
            logger.info(f"发送通知: {message} 给 {recipients}")
            
            return {
                "success": True,
                "notification_id": f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "data": notification_data
            }
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return {"error": str(e)}
    
    async def _schedule_task_tool(self, task_name: str, schedule_time: str, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """调度任务工具"""
        try:
            # 这里可以实现任务调度逻辑
            # 例如：使用APScheduler、Celery等
            
            schedule_data = {
                "task_name": task_name,
                "schedule_time": schedule_time,
                "task_data": task_data,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"调度任务: {task_name} 在 {schedule_time}")
            
            return {
                "success": True,
                "schedule_id": f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "data": schedule_data
            }
        except Exception as e:
            logger.error(f"调度任务失败: {e}")
            return {"error": str(e)}
    
    async def _web_search_tool(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        """网络搜索工具"""
        try:
            # 这里可以实现网络搜索逻辑
            # 例如：使用Google Search API、Bing Search API等
            
            search_results = [
                {
                    "title": f"搜索结果 {i+1}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"这是关于 '{query}' 的搜索结果摘要 {i+1}"
                }
                for i in range(min(max_results, 3))
            ]
            
            logger.info(f"网络搜索: {query}")
            
            return {
                "query": query,
                "results": search_results,
                "count": len(search_results)
            }
        except Exception as e:
            logger.error(f"网络搜索失败: {e}")
            return {"error": str(e)}
    
    async def _file_operation_tool(self, operation: str, file_path: str, content: str = "", **kwargs) -> Dict[str, Any]:
        """文件操作工具"""
        try:
            import os
            
            if operation == "read":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"success": True, "content": content, "operation": "read"}
            
            elif operation == "write":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"success": True, "operation": "write", "file_path": file_path}
            
            elif operation == "exists":
                exists = os.path.exists(file_path)
                return {"success": True, "exists": exists, "file_path": file_path}
            
            else:
                return {"error": f"不支持的文件操作: {operation}"}
                
        except Exception as e:
            logger.error(f"文件操作失败: {e}")
            return {"error": str(e)}
    
    async def _database_query_tool(self, query: str, query_type: str = "select", **kwargs) -> Dict[str, Any]:
        """数据库查询工具"""
        try:
            from ..core.database import db_manager
            
            with db_manager.get_session() as session:
                if query_type == "select":
                    result = session.execute(query).fetchall()
                    return {
                        "success": True,
                        "result": [dict(row) for row in result],
                        "count": len(result)
                    }
                else:
                    session.execute(query)
                    session.commit()
                    return {"success": True, "operation": query_type}
                    
        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
            return {"error": str(e)}
    
    def get_tool_performance_report(self) -> Dict[str, Any]:
        """获取工具性能报告"""
        report = {
            "total_tools": len(self.tools),
            "tool_performance": {},
            "summary": {
                "most_used": None,
                "most_reliable": None,
                "fastest": None,
                "slowest": None
            }
        }
        
        if not self.tool_performance:
            return report
        
        # 分析性能数据
        most_used_count = 0
        most_reliable_rate = 0
        fastest_time = float('inf')
        slowest_time = 0
        
        for tool_name, perf in self.tool_performance.items():
            report["tool_performance"][tool_name] = perf
            
            # 找出最常用的工具
            if perf["total_executions"] > most_used_count:
                most_used_count = perf["total_executions"]
                report["summary"]["most_used"] = tool_name
            
            # 找出最可靠的工具
            if perf["success_rate"] > most_reliable_rate:
                most_reliable_rate = perf["success_rate"]
                report["summary"]["most_reliable"] = tool_name
            
            # 找出最快的工具
            if perf["avg_execution_time"] < fastest_time:
                fastest_time = perf["avg_execution_time"]
                report["summary"]["fastest"] = tool_name
            
            # 找出最慢的工具
            if perf["avg_execution_time"] > slowest_time:
                slowest_time = perf["avg_execution_time"]
                report["summary"]["slowest"] = tool_name
        
        return report
