import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import hashlib

def setup_logging(log_level: str = "INFO", log_file: str = "logs/helpdesk.log"):
    """设置日志配置"""
    import os
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def validate_work_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证工单数据"""
    errors = []
    
    required_fields = ["title", "description", "category"]
    for field in required_fields:
        if not data.get(field):
            errors.append(f"缺少必填字段: {field}")
    
    # 验证优先级
    if "priority" in data and data["priority"] not in ["low", "medium", "high", "critical"]:
        errors.append("优先级必须是: low, medium, high, critical")
    
    # 验证类别
    valid_categories = [
        "技术问题", "账户问题", "支付问题", "产品问题", 
        "服务问题", "投诉建议", "其他"
    ]
    if "category" in data and data["category"] not in valid_categories:
        errors.append(f"类别必须是: {', '.join(valid_categories)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """提取文本关键词"""
    # 简单的关键词提取（可以后续改进为更复杂的算法）
    import jieba
    
    # 停用词
    stop_words = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"
    }
    
    # 分词
    words = jieba.cut(text)
    
    # 过滤停用词和短词
    keywords = []
    for word in words:
        if len(word) > 1 and word not in stop_words and not word.isdigit():
            keywords.append(word)
    
    # 统计词频
    word_count = {}
    for word in keywords:
        word_count[word] = word_count.get(word, 0) + 1
    
    # 返回频率最高的关键词
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]

def calculate_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（使用语义相似度）"""
    try:
        from src.utils.semantic_similarity import calculate_semantic_similarity
        return calculate_semantic_similarity(text1, text2)
    except Exception as e:
        logging.error(f"计算语义相似度失败: {e}")
        # 回退到传统方法
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception as e2:
            logging.error(f"计算TF-IDF相似度失败: {e2}")
            return 0.0

def format_time_duration(seconds: float) -> str:
    """格式化时间持续时间"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}小时"
    else:
        days = seconds / 86400
        return f"{days:.1f}天"

def generate_order_id() -> str:
    """生成工单ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:6]
    return f"WO{timestamp}{random_suffix}"

def parse_date_range(date_range: str) -> tuple:
    """解析日期范围"""
    today = datetime.now().date()
    
    if date_range == "today":
        return today, today
    elif date_range == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif date_range == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    elif date_range == "month":
        start = today.replace(day=1)
        return start, today
    elif date_range == "last_7_days":
        start = today - timedelta(days=7)
        return start, today
    elif date_range == "last_30_days":
        start = today - timedelta(days=30)
        return start, today
    else:
        # 尝试解析自定义日期范围
        try:
            start_str, end_str = date_range.split(" to ")
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
            return start, end
        except:
            return today, today

def sanitize_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符（保留中文、英文、数字和基本标点）
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:()（）]', '', text)
    
    return text

def chunk_text(text: str, max_length: int = 1000) -> List[str]:
    """将长文本分割成小块"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # 按句子分割
    sentences = re.split(r'[。！？.!?]', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + "。"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "。"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def merge_json_safely(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """安全合并两个字典"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json_safely(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key].extend(value)
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result

def get_memory_usage() -> Dict[str, float]:
    """获取内存使用情况"""
    import psutil
    
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
        "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
        "percent": process.memory_percent()
    }
