
# -*- coding: utf-8 -*-
"""
监控服务
实时监控系统状态，执行预警检查
"""

import logging
import threading
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .alert_system import AlertSystem, AlertRule, AlertLevel, AlertType

logger = logging.getLogger(__name__)

class MonitorService:
    """监控服务"""
    
    def __init__(self):
        self.alert_system = AlertSystem()
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 60  # 检查间隔（秒）
        
    def start(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("监控服务已在运行")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("监控服务已启动")
        
    def stop(self):
        """停止监控服务"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("监控服务已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 执行预警检查
                triggered_alerts = self.alert_system.check_all_rules()
                
                if triggered_alerts:
                    logger.info(f"触发 {len(triggered_alerts)} 个预警")
                    for alert in triggered_alerts:
                        self._handle_alert(alert)
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(10)  # 异常时等待10秒再继续
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """处理预警"""
        try:
            # 记录预警
            logger.warning(f"预警触发: {alert['message']}")
            
            # 根据预警级别采取不同措施
            if alert['level'] == 'critical':
                self._handle_critical_alert(alert)
            elif alert['level'] == 'error':
                self._handle_error_alert(alert)
            elif alert['level'] == 'warning':
                self._handle_warning_alert(alert)
            else:
                self._handle_info_alert(alert)
                
        except Exception as e:
            logger.error(f"处理预警失败: {e}")
    
    def _handle_critical_alert(self, alert: Dict[str, Any]):
        """处理严重预警"""
        # 发送紧急通知
        self._send_notification(alert, "紧急")
        
        # 记录到日志
        logger.critical(f"严重预警: {alert['message']}")
        
        # 可以添加自动恢复措施
        self._attempt_auto_recovery(alert)
    
    def _handle_error_alert(self, alert: Dict[str, Any]):
        """处理错误预警"""
        # 发送错误通知
        self._send_notification(alert, "错误")
        
        # 记录到日志
        logger.error(f"错误预警: {alert['message']}")
    
    def _handle_warning_alert(self, alert: Dict[str, Any]):
        """处理警告预警"""
        # 发送警告通知
        self._send_notification(alert, "警告")
        
        # 记录到日志
        logger.warning(f"警告预警: {alert['message']}")
    
    def _handle_info_alert(self, alert: Dict[str, Any]):
        """处理信息预警"""
        # 记录到日志
        logger.info(f"信息预警: {alert['message']}")
    
    def _send_notification(self, alert: Dict[str, Any], level: str):
        """发送通知"""
        notification = {
            "level": level,
            "message": alert['message'],
            "timestamp": alert['timestamp'],
            "rule_name": alert['rule_name']
        }
        
        # 记录通知
        logger.info(f"发送通知: {notification}")
        
        # 发送飞书通知
        if self._should_send_feishu_notification(level):
            self._send_feishu_notification(notification)
    
    def _should_send_feishu_notification(self, level: str) -> bool:
        """判断是否应该发送飞书通知"""
        # 根据预警级别决定是否发送（紧急和错误级别发送）
        return level in ['紧急', '错误']
    
    def _send_feishu_notification(self, notification: Dict[str, Any]):
        """发送飞书通知"""
        try:
            from src.integrations.feishu_client import FeishuClient
            
            # 检查飞书配置是否启用
            try:
                from src.config.unified_config import get_config
                config = get_config()
                if config.feishu.status != "active":
                    logger.info("飞书配置未启用，跳过通知发送")
                    return
            except Exception as e:
                logger.warning(f"获取飞书配置失败: {e}")
                return
            
            # 创建飞书客户端并发送通知
            client = FeishuClient()
            message = self._format_notification_message(notification)
            
            # 使用飞书的消息卡片格式
            result = client.send_text_message(message)
            
            if result:
                logger.info("飞书通知发送成功")
            else:
                logger.warning("飞书通知发送失败")
                
        except ImportError:
            logger.warning("飞书客户端未找到，跳过通知发送")
        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")
    
    def _format_notification_message(self, notification: Dict[str, Any]) -> str:
        """格式化通知消息"""
        return f"""【系统预警】
级别：{notification['level']}
规则：{notification['rule_name']}
消息：{notification['message']}
时间：{notification['timestamp']}
"""
    
    def _attempt_auto_recovery(self, alert: Dict[str, Any]):
        """尝试自动恢复"""
        try:
            rule_name = alert['rule_name']
            
            if rule_name == "内存使用预警":
                # 尝试清理内存
                self._cleanup_memory()
            elif rule_name == "错误率预警":
                # 尝试重启相关服务
                self._restart_services()
            elif rule_name == "响应时间预警":
                # 尝试优化性能
                self._optimize_performance()
                
        except Exception as e:
            logger.error(f"自动恢复失败: {e}")
    
    def _cleanup_memory(self):
        """清理内存"""
        try:
            import gc
            gc.collect()
            logger.info("执行内存清理")
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
    
    def _restart_services(self):
        """重启服务"""
        try:
            # 这里可以实现重启相关服务的逻辑
            logger.info("尝试重启服务")
        except Exception as e:
            logger.error(f"重启服务失败: {e}")
    
    def _optimize_performance(self):
        """优化性能"""
        try:
            # 这里可以实现性能优化的逻辑
            logger.info("尝试优化性能")
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 获取活跃预警
            active_alerts = self.alert_system.get_active_alerts()
            
            # 获取预警统计
            alert_stats = self.alert_system.get_alert_statistics()
            
            # 计算健康分数
            health_score = self._calculate_health_score(active_alerts, alert_stats)
            
            return {
                "health_score": health_score,
                "status": self._get_health_status(health_score),
                "active_alerts": len(active_alerts),
                "alert_statistics": alert_stats,
                "monitor_status": "running" if self.is_running else "stopped",
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            return {"error": str(e)}
    
    def _calculate_health_score(self, active_alerts: List[Dict[str, Any]], alert_stats: Dict[str, Any]) -> float:
        """计算健康分数"""
        try:
            base_score = 100.0
            
            # 根据活跃预警扣分
            for alert in active_alerts:
                if alert['level'] == 'critical':
                    base_score -= 20
                elif alert['level'] == 'error':
                    base_score -= 10
                elif alert['level'] == 'warning':
                    base_score -= 5
                else:
                    base_score -= 1
            
            # 确保分数在0-100之间
            return max(0, min(100, base_score))
            
        except Exception as e:
            logger.error(f"计算健康分数失败: {e}")
            return 50.0
    
    def _get_health_status(self, health_score: float) -> str:
        """获取健康状态"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 70:
            return "good"
        elif health_score >= 50:
            return "fair"
        elif health_score >= 30:
            return "poor"
        else:
            return "critical"
    
    def add_custom_rule(self, rule: AlertRule) -> bool:
        """添加自定义规则"""
        return self.alert_system.add_custom_rule(rule)
    
    def update_rule(self, rule_name: str, **kwargs) -> bool:
        """更新规则"""
        return self.alert_system.update_rule(rule_name, **kwargs)
    
    def delete_rule(self, rule_name: str) -> bool:
        """删除规则"""
        return self.alert_system.delete_rule(rule_name)
    
    def get_rules(self) -> Dict[str, Any]:
        """获取所有规则"""
        return {
            name: {
                "name": rule.name,
                "description": rule.description,
                "alert_type": rule.alert_type.value,
                "level": rule.level.value,
                "threshold": rule.threshold,
                "enabled": rule.enabled,
                "check_interval": rule.check_interval,
                "cooldown": rule.cooldown
            }
            for name, rule in self.alert_system.rules.items()
        }
