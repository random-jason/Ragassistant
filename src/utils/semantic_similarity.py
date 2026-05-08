#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语义相似度计算服务
使用LLM API进行更准确的语义相似度计算，提高理解力并节约服务端资源
"""

import logging
import numpy as np
import re
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SemanticSimilarityCalculator:
    """语义相似度计算器 - 使用LLM API"""
    
    def __init__(self, use_llm: bool = True):
        """
        初始化语义相似度计算器
        
        Args:
            use_llm: 是否使用LLM API计算相似度（默认True，推荐）
                - True: 使用LLM API，理解力更强，无需加载本地模型
                - False: 使用本地模型（需要下载HuggingFace模型）
        """
        self.use_llm = use_llm
        self.model = None
        self.llm_client = None
        
        if use_llm:
            self._init_llm_client()
        else:
            self._load_model()
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from ..core.llm_client import QwenClient
            self.llm_client = QwenClient()
            logger.info("LLM客户端初始化成功，将使用LLM API计算语义相似度")
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
            self.llm_client = None
            # 回退到本地模型
            self.use_llm = False
            self._load_model()
    
    def _load_model(self):
        """加载预训练模型（仅在use_llm=False时使用）"""
        try:
            logger.info(f"正在加载本地语义相似度模型: all-MiniLM-L6-v2")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("本地语义相似度模型加载成功")
        except Exception as e:
            logger.error(f"加载本地语义相似度模型失败: {e}")
            self.model = None
    
    def calculate_similarity(self, text1: str, text2: str, fast_mode: bool = True) -> float:
        """
        计算两个文本的语义相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            fast_mode: 是否使用快速模式（仅在使用本地模型时有效）
            
        Returns:
            相似度分数 (0-1之间)
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            # 优先使用LLM API计算相似度
            if self.use_llm and self.llm_client:
                return self._calculate_llm_similarity(text1, text2)
            
            # 回退到本地模型或TF-IDF
            if self.model is not None:
                if fast_mode:
                    # 快速模式：先使用TF-IDF快速筛选
                    tfidf_sim = self._calculate_tfidf_similarity(text1, text2)
                    if tfidf_sim >= 0.9 or tfidf_sim <= 0.3:
                        return tfidf_sim
                    # 中等相似度时，使用语义方法进行精确计算
                    semantic_sim = self._calculate_semantic_similarity(text1, text2)
                    return (tfidf_sim * 0.3 + semantic_sim * 0.7)
                else:
                    return self._calculate_semantic_similarity(text1, text2)
            else:
                return self._calculate_tfidf_similarity(text1, text2)
                
        except Exception as e:
            logger.error(f"计算语义相似度失败: {e}")
            return self._calculate_tfidf_similarity(text1, text2)
    
    def _calculate_llm_similarity(self, text1: str, text2: str) -> float:
        """使用LLM API计算语义相似度"""
        try:
            # 构建prompt，让LLM比较两个文本的相似度
            prompt = f"""请比较以下两个文本的语义相似度，并给出0-1之间的分数（保留2位小数），其中：
- 1.0 表示完全相同
- 0.8-0.9 表示非常相似
- 0.6-0.7 表示较为相似
- 0.4-0.5 表示部分相似
- 0.0-0.3 表示差异很大

文本1: {text1}

文本2: {text2}

请只返回0-1之间的数字（保留2位小数），不要包含其他文字。例如：0.85"""
            
            messages = [
                {"role": "system", "content": "你是一个专业的文本相似度评估专家，请准确评估两个文本的语义相似度。"},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.1,  # 低温度以获得更稳定的结果
                max_tokens=50
            )
            
            if "error" in result:
                logger.error(f"LLM API调用失败: {result['error']}")
                # 回退到TF-IDF
                return self._calculate_tfidf_similarity(text1, text2)
            
            # 提取响应中的数字
            response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            similarity = self._extract_similarity_from_response(response_content)
            
            logger.debug(f"LLM计算语义相似度: {similarity:.4f}")
            return similarity
            
        except Exception as e:
            logger.error(f"LLM语义相似度计算失败: {e}")
            # 回退到TF-IDF
            return self._calculate_tfidf_similarity(text1, text2)
    
    def _extract_similarity_from_response(self, response: str) -> float:
        """从LLM响应中提取相似度分数"""
        try:
            # 尝试提取0-1之间的浮点数
            patterns = [
                r'(\d+\.\d{1,2})',  # 匹配两位小数的浮点数
                r'(\d+\.\d+)',      # 匹配任意小数的浮点数
                r'(\d+)'            # 匹配整数（可能是百分比形式）
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response)
                if matches:
                    value = float(matches[0])
                    # 如果值大于1，可能是百分比形式，需要除以100
                    if value > 1:
                        value = value / 100.0
                    # 确保在0-1范围内
                    value = max(0.0, min(1.0, value))
                    return value
            
            # 如果没有找到数字，返回默认值
            logger.warning(f"无法从响应中提取相似度分数: {response}")
            return 0.5
            
        except Exception as e:
            logger.error(f"提取相似度分数失败: {e}, 响应: {response}")
            return 0.5
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """使用sentence-transformers计算语义相似度"""
        try:
            # 获取文本嵌入向量
            embeddings = self.model.encode([text1, text2])
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(embeddings[0], embeddings[1])
            
            # 确保结果在0-1范围内
            similarity = max(0.0, min(1.0, similarity))
            
            logger.debug(f"语义相似度计算: {similarity:.4f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"语义相似度计算失败: {e}")
            return self._calculate_tfidf_similarity(text1, text2)
    
    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """使用TF-IDF计算相似度（回退方法）"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
            vectors = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            logger.debug(f"TF-IDF相似度计算: {similarity:.4f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"TF-IDF相似度计算失败: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            # 计算点积
            dot_product = np.dot(vec1, vec2)
            
            # 计算向量的模长
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # 避免除零错误
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            similarity = dot_product / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"余弦相似度计算失败: {e}")
            return 0.0
    
    def batch_calculate_similarity(self, text_pairs: List[Tuple[str, str]]) -> List[float]:
        """
        批量计算相似度
        
        Args:
            text_pairs: 文本对列表 [(text1, text2), ...]
            
        Returns:
            相似度分数列表
        """
        if not text_pairs:
            return []
        
        try:
            # 优先使用LLM API
            if self.use_llm and self.llm_client:
                return [self._calculate_llm_similarity(t1, t2) for t1, t2 in text_pairs]
            
            # 回退到本地模型或TF-IDF
            if self.model is not None:
                return self._batch_semantic_similarity(text_pairs)
            else:
                return [self._calculate_tfidf_similarity(t1, t2) for t1, t2 in text_pairs]
        except Exception as e:
            logger.error(f"批量相似度计算失败: {e}")
            return [0.0] * len(text_pairs)
    
    def _batch_semantic_similarity(self, text_pairs: List[Tuple[str, str]]) -> List[float]:
        """批量计算语义相似度"""
        try:
            # 提取所有文本
            all_texts = []
            for text1, text2 in text_pairs:
                all_texts.extend([text1, text2])
            
            # 批量获取嵌入向量
            embeddings = self.model.encode(all_texts)
            
            # 计算每对的相似度
            similarities = []
            for i in range(0, len(embeddings), 2):
                similarity = self._cosine_similarity(embeddings[i], embeddings[i+1])
                similarities.append(float(similarity))
            
            return similarities
            
        except Exception as e:
            logger.error(f"批量语义相似度计算失败: {e}")
            return [self._calculate_tfidf_similarity(t1, t2) for t1, t2 in text_pairs]
    
    def get_similarity_explanation(self, text1: str, text2: str, similarity: float) -> str:
        """
        获取相似度解释
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            similarity: 相似度分数
            
        Returns:
            相似度解释文本
        """
        if similarity >= 0.95:
            return "语义高度相似，建议自动审批"
        elif similarity >= 0.8:
            return "语义较为相似，建议人工审核"
        elif similarity >= 0.6:
            return "语义部分相似，需要人工判断"
        elif similarity >= 0.4:
            return "语义相似度较低，建议重新生成"
        else:
            return "语义差异较大，建议重新生成"
    
    def is_model_available(self) -> bool:
        """检查模型是否可用（LLM或本地模型）"""
        if self.use_llm:
            return self.llm_client is not None
        else:
            return self.model is not None

# 全局实例
_similarity_calculator = None

def get_similarity_calculator(use_llm: bool = True) -> SemanticSimilarityCalculator:
    """获取全局相似度计算器实例
    
    Args:
        use_llm: 是否使用LLM API（默认True，推荐）
    """
    global _similarity_calculator
    if _similarity_calculator is None:
        _similarity_calculator = SemanticSimilarityCalculator(use_llm=use_llm)
    return _similarity_calculator

def calculate_semantic_similarity(text1: str, text2: str, fast_mode: bool = True) -> float:
    """
    计算语义相似度的便捷函数
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        fast_mode: 是否使用快速模式
        
    Returns:
        相似度分数 (0-1之间)
    """
    calculator = get_similarity_calculator()
    return calculator.calculate_similarity(text1, text2, fast_mode)

def batch_calculate_semantic_similarity(text_pairs: List[Tuple[str, str]]) -> List[float]:
    """
    批量计算语义相似度的便捷函数
    
    Args:
        text_pairs: 文本对列表
        
    Returns:
        相似度分数列表
    """
    calculator = get_similarity_calculator()
    return calculator.batch_calculate_similarity(text_pairs)
