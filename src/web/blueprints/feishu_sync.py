# -*- coding: utf-8 -*-
"""
飞书同步蓝图
处理飞书多维表格与工单系统的同步
"""

from flask import Blueprint, request, jsonify, render_template
from src.integrations.feishu_client import FeishuClient
from src.integrations.workorder_sync import WorkOrderSyncService
from src.integrations.config_manager import config_manager
from src.integrations.feishu_permission_checker import FeishuPermissionChecker
import logging

logger = logging.getLogger(__name__)

feishu_sync_bp = Blueprint('feishu_sync', __name__, url_prefix='/api/feishu-sync')

# 全局同步服务实例
sync_service = None

def get_sync_service():
    """获取同步服务实例"""
    global sync_service
    if sync_service is None:
        # 从配置管理器读取飞书配置
        feishu_config = config_manager.get_feishu_config()
        
        if not all([feishu_config.get("app_id"), feishu_config.get("app_secret"), 
                   feishu_config.get("app_token"), feishu_config.get("table_id")]):
            raise Exception("飞书配置不完整，请先配置飞书应用信息")
        
        feishu_client = FeishuClient(feishu_config["app_id"], feishu_config["app_secret"])
        sync_service = WorkOrderSyncService(feishu_client, feishu_config["app_token"], feishu_config["table_id"])
    
    return sync_service

@feishu_sync_bp.route('/config', methods=['GET', 'POST'])
def manage_config():
    """管理飞书同步配置"""
    if request.method == 'GET':
        # 返回当前配置
        try:
            config_summary = config_manager.get_config_summary()
            return jsonify({
                "success": True,
                "config": config_summary
            })
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        # 更新配置
        try:
            data = request.get_json()
            app_id = data.get('app_id')
            app_secret = data.get('app_secret')
            app_token = data.get('app_token')
            table_id = data.get('table_id')
            
            if not all([app_id, app_secret, app_token, table_id]):
                return jsonify({"error": "缺少必要配置参数"}), 400
            
            # 更新配置管理器
            success = config_manager.update_feishu_config(
                app_id=app_id,
                app_secret=app_secret,
                app_token=app_token,
                table_id=table_id
            )
            
            if success:
                # 重新初始化同步服务
                global sync_service
                sync_service = None  # 强制重新创建
                
                return jsonify({
                    "success": True,
                    "message": "配置更新成功"
                })
            else:
                return jsonify({"error": "配置更新失败"}), 500
                
        except Exception as e:
            logger.error(f"更新飞书配置失败: {e}")
            return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/sync-from-feishu', methods=['POST'])
def sync_from_feishu():
    """从飞书同步数据到本地"""
    try:
        data = request.get_json() or {}
        generate_ai = data.get('generate_ai_suggestions', True)
        limit = data.get('limit', 10)
        
        sync_service = get_sync_service()
        result = sync_service.sync_from_feishu(generate_ai_suggestions=generate_ai, limit=limit)
        
        if result.get("success"):
            message = f"同步完成：创建 {result['created_count']} 条，更新 {result['updated_count']} 条"
            if result.get('ai_suggestions_generated'):
                message += "，AI建议已生成并更新到飞书表格"
            
            return jsonify({
                "success": True,
                "message": message,
                "details": result
            })
        else:
            return jsonify({"error": result.get("error")}), 500
            
    except Exception as e:
        logger.error(f"从飞书同步失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/sync-to-feishu/<int:workorder_id>', methods=['POST'])
def sync_to_feishu(workorder_id):
    """将本地工单同步到飞书"""
    try:
        sync_service = get_sync_service()
        result = sync_service.sync_to_feishu(workorder_id)
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "message": "同步到飞书成功"
            })
        else:
            return jsonify({"error": result.get("error")}), 500
            
    except Exception as e:
        logger.error(f"同步到飞书失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/status')
def get_sync_status():
    """获取同步状态"""
    try:
        sync_service = get_sync_service()
        status = sync_service.get_sync_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/test-connection')
def test_connection():
    """测试飞书连接"""
    try:
        # 使用配置管理器测试连接
        result = config_manager.test_feishu_connection()
        
        if result.get("success"):
            # 如果连接成功，尝试获取表格字段信息
            try:
                sync_service = get_sync_service()
                
                # 使用新的测试连接方法
                connection_test = sync_service.feishu_client.test_connection()
                if not connection_test.get("success"):
                    return jsonify({
                        "success": False,
                        "message": f"飞书连接测试失败: {connection_test.get('message')}"
                    }), 400
                
                fields_info = sync_service.feishu_client.get_table_fields(
                    sync_service.app_token, sync_service.table_id
                )
                
                if fields_info.get("code") == 0:
                    result["fields"] = fields_info.get("data", {}).get("items", [])
            except Exception as e:
                logger.warning(f"获取表格字段信息失败: {e}")
        
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"测试飞书连接失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/create-workorder', methods=['POST'])
def create_workorder_from_feishu():
    """从飞书记录创建工单"""
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        
        if not record_id:
            return jsonify({"success": False, "message": "缺少记录ID"}), 400
        
        sync_service = get_sync_service()
        result = sync_service.create_workorder_from_feishu_record(record_id)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"创建工单失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@feishu_sync_bp.route('/field-mapping/status')
def get_field_mapping_status():
    """获取字段映射状态"""
    try:
        sync_service = get_sync_service()
        status = sync_service.get_mapping_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        logger.error(f"获取字段映射状态失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/field-mapping/discover', methods=['POST'])
def discover_fields():
    """发现字段并生成映射建议"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 5)  # 默认分析5条记录
        
        sync_service = get_sync_service()
        
        # 获取飞书记录进行分析
        feishu_client = sync_service.feishu_client
        records = feishu_client.get_table_records(sync_service.app_token, sync_service.table_id, page_size=limit)
        
        if records.get("code") != 0:
            raise Exception(f"获取飞书记录失败: {records.get('msg', '未知错误')}")
        
        items = records.get("data", {}).get("items", [])
        if not items:
            return jsonify({
                "success": True,
                "message": "没有找到飞书记录",
                "discovery_report": {}
            })
        
        # 分析第一条记录的字段
        first_record = items[0]
        feishu_fields = feishu_client.parse_record_fields(first_record)
        
        # 生成字段发现报告
        discovery_report = sync_service.get_field_discovery_report(feishu_fields)
        
        return jsonify({
            "success": True,
            "discovery_report": discovery_report,
            "sample_record": feishu_fields
        })
        
    except Exception as e:
        logger.error(f"字段发现失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/field-mapping/add', methods=['POST'])
def add_field_mapping():
    """添加字段映射"""
    try:
        data = request.get_json()
        feishu_field = data.get('feishu_field')
        local_field = data.get('local_field')
        aliases = data.get('aliases', [])
        patterns = data.get('patterns', [])
        priority = data.get('priority', 3)
        
        if not feishu_field or not local_field:
            return jsonify({"error": "缺少必要参数"}), 400
        
        sync_service = get_sync_service()
        success = sync_service.add_field_mapping(
            feishu_field=feishu_field,
            local_field=local_field,
            aliases=aliases,
            patterns=patterns,
            priority=priority
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"字段映射 '{feishu_field}' -> '{local_field}' 添加成功"
            })
        else:
            return jsonify({"error": "添加字段映射失败"}), 500
            
    except Exception as e:
        logger.error(f"添加字段映射失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/field-mapping/remove', methods=['POST'])
def remove_field_mapping():
    """移除字段映射"""
    try:
        data = request.get_json()
        feishu_field = data.get('feishu_field')
        
        if not feishu_field:
            return jsonify({"error": "缺少字段名参数"}), 400
        
        sync_service = get_sync_service()
        success = sync_service.remove_field_mapping(feishu_field)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"字段映射 '{feishu_field}' 移除成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"字段映射 '{feishu_field}' 不存在或移除失败"
            })
            
    except Exception as e:
        logger.error(f"移除字段映射失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/check-permissions')
def check_permissions():
    """检查飞书权限"""
    try:
        checker = FeishuPermissionChecker()
        result = checker.check_permissions()
        
        return jsonify({
            "success": True,
            "permission_check": result,
            "summary": checker.get_permission_summary()
        })
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/field-mapping')
def field_mapping_page():
    """字段映射管理页面"""
    return render_template('field_mapping.html')

@feishu_sync_bp.route('/preview-feishu-data')
def preview_feishu_data():
    """预览飞书数据"""
    try:
        sync_service = get_sync_service()
        
        # 获取前10条记录进行预览
        records = sync_service.feishu_client.get_table_records(
            sync_service.app_token, sync_service.table_id, page_size=10
        )
        
        if records.get("code") == 0:
            items = records.get("data", {}).get("items", [])
            preview_data = []
            
            for record in items:
                parsed_fields = sync_service.feishu_client.parse_record_fields(record)
                preview_data.append({
                    "record_id": record.get("record_id"),
                    "fields": parsed_fields
                })
            
            return jsonify({
                "success": True,
                "preview_data": preview_data,
                "total_count": len(preview_data)
            })
        else:
            return jsonify({
                "success": False,
                "error": records.get("msg", "获取数据失败")
            }), 500
            
    except Exception as e:
        logger.error(f"预览飞书数据失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/config/export', methods=['GET'])
def export_config():
    """导出配置"""
    try:
        config_json = config_manager.export_config()
        return jsonify({
            "success": True,
            "config": config_json
        })
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/config/import', methods=['POST'])
def import_config():
    """导入配置"""
    try:
        data = request.get_json()
        config_json = data.get('config')
        
        if not config_json:
            return jsonify({"error": "缺少配置数据"}), 400
        
        success = config_manager.import_config(config_json)
        
        if success:
            # 重新初始化同步服务
            global sync_service
            sync_service = None
            
            return jsonify({
                "success": True,
                "message": "配置导入成功"
            })
        else:
            return jsonify({"error": "配置导入失败"}), 500
            
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return jsonify({"error": str(e)}), 500

@feishu_sync_bp.route('/config/reset', methods=['POST'])
def reset_config():
    """重置配置"""
    try:
        success = config_manager.reset_config()
        
        if success:
            # 重新初始化同步服务
            global sync_service
            sync_service = None
            
            return jsonify({
                "success": True,
                "message": "配置重置成功"
            })
        else:
            return jsonify({"error": "配置重置失败"}), 500
            
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        return jsonify({"error": str(e)}), 500
