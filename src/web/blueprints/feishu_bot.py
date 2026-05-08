# -*- coding: utf-8 -*-
"""
飞书机器人Webhook处理蓝图
"""

import logging
import re
from flask import Blueprint, request, jsonify
import json
from datetime import datetime

from src.config.unified_config import get_config
from src.integrations.feishu_client import FeishuClient
from src.web.service_manager import service_manager

logger = logging.getLogger(__name__)

feishu_bot_bp = Blueprint('feishu_bot', __name__, url_prefix='/api/feishu_bot')

# 初始化服务（延迟初始化，避免模块加载时配置未就绪）
feishu_client = None

def _get_feishu_client():
    global feishu_client
    if feishu_client is None:
        config = get_config()
        feishu_client = FeishuClient(
            app_id=config.feishu.app_id,
            app_secret=config.feishu.app_secret,
            bot_webhook_url=getattr(config.feishu, 'bot_webhook_url', '')
        )
    return feishu_client

@feishu_bot_bp.route('/webhook', methods=['POST'])
def feishu_webhook():
    """
    接收飞书机器人的回调事件
    """
    chat_manager = service_manager.get_chat_manager()
    start_time = datetime.now()  # 记录开始时间
    
    try:
        data = request.json
        if not data:
            raw_data = request.data
            data = json.loads(raw_data)
    except Exception as e:
        logger.error(f"解析请求JSON失败: {e}")
        return jsonify({"code": 1, "msg": "无效的请求体"}), 400

    logger.info(f"接收到飞书回调: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 飞书开放平台校验
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    # 处理消息事件
    header = data.get("header", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        try:
            event = data.get("event", {})
            message = event.get("message", {})
            
            # 只处理文本消息
            if message.get("message_type") != "text":
                return jsonify({"code": 0, "msg": "非文本消息，已忽略"})
            
            sender = event.get("sender", {})
            sender_id = sender.get("sender_id", {}).get("open_id")
            chat_id = message.get("chat_id")
            chat_type = message.get("chat_type", "")
            
            content_str = message.get("content", "{}")
            content_data = json.loads(content_str)
            user_message = content_data.get("text", "").strip()
            
            logger.info(f"收到消息 - chat_type: {chat_type}, sender: {sender_id}, message: {user_message}")

            # 改进的@检测逻辑 - 支持多种@格式
            is_mentioned = False
            
            # 检查是否包含@符号（飞书会话中的@通常包含@_user_或@_all等）
            if "@_user_" in user_message or "@_all" in user_message:
                is_mentioned = True
                # 清理@标记，提取实际消息
                user_message = re.sub(r'@_user_\d+\s*', '', user_message).strip()
                user_message = re.sub(r'@_all\s*', '', user_message).strip()
            
            # 群聊必须@机器人才回复，私聊直接回复
            if chat_type == "group" and not is_mentioned:
                logger.info("群聊消息但未@机器人，已忽略")
                return jsonify({"code": 0, "msg": "群聊消息但未@机器人，已忽略"})

            # 检查消息是否为空
            if not user_message or user_message in ["?", "??", "???", "????", "?????", "？", "？？"]:
                logger.info(f"收到无效消息: '{user_message}'")
                # 对于无效输入给予友好提示
                _get_feishu_client().send_bot_message(
                    "您好！我是AI Helpdesk智能助手，请告诉我您遇到的问题，我会尽力帮您解决。",
                    user_id=sender_id
                )
                return jsonify({"code": 0, "msg": "已提示用户输入有效问题"})

            # 创建或获取会话
            session_id = f"feishu_{chat_id}_{sender_id}"
            if session_id not in chat_manager.active_sessions:
                temp_session_id = chat_manager.create_session(f"{chat_id}_{sender_id}")
                chat_manager.active_sessions[session_id] = chat_manager.active_sessions.pop(temp_session_id)
                chat_manager.message_history[session_id] = chat_manager.message_history.pop(temp_session_id)
                logger.info(f"为飞书用户创建新会话: {session_id}")

            # 处理消息
            response = chat_manager.process_message(session_id, user_message)
            
            # 计算响应时间（毫秒）
            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            bot_response_content = ""
            if response.get("success"):
                bot_response_content = response["content"]
                
                # 发送回复到飞书
                send_result = _get_feishu_client().send_bot_message(bot_response_content, user_id=sender_id)
                
                logger.info(f"飞书消息处理成功 - 响应时间: {response_time_ms:.0f}ms, 发送结果: {send_result}")
            else:
                bot_response_content = f"抱歉，我暂时无法处理您的问题：{response.get('error', '未知错误')}"
                _get_feishu_client().send_bot_message(bot_response_content, user_id=sender_id)
                logger.error(f"处理失败: {response.get('error')}")
            
            return jsonify({
                "code": 0,
                "msg": "成功",
                "bot_response": bot_response_content,
                "response_time_ms": round(response_time_ms, 2)
            })

        except Exception as e:
            logger.error(f"处理飞书消息失败: {e}", exc_info=True)
            # 发送错误提示
            try:
                _get_feishu_client().send_bot_message(
                    "抱歉，系统处理消息时出现错误，请稍后重试或联系技术支持。",
                    user_id=sender.get("sender_id", {}).get("open_id") if 'sender' in locals() else None
                )
            except:
                pass
            return jsonify({"code": 1, "msg": f"处理失败: {e}"}), 500

    return jsonify({"code": 0, "msg": "未处理的事件类型"})
