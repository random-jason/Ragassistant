# -*- coding: utf-8 -*-
"""
启动优化配置
控制启动时的初始化行为，避免重复初始化和阻塞
"""

class StartupConfig:
    """启动配置类"""
    
    # 启动优化设置
    SKIP_SYSTEM_CHECK = True  # 跳过系统检查
    DELAY_REDIS_CONNECTION = True  # 延迟Redis连接
    DELAY_MONITORING_START = True  # 延迟监控启动
    DELAY_AGENT_INIT = True  # 延迟Agent初始化
    
    # 延迟时间（秒）
    REDIS_CONNECTION_DELAY = 2  # Redis连接延迟
    MONITORING_START_DELAY = 5  # 监控启动延迟
    AGENT_INIT_DELAY = 3  # Agent初始化延迟
    
    # 连接超时设置
    REDIS_CONNECT_TIMEOUT = 2  # Redis连接超时
    REDIS_SOCKET_TIMEOUT = 2  # Redis Socket超时
    DATABASE_CONNECT_TIMEOUT = 5  # 数据库连接超时
    
    # 日志级别控制
    REDIS_LOG_LEVEL = "DEBUG"  # Redis日志级别
    STARTUP_LOG_LEVEL = "INFO"  # 启动日志级别
    
    @classmethod
    def should_skip_system_check(cls):
        """是否跳过系统检查"""
        return cls.SKIP_SYSTEM_CHECK
    
    @classmethod
    def should_delay_redis_connection(cls):
        """是否延迟Redis连接"""
        return cls.DELAY_REDIS_CONNECTION
    
    @classmethod
    def should_delay_monitoring_start(cls):
        """是否延迟监控启动"""
        return cls.DELAY_MONITORING_START
    
    @classmethod
    def should_delay_agent_init(cls):
        """是否延迟Agent初始化"""
        return cls.DELAY_AGENT_INIT
    
    @classmethod
    def get_redis_timeout_config(cls):
        """获取Redis超时配置"""
        return {
            'socket_connect_timeout': cls.REDIS_CONNECT_TIMEOUT,
            'socket_timeout': cls.REDIS_SOCKET_TIMEOUT
        }
    
    @classmethod
    def get_delay_times(cls):
        """获取延迟时间配置"""
        return {
            'redis_connection': cls.REDIS_CONNECTION_DELAY,
            'monitoring_start': cls.MONITORING_START_DELAY,
            'agent_init': cls.AGENT_INIT_DELAY
        }
