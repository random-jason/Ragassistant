"""
实时对话管理器
提供实时对话功能，集成知识库搜索和LLM回复
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from ..core.llm_client import QwenClient
from ..knowledge_base.knowledge_manager import KnowledgeManager
from ..core.database import db_manager
from ..core.models import Conversation, WorkOrder

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    message_id: str
    work_order_id: Optional[int] = None
    knowledge_used: Optional[List[Dict]] = None
    confidence_score: Optional[float] = None

class RealtimeChatManager:
    """实时对话管理器"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.knowledge_manager = KnowledgeManager()
        self.active_sessions = {}  # 存储活跃的对话会话
        self.message_history = {}  # 存储消息历史
        
    def create_session(self, user_id: str, work_order_id: Optional[int] = None) -> str:
        """创建新的对话会话"""
        session_id = f"session_{user_id}_{int(time.time())}"
        
        session_data = {
            "user_id": user_id,
            "work_order_id": work_order_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0,
            "context": []
        }
        
        self.active_sessions[session_id] = session_data
        self.message_history[session_id] = []
        
        logger.info(f"创建新会话: {session_id}")
        return session_id
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            if session_id not in self.active_sessions:
                return {"error": "会话不存在"}
            
            session = self.active_sessions[session_id]
            session["last_activity"] = datetime.now()
            session["message_count"] += 1
            
            # 创建用户消息
            user_msg = ChatMessage(
                role="user",
                content=user_message,
                timestamp=datetime.now(),
                message_id=f"msg_{int(time.time())}_{session['message_count']}"
            )
            
            # 添加到消息历史
            self.message_history[session_id].append(user_msg)
            
            # 搜索相关知识
            knowledge_results = self._search_knowledge(user_message)

            # 生成回复
            assistant_response = self._generate_response(
                user_message, 
                knowledge_results, 
                session["context"],
                session["work_order_id"]
            )
            
            # 创建助手消息
            assistant_msg = ChatMessage(
                role="assistant",
                content=assistant_response["content"],
                timestamp=datetime.now(),
                message_id=f"msg_{int(time.time())}_{session['message_count'] + 1}",
                work_order_id=session["work_order_id"],
                knowledge_used=knowledge_results,
                confidence_score=assistant_response.get("confidence", 0.5)
            )
            
            # 添加到消息历史
            self.message_history[session_id].append(assistant_msg)
            
            # 更新上下文
            session["context"].append({
                "role": "user",
                "content": user_message
            })
            session["context"].append({
                "role": "assistant", 
                "content": assistant_response["content"]
            })
            
            # 保持上下文长度
            if len(session["context"]) > 20:  # 保留最近10轮对话
                session["context"] = session["context"][-20:]
            
            # 保存到数据库（每轮一条，带会话标记）
            self._save_conversation(session_id, user_msg, assistant_msg)

            # 更新知识库使用次数
            if knowledge_results:
                used_entry_ids = [result["id"] for result in knowledge_results if result.get("id")]
                if used_entry_ids:
                    self.knowledge_manager.update_usage_count(used_entry_ids)

            return {
                "success": True,
                "response": assistant_response["content"],  # 修改为response字段
                "message_id": assistant_msg.message_id,
                "content": assistant_response["content"],  # 保留content字段以兼容
                "knowledge_used": knowledge_results,
                "confidence_score": assistant_response.get("confidence", 0.5),
                "work_order_id": session["work_order_id"],
                "timestamp": assistant_msg.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {"error": f"处理消息失败: {str(e)}"}
    
    def _search_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        try:
            results = self.knowledge_manager.search_knowledge(query, top_k)
            return results
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    def _generate_response(self, user_message: str, knowledge_results: List[Dict], context: List[Dict], work_order_id: Optional[int] = None) -> Dict[str, Any]:
        """生成回复"""
        try:
            # 检查是否有相关的工单AI建议
            ai_suggestions = self._get_workorder_ai_suggestions(work_order_id)
            
            # 构建提示词
            prompt = self._build_chat_prompt(user_message, knowledge_results, context, ai_suggestions)
            
            # 调用大模型
            response = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
                confidence = self._calculate_confidence(knowledge_results, content)
                
                # 如果有AI建议，在回复中包含
                if ai_suggestions:
                    content = self._format_response_with_ai_suggestions(content, ai_suggestions)
                
                return {
                    "content": content,
                    "confidence": confidence,
                    "ai_suggestions": ai_suggestions
                }
            else:
                return {
                    "content": "抱歉，我暂时无法处理您的问题。请稍后再试或联系人工客服。",
                    "confidence": 0.1,
                    "ai_suggestions": ai_suggestions
                }
                
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return {
                "content": "抱歉，系统出现错误，请稍后再试。",
                "confidence": 0.1,
                "ai_suggestions": []
            }
    
    def _build_chat_prompt(self, user_message: str, knowledge_results: List[Dict], context: List[Dict], ai_suggestions: List[str] = None) -> str:
        """构建聊天提示词"""
        prompt = f"""
你是一个专业的智能客服助手。请根据用户的问题和提供的知识库信息，给出专业、友好的回复。

用户问题：{user_message}

相关知识库信息：
"""
        
        if knowledge_results:
            for i, result in enumerate(knowledge_results, 1):
                prompt += f"\n{i}. 问题：{result.get('question', '')}"
                prompt += f"\n   答案：{result.get('answer', '')}"
                prompt += f"\n   相似度：{result.get('similarity_score', 0):.3f}\n"
        else:
            prompt += "\n未找到相关知识库信息。\n"
        
        # 添加AI建议信息
        if ai_suggestions:
            prompt += "\n相关AI建议：\n"
            for suggestion in ai_suggestions:
                prompt += f"- {suggestion}\n"
        
        # 添加上下文
        if context:
            prompt += "\n对话历史：\n"
            for msg in context[-6:]:  # 最近3轮对话
                prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += """
请按照以下要求回复：
1. 语言要专业、友好、易懂
2. 如果知识库中有相关信息，优先使用知识库内容
3. 如果没有相关知识，请提供一般性建议
4. 如果问题需要进站处理，请明确说明
5. 回复要简洁明了，避免冗长
6. 如果涉及技术问题，要提供具体的操作步骤

请直接给出回复内容，不要包含其他格式：
"""
        
        return prompt

    def _get_workorder_ai_suggestions(self, work_order_id: Optional[int]) -> List[str]:
        """
        获取工单的AI建议
        
        Args:
            work_order_id: 工单ID
            
        Returns:
            AI建议列表
        """
        try:
            if not work_order_id:
                return []
            
            with db_manager.get_session() as session:
                # 查询工单的AI建议
                from ..core.models import WorkOrderSuggestion
                suggestions = session.query(WorkOrderSuggestion).filter(
                    WorkOrderSuggestion.work_order_id == work_order_id
                ).order_by(WorkOrderSuggestion.created_at.desc()).limit(3).all()
                
                ai_suggestions = []
                for suggestion in suggestions:
                    if suggestion.ai_suggestion:
                        ai_suggestions.append(suggestion.ai_suggestion)
                
                return ai_suggestions
                
        except Exception as e:
            logger.error(f"获取工单AI建议失败: {e}")
            return []
    
    def _format_response_with_ai_suggestions(self, content: str, ai_suggestions: List[str]) -> str:
        """
        在回复中格式化AI建议
        
        Args:
            content: 原始回复内容
            ai_suggestions: AI建议列表
            
        Returns:
            包含AI建议的格式化回复
        """
        try:
            if not ai_suggestions:
                return content
            
            # 在回复末尾添加AI建议
            formatted_content = content
            
            formatted_content += "\n\n📋 **相关AI建议：**\n"
            for i, suggestion in enumerate(ai_suggestions, 1):
                formatted_content += f"{i}. {suggestion}\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"格式化AI建议失败: {e}")
            return content

    def _calculate_confidence(self, knowledge_results: List[Dict], response_content: str) -> float:
        """计算回复置信度"""
        if not knowledge_results:
            return 0.3
        
        # 基于知识库结果计算基础置信度
        max_similarity = max([r.get('similarity_score', 0) for r in knowledge_results])
        base_confidence = min(max_similarity * 1.2, 0.9)  # 最高0.9
        
        # 根据回复长度调整
        if len(response_content) < 50:
            base_confidence *= 0.8
        elif len(response_content) > 500:
            base_confidence *= 0.9
        
        return base_confidence
    
    def _save_conversation(self, session_id: str, user_msg: ChatMessage, assistant_msg: ChatMessage):
        """保存对话到数据库"""
        try:
            with db_manager.get_session() as session:
                # 统一为一条记录：包含用户消息与助手回复
                try:
                    response_time = None
                    if assistant_msg.timestamp and user_msg.timestamp:
                        response_time = max(0.0, (assistant_msg.timestamp - user_msg.timestamp).total_seconds() * 1000.0)
                except Exception:
                    response_time = None

                # 在知识字段中打上会话标记，便于结束时合并清理
                marked_knowledge = assistant_msg.knowledge_used or []
                try:
                    marked_knowledge = list(marked_knowledge)
                    marked_knowledge.append({"session_id": session_id, "type": "session_marker"})
                except Exception:
                    pass

                conversation = Conversation(
                    work_order_id=assistant_msg.work_order_id or user_msg.work_order_id,
                    user_message=user_msg.content or "",
                    assistant_response=assistant_msg.content or "",
                    timestamp=assistant_msg.timestamp or user_msg.timestamp,
                    confidence_score=assistant_msg.confidence_score,
                    knowledge_used=json.dumps(marked_knowledge, ensure_ascii=False) if marked_knowledge else None,
                    response_time=response_time
                )
                session.add(conversation)
                session.commit()
                
        except Exception as e:
            logger.error(f"保存对话失败: {e}")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if session_id not in self.message_history:
            return []
        
        history = []
        for msg in self.message_history[session_id]:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_id": msg.message_id,
                "knowledge_used": msg.knowledge_used,
                "confidence_score": msg.confidence_score
            })
        
        return history
    
    def create_work_order(self, session_id: str, title: str, description: str, category: str, priority: str = "medium") -> Dict[str, Any]:
        """创建工单"""
        try:
            if session_id not in self.active_sessions:
                return {"error": "会话不存在"}
            
            session = self.active_sessions[session_id]
            
            with db_manager.get_session() as db_session:
                work_order = WorkOrder(
                    order_id=f"WO_{int(time.time())}",
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    status="open",
                    created_at=datetime.now()
                )
                db_session.add(work_order)
                db_session.commit()
                
                # 更新会话的工单ID
                session["work_order_id"] = work_order.id
                
                return {
                    "success": True,
                    "work_order_id": work_order.id,
                    "order_id": work_order.order_id,
                    "message": "工单创建成功"
                }
                
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            return {"error": f"创建工单失败: {str(e)}"}
    
    def get_work_order_status(self, work_order_id: int) -> Dict[str, Any]:
        """获取工单状态"""
        try:
            with db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
                
                if not work_order:
                    return {"error": "工单不存在"}
                
                return {
                    "work_order_id": work_order.id,
                    "order_id": work_order.order_id,
                    "title": work_order.title,
                    "status": work_order.status,
                    "priority": work_order.priority,
                    "created_at": work_order.created_at.isoformat(),
                    "updated_at": work_order.updated_at.isoformat() if work_order.updated_at else None,
                    "resolution": work_order.resolution,
                    "satisfaction_score": work_order.satisfaction_score
                }
                
        except Exception as e:
            logger.error(f"获取工单状态失败: {e}")
            return {"error": f"获取工单状态失败: {str(e)}"}
    
    def end_session(self, session_id: str) -> bool:
        """结束会话"""
        try:
            if session_id in self.active_sessions:
                session_meta = self.active_sessions[session_id]
                # 汇总本会话为一条记录
                history = self.message_history.get(session_id, [])
                if history:
                    user_parts = []
                    assistant_parts = []
                    response_times = []
                    first_ts = None
                    last_ts = None
                    for i in range(len(history)):
                        msg = history[i]
                        if first_ts is None:
                            first_ts = msg.timestamp
                        last_ts = msg.timestamp
                        if msg.role == "user":
                            user_parts.append(msg.content)
                            # 计算到下一条助手回复的间隔
                            if i + 1 < len(history) and history[i+1].role == "assistant":
                                try:
                                    rt = max(0.0, (history[i+1].timestamp - msg.timestamp).total_seconds() * 1000.0)
                                    response_times.append(rt)
                                except Exception:
                                    pass
                        elif msg.role == "assistant":
                            assistant_parts.append(msg.content)
                    agg_user = "\n\n".join([p for p in user_parts if p])
                    agg_assistant = "\n\n".join([p for p in assistant_parts if p])
                    avg_rt = sum(response_times)/len(response_times) if response_times else None

                    from ..core.database import db_manager as _db
                    from ..core.models import Conversation as _Conv
                    import json as _json
                    with _db.get_session() as dbs:
                        agg = _Conv(
                            work_order_id=session_meta.get("work_order_id"),
                            user_message=agg_user,
                            assistant_response=agg_assistant,
                            timestamp=last_ts or first_ts,
                            confidence_score=None,
                            knowledge_used=_json.dumps({"session_id": session_id, "aggregated": True}, ensure_ascii=False),
                            response_time=avg_rt
                        )
                        dbs.add(agg)
                        # 删除本会话标记的分散记录
                        try:
                            pattern = f'%"session_id":"{session_id}"%'
                            dbs.query(_Conv).filter(_Conv.knowledge_used.like(pattern)).delete(synchronize_session=False)
                        except Exception:
                            pass
                        dbs.commit()
                del self.active_sessions[session_id]
            
            if session_id in self.message_history:
                del self.message_history[session_id]
            
            logger.info(f"结束会话: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"结束会话失败: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取活跃会话列表"""
        sessions = []
        for session_id, session_data in self.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "user_id": session_data["user_id"],
                "work_order_id": session_data["work_order_id"],
                "created_at": session_data["created_at"].isoformat(),
                "last_activity": session_data["last_activity"].isoformat(),
                "message_count": session_data["message_count"]
            })
        
        return sessions
