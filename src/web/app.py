# -*- coding: utf-8 -*-
"""
预警管理Web应用
提供预警系统的Web界面和API接口
重构版本 - 使用蓝图架构
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心模块
from src.core.database import db_manager
from src.core.models import Conversation, Alert, WorkOrder
from src.core.query_optimizer import query_optimizer
from src.web.service_manager import service_manager

# 导入蓝图
from src.web.blueprints.alerts import alerts_bp
from src.web.blueprints.workorders import workorders_bp
from src.web.blueprints.conversations import conversations_bp
from src.web.blueprints.knowledge import knowledge_bp
from src.web.blueprints.monitoring import monitoring_bp
from src.web.blueprints.system import system_bp
from src.web.blueprints.feishu_sync import feishu_sync_bp
from src.web.blueprints.core import core_bp
from src.web.blueprints.auth import auth_bp
from src.web.blueprints.agent import agent_bp
from src.web.blueprints.analytics import analytics_bp
from src.web.blueprints.test import test_bp
from src.web.blueprints.feishu_bot import feishu_bot_bp
from src.web.blueprints.wechat_bot import wechat_bot_bp

# 配置日志
logger = logging.getLogger(__name__)

# 抑制 /api/health 的访问日志
werkzeug_logger = logging.getLogger('werkzeug')

class HealthLogFilter(logging.Filter):
    def filter(self, record):
        try:
            msg = record.getMessage()
            return '/api/health' not in msg
        except Exception:
            return True

werkzeug_logger.addFilter(HealthLogFilter())

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 使用统一的服务管理器

# 注册蓝图
app.register_blueprint(alerts_bp)
app.register_blueprint(workorders_bp)
app.register_blueprint(conversations_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(system_bp)
app.register_blueprint(feishu_sync_bp)
app.register_blueprint(core_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(test_bp)
app.register_blueprint(feishu_bot_bp)
app.register_blueprint(wechat_bot_bp)

# 页面路由
@app.route('/')
@app.route('/dashboard')
def index():
    """主页 - 综合管理平台"""
    response = make_response(render_template('dashboard.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/alerts')
def alerts():
    """预警管理页面"""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """实时对话页面 (WebSocket版本)"""
    return render_template('chat.html')

@app.route('/chat-http')
def chat_http():
    """实时对话页面 (HTTP版本)"""
    return render_template('chat_http.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的下载服务"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================================================
# 核心API路由
# ============================================================================
# 以下路由因功能特殊性保留在主应用中：
# - Chat相关路由：使用RealtimeChatManager进行实时对话
# - 健康检查、预警规则、监控状态等核心功能已迁移到 core 蓝图
# - 分析数据相关功能已迁移到 analytics 蓝图

# ============================================================================
# 实时对话相关路由
# ============================================================================
@app.route('/api/chat/session', methods=['POST'])
def create_chat_session():
    """创建对话会话"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        work_order_id = data.get('work_order_id')
        
        session_id = service_manager.get_chat_manager().create_session(user_id, work_order_id)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "会话创建成功"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/message', methods=['POST'])
def send_chat_message():
    """发送聊天消息"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({"error": "缺少必要参数"}), 400
        
        result = service_manager.get_chat_manager().process_message(session_id, message)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history/<session_id>')
def get_chat_history(session_id):
    """获取对话历史"""
    try:
        history = service_manager.get_chat_manager().get_session_history(session_id)
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/work-order', methods=['POST'])
def create_work_order():
    """创建工单"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        title = data.get('title')
        description = data.get('description')
        category = data.get('category', '技术问题')
        priority = data.get('priority', 'medium')
        
        if not session_id or not title or not description:
            return jsonify({"error": "缺少必要参数"}), 400
        
        result = service_manager.get_chat_manager().create_work_order(session_id, title, description, category, priority)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/work-order/<int:work_order_id>')
def get_work_order_status(work_order_id):
    """获取工单状态"""
    try:
        result = service_manager.get_chat_manager().get_work_order_status(work_order_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/session/<session_id>', methods=['DELETE'])
def end_chat_session(session_id):
    """结束对话会话"""
    try:
        success = service_manager.get_chat_manager().end_session(session_id)
        return jsonify({
            "success": success,
            "message": "会话已结束" if success else "结束会话失败"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions')
def get_active_sessions():
    """获取活跃会话列表"""
    try:
        # 确保chat_manager已初始化
        manager = service_manager.get_chat_manager()
        sessions = manager.get_active_sessions()
        return jsonify({
            "success": True,
            "sessions": sessions
        })
    except Exception as e:
        logger.error(f"获取活跃会话失败: {e}")
        return jsonify({"error": str(e)}), 500

# Agent相关路由已移动到 agent_bp 蓝图

# 分析相关路由已移动到 analytics_bp 蓝图

# API测试相关路由已移动到 test_bp 蓝图

# ============================================================================
# 应用启动配置
# ============================================================================
# 飞书同步功能已合并到主页面，不再需要单独的路由

if __name__ == '__main__':
    import time
    app.config['START_TIME'] = time.time()
    app.config['SERVER_PORT'] = 5000
    app.config['WEBSOCKET_PORT'] = 8765
    app.run(debug=True, host='0.0.0.0', port=5000)
