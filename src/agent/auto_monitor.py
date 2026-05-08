
# -*- coding: utf-8 -*-
"""
自动监控服务
实现Agent的主动调用功能
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class AutoMonitorService:
    """自动监控服务"""
    
    def __init__(self, agent_assistant):
        self.agent_assistant = agent_assistant
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 300  # 5分钟检查一次
        self.last_check_time = None
        self.monitoring_stats = {
            "total_checks": 0,
            "proactive_actions": 0,
            "last_action_time": None,
            "error_count": 0
        }
        
    def start_auto_monitoring(self) -> bool:
        """启动自动监控"""
        try:
            if self.is_running:
                logger.warning("自动监控已在运行中")
                return True
                
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("自动监控服务已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动自动监控失败: {e}")
            return False
    
    def stop_auto_monitoring(self) -> bool:
        """停止自动监控"""
        try:
            self.is_running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            logger.info("自动监控服务已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止自动监控失败: {e}")
            return False
    
    def _monitoring_loop(self):
        """监控循环"""
        logger.info("自动监控循环已启动")
        
        while self.is_running:
            try:
                # 执行监控检查
                self._perform_monitoring_check()
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                self.monitoring_stats["error_count"] += 1
                time.sleep(60)  # 出错后等待1分钟
    
    def _perform_monitoring_check(self):
        """执行监控检查"""
        try:
            self.monitoring_stats["total_checks"] += 1
            self.last_check_time = datetime.now()
            
            logger.info(f"执行第 {self.monitoring_stats['total_checks']} 次自动监控检查")
            
            # 1. 检查系统健康状态
            self._check_system_health()
            
            # 2. 检查预警状态
            self._check_alert_status()
            
            # 3. 检查工单积压
            self._check_workorder_backlog()
            
            # 4. 检查知识库质量
            self._check_knowledge_quality()
            
            # 5. 检查用户满意度
            self._check_user_satisfaction()
            
            # 6. 检查系统性能
            self._check_system_performance()
            
        except Exception as e:
            logger.error(f"执行监控检查失败: {e}")
            self.monitoring_stats["error_count"] += 1
    
    def _check_system_health(self):
        """检查系统健康状态"""
        try:
            health = self.agent_assistant.get_system_health()
            health_score = health.get("health_score", 1.0)
            
            if health_score < 0.7:
                self._trigger_proactive_action({
                    "type": "system_health_warning",
                    "priority": "high",
                    "description": f"系统健康分数较低: {health_score:.2f}",
                    "action": "建议立即检查系统状态",
                    "data": health
                })
                
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}")
    
    def _check_alert_status(self):
        """检查预警状态"""
        try:
            alerts = self.agent_assistant.get_active_alerts()
            alert_count = len(alerts) if isinstance(alerts, list) else 0
            
            if alert_count > 5:
                self._trigger_proactive_action({
                    "type": "alert_overflow",
                    "priority": "high",
                    "description": f"活跃预警数量过多: {alert_count}",
                    "action": "建议立即处理预警",
                    "data": {"alert_count": alert_count}
                })
                
        except Exception as e:
            logger.error(f"检查预警状态失败: {e}")
    
    def _check_workorder_backlog(self):
        """检查工单积压"""
        try:
            # 获取工单统计
            workorders = self.agent_assistant.get_workorders()
            if isinstance(workorders, list):
                open_count = len([w for w in workorders if w.get("status") == "open"])
                in_progress_count = len([w for w in workorders if w.get("status") == "in_progress"])
                total_pending = open_count + in_progress_count
                
                if total_pending > 10:
                    self._trigger_proactive_action({
                        "type": "workorder_backlog",
                        "priority": "medium",
                        "description": f"待处理工单过多: {total_pending}",
                        "action": "建议增加处理人员或优化流程",
                        "data": {
                            "open_count": open_count,
                            "in_progress_count": in_progress_count,
                            "total_pending": total_pending
                        }
                    })
                    
        except Exception as e:
            logger.error(f"检查工单积压失败: {e}")
    
    def _check_knowledge_quality(self):
        """检查知识库质量"""
        try:
            stats = self.agent_assistant.knowledge_manager.get_knowledge_stats()
            avg_confidence = stats.get("average_confidence", 0.8)
            total_entries = stats.get("total_entries", 0)
            
            if avg_confidence < 0.6:
                self._trigger_proactive_action({
                    "type": "knowledge_quality_low",
                    "priority": "medium",
                    "description": f"知识库平均置信度较低: {avg_confidence:.2f}",
                    "action": "建议更新和优化知识库内容",
                    "data": {"avg_confidence": avg_confidence, "total_entries": total_entries}
                })
                
        except Exception as e:
            logger.error(f"检查知识库质量失败: {e}")
    
    def _check_user_satisfaction(self):
        """检查用户满意度"""
        try:
            # 模拟检查用户满意度
            # 这里可以从数据库或API获取真实的满意度数据
            satisfaction_score = 0.75  # 模拟数据
            
            if satisfaction_score < 0.7:
                self._trigger_proactive_action({
                    "type": "low_satisfaction",
                    "priority": "high",
                    "description": f"用户满意度较低: {satisfaction_score:.2f}",
                    "action": "建议分析低满意度原因并改进服务",
                    "data": {"satisfaction_score": satisfaction_score}
                })
                
        except Exception as e:
            logger.error(f"检查用户满意度失败: {e}")
    
    def _check_system_performance(self):
        """检查系统性能"""
        try:
            # 模拟检查系统性能指标
            response_time = 1.2  # 模拟响应时间（秒）
            error_rate = 0.02  # 模拟错误率
            
            if response_time > 2.0:
                self._trigger_proactive_action({
                    "type": "slow_response",
                    "priority": "medium",
                    "description": f"系统响应时间过慢: {response_time:.2f}秒",
                    "action": "建议优化系统性能",
                    "data": {"response_time": response_time}
                })
            
            if error_rate > 0.05:
                self._trigger_proactive_action({
                    "type": "high_error_rate",
                    "priority": "high",
                    "description": f"系统错误率过高: {error_rate:.2%}",
                    "action": "建议立即检查系统错误",
                    "data": {"error_rate": error_rate}
                })
                
        except Exception as e:
            logger.error(f"检查系统性能失败: {e}")
    
    def _trigger_proactive_action(self, action_data: Dict[str, Any]):
        """触发主动行动"""
        try:
            self.monitoring_stats["proactive_actions"] += 1
            self.monitoring_stats["last_action_time"] = datetime.now()
            
            logger.info(f"触发主动行动: {action_data['type']} - {action_data['description']}")
            
            # 记录主动行动
            self._log_proactive_action(action_data)
            
            # 根据行动类型执行相应操作
            self._execute_proactive_action(action_data)
            
        except Exception as e:
            logger.error(f"触发主动行动失败: {e}")
    
    def _log_proactive_action(self, action_data: Dict[str, Any]):
        """记录主动行动"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action_type": action_data["type"],
                "priority": action_data["priority"],
                "description": action_data["description"],
                "action": action_data["action"],
                "data": action_data.get("data", {})
            }
            
            # 这里可以将日志保存到数据库或文件
            logger.info(f"主动行动记录: {json.dumps(log_entry, ensure_ascii=False)}")
            
        except Exception as e:
            logger.error(f"记录主动行动失败: {e}")
    
    def _execute_proactive_action(self, action_data: Dict[str, Any]):
        """执行主动行动"""
        try:
            action_type = action_data["type"]
            
            if action_type == "system_health_warning":
                self._handle_system_health_warning(action_data)
            elif action_type == "alert_overflow":
                self._handle_alert_overflow(action_data)
            elif action_type == "workorder_backlog":
                self._handle_workorder_backlog(action_data)
            elif action_type == "knowledge_quality_low":
                self._handle_knowledge_quality_low(action_data)
            elif action_type == "low_satisfaction":
                self._handle_low_satisfaction(action_data)
            elif action_type == "slow_response":
                self._handle_slow_response(action_data)
            elif action_type == "high_error_rate":
                self._handle_high_error_rate(action_data)
            else:
                logger.warning(f"未知的主动行动类型: {action_type}")
                
        except Exception as e:
            logger.error(f"执行主动行动失败: {e}")
    
    def _handle_system_health_warning(self, action_data: Dict[str, Any]):
        """处理系统健康警告"""
        logger.info("处理系统健康警告")
        # 这里可以实现具体的处理逻辑，如发送通知、重启服务等
    
    def _handle_alert_overflow(self, action_data: Dict[str, Any]):
        """处理预警溢出"""
        logger.info("处理预警溢出")
        # 这里可以实现具体的处理逻辑，如自动处理预警、发送通知等
    
    def _handle_workorder_backlog(self, action_data: Dict[str, Any]):
        """处理工单积压"""
        logger.info("处理工单积压")
        # 这里可以实现具体的处理逻辑，如自动分配工单、发送提醒等
    
    def _handle_knowledge_quality_low(self, action_data: Dict[str, Any]):
        """处理知识库质量低"""
        logger.info("处理知识库质量低")
        # 这里可以实现具体的处理逻辑，如自动更新知识库、发送提醒等
    
    def _handle_low_satisfaction(self, action_data: Dict[str, Any]):
        """处理低满意度"""
        logger.info("处理低满意度")
        # 这里可以实现具体的处理逻辑，如分析原因、发送通知等
    
    def _handle_slow_response(self, action_data: Dict[str, Any]):
        """处理响应慢"""
        logger.info("处理响应慢")
        # 这里可以实现具体的处理逻辑，如优化配置、发送通知等
    
    def _handle_high_error_rate(self, action_data: Dict[str, Any]):
        """处理高错误率"""
        logger.info("处理高错误率")
        # 这里可以实现具体的处理逻辑，如检查日志、发送通知等
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "stats": self.monitoring_stats
        }
    
    def update_check_interval(self, interval: int) -> bool:
        """更新检查间隔"""
        try:
            if interval < 60:  # 最少1分钟
                logger.warning("检查间隔不能少于60秒")
                return False
            
            self.check_interval = interval
            logger.info(f"检查间隔已更新为 {interval} 秒")
            return True
            
        except Exception as e:
            logger.error(f"更新检查间隔失败: {e}")
            return False
