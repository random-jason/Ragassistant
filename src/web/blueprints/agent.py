# -*- coding: utf-8 -*-
"""
Agent相关API蓝图
处理智能代理、工具执行、监控等功能
"""

from flask import Blueprint, request, jsonify
import asyncio

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')


@agent_bp.route('/status')
def get_agent_status():
    """获取Agent状态"""
    try:
        from src.web.service_manager import service_manager
        status = service_manager.get_agent_assistant().get_agent_status()
        return jsonify({"success": True, **status})
    except Exception as e:
        # 返回默认状态，避免500错误
        return jsonify({
            "success": False,
            "status": "inactive",
            "active_goals": 0,
            "available_tools": 0,
            "error": "Agent服务暂时不可用"
        })


@agent_bp.route('/action-history')
def get_agent_action_history():
    """获取Agent动作执行历史"""
    try:
        from src.web.service_manager import service_manager
        limit = request.args.get('limit', 50, type=int)
        history = service_manager.get_agent_assistant().get_action_history(limit)
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/trigger-sample', methods=['POST'])
def trigger_sample_action():
    """触发示例动作"""
    try:
        from src.web.service_manager import service_manager
        import asyncio
        result = asyncio.run(service_manager.get_agent_assistant().trigger_sample_actions())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/clear-history', methods=['POST'])
def clear_agent_history():
    """清空Agent执行历史"""
    try:
        from src.web.service_manager import service_manager
        result = service_manager.get_agent_assistant().clear_execution_history()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/llm-stats')
def get_llm_stats():
    """获取LLM使用统计"""
    try:
        from src.web.service_manager import service_manager
        stats = service_manager.get_agent_assistant().get_llm_usage_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/toggle', methods=['POST'])
def toggle_agent_mode():
    """切换Agent模式"""
    try:
        from src.web.service_manager import service_manager
        data = request.get_json()
        enabled = data.get('enabled', True)
        success = service_manager.get_agent_assistant().toggle_agent_mode(enabled)
        return jsonify({
            "success": success,
            "message": f"Agent模式已{'启用' if enabled else '禁用'}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/monitoring/start', methods=['POST'])
def start_agent_monitoring():
    """启动Agent监控"""
    try:
        from src.web.service_manager import service_manager
        success = service_manager.get_agent_assistant().start_proactive_monitoring()
        return jsonify({
            "success": success,
            "message": "Agent监控已启动" if success else "启动失败"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/monitoring/stop', methods=['POST'])
def stop_agent_monitoring():
    """停止Agent监控"""
    try:
        from src.web.service_manager import service_manager
        success = service_manager.get_agent_assistant().stop_proactive_monitoring()
        return jsonify({
            "success": success,
            "message": "Agent监控已停止" if success else "停止失败"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/proactive-monitoring', methods=['POST'])
def proactive_monitoring():
    """主动监控检查"""
    try:
        from src.web.service_manager import service_manager
        result = service_manager.get_agent_assistant().run_proactive_monitoring()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/intelligent-analysis', methods=['POST'])
def intelligent_analysis():
    """智能分析"""
    try:
        from src.web.service_manager import service_manager
        analysis = service_manager.get_agent_assistant().run_intelligent_analysis()
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/chat', methods=['POST'])
def agent_chat():
    """Agent对话接口"""
    try:
        from src.web.service_manager import service_manager
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})

        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        # 使用Agent助手处理消息
        agent_assistant = service_manager.get_agent_assistant()

        # 模拟Agent处理（实际应该调用真正的Agent处理逻辑）
        import asyncio
        result = asyncio.run(agent_assistant.process_message_agent(
            message=message,
            user_id=context.get('user_id', 'admin'),
            work_order_id=None,
            enable_proactive=True
        ))

        return jsonify({
            "success": True,
            "response": result.get('response', 'Agent已处理您的请求'),
            "actions": result.get('actions', []),
            "status": result.get('status', 'completed')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/tools/stats')
def get_agent_tools_stats():
    """获取Agent工具统计"""
    try:
        from src.web.service_manager import service_manager
        agent_assistant = service_manager.get_agent_assistant()
        tools = agent_assistant.agent_core.tool_manager.get_available_tools()
        performance = agent_assistant.agent_core.tool_manager.get_tool_performance_report()
        return jsonify({
            "success": True,
            "tools": tools,
            "performance": performance
        })
    except Exception as e:
        # 返回默认工具列表，避免500错误
        return jsonify({
            "success": False,
            "tools": [],
            "performance": {},
            "error": "工具统计暂时不可用"
        })


@agent_bp.route('/tools/execute', methods=['POST'])
def execute_agent_tool():
    """执行指定的Agent工具"""
    try:
        from src.web.service_manager import service_manager
        data = request.get_json() or {}
        tool_name = data.get('tool') or data.get('name')
        parameters = data.get('parameters') or {}
        if not tool_name:
            return jsonify({"error": "缺少工具名称tool"}), 400

        import asyncio
        result = asyncio.run(service_manager.get_agent_assistant().agent_core.tool_manager.execute_tool(tool_name, parameters))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/tools/register', methods=['POST'])
def register_custom_tool():
    """注册自定义工具（仅登记元数据，函数为占位符）"""
    try:
        from src.web.service_manager import service_manager
        data = request.get_json() or {}
        name = data.get('name')
        description = data.get('description', '')
        if not name:
            return jsonify({"error": "缺少工具名称"}), 400

        def _placeholder_tool(**kwargs):
            return {"message": f"自定义工具 {name} 已登记（占位），当前不可执行", "params": kwargs}

        service_manager.get_agent_assistant().agent_core.tool_manager.register_tool(
            name,
            _placeholder_tool,
            metadata={"description": description, "custom": True}
        )
        return jsonify({"success": True, "message": "工具已注册"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@agent_bp.route('/tools/unregister/<name>', methods=['DELETE'])
def unregister_custom_tool(name):
    """注销自定义工具"""
    try:
        from src.web.service_manager import service_manager
        success = service_manager.get_agent_assistant().agent_core.tool_manager.unregister_tool(name)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
