import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.unified_config import get_config
from src.utils.helpers import setup_logging
from src.core.database import db_manager
from src.core.llm_client import QwenClient
from src.knowledge_base.knowledge_manager import KnowledgeManager
from src.dialogue.dialogue_manager import DialogueManager
from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.alert_system import AlertSystem
from src.analytics.monitor_service import MonitorService
from src.analytics.token_monitor import TokenMonitor
from src.analytics.ai_success_monitor import AISuccessMonitor
from src.core.system_optimizer import SystemOptimizer
from src.core.models import WorkOrder, Alert

class Assistant:
    """主类"""
    
    def __init__(self):
        # 设置日志
        config = get_config()
        setup_logging(config.server.log_level)
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个管理器
        self.llm_client = QwenClient()
        self.knowledge_manager = KnowledgeManager()
        self.dialogue_manager = DialogueManager()
        self.analytics_manager = AnalyticsManager()
        self.alert_system = AlertSystem()
        self.monitor_service = MonitorService()
        self.token_monitor = TokenMonitor()
        self.ai_success_monitor = AISuccessMonitor()
        self.system_optimizer = SystemOptimizer()

    
    def test_system(self) -> Dict[str, Any]:
        """测试系统各个组件"""
        results = {
            "database": False,
            "llm_api": False,
            "knowledge_base": False,
            "overall": False
        }
        
        try:
            # 测试数据库连接
            if db_manager.test_connection():
                results["database"] = True
                self.logger.info("数据库连接测试成功")
            else:
                self.logger.error("数据库连接测试失败")
            
            # 测试LLM API连接
            if self.llm_client.test_connection():
                results["llm_api"] = True
                self.logger.info("LLM API连接测试成功")
            else:
                self.logger.error("LLM API连接测试失败")
            
            # 测试知识库
            knowledge_stats = self.knowledge_manager.get_knowledge_stats()
            if knowledge_stats:
                results["knowledge_base"] = True
                self.logger.info("知识库测试成功")
            else:
                self.logger.warning("知识库为空或测试失败")
            
            # 整体状态
            results["overall"] = all([results["database"], results["llm_api"]])
            
        except Exception as e:
            self.logger.error(f"系统测试失败: {e}")
        
        return results
    
    def process_message(self, message: str, user_id: str = None, work_order_id: int = None) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            result = self.dialogue_manager.process_user_message(
                user_message=message,
                user_id=user_id,
                work_order_id=work_order_id
            )
            
            if "error" in result:
                self.logger.error(f"处理消息失败: {result['error']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理消息异常: {e}")
            return {"error": f"处理异常: {str(e)}"}
    
    def create_work_order(self, title: str, description: str, category: str, priority: str = "medium") -> Dict[str, Any]:
        """创建工单"""
        try:
            result = self.dialogue_manager.create_work_order(
                title=title,
                description=description,
                category=category,
                priority=priority
            )
            
            if "error" in result:
                self.logger.error(f"创建工单失败: {result['error']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"创建工单异常: {e}")
            return {"error": f"创建异常: {str(e)}"}
    
    def update_work_order(self, work_order_id: int, **kwargs) -> bool:
        """更新工单"""
        try:
            return self.dialogue_manager.update_work_order(work_order_id, **kwargs)
        except Exception as e:
            self.logger.error(f"更新工单异常: {e}")
            return False
    
    def search_knowledge(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """搜索知识库"""
        try:
            results = self.knowledge_manager.search_knowledge(query, top_k)
            return {
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            self.logger.error(f"搜索知识库异常: {e}")
            return {"error": f"搜索异常: {str(e)}"}
    
    def add_knowledge(self, question: str, answer: str, category: str, confidence_score: float = 0.5) -> bool:
        """添加知识库条目"""
        try:
            return self.knowledge_manager.add_knowledge_entry(question, answer, category, confidence_score)
        except Exception as e:
            self.logger.error(f"添加知识库异常: {e}")
            return False
    
    def generate_analytics(self, date_range: str = "today") -> Dict[str, Any]:
        """生成分析报告"""
        try:
            from src.utils.helpers import parse_date_range
            
            start_date, end_date = parse_date_range(date_range)
            
            # 生成每日分析
            analytics_results = []
            current_date = start_date
            while current_date <= end_date:
                result = self.analytics_manager.generate_daily_analytics(current_date)
                if "error" not in result:
                    analytics_results.append(result)
                current_date += timedelta(days=1)
            
            # 获取汇总统计
            summary = self.analytics_manager.get_analytics_summary((end_date - start_date).days + 1)
            
            return {
                "period": f"{start_date} 到 {end_date}",
                "daily_analytics": analytics_results,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"生成分析报告异常: {e}")
            return {"error": f"生成异常: {str(e)}"}
    
    def get_alerts(self) -> Dict[str, Any]:
        """获取预警信息"""
        try:
            active_alerts = self.analytics_manager.get_active_alerts()
            return {
                "active_alerts": active_alerts,
                "count": len(active_alerts)
            }
        except Exception as e:
            self.logger.error(f"获取预警异常: {e}")
            return {"error": f"获取异常: {str(e)}"}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            from src.utils.helpers import get_memory_usage
            
            # 系统测试
            test_results = self.test_system()
            
            # 知识库统计
            knowledge_stats = self.knowledge_manager.get_knowledge_stats()
            
            # 内存使用
            memory_usage = get_memory_usage()
            
            # 活跃预警
            alerts = self.alert_system.get_active_alerts()
            
            # 系统健康状态
            health_status = self.monitor_service.get_system_health()
            
            return {
                "system_status": test_results,
                "knowledge_base": knowledge_stats,
                "memory_usage": memory_usage,
                "active_alerts": len(alerts),
                "health_score": health_status.get("health_score", 0),
                "health_status": health_status.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取系统状态异常: {e}")
            return {"error": f"获取状态异常: {str(e)}"}
    
    def start_monitoring(self):
        """启动监控服务"""
        try:
            self.monitor_service.start()
            self.logger.info("监控服务已启动")
            return True
        except Exception as e:
            self.logger.error(f"启动监控服务失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止监控服务"""
        try:
            self.monitor_service.stop()
            self.logger.info("监控服务已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止监控服务失败: {e}")
            return False
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查预警"""
        try:
            return self.alert_system.check_all_rules()
        except Exception as e:
            self.logger.error(f"检查预警失败: {e}")
            return []
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃预警"""
        try:
            return self.alert_system.get_active_alerts()
        except Exception as e:
            self.logger.error(f"获取活跃预警失败: {e}")
            return []
    
    def create_alert(self, alert_type: str, title: str, description: str, level: str = "medium") -> Dict[str, Any]:
        """创建预警"""
        try:
            with db_manager.get_session() as session:
                alert = Alert(
                    rule_name=f"手动预警_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type=alert_type,
                    level=level,
                    message=f"{title}: {description}",
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(alert)
                session.commit()
                
                self.logger.info(f"创建预警成功: {title}")
                return {
                    "id": alert.id,
                    "title": title,
                    "description": description,
                    "level": level,
                    "alert_type": alert_type,
                    "created_at": alert.created_at.isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"创建预警异常: {e}")
            return {"error": f"创建异常: {str(e)}"}
    
    def resolve_alert(self, alert_id: int) -> bool:
        """解决预警"""
        try:
            return self.alert_system.resolve_alert(alert_id)
        except Exception as e:
            self.logger.error(f"解决预警失败: {e}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取预警统计"""
        try:
            return self.alert_system.get_alert_statistics()
        except Exception as e:
            self.logger.error(f"获取预警统计失败: {e}")
            return {}

    def get_workorders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的工单列表（按创建时间倒序）"""
        try:
            with db_manager.get_session() as session:
                q = session.query(WorkOrder).order_by(WorkOrder.created_at.desc())
                if limit:
                    q = q.limit(limit)
                rows = q.all()
                results: List[Dict[str, Any]] = []
                for w in rows:
                    results.append({
                        "id": w.id,
                        "order_id": w.order_id,
                        "title": w.title,
                        "description": w.description,
                        "category": w.category,
                        "priority": w.priority,
                        "status": w.status,
                        "created_at": w.created_at.isoformat() if w.created_at else None,
                        "updated_at": w.updated_at.isoformat() if w.updated_at else None,
                        "resolution": w.resolution,
                        "satisfaction_score": w.satisfaction_score
                    })
                return results
        except Exception as e:
            self.logger.error(f"获取工单列表失败: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            return self.monitor_service.get_system_health()
        except Exception as e:
            self.logger.error(f"获取系统健康状态失败: {e}")
            return {"error": f"获取健康状态失败: {str(e)}"}
    
    def get_token_usage_stats(self, user_id: str = None, days: int = 7) -> Dict[str, Any]:
        """获取Token使用统计"""
        try:
            if user_id:
                return self.token_monitor.get_user_token_stats(user_id, days)
            else:
                return self.token_monitor.get_system_token_stats(days)
        except Exception as e:
            self.logger.error(f"获取Token使用统计失败: {e}")
            return {"error": f"获取Token统计失败: {str(e)}"}
    
    def get_ai_performance_stats(self, model_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """获取AI性能统计"""
        try:
            if model_name:
                return self.ai_success_monitor.get_model_performance(model_name, hours)
            else:
                return self.ai_success_monitor.get_system_performance(hours)
        except Exception as e:
            self.logger.error(f"获取AI性能统计失败: {e}")
            return {"error": f"获取AI性能统计失败: {str(e)}"}
    
    def get_cost_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取成本趋势"""
        try:
            return self.token_monitor.get_cost_trend(days)
        except Exception as e:
            self.logger.error(f"获取成本趋势失败: {e}")
            return []
    
    def get_performance_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取性能趋势"""
        try:
            return self.ai_success_monitor.get_performance_trend(days)
        except Exception as e:
            self.logger.error(f"获取性能趋势失败: {e}")
            return []
    
    def get_user_conversation_history(
        self,
        user_id: str,
        work_order_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户对话历史"""
        try:
            return self.dialogue_manager.get_user_conversation_history(
                user_id=user_id,
                work_order_id=work_order_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            self.logger.error(f"获取用户对话历史失败: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话记录"""
        try:
            return self.dialogue_manager.delete_conversation(conversation_id)
        except Exception as e:
            self.logger.error(f"删除对话记录失败: {e}")
            return False
    
    def delete_user_conversations(self, user_id: str, work_order_id: Optional[int] = None) -> int:
        """删除用户的所有对话记录"""
        try:
            return self.dialogue_manager.delete_user_conversations(user_id, work_order_id)
        except Exception as e:
            self.logger.error(f"删除用户对话记录失败: {e}")
            return 0
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """清理旧数据"""
        try:
            results = {}
            
            # 清理对话历史
            conversation_cleaned = self.dialogue_manager.history_manager.cleanup_old_conversations(days)
            results["conversations"] = conversation_cleaned
            
            # 清理Token监控数据
            token_cleaned = self.token_monitor.cleanup_old_data(days)
            results["token_data"] = token_cleaned
            
            # 清理AI成功率监控数据
            ai_cleaned = self.ai_success_monitor.cleanup_old_data(days)
            results["ai_data"] = ai_cleaned
            
            self.logger.info(f"数据清理完成: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return {}
    
    def check_rate_limit(self, user_id: str) -> bool:
        """检查用户请求频率限制"""
        try:
            return self.system_optimizer.check_rate_limit(user_id)
        except Exception as e:
            self.logger.error(f"检查频率限制失败: {e}")
            return True
    
    def check_input_security(self, user_input: str) -> Dict[str, Any]:
        """检查输入安全性"""
        try:
            return self.system_optimizer.check_input_security(user_input)
        except Exception as e:
            self.logger.error(f"检查输入安全性失败: {e}")
            return {"is_safe": True, "message": "安全检查异常"}
    
    def check_cost_limit(self, estimated_cost: float) -> bool:
        """检查成本限制"""
        try:
            return self.system_optimizer.check_cost_limit(estimated_cost)
        except Exception as e:
            self.logger.error(f"检查成本限制失败: {e}")
            return True
    
    def get_system_optimization_status(self) -> Dict[str, Any]:
        """获取系统优化状态"""
        try:
            return self.system_optimizer.get_system_status()
        except Exception as e:
            self.logger.error(f"获取系统优化状态失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def optimize_response_time(self, response_time: float) -> Dict[str, Any]:
        """优化响应时间"""
        try:
            return self.system_optimizer.optimize_response_time(response_time)
        except Exception as e:
            self.logger.error(f"优化响应时间失败: {e}")
            return {}

def main():
    """主函数"""
    # 创建实例
    assistant = Assistant()
    
    # 测试系统
    test_results = assistant.test_system()
    print("系统测试结果:", test_results)
    
    if not test_results["overall"]:
        print("系统初始化失败，请检查配置")
        return
    
    print("启动成功！")
    
    # 示例用法
    # 创建工单
    work_order = assistant.create_work_order(
        title="测试工单",
        description="这是一个测试工单",
        category="技术问题",
        priority="medium"
    )
    print("创建工单:", work_order)
    
    # 处理消息
    if "work_order_id" in work_order:
        response = assistant.process_message(
            message="我的账户无法登录",
            work_order_id=work_order["work_order_id"]
        )
        print("处理消息:", response)
    
    # 获取系统状态
    status = assistant.get_system_status()
    print("系统状态:", status)

if __name__ == "__main__":
    main()
