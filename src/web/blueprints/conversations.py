# -*- coding: utf-8 -*-
"""
对话管理蓝图
处理对话相关的API路由，整合飞书工单和AI建议
"""

from flask import Blueprint, request, jsonify
from src.core.database import db_manager
from src.core.models import Conversation, WorkOrder, WorkOrderSuggestion
from src.core.query_optimizer import query_optimizer
from src.dialogue.conversation_history import ConversationHistoryManager
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')

# 初始化对话历史管理器
history_manager = ConversationHistoryManager()

@conversations_bp.route('')
def get_conversations():
    """获取对话历史列表（分页）- 优化版"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        user_id = request.args.get('user_id', '')
        date_filter = request.args.get('date_filter', '')
        
        # 使用优化后的查询
        result = query_optimizer.get_conversations_paginated(
            page=page, per_page=per_page, search=search, 
            user_id=user_id, date_filter=date_filter
        )
        
        # 规范化：移除不存在的user_id字段，避免前端误用
        for conv in result.get('conversations', []):
            if 'user_id' in conv and conv['user_id'] is None:
                conv.pop('user_id', None)
        
        # 扁平化分页信息，与前端期望格式一致
        if result.get('success'):
            pagination = result.get('pagination', {})
            return jsonify({
                'conversations': result.get('conversations', []),
                'page': pagination.get('current_page', page),
                'per_page': pagination.get('per_page', per_page),
                'total': pagination.get('total', 0),
                'total_pages': pagination.get('total_pages', 1),
                'stats': result.get('stats', {})
            })
        else:
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/<int:conversation_id>')
def get_conversation_detail(conversation_id):
    """获取对话详情"""
    try:
        with db_manager.get_session() as session:
            conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conv:
                return jsonify({"error": "对话不存在"}), 404
            
            # Conversation模型没有user_id字段，这里用占位或由外层推断
            return jsonify({
                'success': True,
                'id': conv.id,
                'user_id': None,
                'user_message': conv.user_message,
                'assistant_response': conv.assistant_response,
                'timestamp': conv.timestamp.isoformat() if conv.timestamp else None,
                'response_time': conv.response_time,
                'work_order_id': conv.work_order_id
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话记录"""
    try:
        with db_manager.get_session() as session:
            conv = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conv:
                return jsonify({"error": "对话不存在"}), 404
            
            session.delete(conv)
            session.commit()
            
            # 清除对话历史相关缓存
            from src.core.cache_manager import cache_manager
            cache_manager.clear()  # 清除所有缓存
            
            return jsonify({"success": True, "message": "对话记录已删除"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/clear', methods=['DELETE'])
def clear_all_conversations():
    """清空所有对话历史"""
    try:
        with db_manager.get_session() as session:
            session.query(Conversation).delete()
            session.commit()
            
            # 清除对话历史相关缓存
            from src.core.cache_manager import cache_manager
            cache_manager.clear()  # 清除所有缓存
            
            return jsonify({"success": True, "message": "对话历史已清空"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/migrate-merge', methods=['POST'])
def migrate_merge_conversations():
    """一次性迁移：将历史上拆分存储的用户/助手两条记录合并为一条
    规则：
      - 只处理一端为空的记录（user_only 或 assistant_only）
      - 优先将 user_only 与其后最近的 assistant_only 合并（同工单且5分钟内）
      - 若当前为 assistant_only 且前一条是 user_only 也合并到前一条
      - 合并后删除被吸收的那条记录
      - 可重复执行（幂等）：已合并的不再满足“一端为空”的条件
    """
    try:
        merged_pairs = 0
        deleted_rows = 0
        time_threshold_seconds = 300
        to_delete_ids = []
        with db_manager.get_session() as session:
            conversations = session.query(Conversation).order_by(Conversation.timestamp.asc(), Conversation.id.asc()).all()
            total = len(conversations)
            i = 0

            def is_empty(text: str) -> bool:
                return (text is None) or (str(text).strip() == '')

            while i < total:
                c = conversations[i]
                user_only = (not is_empty(c.user_message)) and is_empty(c.assistant_response)
                assistant_only = (not is_empty(c.assistant_response)) and is_empty(c.user_message)

                if user_only:
                    # 向后寻找匹配的assistant_only
                    j = i + 1
                    while j < total:
                        n = conversations[j]
                        # 跳过已经标记删除的
                        if n.id in to_delete_ids:
                            j += 1
                            continue
                        # 超过阈值不再尝试
                        if c.timestamp and n.timestamp and (n.timestamp - c.timestamp).total_seconds() > time_threshold_seconds:
                            break
                        # 同工单或两者都为空均可
                        same_wo = (c.work_order_id == n.work_order_id) or (c.work_order_id is None and n.work_order_id is None)
                        if same_wo and (not is_empty(n.assistant_response)) and is_empty(n.user_message):
                            # 合并
                            c.assistant_response = n.assistant_response
                            if c.response_time is None and c.timestamp and n.timestamp:
                                try:
                                    c.response_time = max(0.0, (n.timestamp - c.timestamp).total_seconds() * 1000.0)
                                except Exception:
                                    pass
                            # 继承辅助信息
                            if (not c.confidence_score) and n.confidence_score is not None:
                                c.confidence_score = n.confidence_score
                            if (not c.knowledge_used) and n.knowledge_used:
                                c.knowledge_used = n.knowledge_used
                            session.add(c)
                            to_delete_ids.append(n.id)
                            merged_pairs += 1
                            break
                        j += 1

                elif assistant_only:
                    # 向前与最近的 user_only 合并（如果尚未被其他合并吸收）
                    j = i - 1
                    while j >= 0:
                        p = conversations[j]
                        if p.id in to_delete_ids:
                            j -= 1
                            continue
                        if p.timestamp and c.timestamp and (c.timestamp - p.timestamp).total_seconds() > time_threshold_seconds:
                            break
                        same_wo = (c.work_order_id == p.work_order_id) or (c.work_order_id is None and p.work_order_id is None)
                        if same_wo and (not is_empty(p.user_message)) and is_empty(p.assistant_response):
                            p.assistant_response = c.assistant_response
                            if p.response_time is None and p.timestamp and c.timestamp:
                                try:
                                    p.response_time = max(0.0, (c.timestamp - p.timestamp).total_seconds() * 1000.0)
                                except Exception:
                                    pass
                            if (not p.confidence_score) and c.confidence_score is not None:
                                p.confidence_score = c.confidence_score
                            if (not p.knowledge_used) and c.knowledge_used:
                                p.knowledge_used = c.knowledge_used
                            session.add(p)
                            to_delete_ids.append(c.id)
                            merged_pairs += 1
                            break
                        j -= 1

                i += 1

            if to_delete_ids:
                deleted_rows = session.query(Conversation).filter(Conversation.id.in_(to_delete_ids)).delete(synchronize_session=False)
            session.commit()

        return jsonify({
            'success': True,
            'merged_pairs': merged_pairs,
            'deleted_rows': deleted_rows
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/workorder/<int:work_order_id>/timeline')
def get_workorder_timeline(work_order_id):
    """获取工单的完整对话时间线（包含AI建议和飞书同步）"""
    try:
        include_ai_suggestions = request.args.get('include_ai_suggestions', 'true').lower() == 'true'
        include_feishu_sync = request.args.get('include_feishu_sync', 'true').lower() == 'true'
        limit = request.args.get('limit', 20, type=int)
        
        timeline = history_manager.get_workorder_complete_timeline(
            work_order_id=work_order_id,
            include_ai_suggestions=include_ai_suggestions,
            include_feishu_sync=include_feishu_sync,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'work_order_id': work_order_id,
            'timeline': timeline,
            'total_count': len(timeline)
        })
        
    except Exception as e:
        logger.error(f"获取工单时间线失败: {e}")
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/workorder/<int:work_order_id>/context')
def get_workorder_context(work_order_id):
    """获取工单的AI建议对话上下文"""
    try:
        suggestion_id = request.args.get('suggestion_id', type=int)
        
        context = history_manager.get_ai_suggestion_context(
            work_order_id=work_order_id,
            suggestion_id=suggestion_id
        )
        
        return jsonify({
            'success': True,
            'work_order_id': work_order_id,
            'context': context
        })
        
    except Exception as e:
        logger.error(f"获取工单上下文失败: {e}")
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/workorder/<int:work_order_id>/summary')
def get_workorder_summary(work_order_id):
    """获取工单对话摘要"""
    try:
        # 获取时间线数据
        timeline = history_manager.get_workorder_complete_timeline(
            work_order_id=work_order_id,
            include_ai_suggestions=True,
            include_feishu_sync=True,
            limit=50
        )
        
        if not timeline:
            return jsonify({"error": "没有找到对话记录"}), 404
        
        # 生成简单摘要
        summary = {
            "work_order_id": work_order_id,
            "total_interactions": len(timeline),
            "conversations": len([t for t in timeline if t["type"] == "conversation"]),
            "ai_suggestions": len([t for t in timeline if t["type"] == "ai_suggestion"]),
            "feishu_syncs": len([t for t in timeline if t["type"] == "feishu_sync"]),
            "generated_at": timeline[0]["timestamp"].isoformat() if timeline else None
        }
        
        return jsonify({
            'success': True,
            'work_order_id': work_order_id,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"获取工单摘要失败: {e}")
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/search')
def search_conversations():
    """搜索对话记录（包含AI建议）"""
    try:
        search_query = request.args.get('q', '')
        work_order_id = request.args.get('work_order_id', type=int)
        conversation_type = request.args.get('type')  # conversation, ai_suggestion, all
        limit = request.args.get('limit', 20, type=int)
        
        if not search_query:
            return jsonify({"error": "搜索查询不能为空"}), 400
        
        results = history_manager.search_conversations_by_content(
            search_query=search_query,
            work_order_id=work_order_id,
            conversation_type=conversation_type,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'query': search_query,
            'results': results,
            'total_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索对话记录失败: {e}")
        return jsonify({"error": str(e)}), 500

@conversations_bp.route('/analytics')
def get_conversation_analytics():
    """获取对话分析数据"""
    try:
        work_order_id = request.args.get('work_order_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        analytics = history_manager.get_conversation_analytics(
            work_order_id=work_order_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"获取对话分析数据失败: {e}")
        return jsonify({"error": str(e)}), 500
