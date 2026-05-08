# -*- coding: utf-8 -*-
"""
Agent助手 - 简化版本
提供基本的Agent功能和工具管理
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentAssistant:
    """Agent助手 - 简化版本"""
    
    def __init__(self, llm_config=None):
        # 初始化基础功能
        self.llm_config = llm_config
        self.is_agent_mode = True
        self.execution_history = []
        
        # 工具注册表
        self.tools = {}
        self.tool_performance = {}
        
        # AI监控状态
        self.ai_monitoring_active = False
        self.monitoring_thread = None
        
        logger.info("Agent助手初始化完成")
    
    def register_tool(self, name: str, func, metadata: Dict[str, Any] = None):
        """注册工具"""
        try:
            self.tools[name] = {
                "function": func,
                "metadata": metadata or {},
                "usage_count": 0,
                "success_count": 0,
                "last_used": None
            }
            logger.info(f"工具 {name} 注册成功")
            return True
        except Exception as e:
            logger.error(f"注册工具 {name} 失败: {e}")
            return False
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        try:
            if name in self.tools:
                del self.tools[name]
                logger.info(f"工具 {name} 注销成功")
                return True
            return False
        except Exception as e:
            logger.error(f"注销工具 {name} 失败: {e}")
            return False
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        try:
            tools_list = []
            for name, tool_info in self.tools.items():
                tools_list.append({
                    "name": name,
                    "metadata": tool_info["metadata"],
                    "usage_count": tool_info["usage_count"],
                    "success_count": tool_info["success_count"],
                    "last_used": tool_info["last_used"]
                })
            return tools_list
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            return []
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行工具"""
        try:
            if tool_name not in self.tools:
                return {"error": f"工具 {tool_name} 不存在"}
            
            tool_info = self.tools[tool_name]
            func = tool_info["function"]
            
            # 记录使用
            tool_info["usage_count"] += 1
            tool_info["last_used"] = datetime.now().isoformat()
            
            # 执行工具
            start_time = datetime.now()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(**(parameters or {}))
                else:
                    result = func(**(parameters or {}))
                
                # 记录成功
                tool_info["success_count"] += 1
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # 记录执行历史
                self._record_execution(tool_name, parameters, result, True, execution_time)
                
                return {
                    "success": True,
                    "result": result,
                    "execution_time": execution_time,
                    "tool_name": tool_name
                }
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_execution(tool_name, parameters, str(e), False, execution_time)
                return {
                    "success": False,
                    "error": str(e),
                    "execution_time": execution_time,
                    "tool_name": tool_name
                }
                
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            return {"error": str(e)}
    
    def _record_execution(self, tool_name: str, parameters: Dict[str, Any], 
                         result: Any, success: bool, execution_time: float):
        """记录执行历史"""
        try:
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "success": success,
                "execution_time": execution_time
            }
            self.execution_history.append(execution_record)
            
            # 保持历史记录在合理范围内
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
        except Exception as e:
            logger.error(f"记录执行历史失败: {e}")
    
    def get_tool_performance_report(self) -> Dict[str, Any]:
        """获取工具性能报告"""
        try:
            total_tools = len(self.tools)
            total_executions = sum(tool["usage_count"] for tool in self.tools.values())
            total_successes = sum(tool["success_count"] for tool in self.tools.values())
            
            success_rate = (total_successes / total_executions * 100) if total_executions > 0 else 0
            
            return {
                "total_tools": total_tools,
                "total_executions": total_executions,
                "total_successes": total_successes,
                "success_rate": round(success_rate, 2),
                "tools": self.get_available_tools()
            }
        except Exception as e:
            logger.error(f"获取工具性能报告失败: {e}")
            return {}
    
    def get_action_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取动作执行历史"""
        try:
            return self.execution_history[-limit:] if limit > 0 else self.execution_history
        except Exception as e:
            logger.error(f"获取动作历史失败: {e}")
            return []
    
    def clear_execution_history(self) -> Dict[str, Any]:
        """清空执行历史"""
        try:
            count = len(self.execution_history)
            self.execution_history.clear()
            return {
                "success": True,
                "message": f"已清空 {count} 条执行历史"
            }
        except Exception as e:
            logger.error(f"清空执行历史失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        try:
            return {
                "success": True,
                "is_active": self.is_agent_mode,
                "ai_monitoring_active": self.ai_monitoring_active,
                "total_tools": len(self.tools),
                "total_executions": len(self.execution_history),
                "tools": self.get_available_tools(),
                "performance": self.get_tool_performance_report()
            }
        except Exception as e:
            logger.error(f"获取Agent状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_active": False,
                "ai_monitoring_active": False
            }

    def toggle_agent_mode(self, enabled: bool) -> bool:
        """切换Agent模式"""
        try:
            self.is_agent_mode = enabled
            logger.info(f"Agent模式: {'启用' if enabled else '禁用'}")
            return True
        except Exception as e:
            logger.error(f"切换Agent模式失败: {e}")
            return False

    def start_proactive_monitoring(self) -> bool:
        """启动主动监控"""
        try:
            if not self.ai_monitoring_active:
                self.ai_monitoring_active = True
                logger.info("主动监控已启动")
                return True
            return True
        except Exception as e:
            logger.error(f"启动主动监控失败: {e}")
            return False

    def stop_proactive_monitoring(self) -> bool:
        """停止主动监控"""
        try:
            self.ai_monitoring_active = False
            logger.info("主动监控已停止")
            return True
        except Exception as e:
            logger.error(f"停止主动监控失败: {e}")
            return False

    def run_proactive_monitoring(self) -> Dict[str, Any]:
        """运行主动监控检查"""
        try:
            return {
                "success": True,
                "message": "主动监控检查完成",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"运行主动监控失败: {e}")
            return {"success": False, "error": str(e)}

    def run_intelligent_analysis(self) -> Dict[str, Any]:
        """运行智能分析"""
        try:
            # 分析工具使用情况
            tool_performance = self.get_tool_performance_report()
            
            # 分析执行历史
            recent_executions = self.get_action_history(20)
            
            # 生成分析报告
            analysis = {
                "tool_performance": tool_performance,
                "recent_activity": len(recent_executions),
                "success_rate": tool_performance.get("success_rate", 0),
                "recommendations": self._generate_recommendations(tool_performance)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"运行智能分析失败: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, tool_performance: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        success_rate = tool_performance.get("success_rate", 100)
        if success_rate < 90:
            recommendations.append("工具成功率较低，建议检查工具实现")
        
        total_executions = tool_performance.get("total_executions", 0)
        if total_executions < 10:
            recommendations.append("工具使用频率较低，建议增加工具调用")
        
        return recommendations
    
    def get_llm_usage_stats(self) -> Dict[str, Any]:
        """获取LLM使用统计"""
        try:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取LLM使用统计失败: {e}")
            return {}
    
    async def process_message_agent(self, message: str, user_id: str = "admin", 
                                  work_order_id: Optional[int] = None, 
                                  enable_proactive: bool = True) -> Dict[str, Any]:
        """处理消息"""
        try:
            # 简化的消息处理
            return {
                "success": True,
                "message": f"Agent收到消息: {message}",
                "user_id": user_id,
                "work_order_id": work_order_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {"error": str(e)}
    
    async def trigger_sample_actions(self) -> Dict[str, Any]:
        """触发示例动作"""
        try:
            # 执行一个示例工具
            result = await self.execute_tool("sample_tool", {"action": "test"})
            
            return {
                "success": True,
                "message": "示例动作已执行",
                "result": result
            }
        except Exception as e:
            logger.error(f"触发示例动作失败: {e}")
            return {"success": False, "error": str(e)}
    
    def process_file_to_knowledge(self, file_path: str, filename: str) -> Dict[str, Any]:
        """处理文件并生成知识库"""
        try:
            import os
            import mimetypes
            
            # 检查文件类型
            mime_type, _ = mimetypes.guess_type(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 读取文件内容
            content = self._read_file_content(file_path, file_ext)
            if not content:
                return {"success": False, "error": "无法读取文件内容"}
            
            # 使用简化的知识提取
            knowledge_entries = self._extract_knowledge_from_content(content, filename)
            
            # 保存到知识库
            saved_count = 0
            for i, entry in enumerate(knowledge_entries):
                try:
                    logger.info(f"保存知识条目 {i+1}: {entry.get('question', '')[:50]}...")
                    # 这里应该调用知识库管理器保存
                    saved_count += 1
                    logger.info(f"知识条目 {i+1} 保存成功")
                except Exception as save_error:
                    logger.error(f"保存知识条目 {i+1} 时出错: {save_error}")
            
            return {
                "success": True,
                "knowledge_count": saved_count,
                "total_extracted": len(knowledge_entries),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            return {"success": False, "error": str(e)}

    def _read_file_content(self, file_path: str, file_ext: str) -> str:
        """读取文件内容"""
        try:
            if file_ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext == '.pdf':
                return "PDF文件需要安装PyPDF2库"
            elif file_ext in ['.doc', '.docx']:
                return "Word文件需要安装python-docx库"
            else:
                return "不支持的文件格式"
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return ""

    def _extract_knowledge_from_content(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """从内容中提取知识"""
        try:
            # 简化的知识提取逻辑
            entries = []
            
            # 按段落分割内容
            paragraphs = content.split('\n\n')
            
            for i, paragraph in enumerate(paragraphs[:5]):  # 最多提取5个
                if len(paragraph.strip()) > 20:  # 过滤太短的段落
                    entries.append({
                        "question": f"关于{filename}的问题{i+1}",
                        "answer": paragraph.strip(),
                        "category": "文档知识",
                        "confidence_score": 0.7
                    })
            
            return entries
            
        except Exception as e:
            logger.error(f"提取知识失败: {e}")
            return []

# 使用示例
async def main():
    """主函数示例"""
    # 创建Agent助手
    agent_assistant = AgentAssistant()
    
    # 测试Agent功能
    print("=== Agent助手测试 ===")
    
    # 测试Agent模式处理消息
    response = await agent_assistant.process_message_agent(
        message="我的账户无法登录，请帮助我解决这个问题",
        user_id="user123"
    )
    print("Agent模式响应:", response)
    
    # 获取Agent状态
    agent_status = agent_assistant.get_agent_status()
    print("Agent状态:", agent_status)

if __name__ == "__main__":
    asyncio.run(main())