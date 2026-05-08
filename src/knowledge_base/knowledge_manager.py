import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func

from ..core.database import db_manager
from ..core.models import KnowledgeEntry, WorkOrder, Conversation
from ..core.llm_client import QwenClient

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 不使用英文停用词，因为数据是中文
            ngram_range=(1, 2)
        )
        self._load_vectorizer()
    
    def _load_vectorizer(self):
        """加载向量化器"""
        try:
            with db_manager.get_session() as session:
                entries = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_active == True
                ).all()
                
                if entries:
                    texts = [entry.question + " " + entry.answer for entry in entries]
                    self.vectorizer.fit(texts)
                    logger.info(f"向量化器加载成功，包含 {len(entries)} 个条目")
        except Exception as e:
            logger.error(f"加载向量化器失败: {e}")
    
    def learn_from_work_order(self, work_order_id: int) -> bool:
        """从工单中学习知识"""
        try:
            with db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order or not work_order.resolution:
                    return False
                
                # 提取问题和答案
                question = work_order.title + " " + work_order.description
                answer = work_order.resolution
                
                # 检查是否已存在相似条目
                existing_entry = self._find_similar_entry(question, session)
                
                if existing_entry:
                    # 更新现有条目
                    existing_entry.answer = answer
                    existing_entry.usage_count += 1
                    existing_entry.updated_at = datetime.now()
                    if work_order.satisfaction_score:
                        existing_entry.confidence_score = work_order.satisfaction_score
                else:
                    # 创建新条目
                    new_entry = KnowledgeEntry(
                        question=question,
                        answer=answer,
                        category=work_order.category,
                        confidence_score=work_order.satisfaction_score or 0.5,
                        usage_count=1
                    )
                    session.add(new_entry)
                
                session.commit()
                logger.info(f"从工单 {work_order_id} 学习知识成功")
                return True
                
        except Exception as e:
            logger.error(f"从工单学习知识失败: {e}")
            return False
    
    def _find_similar_entry(self, question: str, session) -> Optional[KnowledgeEntry]:
        """查找相似的知识库条目"""
        try:
            entries = session.query(KnowledgeEntry).filter(
                KnowledgeEntry.is_active == True
            ).all()
            
            if not entries:
                return None
            
            # 计算相似度
            texts = [entry.question for entry in entries]
            question_vector = self.vectorizer.transform([question])
            entry_vectors = self.vectorizer.transform(texts)
            
            similarities = cosine_similarity(question_vector, entry_vectors)[0]
            max_similarity_idx = np.argmax(similarities)
            
            if similarities[max_similarity_idx] > 0.8:  # 相似度阈值
                return entries[max_similarity_idx]
            
            return None
            
        except Exception as e:
            logger.error(f"查找相似条目失败: {e}")
            return None
    
    def search_knowledge(self, query: str, top_k: int = 3, verified_only: bool = True) -> List[Dict[str, Any]]:
        """搜索知识库"""
        try:
            with db_manager.get_session() as session:
                # 构建查询条件
                query_filter = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_active == True
                )
                
                # 如果只搜索已验证的知识库
                if verified_only:
                    query_filter = query_filter.filter(KnowledgeEntry.is_verified == True)
                
                entries = query_filter.all()
                # 若已验证为空，则回退到全部活跃条目
                if not entries and verified_only:
                    entries = session.query(KnowledgeEntry).filter(KnowledgeEntry.is_active == True).all()
                
                if not entries:
                    logger.warning("知识库中没有活跃条目")
                    return []
                
                # 如果查询为空，返回所有条目
                if not query.strip():
                    logger.info("查询为空，返回所有条目")
                    return [{
                        "id": entry.id,
                        "question": entry.question,
                        "answer": entry.answer,
                        "category": entry.category,
                        "confidence_score": entry.confidence_score,
                        "similarity_score": 1.0,
                        "usage_count": entry.usage_count,
                        "is_verified": entry.is_verified
                    } for entry in entries[:top_k]]
                
                # 使用简化的关键词匹配搜索
                q = query.strip().lower()
                results = []
                
                for entry in entries:
                    # 组合问题和答案进行搜索
                    search_text = (entry.question + " " + entry.answer).lower()
                    
                    # 计算匹配分数
                    score = 0.0
                    
                    # 完全匹配
                    if q in search_text:
                        score = 1.0
                    else:
                        # 分词匹配
                        query_words = q.split()
                        text_words = search_text.split()
                        
                        # 计算单词匹配度
                        matched_words = 0
                        for word in query_words:
                            if word in text_words:
                                matched_words += 1
                        
                        if matched_words > 0:
                            score = matched_words / len(query_words) * 0.8
                    
                    # 如果分数大于0，添加到结果中
                    if score > 0:
                        results.append({
                            "id": entry.id,
                            "question": entry.question,
                            "answer": entry.answer,
                            "category": entry.category,
                            "confidence_score": entry.confidence_score,
                            "similarity_score": score,
                            "usage_count": entry.usage_count,
                            "is_verified": entry.is_verified
                        })
                
                # 按相似度排序并返回top_k个结果
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                results = results[:top_k]
                
                logger.info(f"搜索查询 '{query}' 返回 {len(results)} 个结果")
                return results
                
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    def add_knowledge_entry(
        self,
        question: str,
        answer: str,
        category: str,
        confidence_score: float = 0.5,
        is_verified: bool = False
    ) -> bool:
        """添加知识库条目"""
        try:
            with db_manager.get_session() as session:
                entry = KnowledgeEntry(
                    question=question,
                    answer=answer,
                    category=category,
                    confidence_score=confidence_score,
                    usage_count=0,
                    is_verified=is_verified
                )
                session.add(entry)
                session.commit()
                
                # 重新训练向量化器
                self._load_vectorizer()
                
                logger.info(f"添加知识库条目成功: {question[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"添加知识库条目失败: {e}")
            return False
    
    def update_knowledge_entry(
        self,
        entry_id: int,
        question: str = None,
        answer: str = None,
        category: str = None,
        confidence_score: float = None
    ) -> bool:
        """更新知识库条目"""
        try:
            with db_manager.get_session() as session:
                entry = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.id == entry_id
                ).first()
                
                if not entry:
                    return False
                
                if question:
                    entry.question = question
                if answer:
                    entry.answer = answer
                if category:
                    entry.category = category
                if confidence_score is not None:
                    entry.confidence_score = confidence_score
                
                entry.updated_at = datetime.now()
                session.commit()
                
                logger.info(f"更新知识库条目成功: {entry_id}")
                return True
                
        except Exception as e:
            logger.error(f"更新知识库条目失败: {e}")
            return False
    
    def get_knowledge_entries(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """获取知识库条目（分页）"""
        try:
            with db_manager.get_session() as session:
                # 计算偏移量
                offset = (page - 1) * per_page
                
                # 获取总数
                total = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_active == True
                ).count()
                
                # 获取分页数据
                entries = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_active == True
                ).order_by(KnowledgeEntry.created_at.desc()).offset(offset).limit(per_page).all()
                
                # 转换为字典格式
                knowledge_list = []
                for entry in entries:
                    knowledge_list.append({
                        "id": entry.id,
                        "question": entry.question,
                        "answer": entry.answer,
                        "category": entry.category,
                        "confidence_score": entry.confidence_score,
                        "usage_count": entry.usage_count,
                        "created_at": entry.created_at.isoformat() if entry.created_at else None,
                        "is_verified": getattr(entry, 'is_verified', False)  # 添加验证状态
                    })
                
                return {
                    "knowledge": knowledge_list,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
        except Exception as e:
            logger.error(f"获取知识库条目失败: {e}")
            return {"knowledge": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}
    
    def verify_knowledge_entry(self, entry_id: int, verified_by: str = "admin") -> bool:
        """验证知识库条目"""
        try:
            with db_manager.get_session() as session:
                entry = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.id == entry_id
                ).first()
                
                if not entry:
                    return False
                
                entry.is_verified = True
                entry.verified_by = verified_by
                entry.verified_at = datetime.now()
                
                session.commit()
                logger.info(f"知识库条目验证成功: {entry_id}")
                return True
                
        except Exception as e:
            logger.error(f"验证知识库条目失败: {e}")
            return False
    
    def unverify_knowledge_entry(self, entry_id: int) -> bool:
        """取消验证知识库条目"""
        try:
            with db_manager.get_session() as session:
                entry = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.id == entry_id
                ).first()
                
                if not entry:
                    return False
                
                entry.is_verified = False
                entry.verified_by = None
                entry.verified_at = None
                
                session.commit()
                logger.info(f"知识库条目取消验证成功: {entry_id}")
                return True
                
        except Exception as e:
            logger.error(f"取消验证知识库条目失败: {e}")
            return False
    
    def delete_knowledge_entry(self, entry_id: int) -> bool:
        """删除知识库条目（软删除）"""
        try:
            with db_manager.get_session() as session:
                entry = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.id == entry_id
                ).first()
                
                if not entry:
                    logger.warning(f"知识库条目不存在: {entry_id}")
                    return False
                
                entry.is_active = False
                session.commit()
                
                # 重新训练向量化器（如果还有活跃条目）
                try:
                    self._load_vectorizer()
                except Exception as vectorizer_error:
                    logger.warning(f"重新加载向量化器失败: {vectorizer_error}")
                    # 即使向量化器加载失败，删除操作仍然成功
                
                logger.info(f"删除知识库条目成功: {entry_id}")
                return True
                
        except Exception as e:
            logger.error(f"删除知识库条目失败: {e}")
            return False
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            with db_manager.get_session() as session:
                total_entries = session.query(KnowledgeEntry).count()
                active_entries = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_active == True
                ).count()
                
                # 按类别统计
                category_stats = session.query(
                    KnowledgeEntry.category,
                    session.query(KnowledgeEntry).filter(
                        KnowledgeEntry.category == KnowledgeEntry.category
                    ).count()
                ).group_by(KnowledgeEntry.category).all()
                
                # 平均置信度
                avg_confidence = session.query(
                    func.avg(KnowledgeEntry.confidence_score)
                ).scalar() or 0.0
                
                return {
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "category_distribution": dict(category_stats),
                    "average_confidence": float(avg_confidence)
                }
                
        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return {}

    def update_usage_count(self, entry_ids: List[int]) -> bool:
        """更新知识库条目的使用次数"""
        try:
            with db_manager.get_session() as session:
                # 批量更新使用次数
                session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.id.in_(entry_ids)
                ).update({
                    "usage_count": KnowledgeEntry.usage_count + 1,
                    "updated_at": datetime.now()
                })
                session.commit()

                logger.info(f"成功更新 {len(entry_ids)} 个知识库条目的使用次数")
                return True

        except Exception as e:
            logger.error(f"更新知识库使用次数失败: {e}")
            return False