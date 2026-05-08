# -*- coding: utf-8 -*-
"""
性能优化配置
集中管理所有性能相关的配置参数
"""

class PerformanceConfig:
    """性能配置类"""
    
    # 数据库连接池配置
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    DATABASE_POOL_RECYCLE = 1800
    DATABASE_POOL_TIMEOUT = 10
    
    # 缓存配置
    CACHE_DEFAULT_TTL = 60  # 默认缓存时间（秒）
    CACHE_MAX_MEMORY_SIZE = 2000  # 最大内存缓存条目数
    CACHE_CONVERSATION_TTL = 60  # 对话缓存时间
    CACHE_WORKORDER_TTL = 30  # 工单缓存时间
    CACHE_MONITORING_TTL = 30  # 监控数据缓存时间
    
    # 查询优化配置
    QUERY_LIMIT_DEFAULT = 100  # 默认查询限制
    QUERY_LIMIT_CONVERSATIONS = 1000  # 对话查询限制
    QUERY_LIMIT_WORKORDERS = 100  # 工单查询限制
    QUERY_LIMIT_MONITORING = 1000  # 监控查询限制
    
    # 前端缓存配置
    FRONTEND_CACHE_TIMEOUT = 30000  # 前端缓存时间（毫秒）
    FRONTEND_PARALLEL_LOADING = True  # 是否启用并行加载
    
    # API响应优化
    API_TIMEOUT = 10  # API超时时间（秒）
    API_RETRY_COUNT = 3  # API重试次数
    API_BATCH_SIZE = 50  # 批量操作大小
    
    # 系统监控配置
    MONITORING_INTERVAL = 60  # 监控间隔（秒）
    SLOW_QUERY_THRESHOLD = 1.0  # 慢查询阈值（秒）
    PERFORMANCE_LOG_ENABLED = True  # 是否启用性能日志
    
    @classmethod
    def get_database_config(cls):
        """获取数据库配置"""
        return {
            'pool_size': cls.DATABASE_POOL_SIZE,
            'max_overflow': cls.DATABASE_MAX_OVERFLOW,
            'pool_recycle': cls.DATABASE_POOL_RECYCLE,
            'pool_timeout': cls.DATABASE_POOL_TIMEOUT
        }
    
    @classmethod
    def get_cache_config(cls):
        """获取缓存配置"""
        return {
            'default_ttl': cls.CACHE_DEFAULT_TTL,
            'max_memory_size': cls.CACHE_MAX_MEMORY_SIZE,
            'conversation_ttl': cls.CACHE_CONVERSATION_TTL,
            'workorder_ttl': cls.CACHE_WORKORDER_TTL,
            'monitoring_ttl': cls.CACHE_MONITORING_TTL
        }
    
    @classmethod
    def get_query_config(cls):
        """获取查询配置"""
        return {
            'default_limit': cls.QUERY_LIMIT_DEFAULT,
            'conversations_limit': cls.QUERY_LIMIT_CONVERSATIONS,
            'workorders_limit': cls.QUERY_LIMIT_WORKORDERS,
            'monitoring_limit': cls.QUERY_LIMIT_MONITORING
        }
    
    @classmethod
    def get_frontend_config(cls):
        """获取前端配置"""
        return {
            'cache_timeout': cls.FRONTEND_CACHE_TIMEOUT,
            'parallel_loading': cls.FRONTEND_PARALLEL_LOADING
        }
    
    @classmethod
    def get_api_config(cls):
        """获取API配置"""
        return {
            'timeout': cls.API_TIMEOUT,
            'retry_count': cls.API_RETRY_COUNT,
            'batch_size': cls.API_BATCH_SIZE
        }
