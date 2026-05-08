# -*- coding: utf-8 -*-
"""
缓存管理器
提供内存缓存和Redis缓存支持，减少数据库查询延迟
"""

import json
import time
import threading
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.memory_cache = {}
        self.cache_lock = threading.RLock()
        self.default_ttl = 60  # 默认1分钟过期，提高响应速度
        self.max_memory_size = 2000  # 增加内存缓存条目数
        
        # Redis支持（可选）- 延迟连接
        self.redis_client = None
        self.redis_url = redis_url
        self.redis_connected = False
    
    def _ensure_redis_connection(self):
        """确保Redis连接（延迟连接）"""
        if self.redis_url and not self.redis_connected:
            try:
                import redis
                self.redis_client = redis.from_url(self.redis_url, socket_connect_timeout=2, socket_timeout=2)
                self.redis_client.ping()  # 测试连接
                self.redis_connected = True
                logger.info("Redis缓存已启用")
            except ImportError:
                logger.debug("Redis未安装，使用内存缓存")
            except Exception as e:
                logger.debug(f"Redis连接失败: {e}，使用内存缓存")
                self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            # 确保Redis连接
            self._ensure_redis_connection()
            
            # 先尝试Redis
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value:
                        return json.loads(value)
                except Exception as e:
                    logger.warning(f"Redis获取失败: {e}")
            
            # 回退到内存缓存
            with self.cache_lock:
                if key in self.memory_cache:
                    cache_item = self.memory_cache[key]
                    if cache_item['expires_at'] > time.time():
                        return cache_item['value']
                    else:
                        del self.memory_cache[key]
            
            return None
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            
            # 确保Redis连接
            self._ensure_redis_connection()
            
            # 先尝试Redis
            if self.redis_client:
                try:
                    self.redis_client.setex(key, ttl, json.dumps(value, default=str))
                    return True
                except Exception as e:
                    logger.warning(f"Redis设置失败: {e}")
            
            # 回退到内存缓存
            with self.cache_lock:
                # 清理过期缓存
                self._cleanup_expired()
                
                # 检查内存限制
                if len(self.memory_cache) >= self.max_memory_size:
                    self._evict_oldest()
                
                self.memory_cache[key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': time.time()
                }
            
            return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            # Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis删除失败: {e}")
            
            # 内存缓存
            with self.cache_lock:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            return True
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            # Redis
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"Redis清空失败: {e}")
            
            # 内存缓存
            with self.cache_lock:
                self.memory_cache.clear()
            
            return True
        except Exception as e:
            logger.error(f"缓存清空失败: {e}")
            return False
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item['expires_at'] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    def _evict_oldest(self):
        """淘汰最旧的缓存"""
        if not self.memory_cache:
            return
        
        oldest_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k]['created_at']
        )
        del self.memory_cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.cache_lock:
            memory_size = len(self.memory_cache)
            memory_keys = list(self.memory_cache.keys())
        
        redis_info = {}
        if self.redis_client:
            try:
                redis_info = {
                    'redis_connected': True,
                    'redis_keys': self.redis_client.dbsize()
                }
            except Exception as e:
                redis_info = {
                    'redis_connected': False,
                    'redis_error': str(e)
                }
        
        return {
            'memory_cache_size': memory_size,
            'memory_cache_keys': memory_keys,
            'max_memory_size': self.max_memory_size,
            'default_ttl': self.default_ttl,
            **redis_info
        }


class DatabaseCache:
    """数据库查询缓存装饰器"""
    
    def __init__(self, cache_manager: CacheManager, ttl: int = 300):
        self.cache_manager = cache_manager
        self.ttl = ttl
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            logger.debug(f"缓存未命中: {cache_key}")
            result = func(*args, **kwargs)
            self.cache_manager.set(cache_key, result, self.ttl)
            
            return result
        return wrapper


# 全局缓存管理器实例
cache_manager = CacheManager()

# 常用缓存装饰器
def cache_query(ttl: int = 300):
    """数据库查询缓存装饰器"""
    return DatabaseCache(cache_manager, ttl)

def cache_result(ttl: int = 300):
    """结果缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__module__}.{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
