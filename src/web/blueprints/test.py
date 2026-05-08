# -*- coding: utf-8 -*-
"""
API测试相关蓝图
处理API连接测试、模型测试等功能
"""

from flask import Blueprint, request, jsonify

test_bp = Blueprint('test', __name__, url_prefix='/api/test')


@test_bp.route('/connection', methods=['POST'])
def test_api_connection():
    """测试API连接"""
    try:
        data = request.get_json()
        api_provider = data.get('api_provider', 'openai')
        api_base_url = data.get('api_base_url', '')
        api_key = data.get('api_key', '')
        model_name = data.get('model_name', 'qwen-turbo')

        # 这里可以调用LLM客户端进行连接测试
        # 暂时返回模拟结果

        return jsonify({
            "success": True,
            "message": f"API连接测试成功 - {api_provider}",
            "response_time": "150ms",
            "model_status": "可用"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@test_bp.route('/model', methods=['POST'])
def test_model_response():
    """测试模型回答"""
    try:
        data = request.get_json()
        test_message = data.get('test_message', '你好，请简单介绍一下你自己')

        # 这里可以调用LLM客户端进行回答测试
        # 暂时返回模拟结果
        return jsonify({
            "success": True,
            "test_message": test_message,
            "response": "你好！我是智能助手，基于大语言模型构建的智能客服系统。我可以帮助您解决问题，提供技术支持和服务。",
            "response_time": "1.2s",
            "tokens_used": 45
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
