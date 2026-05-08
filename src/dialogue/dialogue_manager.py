import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..core.database import db_manager
from ..core.models import WorkOrder, Conversation
from ..core.llm_client import QwenClient
from ..knowledge_base.knowledge_manager import KnowledgeManager
from .conversation_history import ConversationHistoryManager
from ..analytics.token_monitor import TokenMonitor
from ..analytics.ai_success_monitor import AISuccessMonitor
from ..core.system_optimizer import SystemOptimizer

logger = logging.getLogger(__name__)

class DialogueManager:
    """对话管理器"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.knowledge_manager = KnowledgeManager()
        self.history_manager = ConversationHistoryManager()
        self.token_monitor = TokenMonitor()
        self.ai_success_monitor = AISuccessMonitor()
        self.system_optimizer = SystemOptimizer()
        self.conversation_history = {}  # 存储对话历史
    
    def process_user_message(
        self,
        user_message: str,
        work_order_id: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理用户消息"""
        start_time = datetime.now()
        success = False
        error_message = None
        
        try:
            # 检查频率限制
            if not self.system_optimizer.check_rate_limit(user_id or "anonymous"):
                return {"error": "请求频率过高，请稍后再试"}
            
            # 检查输入安全性
            security_check = self.system_optimizer.check_input_security(user_message)
            if not security_check["is_safe"]:
                return {"error": f"输入不安全: {security_check['message']}"}
            
            # 搜索相关知识库（只搜索已验证的）
            knowledge_results = self.knowledge_manager.search_knowledge(
                user_message, top_k=3, verified_only=True
            )
            
            # 构建上下文（包含历史对话）
            context = self._build_context(work_order_id, user_id)

            # 准备知识库信息
            knowledge_context = ""
            if knowledge_results:
                knowledge_context = "相关知识库信息:\n"
                for i, result in enumerate(knowledge_results[:2], 1):
                    knowledge_context += f"{i}. 问题: {result['question']}\n"
                    knowledge_context += f"   答案: {result['answer']}\n"
                    knowledge_context += f"   置信度: {result['confidence_score']:.2f}\n\n"

            # 生成回复
            response_result = self.llm_client.generate_response(
                user_message=user_message,
                context=context,
                knowledge_base=[knowledge_context] if knowledge_context else None
            )
            
            if "error" in response_result:
                error_message = response_result["error"]
                success = False
            else:
                success = True
            
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 性能优化分析
            optimization_result = self.system_optimizer.optimize_response_time(response_time)
            
            # 记录Token使用情况（兼容多种返回格式）
            if success:
                # 兼容返回 usage: {prompt_tokens, completion_tokens}
                usage = response_result.get("usage", {}) or {}
                token_usage = response_result.get("token_usage", {}) or {}
                input_tokens = token_usage.get("input_tokens")
                output_tokens = token_usage.get("output_tokens")
                if input_tokens is None and isinstance(usage, dict):
                    input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                if output_tokens is None and isinstance(usage, dict):
                    output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0

                # 若均为0，使用简易估算（避免记录缺失）
                if not input_tokens and user_message:
                    try:
                        input_tokens = max(1, len(user_message) // 4)
                    except Exception:
                        input_tokens = 0
                if not output_tokens and response_result.get("response"):
                    try:
                        output_tokens = max(1, len(response_result.get("response")) // 4)
                    except Exception:
                        output_tokens = 0

                model_name = response_result.get("model") or response_result.get("model_name") or "qwen-plus-latest"

                # 计算成本并限制
                estimated_cost = self.token_monitor._calculate_cost(
                    model_name,
                    int(input_tokens or 0),
                    int(output_tokens or 0)
                )
                if not self.system_optimizer.check_cost_limit(estimated_cost):
                    return {"error": "请求成本超限，请稍后再试"}

                self.token_monitor.record_token_usage(
                    user_id=user_id or "anonymous",
                    work_order_id=work_order_id,
                    model_name=model_name,
                    input_tokens=int(input_tokens or 0),
                    output_tokens=int(output_tokens or 0),
                    response_time=response_time,
                    success=success,
                    error_message=error_message
                )
            
            # 记录API调用
            self.ai_success_monitor.record_api_call(
                user_id=user_id or "anonymous",
                work_order_id=work_order_id,
                model_name=response_result.get("model_name", "qwen-plus-latest"),
                endpoint="chat/completions",
                success=success,
                response_time=response_time,
                error_message=error_message,
                input_length=len(user_message),
                output_length=len(response_result.get("response", ""))
            )
            
            if not success:
                return response_result
            
            # 保存对话记录到历史管理器
            conversation_id = self.history_manager.save_conversation(
                user_id=user_id or "anonymous",
                work_order_id=work_order_id,
                user_message=user_message,
                assistant_response=response_result["response"],
                confidence_score=self._calculate_confidence(knowledge_results),
                response_time=response_time,
                knowledge_used=[r["id"] for r in knowledge_results]
            )
            
            # 更新内存中的对话历史
            if user_id:
                if user_id not in self.conversation_history:
                    self.conversation_history[user_id] = []
                self.conversation_history[user_id].append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history[user_id].append({
                    "role": "assistant",
                    "content": response_result["response"],
                    "timestamp": datetime.now().isoformat()
                })
                
                # 保持历史记录在限制范围内
                if len(self.conversation_history[user_id]) > 20:  # 10轮对话
                    self.conversation_history[user_id] = self.conversation_history[user_id][-20:]
            
            return {
                "response": response_result["response"],
                "conversation_id": conversation_id,
                "knowledge_used": knowledge_results,
                "confidence_score": self._calculate_confidence(knowledge_results),
                "response_time": response_time,
                "optimization": optimization_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_message = str(e)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 记录失败的API调用
            self.ai_success_monitor.record_api_call(
                user_id=user_id or "anonymous",
                work_order_id=work_order_id,
                model_name="qwen-plus-latest",
                endpoint="chat/completions",
                success=False,
                response_time=response_time,
                error_message=error_message,
                input_length=len(user_message),
                output_length=0
            )
            
            logger.error(f"处理用户消息失败: {e}")
            return {"error": f"处理失败: {str(e)}"}
    
    def _build_context(self, work_order_id: Optional[int], user_id: Optional[str]) -> str:
        """构建对话上下文"""
        context_parts = []
        
        # 添加工单信息
        if work_order_id:
            try:
                with db_manager.get_session() as session:
                    work_order = session.query(WorkOrder).filter(
                        WorkOrder.id == work_order_id
                    ).first()
                    
                    if work_order:
                        context_parts.append(f"当前工单信息:")
                        context_parts.append(f"工单号: {work_order.order_id}")
                        context_parts.append(f"标题: {work_order.title}")
                        context_parts.append(f"描述: {work_order.description}")
                        context_parts.append(f"类别: {work_order.category}")
                        context_parts.append(f"优先级: {work_order.priority}")
                        context_parts.append(f"状态: {work_order.status}")
            except Exception as e:
                logger.error(f"获取工单信息失败: {e}")
        
        # 添加用户历史对话（优先从历史管理器获取）
        if user_id:
            # 尝试从历史管理器获取上下文
            history_context = self.history_manager.get_conversation_context(
                user_id=user_id,
                work_order_id=work_order_id,
                context_length=6
            )
            if history_context:
                context_parts.append("最近的对话历史:")
                context_parts.append(history_context)
            elif user_id in self.conversation_history:
                # 回退到内存中的历史
                recent_history = self.conversation_history[user_id][-6:]  # 最近3轮对话
                if recent_history:
                    context_parts.append("最近的对话历史:")
                    for msg in recent_history:
                        role = "用户" if msg["role"] == "user" else "助手"
                        context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _save_conversation(
        self,
        work_order_id: Optional[int],
        user_message: str,
        assistant_response: str,
        knowledge_used: str
    ) -> int:
        """保存对话记录"""
        try:
            with db_manager.get_session() as session:
                conversation = Conversation(
                    work_order_id=work_order_id,
                    user_message=user_message,
                    assistant_response=assistant_response,
                    knowledge_used=knowledge_used,
                    timestamp=datetime.now()
                )
                session.add(conversation)
                session.commit()
                return conversation.id
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
            return 0
    
    def _calculate_confidence(self, knowledge_results: List[Dict[str, Any]]) -> float:
        """计算回复置信度"""
        if not knowledge_results:
            return 0.5  # 默认置信度
        
        # 基于知识库匹配度和置信度计算
        max_similarity = max(result.get("similarity_score", 0) for result in knowledge_results)
        avg_confidence = sum(result.get("confidence_score", 0) for result in knowledge_results) / len(knowledge_results)
        
        # 综合评分
        confidence = (max_similarity * 0.6 + avg_confidence * 0.4)
        return min(confidence, 1.0)
    
    def create_work_order(
        self,
        title: str,
        description: str,
        category: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """创建工单"""
        try:
            with db_manager.get_session() as session:
                work_order = WorkOrder(
                    order_id=f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    status="open",
                    created_at=datetime.now()
                )
                session.add(work_order)
                session.commit()
                
                logger.info(f"创建工单成功: {work_order.order_id}")
                return {
                    "work_order_id": work_order.id,
                    "order_id": work_order.order_id,
                    "status": "success"
                }
                
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            return {"error": f"创建失败: {str(e)}"}
    
    def update_work_order(
        self,
        work_order_id: int,
        status: Optional[str] = None,
        resolution: Optional[str] = None,
        satisfaction_score: Optional[float] = None
    ) -> bool:
        """更新工单"""
        try:
            with db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order:
                    return False
                
                if status:
                    work_order.status = status
                if resolution:
                    work_order.resolution = resolution
                if satisfaction_score is not None:
                    work_order.satisfaction_score = satisfaction_score
                
                work_order.updated_at = datetime.now()
                session.commit()
                
                # 如果工单已解决，学习知识
                if status == "resolved" and resolution:
                    self.knowledge_manager.learn_from_work_order(work_order_id)
                
                logger.info(f"更新工单成功: {work_order_id}")
                return True
                
        except Exception as e:
            logger.error(f"更新工单失败: {e}")
            return False
    
    def get_conversation_history(self, work_order_id: int) -> List[Dict[str, Any]]:
        """获取工单对话历史"""
        try:
            with db_manager.get_session() as session:
                conversations = session.query(Conversation).filter(
                    Conversation.work_order_id == work_order_id
                ).order_by(Conversation.timestamp).all()
                
                return [
                    {
                        "id": conv.id,
                        "user_message": conv.user_message,
                        "assistant_response": conv.assistant_response,
                        "timestamp": conv.timestamp.isoformat(),
                        "confidence_score": conv.confidence_score
                    }
                    for conv in conversations
                ]
                
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    def get_user_conversation_history(
        self,
        user_id: str,
        work_order_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户对话历史（支持分页）"""
        try:
            return self.history_manager.get_conversation_history(
                user_id=user_id,
                work_order_id=work_order_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"获取用户对话历史失败: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话记录"""
        try:
            return self.history_manager.delete_conversation(conversation_id)
        except Exception as e:
            logger.error(f"删除对话记录失败: {e}")
            return False
    
    def delete_user_conversations(self, user_id: str, work_order_id: Optional[int] = None) -> int:
        """删除用户的所有对话记录"""
        try:
            return self.history_manager.delete_user_conversations(user_id, work_order_id)
        except Exception as e:
            logger.error(f"删除用户对话记录失败: {e}")
            return 0
    
    def get_conversation_stats(self, user_id: str, work_order_id: Optional[int] = None) -> Dict[str, Any]:
        """获取对话统计信息"""
        try:
            return self.history_manager.get_conversation_stats(user_id, work_order_id)
        except Exception as e:
            logger.error(f"获取对话统计失败: {e}")
            return {}
    
    def get_token_usage_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取Token使用统计"""
        try:
            return self.token_monitor.get_user_token_stats(user_id, days)
        except Exception as e:
            logger.error(f"获取Token使用统计失败: {e}")
            return {}
    
    def get_ai_performance_stats(self, model_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """获取AI性能统计"""
        try:
            if model_name:
                return self.ai_success_monitor.get_model_performance(model_name, hours)
            else:
                return self.ai_success_monitor.get_system_performance(hours)
        except Exception as e:
            logger.error(f"获取AI性能统计失败: {e}")
            return {}
