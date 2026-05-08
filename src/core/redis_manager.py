# -*- coding: utf-8 -*-
"""
统一Redis连接管理器
避免多个模块重复连接Redis，提供单例模式管理
"""

import os
import logging
import threading
from typing import Optional
import redis

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis连接管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.redis_client = None
        self.connected = False
        self.connection_lock = threading.Lock()
        self._initialized = True
        
        # Redis配置
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.password = os.getenv("REDIS_PASSWORD", "")
        self.connect_timeout = 2
        self.socket_timeout = 2
    
    def get_connection(self) -> Optional[redis.Redis]:
        """获取Redis连接（懒加载）"""
        if not self.connected:
            with self.connection_lock:
                if not self.connected:
                    try:
                        self.redis_client = redis.Redis(
                            host=self.host,
                            port=self.port,
                            password=self.password,
                            decode_responses=True,
                            socket_connect_timeout=self.connect_timeout,
                            socket_timeout=self.socket_timeout,
                            retry_on_timeout=True
                        )
                        # 测试连接
                        self.redis_client.ping()
                        self.connected = True
                        logger.info("Redis连接成功")
                    except Exception as e:
                        logger.debug(f"Redis连接失败: {e}")
                        self.redis_client = None
                        self.connected = False
        
        return self.redis_client
    
    def test_connection(self) -> bool:
        """测试Redis连接"""
        try:
            client = self.get_connection()
            if client:
                client.ping()
                return True
            return False
        except Exception as e:
            logger.debug(f"Redis连接测试失败: {e}")
            return False
    
    def close_connection(self):
        """关闭Redis连接"""
        with self.connection_lock:
            if self.redis_client:
                try:
                    self.redis_client.close()
                except Exception as e:
                    logger.debug(f"关闭Redis连接失败: {e}")
                finally:
                    self.redis_client = None
                    self.connected = False

# 全局Redis管理器实例
redis_manager = RedisManager()
