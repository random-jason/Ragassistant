import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

from ..core.database import db_manager
from ..core.models import WorkOrder, Conversation, Analytics, Alert, KnowledgeEntry

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """分析统计管理器"""
    
    def __init__(self):
        self.alert_thresholds = {
            "low_satisfaction": 0.6,
            "high_resolution_time": 24,  # 小时
            "knowledge_hit_rate": 0.5,
            "error_rate": 0.1
        }
    
    def generate_daily_analytics(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """生成每日分析报告"""
        if date is None:
            date = datetime.now().date()
        
        try:
            with db_manager.get_session() as session:
                # 获取指定日期的工单数据
                start_time = datetime.combine(date, datetime.min.time())
                end_time = datetime.combine(date, datetime.max.time())
                
                work_orders = session.query(WorkOrder).filter(
                    WorkOrder.created_at >= start_time,
                    WorkOrder.created_at <= end_time
                ).all()
                
                if not work_orders:
                    return {"message": f"{date} 没有工单数据"}
                
                # 计算基础统计
                total_orders = len(work_orders)
                resolved_orders = len([wo for wo in work_orders if wo.status == "resolved"])
                
                # 平均解决时间
                resolution_times = []
                for wo in work_orders:
                    if wo.status == "resolved" and wo.updated_at:
                        resolution_time = (wo.updated_at - wo.created_at).total_seconds() / 3600
                        resolution_times.append(resolution_time)
                
                avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
                
                # 平均满意度
                satisfaction_scores = [wo.satisfaction_score for wo in work_orders if wo.satisfaction_score]
                satisfaction_avg = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
                
                # 知识库命中率
                conversations = session.query(Conversation).filter(
                    Conversation.timestamp >= start_time,
                    Conversation.timestamp <= end_time
                ).all()
                
                knowledge_hit_rate = self._calculate_knowledge_hit_rate(conversations)
                
                # 类别分布
                category_distribution = defaultdict(int)
                for wo in work_orders:
                    category_distribution[wo.category] += 1
                
                # 保存分析结果
                analytics = Analytics(
                    date=start_time,
                    total_orders=total_orders,
                    resolved_orders=resolved_orders,
                    avg_resolution_time=avg_resolution_time,
                    satisfaction_avg=satisfaction_avg,
                    knowledge_hit_rate=knowledge_hit_rate,
                    category_distribution=json.dumps(dict(category_distribution))
                )
                session.add(analytics)
                session.commit()
                
                # 检查预警条件
                self._check_alerts(
                    session,
                    satisfaction_avg,
                    avg_resolution_time,
                    knowledge_hit_rate,
                    total_orders
                )
                
                return {
                    "date": date.isoformat(),
                    "total_orders": total_orders,
                    "resolved_orders": resolved_orders,
                    "resolution_rate": resolved_orders / total_orders if total_orders > 0 else 0,
                    "avg_resolution_time_hours": round(avg_resolution_time, 2),
                    "satisfaction_avg": round(satisfaction_avg, 2),
                    "knowledge_hit_rate": round(knowledge_hit_rate, 2),
                    "category_distribution": dict(category_distribution)
                }
                
        except Exception as e:
            logger.error(f"生成每日分析报告失败: {e}")
            return {"error": f"生成失败: {str(e)}"}
    
    def _calculate_knowledge_hit_rate(self, conversations: List[Conversation]) -> float:
        """计算知识库命中率"""
        if not conversations:
            return 0.0
        
        hit_count = 0
        for conv in conversations:
            if conv.knowledge_used and conv.knowledge_used != "[]":
                hit_count += 1
        
        return hit_count / len(conversations)
    
    def _check_alerts(
        self,
        session,
        satisfaction_avg: float,
        avg_resolution_time: float,
        knowledge_hit_rate: float,
        total_orders: int
    ):
        """检查预警条件"""
        alerts = []
        
        # 满意度预警
        if satisfaction_avg < self.alert_thresholds["low_satisfaction"]:
            alerts.append({
                "type": "low_satisfaction",
                "message": f"客户满意度较低: {satisfaction_avg:.2f}",
                "severity": "high"
            })
        
        # 解决时间预警
        if avg_resolution_time > self.alert_thresholds["high_resolution_time"]:
            alerts.append({
                "type": "high_resolution_time",
                "message": f"平均解决时间过长: {avg_resolution_time:.2f}小时",
                "severity": "medium"
            })
        
        # 知识库命中率预警
        if knowledge_hit_rate < self.alert_thresholds["knowledge_hit_rate"]:
            alerts.append({
                "type": "low_knowledge_hit_rate",
                "message": f"知识库命中率较低: {knowledge_hit_rate:.2f}",
                "severity": "medium"
            })
        
        # 创建预警记录
        for alert_data in alerts:
            alert = Alert(
                rule_name=alert_data.get("rule_name", "系统预警"),
                alert_type=alert_data["type"],
                level=alert_data["severity"],
                severity=alert_data["severity"],
                message=alert_data["message"],
                is_active=True,
                created_at=datetime.now()
            )
            session.add(alert)
        
        session.commit()
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取分析摘要"""
        try:
            with db_manager.get_session() as session:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                analytics = session.query(Analytics).filter(
                    Analytics.date >= start_date,
                    Analytics.date <= end_date
                ).order_by(Analytics.date).all()
                
                if not analytics:
                    return {"message": f"最近{days}天没有分析数据"}
                
                # 计算汇总统计
                total_orders = sum(a.total_orders for a in analytics)
                total_resolved = sum(a.resolved_orders for a in analytics)
                avg_resolution_time = sum(a.avg_resolution_time for a in analytics) / len(analytics)
                avg_satisfaction = sum(a.satisfaction_avg for a in analytics) / len(analytics)
                avg_knowledge_hit_rate = sum(a.knowledge_hit_rate for a in analytics) / len(analytics)
                
                # 趋势分析
                trends = {
                    "orders_trend": [a.total_orders for a in analytics],
                    "satisfaction_trend": [a.satisfaction_avg for a in analytics],
                    "resolution_time_trend": [a.avg_resolution_time for a in analytics]
                }
                
                return {
                    "period": f"{days}天",
                    "total_orders": total_orders,
                    "total_resolved": total_resolved,
                    "resolution_rate": total_resolved / total_orders if total_orders > 0 else 0,
                    "avg_resolution_time_hours": round(avg_resolution_time, 2),
                    "avg_satisfaction": round(avg_satisfaction, 2),
                    "avg_knowledge_hit_rate": round(avg_knowledge_hit_rate, 2),
                    "trends": trends
                }
                
        except Exception as e:
            logger.error(f"获取分析摘要失败: {e}")
            return {"error": f"获取失败: {str(e)}"}
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃预警"""
        try:
            with db_manager.get_session() as session:
                alerts = session.query(Alert).filter(
                    Alert.is_active == True
                ).order_by(Alert.created_at.desc()).all()
                
                return [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "message": alert.message,
                        "severity": alert.level,
                        "created_at": alert.created_at.isoformat()
                    }
                    for alert in alerts
                ]
                
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
    
    def get_category_performance(self, days: int = 30) -> Dict[str, Any]:
        """获取类别性能分析"""
        try:
            with db_manager.get_session() as session:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                work_orders = session.query(WorkOrder).filter(
                    WorkOrder.created_at >= start_date,
                    WorkOrder.created_at <= end_date
                ).all()
                
                category_stats = defaultdict(lambda: {
                    "total": 0,
                    "resolved": 0,
                    "satisfaction_scores": [],
                    "resolution_times": []
                })
                
                for wo in work_orders:
                    category_stats[wo.category]["total"] += 1
                    if wo.status == "resolved":
                        category_stats[wo.category]["resolved"] += 1
                    
                    if wo.satisfaction_score:
                        category_stats[wo.category]["satisfaction_scores"].append(wo.satisfaction_score)
                    
                    if wo.status == "resolved" and wo.updated_at:
                        resolution_time = (wo.updated_at - wo.created_at).total_seconds() / 3600
                        category_stats[wo.category]["resolution_times"].append(resolution_time)
                
                # 计算性能指标
                performance = {}
                for category, stats in category_stats.items():
                    resolution_rate = stats["resolved"] / stats["total"] if stats["total"] > 0 else 0
                    avg_satisfaction = sum(stats["satisfaction_scores"]) / len(stats["satisfaction_scores"]) if stats["satisfaction_scores"] else 0
                    avg_resolution_time = sum(stats["resolution_times"]) / len(stats["resolution_times"]) if stats["resolution_times"] else 0
                    
                    performance[category] = {
                        "total_orders": stats["total"],
                        "resolution_rate": round(resolution_rate, 2),
                        "avg_satisfaction": round(avg_satisfaction, 2),
                        "avg_resolution_time_hours": round(avg_resolution_time, 2)
                    }
                
                return performance
                
        except Exception as e:
            logger.error(f"获取类别性能分析失败: {e}")
            return {}
