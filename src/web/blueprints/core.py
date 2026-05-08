# -*- coding: utf-8 -*-
"""
核心功能蓝图
处理系统核心功能的API路由
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
from datetime import datetime, timedelta

from src.web.service_manager import service_manager
from src.web.error_handlers import handle_api_errors, create_error_response, create_success_response
from src.core.database import db_manager
from src.core.models import Conversation, Alert, WorkOrder
from src.core.query_optimizer import query_optimizer

core_bp = Blueprint('core', __name__, url_prefix='/api')


@core_bp.route('/health')
@handle_api_errors
def get_health() -> Dict[str, Any]:
    """获取系统健康状态（附加1小时业务指标）"""
    base = service_manager.get_assistant().get_system_health() or {}
    
    # 追加数据库近1小时指标
    with db_manager.get_session() as session:
        since = datetime.now() - timedelta(hours=1)
        conv_count = session.query(Conversation).filter(Conversation.timestamp >= since).count()
        resp_times = [c.response_time for c in session.query(Conversation).filter(Conversation.timestamp >= since).all() if c.response_time]
        avg_resp = round(sum(resp_times)/len(resp_times), 2) if resp_times else 0
        open_wos = session.query(WorkOrder).filter(WorkOrder.status == 'open').count()
        levels = session.query(Alert.level).filter(Alert.is_active == True).all()
        level_map = {}
        for (lvl,) in levels:
            level_map[lvl] = level_map.get(lvl, 0) + 1
    
    base.update({
        "throughput_1h": conv_count,
        "avg_response_time_1h": avg_resp,
        "open_workorders": open_wos,
        "active_alerts_by_level": level_map
    })
    return jsonify(base)


@core_bp.route('/rules')
@handle_api_errors
def get_rules() -> Dict[str, Any]:
    """获取预警规则列表"""
    rules = service_manager.get_assistant().alert_system.rules
    rules_data = []
    for name, rule in rules.items():
        rules_data.append({
            "name": rule.name,
            "description": rule.description,
            "alert_type": rule.alert_type.value,
            "level": rule.level.value,
            "threshold": rule.threshold,
            "condition": rule.condition,
            "enabled": rule.enabled,
            "check_interval": rule.check_interval,
            "cooldown": rule.cooldown
        })
    return jsonify(rules_data)


@core_bp.route('/rules', methods=['POST'])
@handle_api_errors
def create_rule() -> Dict[str, Any]:
    """创建预警规则"""
    from src.analytics.alert_system import AlertRule, AlertLevel, AlertType
    
    data = request.get_json()
    rule = AlertRule(
        name=data['name'],
        description=data['description'],
        alert_type=AlertType(data['alert_type']),
        level=AlertLevel(data['level']),
        threshold=float(data['threshold']),
        condition=data['condition'],
        enabled=data.get('enabled', True),
        check_interval=int(data.get('check_interval', 300)),
        cooldown=int(data.get('cooldown', 3600))
    )
    
    success = service_manager.get_assistant().alert_system.add_custom_rule(rule)
    if success:
        return jsonify(create_success_response(message="规则创建成功"))
    else:
        return create_error_response("规则创建失败", 400)


@core_bp.route('/rules/<rule_name>', methods=['PUT'])
@handle_api_errors
def update_rule(rule_name: str) -> Dict[str, Any]:
    """更新预警规则"""
    data = request.get_json()
    success = service_manager.get_assistant().alert_system.update_rule(rule_name, **data)
    if success:
        return jsonify(create_success_response(message="规则更新成功"))
    else:
        return create_error_response("规则更新失败", 400)


@core_bp.route('/rules/<rule_name>', methods=['DELETE'])
@handle_api_errors
def delete_rule(rule_name: str) -> Dict[str, Any]:
    """删除预警规则"""
    success = service_manager.get_assistant().alert_system.delete_rule(rule_name)
    if success:
        return jsonify(create_success_response(message="规则删除成功"))
    else:
        return create_error_response("规则删除失败", 400)


@core_bp.route('/monitor/start', methods=['POST'])
@handle_api_errors
def start_monitoring() -> Dict[str, Any]:
    """启动监控服务"""
    success = service_manager.get_assistant().start_monitoring()
    if success:
        return jsonify(create_success_response(message="监控服务已启动"))
    else:
        return create_error_response("启动监控服务失败", 400)


@core_bp.route('/monitor/stop', methods=['POST'])
@handle_api_errors
def stop_monitoring() -> Dict[str, Any]:
    """停止监控服务"""
    success = service_manager.get_assistant().stop_monitoring()
    if success:
        return jsonify(create_success_response(message="监控服务已停止"))
    else:
        return create_error_response("停止监控服务失败", 400)


@core_bp.route('/monitor/status')
@handle_api_errors
def get_monitor_status() -> Dict[str, Any]:
    """获取监控服务状态"""
    health = service_manager.get_assistant().get_system_health()
    return jsonify({
        "monitor_status": health.get("monitor_status", "unknown"),
        "health_score": health.get("health_score", 0),
        "active_alerts": health.get("active_alerts", 0)
    })


@core_bp.route('/check-alerts', methods=['POST'])
@handle_api_errors
def check_alerts() -> Dict[str, Any]:
    """手动检查预警"""
    alerts = service_manager.get_assistant().check_alerts()
    return jsonify({
        "success": True,
        "alerts": alerts,
        "count": len(alerts)
    })


@core_bp.route('/analytics')
@handle_api_errors
def get_analytics() -> Dict[str, Any]:
    """获取分析数据"""
    # 支持多种参数
    time_range = request.args.get('timeRange', request.args.get('days', '30'))
    dimension = request.args.get('dimension', 'workorders')
    
    # 参数验证
    try:
        days = int(time_range)
        if days <= 0 or days > 365:
            days = 30
    except (ValueError, TypeError):
        days = 30
    
    analytics = query_optimizer.get_analytics_optimized(days)
    
    # 确保返回的数据结构完整
    if not analytics:
        analytics = {
            "workorders": {"total": 0, "open": 0, "resolved": 0, "trend": []},
            "alerts": {"total": 0, "critical": 0, "warning": 0, "trend": []},
            "conversations": {"total": 0, "avg_confidence": 0, "trend": []},
            "performance": {"avg_response_time": 0, "success_rate": 0}
        }
    
    return jsonify(analytics)


@core_bp.route('/workorders/by-status/<status>')
@handle_api_errors
def get_workorders_by_status(status: str) -> Dict[str, Any]:
    """根据状态获取工单列表"""
    try:
        with db_manager.get_session() as session:
            # 状态映射
            status_mapping = {
                'open': ['open', '待处理', '新建', 'new'],
                'in_progress': ['in_progress', '处理中', '进行中', 'progress', 'processing'],
                'resolved': ['resolved', '已解决', '已完成'],
                'closed': ['closed', '已关闭', '关闭']
            }
            
            # 处理特殊状态
            if status == 'all':
                # 查询所有工单
                workorders = session.query(WorkOrder).order_by(WorkOrder.created_at.desc()).limit(50).all()
            else:
                # 查找匹配的状态值
                actual_statuses = []
                for mapped_status, possible_values in status_mapping.items():
                    if mapped_status == status:
                        actual_statuses = possible_values
                        break
                
                if not actual_statuses:
                    return create_error_response(f"无效的状态: {status}")
                
                # 查询工单
                workorders = session.query(WorkOrder).filter(
                    WorkOrder.status.in_(actual_statuses)
                ).order_by(WorkOrder.created_at.desc()).limit(50).all()
            
            result = []
            for wo in workorders:
                result.append({
                    "id": wo.id,
                    "order_id": wo.order_id,
                    "title": wo.title,
                    "description": wo.description,
                    "category": wo.category,
                    "priority": wo.priority,
                    "status": wo.status,
                    "created_at": wo.created_at.isoformat() if wo.created_at else None,
                    "updated_at": wo.updated_at.isoformat() if wo.updated_at else None,
                    "resolution": wo.resolution,
                    "satisfaction_score": wo.satisfaction_score
                })
            
            return create_success_response({
                "workorders": result,
                "count": len(result),
                "status": status
            })
            
    except Exception as e:
        return create_error_response(f"获取工单失败: {str(e)}")


@core_bp.route('/alerts/by-level/<level>')
@handle_api_errors
def get_alerts_by_level(level: str) -> Dict[str, Any]:
    """根据级别获取预警列表"""
    try:
        with db_manager.get_session() as session:
            alerts = session.query(Alert).filter(
                Alert.level == level,
                Alert.is_active == True
            ).order_by(Alert.created_at.desc()).limit(50).all()
            
            result = []
            for alert in alerts:
                result.append({
                    "id": alert.id,
                    "message": alert.message,
                    "level": alert.level,
                    "alert_type": alert.alert_type,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    "is_active": alert.is_active
                })
            
            return create_success_response({
                "alerts": result,
                "count": len(result),
                "level": level
            })
            
    except Exception as e:
        return create_error_response(f"获取预警失败: {str(e)}")


@core_bp.route('/knowledge/by-status/<status>')
@handle_api_errors
def get_knowledge_by_status(status: str) -> Dict[str, Any]:
    """根据验证状态获取知识库条目"""
    try:
        with db_manager.get_session() as session:
            from src.core.models import KnowledgeEntry
            
            is_verified = status == 'verified'
            knowledge_entries = session.query(KnowledgeEntry).filter(
                KnowledgeEntry.is_verified == is_verified
            ).order_by(KnowledgeEntry.created_at.desc()).limit(50).all()
            
            result = []
            for entry in knowledge_entries:
                result.append({
                    "id": entry.id,
                    "title": entry.title,
                    "content": entry.content,
                    "category": entry.category,
                    "is_verified": entry.is_verified,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
                })
            
            return create_success_response({
                "knowledge": result,
                "count": len(result),
                "status": status
            })
            
    except Exception as e:
        return create_error_response(f"获取知识库条目失败: {str(e)}")


@core_bp.route('/batch-delete/workorders', methods=['POST'])
@handle_api_errors
def batch_delete_workorders() -> Dict[str, Any]:
    """批量删除工单"""
    data = request.get_json()
    workorder_ids = data.get('ids', [])
    
    if not workorder_ids:
        return create_error_response("请选择要删除的工单", 400)
    
    try:
        with db_manager.get_session() as session:
            # 验证工单是否存在
            existing_workorders = session.query(WorkOrder).filter(WorkOrder.id.in_(workorder_ids)).all()
            existing_ids = [wo.id for wo in existing_workorders]
            
            if len(existing_ids) != len(workorder_ids):
                missing_ids = set(workorder_ids) - set(existing_ids)
                return create_error_response(f"工单不存在: {list(missing_ids)}", 404)
            
            # 先删除相关的工单建议记录
            from src.core.models import WorkOrderSuggestion
            session.query(WorkOrderSuggestion).filter(WorkOrderSuggestion.work_order_id.in_(workorder_ids)).delete(synchronize_session=False)
            
            # 再删除工单
            deleted_count = session.query(WorkOrder).filter(WorkOrder.id.in_(workorder_ids)).delete(synchronize_session=False)
            session.commit()
            
            return jsonify(create_success_response(
                data={"deleted_count": deleted_count},
                message=f"成功删除 {deleted_count} 个工单"
            ))
            
    except Exception as e:
        return create_error_response(f"批量删除工单失败: {str(e)}", 500)


@core_bp.route('/batch-delete/alerts', methods=['POST'])
@handle_api_errors
def batch_delete_alerts() -> Dict[str, Any]:
    """批量删除预警"""
    data = request.get_json()
    alert_ids = data.get('ids', [])
    
    if not alert_ids:
        return create_error_response("请选择要删除的预警", 400)
    
    try:
        with db_manager.get_session() as session:
            # 验证预警是否存在
            existing_alerts = session.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            existing_ids = [alert.id for alert in existing_alerts]
            
            if len(existing_ids) != len(alert_ids):
                missing_ids = set(alert_ids) - set(existing_ids)
                return create_error_response(f"预警不存在: {list(missing_ids)}", 404)
            
            # 删除预警
            deleted_count = session.query(Alert).filter(Alert.id.in_(alert_ids)).delete(synchronize_session=False)
            session.commit()
            
            return jsonify(create_success_response(
                data={"deleted_count": deleted_count},
                message=f"成功删除 {deleted_count} 个预警"
            ))
            
    except Exception as e:
        return create_error_response(f"批量删除预警失败: {str(e)}", 500)


@core_bp.route('/batch-delete/knowledge', methods=['POST'])
@handle_api_errors
def batch_delete_knowledge() -> Dict[str, Any]:
    """批量删除知识库条目"""
    data = request.get_json()
    knowledge_ids = data.get('ids', [])
    
    if not knowledge_ids:
        return create_error_response("请选择要删除的知识库条目", 400)
    
    try:
        with db_manager.get_session() as session:
            # 验证知识库条目是否存在
            existing_knowledge = session.query(KnowledgeEntry).filter(KnowledgeEntry.id.in_(knowledge_ids)).all()
            existing_ids = [kb.id for kb in existing_knowledge]
            
            if len(existing_ids) != len(knowledge_ids):
                missing_ids = set(knowledge_ids) - set(existing_ids)
                return create_error_response(f"知识库条目不存在: {list(missing_ids)}", 404)
            
            # 删除知识库条目
            deleted_count = session.query(KnowledgeEntry).filter(KnowledgeEntry.id.in_(knowledge_ids)).delete(synchronize_session=False)
            session.commit()
            
            return jsonify(create_success_response(
                data={"deleted_count": deleted_count},
                message=f"成功删除 {deleted_count} 个知识库条目"
            ))
            
    except Exception as e:
        return create_error_response(f"批量删除知识库条目失败: {str(e)}", 500)
