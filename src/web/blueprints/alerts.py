# -*- coding: utf-8 -*-
"""
预警管理蓝图
处理预警相关的API路由
"""

from flask import Blueprint, request, jsonify
from src.web.service_manager import service_manager
from src.web.error_handlers import handle_api_errors, create_error_response, create_success_response
from src.analytics.alert_system import AlertRule, AlertLevel, AlertType

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('')
@handle_api_errors
def get_alerts():
    """获取预警列表（分页）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        level_filter = request.args.get('level', '')
        status_filter = request.args.get('status', '')
        
        # 从数据库获取分页数据
        from src.core.database import db_manager
        from src.core.models import Alert
        
        with db_manager.get_session() as session:
            # 构建查询
            query = session.query(Alert)
            
            # 应用过滤器
            if level_filter:
                query = query.filter(Alert.level == level_filter)
            if status_filter:
                if status_filter == 'active':
                    query = query.filter(Alert.is_active == True)
                elif status_filter == 'resolved':
                    query = query.filter(Alert.is_active == False)
            
            # 按创建时间倒序排列
            query = query.order_by(Alert.created_at.desc())
            
            # 计算总数
            total = query.count()
            
            # 分页查询
            alerts = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'id': alert.id,
                    'rule_name': alert.rule_name,
                    'alert_type': alert.alert_type,
                    'level': alert.level,
                    'severity': alert.severity,
                    'message': alert.message,
                    'data': alert.data,
                    'is_active': alert.is_active,
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                })
            
            # 计算分页信息
            total_pages = (total + per_page - 1) // per_page
            
            return jsonify({
                'alerts': alerts_data,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            })
            
    except Exception as e:
        return create_error_response(f"获取预警列表失败: {str(e)}", 500)

@alerts_bp.route('', methods=['POST'])
def create_alert():
    """创建预警"""
    try:
        data = request.get_json()
        alert = service_manager.get_assistant().create_alert(
            alert_type=data.get('alert_type', 'manual'),
            title=data.get('title', '手动预警'),
            description=data.get('description', ''),
            level=data.get('level', 'medium')
        )
        return jsonify({"success": True, "alert": alert})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_bp.route('/statistics')
def get_alert_statistics():
    """获取预警统计"""
    try:
        stats = service_manager.get_assistant().get_alert_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """解决预警"""
    try:
        success = service_manager.get_assistant().resolve_alert(alert_id)
        if success:
            return jsonify({"success": True, "message": "预警已解决"})
        else:
            return jsonify({"success": False, "message": "解决预警失败"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
