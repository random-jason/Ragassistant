
# -*- coding: utf-8 -*-
"""
智能预警系统
支持多种预警规则、实时监控和智能分析
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from ..core.database import db_manager
from ..core.models import WorkOrder, Conversation, Analytics, Alert

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"          # 信息
    WARNING = "warning"    # 警告
    ERROR = "error"        # 错误
    CRITICAL = "critical"  # 严重

class AlertType(Enum):
    """预警类型"""
    PERFORMANCE = "performance"      # 性能预警
    QUALITY = "quality"             # 质量预警
    VOLUME = "volume"               # 量级预警
    SYSTEM = "system"               # 系统预警
    BUSINESS = "business"           # 业务预警

@dataclass
class AlertRule:
    """预警规则"""
    name: str
    description: str
    alert_type: AlertType
    level: AlertLevel
    threshold: float
    condition: str  # 条件表达式
    enabled: bool = True
    check_interval: int = 300  # 检查间隔（秒）
    last_check: Optional[datetime] = None
    cooldown: int = 3600  # 冷却时间（秒）

class AlertSystem:
    """智能预警系统"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.alert_history = []
        self.active_alerts = {}
        
    def _initialize_rules(self) -> Dict[str, AlertRule]:
        """初始化预警规则"""
        rules = {}
        
        # 性能预警规则
        rules["low_satisfaction"] = AlertRule(
            name="满意度预警",
            description="用户满意度低于阈值",
            alert_type=AlertType.QUALITY,
            level=AlertLevel.WARNING,
            threshold=0.6,
            condition="satisfaction_avg < threshold",
            check_interval=1800  # 30分钟
        )
        
        rules["high_resolution_time"] = AlertRule(
            name="解决时间预警",
            description="平均解决时间过长",
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING,
            threshold=24,  # 24小时
            condition="avg_resolution_time > threshold",
            check_interval=3600  # 1小时
        )
        
        rules["low_knowledge_hit_rate"] = AlertRule(
            name="知识库命中率预警",
            description="知识库命中率过低",
            alert_type=AlertType.QUALITY,
            level=AlertLevel.WARNING,
            threshold=0.5,
            condition="knowledge_hit_rate < threshold",
            check_interval=1800  # 30分钟
        )
        
        rules["high_error_rate"] = AlertRule(
            name="错误率预警",
            description="系统错误率过高",
            alert_type=AlertType.SYSTEM,
            level=AlertLevel.ERROR,
            threshold=0.1,
            condition="error_rate > threshold",
            check_interval=300  # 5分钟
        )
        
        rules["high_volume"] = AlertRule(
            name="工单量预警",
            description="工单量异常增长",
            alert_type=AlertType.VOLUME,
            level=AlertLevel.INFO,
            threshold=50,  # 每小时50个工单
            condition="hourly_orders > threshold",
            check_interval=600  # 10分钟
        )
        
        rules["low_response_time"] = AlertRule(
            name="响应时间预警",
            description="系统响应时间过长",
            alert_type=AlertType.PERFORMANCE,
            level=AlertLevel.WARNING,
            threshold=5.0,  # 5秒
            condition="avg_response_time > threshold",
            check_interval=300  # 5分钟
        )
        
        rules["memory_usage"] = AlertRule(
            name="内存使用预警",
            description="系统内存使用率过高",
            alert_type=AlertType.SYSTEM,
            level=AlertLevel.WARNING,
            threshold=80.0,  # 80%
            condition="memory_usage > threshold",
            check_interval=300  # 5分钟
        )
        
        rules["conversation_drop"] = AlertRule(
            name="对话中断预警",
            description="用户对话中断率过高",
            alert_type=AlertType.QUALITY,
            level=AlertLevel.WARNING,
            threshold=0.3,  # 30%
            condition="conversation_drop_rate > threshold",
            check_interval=1800  # 30分钟
        )
        
        return rules
    
    def check_all_rules(self) -> List[Dict[str, Any]]:
        """检查所有预警规则"""
        triggered_alerts = []
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            # 检查冷却时间
            if rule.last_check and (datetime.now() - rule.last_check).seconds < rule.cooldown:
                continue
            
            try:
                # 获取相关数据
                data = self._get_rule_data(rule_name)
                
                # 评估规则条件
                if self._evaluate_rule(rule, data):
                    alert = self._create_alert(rule, data)
                    triggered_alerts.append(alert)
                    
                    # 更新规则状态
                    rule.last_check = datetime.now()
                    
            except Exception as e:
                logger.error(f"检查规则 {rule_name} 失败: {e}")
                # 如果规则检查失败，也可以考虑生成一个系统级别的预警
                system_alert = {
                    "rule_name": f"系统预警 - 规则检查失败: {rule_name}",
                    "alert_type": AlertType.SYSTEM.value,
                    "level": AlertLevel.ERROR.value,
                    "message": f"规则 \'{rule_name}\' 检查失败: {e}",
                    "data": {"error": str(e)},
                    "timestamp": datetime.now().isoformat(),
                    "rule_id": "system_rule_check_failure"
                }
                self._save_alert(system_alert) # 保存系统预警
        
        return triggered_alerts
    
    def _get_rule_data(self, rule_name: str) -> Dict[str, Any]:
        """获取规则相关数据"""
        data = {}
        
        try:
            with db_manager.get_session() as session:
                # 获取最近24小时的数据
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                # 工单数据
                work_orders = session.query(WorkOrder).filter(
                    WorkOrder.created_at >= start_time,
                    WorkOrder.created_at <= end_time
                ).all()
                
                # 对话数据
                conversations = session.query(Conversation).filter(
                    Conversation.timestamp >= start_time,
                    Conversation.timestamp <= end_time
                ).all()
                
                # 计算基础指标
                total_orders = len(work_orders)
                resolved_orders = len([wo for wo in work_orders if wo.status == "resolved"])
                
                # 满意度
                satisfaction_scores = [wo.satisfaction_score for wo in work_orders if wo.satisfaction_score]
                data["satisfaction_avg"] = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
                
                # 解决时间
                resolution_times = []
                for wo in work_orders:
                    if wo.status == "resolved" and wo.updated_at:
                        resolution_time = (wo.updated_at - wo.created_at).total_seconds() / 3600
                        resolution_times.append(resolution_time)
                data["avg_resolution_time"] = sum(resolution_times) / len(resolution_times) if resolution_times else 0
                
                # 知识库命中率
                knowledge_hits = len([c for c in conversations if c.knowledge_used])
                data["knowledge_hit_rate"] = knowledge_hits / len(conversations) if conversations else 0
                
                # 错误率
                error_conversations = len([c for c in conversations if "error" in c.assistant_response.lower()])
                data["error_rate"] = error_conversations / len(conversations) if conversations else 0
                
                # 工单量
                data["hourly_orders"] = total_orders / 24
                
                # 响应时间
                response_times = []
                for c in conversations:
                    if c.response_time:
                        response_times.append(c.response_time)
                data["avg_response_time"] = sum(response_times) / len(response_times) if response_times else 0
                
                # 内存使用
                from ..utils.helpers import get_memory_usage
                memory_info = get_memory_usage()
                data["memory_usage"] = memory_info.get("percent", 0) * 100
                
                # 对话中断率
                total_conversations = len(conversations)
                dropped_conversations = len([c for c in conversations if c.user_message and not c.assistant_response])
                data["conversation_drop_rate"] = dropped_conversations / total_conversations if total_conversations else 0
                
        except Exception as e:
            logger.error(f"获取规则数据失败: {e}")
            # 重新抛出异常，让上层调用者决定如何处理
            raise
        
        return data
    
    def _evaluate_rule(self, rule: AlertRule, data: Dict[str, Any]) -> bool:
        """评估规则条件"""
        try:
            # 简单的条件评估
            if rule.condition == "satisfaction_avg < threshold":
                return data.get("satisfaction_avg", 0) < rule.threshold
            elif rule.condition == "avg_resolution_time > threshold":
                return data.get("avg_resolution_time", 0) > rule.threshold
            elif rule.condition == "knowledge_hit_rate < threshold":
                return data.get("knowledge_hit_rate", 0) < rule.threshold
            elif rule.condition == "error_rate > threshold":
                return data.get("error_rate", 0) > rule.threshold
            elif rule.condition == "hourly_orders > threshold":
                return data.get("hourly_orders", 0) > rule.threshold
            elif rule.condition == "avg_response_time > threshold":
                return data.get("avg_response_time", 0) > rule.threshold
            elif rule.condition == "memory_usage > threshold":
                return data.get("memory_usage", 0) > rule.threshold
            elif rule.condition == "conversation_drop_rate > threshold":
                return data.get("conversation_drop_rate", 0) > rule.threshold
            
            return False
        except Exception as e:
            logger.error(f"评估规则条件失败: {e}")
            return False
    
    def _create_alert(self, rule: AlertRule, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建预警"""
        alert = {
            "rule_name": rule.name,
            "alert_type": rule.alert_type.value,
            "level": rule.level.value,
            "message": self._generate_alert_message(rule, data),
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "rule_id": rule.name
        }
        
        # 保存到数据库
        self._save_alert(alert)
        
        # 添加到活跃预警
        self.active_alerts[rule.name] = alert
        
        return alert
    
    def _generate_alert_message(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """生成预警消息"""
        if rule.name == "满意度预警":
            return f"用户满意度较低: {data.get('satisfaction_avg', 0):.2f} (阈值: {rule.threshold})"
        elif rule.name == "解决时间预警":
            return f"平均解决时间过长: {data.get('avg_resolution_time', 0):.1f}小时 (阈值: {rule.threshold}小时)"
        elif rule.name == "知识库命中率预警":
            return f"知识库命中率较低: {data.get('knowledge_hit_rate', 0):.2f} (阈值: {rule.threshold})"
        elif rule.name == "错误率预警":
            return f"系统错误率过高: {data.get('error_rate', 0):.2f} (阈值: {rule.threshold})"
        elif rule.name == "工单量预警":
            return f"工单量异常增长: {data.get('hourly_orders', 0):.1f}个/小时 (阈值: {rule.threshold}个/小时)"
        elif rule.name == "响应时间预警":
            return f"系统响应时间过长: {data.get('avg_response_time', 0):.2f}秒 (阈值: {rule.threshold}秒)"
        elif rule.name == "内存使用预警":
            return f"系统内存使用率过高: {data.get('memory_usage', 0):.1f}% (阈值: {rule.threshold}%)"
        elif rule.name == "对话中断预警":
            return f"用户对话中断率过高: {data.get('conversation_drop_rate', 0):.2f} (阈值: {rule.threshold})"
        else:
            return f"触发预警: {rule.name}"
    
    def _save_alert(self, alert: Dict[str, Any]) -> None:
        """保存预警到数据库"""
        try:
            with db_manager.get_session() as session:
                db_alert = Alert(
                    rule_name=alert["rule_name"],
                    alert_type=alert["alert_type"],
                    level=alert["level"],
                    message=alert["message"],
                    data=json.dumps(alert["data"], ensure_ascii=False),
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(db_alert)
                session.commit()
                
        except Exception as e:
            logger.error(f"保存预警失败: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃预警"""
        try:
            with db_manager.get_session() as session:
                alerts = session.query(Alert).filter(
                    Alert.is_active == True
                ).order_by(Alert.created_at.desc()).all()
                
                return [{
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "alert_type": alert.alert_type,
                    "level": alert.level,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat(),
                    "data": json.loads(alert.data) if alert.data else {}
                } for alert in alerts]
                
        except Exception as e:
            logger.error(f"获取活跃预警失败: {e}")
            return []
    
    def resolve_alert(self, alert_id: int) -> bool:
        """解决预警"""
        try:
            with db_manager.get_session() as session:
                alert = session.query(Alert).filter(Alert.id == alert_id).first()
                if alert:
                    alert.is_active = False
                    alert.resolved_at = datetime.now()
                    session.commit()
                    return True
            return False
        except Exception as e:
            logger.error(f"解决预警失败: {e}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取预警统计"""
        try:
            with db_manager.get_session() as session:
                total_alerts = session.query(Alert).count()
                active_alerts = session.query(Alert).filter(Alert.is_active == True).count()
                
                # 按级别统计
                level_stats = {}
                for level in AlertLevel:
                    count = session.query(Alert).filter(Alert.level == level.value).count()
                    level_stats[level.value] = count
                
                # 按类型统计
                type_stats = {}
                for alert_type in AlertType:
                    count = session.query(Alert).filter(Alert.alert_type == alert_type.value).count()
                    type_stats[alert_type.value] = count
                
                return {
                    "total_alerts": total_alerts,
                    "active_alerts": active_alerts,
                    "level_distribution": level_stats,
                    "type_distribution": type_stats
                }
                
        except Exception as e:
            logger.error(f"获取预警统计失败: {e}")
            return {}
    
    def add_custom_rule(self, rule: AlertRule) -> bool:
        """添加自定义规则"""
        try:
            self.rules[rule.name] = rule
            logger.info(f"添加自定义规则: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加自定义规则失败: {e}")
            return False
    
    def update_rule(self, rule_name: str, **kwargs) -> bool:
        """更新规则"""
        try:
            if rule_name in self.rules:
                rule = self.rules[rule_name]
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"更新规则: {rule_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新规则失败: {e}")
            return False
    
    def delete_rule(self, rule_name: str) -> bool:
        """删除规则"""
        try:
            if rule_name in self.rules:
                del self.rules[rule_name]
                logger.info(f"删除规则: {rule_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            return False
