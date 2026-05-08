# -*- coding: utf-8 -*-
"""
对话历史管理器
支持Redis缓存和数据库持久化
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..core.database import db_manager
from ..core.models import Conversation, WorkOrder, WorkOrderSuggestion, KnowledgeEntry
from ..core.redis_manager import redis_manager
from ..config.unified_config import get_config
from sqlalchemy import and_, or_, desc

logger = logging.getLogger(__name__)

class ConversationHistoryManager:
    """对话历史管理器"""
    
    def __init__(self):
        self.max_history_length = 20  # 最大历史记录数
        self.cache_ttl = 3600 * 24  # 缓存24小时
    
    def _get_redis_client(self):
        """获取Redis客户端"""
        return redis_manager.get_connection()
    
    def _get_cache_key(self, user_id: str, work_order_id: Optional[int] = None) -> str:
        """生成缓存键"""
        if work_order_id:
            return f"conversation_history:work_order:{work_order_id}"
        return f"conversation_history:user:{user_id}"
    
    def save_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        work_order_id: Optional[int] = None,
        confidence_score: Optional[float] = None,
        response_time: Optional[float] = None,
        knowledge_used: Optional[List[int]] = None
    ) -> int:
        """保存对话记录到数据库和Redis"""
        conversation_id = 0
        
        try:
            # 保存到数据库
            with db_manager.get_session() as session:
                conversation = Conversation(
                    work_order_id=work_order_id,
                    user_message=user_message,
                    assistant_response=assistant_response,
                    confidence_score=confidence_score,
                    response_time=response_time,
                    knowledge_used=json.dumps(knowledge_used or [], ensure_ascii=False),
                    timestamp=datetime.now()
                )
                session.add(conversation)
                session.commit()
                conversation_id = conversation.id
            
            # 保存到Redis缓存
            self._save_to_cache(
                user_id=user_id,
                work_order_id=work_order_id,
                user_message=user_message,
                assistant_response=assistant_response,
                conversation_id=conversation_id,
                confidence_score=confidence_score,
                response_time=response_time
            )
            
            logger.info(f"对话记录保存成功: ID={conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
            return conversation_id
    
    def _save_to_cache(
        self,
        user_id: str,
        work_order_id: Optional[int],
        user_message: str,
        assistant_response: str,
        conversation_id: int,
        confidence_score: Optional[float] = None,
        response_time: Optional[float] = None
    ):
        """保存对话到Redis缓存"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(user_id, work_order_id)
            
            # 构建对话记录
            conversation_record = {
                "id": conversation_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "confidence_score": confidence_score,
                "response_time": response_time
            }
            
            # 添加到Redis列表
            redis_client.lpush(cache_key, json.dumps(conversation_record, ensure_ascii=False))
            
            # 限制列表长度
            redis_client.ltrim(cache_key, 0, self.max_history_length - 1)
            
            # 设置过期时间
            redis_client.expire(cache_key, self.cache_ttl)
            
        except Exception as e:
            logger.error(f"保存到Redis缓存失败: {e}")
    
    def get_conversation_history(
        self,
        user_id: str,
        work_order_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取对话历史（优先从Redis获取）"""
        try:
            # 先尝试从Redis获取
            if redis_client:
                cached_history = self._get_from_cache(user_id, work_order_id, limit, offset)
                if cached_history:
                    return cached_history
            
            # 从数据库获取
            return self._get_from_database(user_id, work_order_id, limit, offset)
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    def _get_from_cache(
        self,
        user_id: str,
        work_order_id: Optional[int],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """从Redis缓存获取对话历史"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return []
        
        try:
            cache_key = self._get_cache_key(user_id, work_order_id)
            
            # 获取指定范围的记录
            start = offset
            end = offset + limit - 1
            
            cached_data = redis_client.lrange(cache_key, start, end)
            
            history = []
            for data in cached_data:
                try:
                    record = json.loads(data)
                    history.append(record)
                except json.JSONDecodeError:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"从Redis获取对话历史失败: {e}")
            return []
    
    def _get_from_database(
        self,
        user_id: str,
        work_order_id: Optional[int],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """从数据库获取对话历史"""
        try:
            with db_manager.get_session() as session:
                query = session.query(Conversation)
                
                if work_order_id:
                    query = query.filter(Conversation.work_order_id == work_order_id)
                
                conversations = query.order_by(Conversation.timestamp.desc()).offset(offset).limit(limit).all()
                
                history = []
                for conv in conversations:
                    history.append({
                        "id": conv.id,
                        "user_message": conv.user_message,
                        "assistant_response": conv.assistant_response,
                        "timestamp": conv.timestamp.isoformat(),
                        "confidence_score": conv.confidence_score,
                        "response_time": conv.response_time,
                        "knowledge_used": json.loads(conv.knowledge_used) if conv.knowledge_used else []
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"从数据库获取对话历史失败: {e}")
            return []
    
    def get_conversation_context(
        self,
        user_id: str,
        work_order_id: Optional[int] = None,
        context_length: int = 6
    ) -> str:
        """获取对话上下文（用于LLM）"""
        try:
            history = self.get_conversation_history(user_id, work_order_id, context_length)
            
            if not history:
                return ""
            
            context_parts = []
            for record in reversed(history):  # 按时间正序
                context_parts.append(f"用户: {record['user_message']}")
                context_parts.append(f"助手: {record['assistant_response']}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return ""
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话记录"""
        try:
            with db_manager.get_session() as session:
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    return False
                
                # 从数据库删除
                session.delete(conversation)
                session.commit()
                
                # 从Redis缓存删除（需要重建缓存）
                self._invalidate_cache(conversation.work_order_id)
                
                logger.info(f"对话记录删除成功: ID={conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"删除对话记录失败: {e}")
            return False
    
    def delete_user_conversations(self, user_id: str, work_order_id: Optional[int] = None) -> int:
        """删除用户的所有对话记录"""
        try:
            with db_manager.get_session() as session:
                query = session.query(Conversation)
                
                if work_order_id:
                    query = query.filter(Conversation.work_order_id == work_order_id)
                
                conversations = query.all()
                count = len(conversations)
                
                # 删除数据库记录
                for conv in conversations:
                    session.delete(conv)
                
                session.commit()
                
                # 清除Redis缓存
                self._invalidate_cache(work_order_id)
                
                logger.info(f"删除用户对话记录成功: 用户={user_id}, 数量={count}")
                return count
                
        except Exception as e:
            logger.error(f"删除用户对话记录失败: {e}")
            return 0
    
    def _invalidate_cache(self, work_order_id: Optional[int] = None):
        """清除相关缓存"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return
        
        try:
            # 清除工单相关缓存
            if work_order_id:
                cache_key = f"conversation_history:work_order:{work_order_id}"
                redis_client.delete(cache_key)
            
            # 清除所有用户缓存（简单粗暴的方式）
            pattern = "conversation_history:user:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def get_conversation_stats(self, user_id: str, work_order_id: Optional[int] = None) -> Dict[str, Any]:
        """获取对话统计信息"""
        try:
            with db_manager.get_session() as session:
                query = session.query(Conversation)
                
                if work_order_id:
                    query = query.filter(Conversation.work_order_id == work_order_id)
                
                total_count = query.count()
                
                # 计算平均响应时间
                conversations_with_time = query.filter(Conversation.response_time.isnot(None)).all()
                avg_response_time = 0
                if conversations_with_time:
                    total_time = sum(conv.response_time for conv in conversations_with_time)
                    avg_response_time = total_time / len(conversations_with_time)
                
                # 计算平均置信度
                conversations_with_confidence = query.filter(Conversation.confidence_score.isnot(None)).all()
                avg_confidence = 0
                if conversations_with_confidence:
                    total_confidence = sum(conv.confidence_score for conv in conversations_with_confidence)
                    avg_confidence = total_confidence / len(conversations_with_confidence)
                
                return {
                    "total_conversations": total_count,
                    "avg_response_time": round(avg_response_time, 2),
                    "avg_confidence": round(avg_confidence, 2),
                    "cache_status": "connected" if redis_manager.test_connection() else "disconnected"
                }
                
        except Exception as e:
            logger.error(f"获取对话统计失败: {e}")
            return {
                "total_conversations": 0,
                "avg_response_time": 0,
                "avg_confidence": 0,
                "cache_status": "error"
            }
    
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """清理旧对话记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with db_manager.get_session() as session:
                old_conversations = session.query(Conversation).filter(
                    Conversation.timestamp < cutoff_date
                ).all()
                
                count = len(old_conversations)
                
                for conv in old_conversations:
                    session.delete(conv)
                
                session.commit()
                
                logger.info(f"清理旧对话记录成功: 数量={count}")
                return count
                
        except Exception as e:
            logger.error(f"清理旧对话记录失败: {e}")
            return 0
    
    def get_workorder_complete_timeline(
        self,
        work_order_id: int,
        include_ai_suggestions: bool = True,
        include_feishu_sync: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取工单的完整时间线（包含对话、AI建议、飞书同步）"""
        try:
            timeline = []
            
            with db_manager.get_session() as session:
                # 1. 获取基础对话记录
                conversations = session.query(Conversation).filter(
                    Conversation.work_order_id == work_order_id
                ).order_by(Conversation.timestamp.desc()).limit(limit).all()
                
                for conv in conversations:
                    timeline.append({
                        "id": conv.id,
                        "type": "conversation",
                        "timestamp": conv.timestamp,
                        "user_message": conv.user_message,
                        "assistant_response": conv.assistant_response,
                        "confidence_score": conv.confidence_score,
                        "response_time": conv.response_time,
                        "knowledge_used": json.loads(conv.knowledge_used) if conv.knowledge_used else []
                    })
                
                # 2. 获取AI建议记录
                if include_ai_suggestions:
                    suggestions = session.query(WorkOrderSuggestion).filter(
                        WorkOrderSuggestion.work_order_id == work_order_id
                    ).order_by(WorkOrderSuggestion.created_at.desc()).limit(limit).all()
                    
                    for suggestion in suggestions:
                        timeline.append({
                            "id": f"suggestion_{suggestion.id}",
                            "type": "ai_suggestion",
                            "timestamp": suggestion.created_at,
                            "ai_suggestion": suggestion.ai_suggestion,
                            "human_resolution": suggestion.human_resolution,
                            "ai_similarity": suggestion.ai_similarity,
                            "approved": suggestion.approved,
                            "use_human_resolution": suggestion.use_human_resolution,
                            "updated_at": suggestion.updated_at
                        })
                
                # 3. 获取飞书同步记录（从工单的feishu_record_id推断）
                if include_feishu_sync:
                    work_order = session.query(WorkOrder).filter(
                        WorkOrder.id == work_order_id
                    ).first()
                    
                    if work_order and work_order.feishu_record_id:
                        timeline.append({
                            "id": f"feishu_{work_order.feishu_record_id}",
                            "type": "feishu_sync",
                            "timestamp": work_order.created_at,
                            "feishu_record_id": work_order.feishu_record_id,
                            "order_id": work_order.order_id,
                            "title": work_order.title,
                            "description": work_order.description,
                            "category": work_order.category,
                            "priority": work_order.priority,
                            "status": work_order.status,
                            "source": work_order.source
                        })
            
            # 按时间排序
            timeline.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return timeline[:limit]
            
        except Exception as e:
            logger.error(f"获取工单完整时间线失败: {e}")
            return []
    
    def get_ai_suggestion_context(
        self,
        work_order_id: int,
        suggestion_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取AI建议的对话上下文"""
        try:
            context = {
                "work_order_info": {},
                "conversation_history": [],
                "ai_suggestions": [],
                "knowledge_base": []
            }
            
            with db_manager.get_session() as session:
                # 1. 获取工单信息
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if work_order:
                    context["work_order_info"] = {
                        "id": work_order.id,
                        "order_id": work_order.order_id,
                        "title": work_order.title,
                        "description": work_order.description,
                        "category": work_order.category,
                        "priority": work_order.priority,
                        "status": work_order.status,
                        "created_at": work_order.created_at.isoformat(),
                        "feishu_record_id": work_order.feishu_record_id
                    }
                
                # 2. 获取相关对话历史
                conversations = session.query(Conversation).filter(
                    Conversation.work_order_id == work_order_id
                ).order_by(Conversation.timestamp.desc()).limit(10).all()
                
                for conv in conversations:
                    context["conversation_history"].append({
                        "id": conv.id,
                        "user_message": conv.user_message,
                        "assistant_response": conv.assistant_response,
                        "timestamp": conv.timestamp.isoformat(),
                        "confidence_score": conv.confidence_score
                    })
                
                # 3. 获取AI建议历史
                suggestions = session.query(WorkOrderSuggestion).filter(
                    WorkOrderSuggestion.work_order_id == work_order_id
                ).order_by(WorkOrderSuggestion.created_at.desc()).limit(5).all()
                
                for suggestion in suggestions:
                    context["ai_suggestions"].append({
                        "id": suggestion.id,
                        "ai_suggestion": suggestion.ai_suggestion,
                        "human_resolution": suggestion.human_resolution,
                        "ai_similarity": suggestion.ai_similarity,
                        "approved": suggestion.approved,
                        "use_human_resolution": suggestion.use_human_resolution,
                        "created_at": suggestion.created_at.isoformat()
                    })
                
                # 4. 获取相关知识库条目
                if work_order:
                    knowledge_entries = session.query(KnowledgeEntry).filter(
                        and_(
                            KnowledgeEntry.is_active == True,
                            or_(
                                KnowledgeEntry.category == work_order.category,
                                KnowledgeEntry.question.contains(work_order.title[:20])
                            )
                        )
                    ).limit(5).all()
                    
                    for entry in knowledge_entries:
                        context["knowledge_base"].append({
                            "id": entry.id,
                            "question": entry.question,
                            "answer": entry.answer,
                            "category": entry.category,
                            "confidence_score": entry.confidence_score,
                            "is_verified": entry.is_verified
                        })
            
            return context
            
        except Exception as e:
            logger.error(f"获取AI建议对话上下文失败: {e}")
            return {}
    
    def search_conversations_by_content(
        self,
        search_query: str,
        work_order_id: Optional[int] = None,
        conversation_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """根据内容搜索对话记录（包含AI建议）"""
        try:
            results = []
            
            with db_manager.get_session() as session:
                # 搜索基础对话
                conv_query = session.query(Conversation)
                if work_order_id:
                    conv_query = conv_query.filter(Conversation.work_order_id == work_order_id)
                
                conversations = conv_query.filter(
                    or_(
                        Conversation.user_message.contains(search_query),
                        Conversation.assistant_response.contains(search_query)
                    )
                ).order_by(Conversation.timestamp.desc()).limit(limit).all()
                
                for conv in conversations:
                    results.append({
                        "id": conv.id,
                        "type": "conversation",
                        "timestamp": conv.timestamp,
                        "user_message": conv.user_message,
                        "assistant_response": conv.assistant_response,
                        "work_order_id": conv.work_order_id,
                        "confidence_score": conv.confidence_score
                    })
                
                # 搜索AI建议
                if not conversation_type or conversation_type == "ai_suggestion":
                    suggestion_query = session.query(WorkOrderSuggestion)
                    if work_order_id:
                        suggestion_query = suggestion_query.filter(
                            WorkOrderSuggestion.work_order_id == work_order_id
                        )
                    
                    suggestions = suggestion_query.filter(
                        or_(
                            WorkOrderSuggestion.ai_suggestion.contains(search_query),
                            WorkOrderSuggestion.human_resolution.contains(search_query)
                        )
                    ).order_by(WorkOrderSuggestion.created_at.desc()).limit(limit).all()
                    
                    for suggestion in suggestions:
                        results.append({
                            "id": f"suggestion_{suggestion.id}",
                            "type": "ai_suggestion",
                            "timestamp": suggestion.created_at,
                            "ai_suggestion": suggestion.ai_suggestion,
                            "human_resolution": suggestion.human_resolution,
                            "work_order_id": suggestion.work_order_id,
                            "ai_similarity": suggestion.ai_similarity,
                            "approved": suggestion.approved
                        })
            
            # 按时间排序
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索对话记录失败: {e}")
            return []
    
    def get_conversation_analytics(
        self,
        work_order_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取对话分析数据（包含AI建议统计）"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with db_manager.get_session() as session:
                analytics = {
                    "period_days": days,
                    "conversations": {},
                    "ai_suggestions": {},
                    "performance": {}
                }
                
                # 对话统计
                conv_query = session.query(Conversation)
                if work_order_id:
                    conv_query = conv_query.filter(Conversation.work_order_id == work_order_id)
                
                conversations = conv_query.filter(
                    Conversation.timestamp >= cutoff_date
                ).all()
                
                analytics["conversations"] = {
                    "total": len(conversations),
                    "avg_confidence": 0,
                    "avg_response_time": 0,
                    "high_confidence_count": 0
                }
                
                if conversations:
                    confidences = [c.confidence_score for c in conversations if c.confidence_score]
                    response_times = [c.response_time for c in conversations if c.response_time]
                    
                    if confidences:
                        analytics["conversations"]["avg_confidence"] = sum(confidences) / len(confidences)
                        analytics["conversations"]["high_confidence_count"] = len([c for c in confidences if c >= 0.8])
                    
                    if response_times:
                        analytics["conversations"]["avg_response_time"] = sum(response_times) / len(response_times)
                
                # AI建议统计
                suggestion_query = session.query(WorkOrderSuggestion)
                if work_order_id:
                    suggestion_query = suggestion_query.filter(
                        WorkOrderSuggestion.work_order_id == work_order_id
                    )
                
                suggestions = suggestion_query.filter(
                    WorkOrderSuggestion.created_at >= cutoff_date
                ).all()
                
                analytics["ai_suggestions"] = {
                    "total": len(suggestions),
                    "approved_count": len([s for s in suggestions if s.approved]),
                    "avg_similarity": 0,
                    "human_resolution_count": len([s for s in suggestions if s.use_human_resolution])
                }
                
                if suggestions:
                    similarities = [s.ai_similarity for s in suggestions if s.ai_similarity]
                    if similarities:
                        analytics["ai_suggestions"]["avg_similarity"] = sum(similarities) / len(similarities)
                
                # 性能指标
                analytics["performance"] = {
                    "conversation_success_rate": 0,
                    "ai_suggestion_approval_rate": 0,
                    "knowledge_base_usage_rate": 0
                }
                
                if conversations:
                    successful_convs = len([c for c in conversations if c.confidence_score and c.confidence_score >= 0.5])
                    analytics["performance"]["conversation_success_rate"] = successful_convs / len(conversations)
                
                if suggestions:
                    analytics["performance"]["ai_suggestion_approval_rate"] = len([s for s in suggestions if s.approved]) / len(suggestions)
                
                return analytics
                
        except Exception as e:
            logger.error(f"获取对话分析数据失败: {e}")
            return {}
