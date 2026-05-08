#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一配置管理模块
所有配置通过环境变量(.env)加载，JSON文件作为可选覆盖
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, fields
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///local_test.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "qwen"
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus-latest"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30

@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 5000
    websocket_port: int = 8765
    debug: bool = False
    log_level: str = "INFO"

@dataclass
class FeishuConfig:
    """飞书配置"""
    app_id: str = ""
    app_secret: str = ""
    app_token: str = ""
    table_id: str = ""
    bot_webhook_url: str = ""
    status: str = "active"
    sync_limit: int = 10
    auto_sync_interval: int = 0

@dataclass
class AIAccuracyConfig:
    """AI准确率配置"""
    auto_approve_threshold: float = 0.95
    use_human_resolution_threshold: float = 0.90
    manual_review_threshold: float = 0.80
    ai_suggestion_confidence: float = 0.95
    human_resolution_confidence: float = 0.90
    prefer_human_when_low_accuracy: bool = True
    enable_auto_approval: bool = True
    enable_human_fallback: bool = True

@dataclass
class SystemConfig:
    """系统配置"""
    backup_enabled: bool = True
    backup_interval: int = 24
    max_backup_files: int = 7
    cache_enabled: bool = True
    cache_ttl: int = 3600
    monitoring_enabled: bool = True

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""

@dataclass
class AuthConfig:
    """认证配置"""
    jwt_secret_key: str = "change-me-in-production"
    jwt_token_expiry_hours: int = 24

@dataclass
class WeChatConfig:
    """微信机器人配置"""
    app_id: str = ""
    app_secret: str = ""
    token: str = ""
    encoding_aes_key: str = ""
    enabled: bool = False


class UnifiedConfig:
    """统一配置管理器"""

    def __init__(self, config_dir: str = "config"):
        # 加载 .env 文件
        if load_dotenv:
            load_dotenv()
            logger.info("已加载 .env 配置文件")

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "unified_config.json"

        # 初始化所有配置
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.server = ServerConfig()
        self.feishu = FeishuConfig()
        self.ai_accuracy = AIAccuracyConfig()
        self.system = SystemConfig()
        self.redis = RedisConfig()
        self.auth = AuthConfig()
        self.wechat = WeChatConfig()

        # 从JSON文件加载（可选覆盖）
        self._load_from_json()
        # 从环境变量加载（最高优先级）
        self.load_from_env()

    def _load_from_json(self):
        """从JSON配置文件加载（可选）"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                if 'database' in config_data:
                    self.database = DatabaseConfig(**config_data['database'])
                if 'llm' in config_data:
                    self.llm = LLMConfig(**config_data['llm'])
                if 'server' in config_data:
                    self.server = ServerConfig(**config_data['server'])
                if 'feishu' in config_data:
                    self.feishu = FeishuConfig(**config_data['feishu'])
                if 'ai_accuracy' in config_data:
                    self.ai_accuracy = AIAccuracyConfig(**config_data['ai_accuracy'])
                if 'system' in config_data:
                    self.system = SystemConfig(**config_data['system'])

                logger.info("JSON配置文件加载成功")
        except Exception as e:
            logger.warning(f"JSON配置文件加载失败（忽略）: {e}")

    def load_from_env(self):
        """从环境变量加载配置（最高优先级）"""
        # 数据库
        if os.getenv('DATABASE_URL'):
            self.database.url = os.getenv('DATABASE_URL')

        # LLM
        if os.getenv('LLM_PROVIDER'):
            self.llm.provider = os.getenv('LLM_PROVIDER')
        if os.getenv('LLM_API_KEY'):
            self.llm.api_key = os.getenv('LLM_API_KEY')
        if os.getenv('LLM_BASE_URL'):
            self.llm.base_url = os.getenv('LLM_BASE_URL')
        if os.getenv('LLM_MODEL'):
            self.llm.model = os.getenv('LLM_MODEL')
        if os.getenv('LLM_TEMPERATURE'):
            self.llm.temperature = float(os.getenv('LLM_TEMPERATURE'))
        if os.getenv('LLM_MAX_TOKENS'):
            self.llm.max_tokens = int(os.getenv('LLM_MAX_TOKENS'))
        if os.getenv('LLM_TIMEOUT'):
            self.llm.timeout = int(os.getenv('LLM_TIMEOUT'))

        # 服务器
        if os.getenv('SERVER_HOST'):
            self.server.host = os.getenv('SERVER_HOST')
        if os.getenv('SERVER_PORT'):
            self.server.port = int(os.getenv('SERVER_PORT'))
        if os.getenv('WEBSOCKET_PORT'):
            self.server.websocket_port = int(os.getenv('WEBSOCKET_PORT'))
        if os.getenv('SERVER_DEBUG'):
            self.server.debug = os.getenv('SERVER_DEBUG').lower() in ('true', '1', 'yes')
        if os.getenv('LOG_LEVEL'):
            self.server.log_level = os.getenv('LOG_LEVEL')

        # 飞书
        if os.getenv('FEISHU_APP_ID'):
            self.feishu.app_id = os.getenv('FEISHU_APP_ID')
        if os.getenv('FEISHU_APP_SECRET'):
            self.feishu.app_secret = os.getenv('FEISHU_APP_SECRET')
        if os.getenv('FEISHU_APP_TOKEN'):
            self.feishu.app_token = os.getenv('FEISHU_APP_TOKEN')
        if os.getenv('FEISHU_TABLE_ID'):
            self.feishu.table_id = os.getenv('FEISHU_TABLE_ID')
        if os.getenv('FEISHU_BOT_WEBHOOK_URL'):
            self.feishu.bot_webhook_url = os.getenv('FEISHU_BOT_WEBHOOK_URL')

        # Redis
        if os.getenv('REDIS_HOST'):
            self.redis.host = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            self.redis.port = int(os.getenv('REDIS_PORT'))
        if os.getenv('REDIS_PASSWORD'):
            self.redis.password = os.getenv('REDIS_PASSWORD')

        # 认证
        if os.getenv('JWT_SECRET_KEY'):
            self.auth.jwt_secret_key = os.getenv('JWT_SECRET_KEY')
        if os.getenv('JWT_TOKEN_EXPIRY_HOURS'):
            self.auth.jwt_token_expiry_hours = int(os.getenv('JWT_TOKEN_EXPIRY_HOURS'))

        # 微信
        if os.getenv('WECHAT_APP_ID'):
            self.wechat.app_id = os.getenv('WECHAT_APP_ID')
        if os.getenv('WECHAT_APP_SECRET'):
            self.wechat.app_secret = os.getenv('WECHAT_APP_SECRET')
        if os.getenv('WECHAT_TOKEN'):
            self.wechat.token = os.getenv('WECHAT_TOKEN')
        if os.getenv('WECHAT_ENCODING_AES_KEY'):
            self.wechat.encoding_aes_key = os.getenv('WECHAT_ENCODING_AES_KEY')
        if os.getenv('WECHAT_ENABLED'):
            self.wechat.enabled = os.getenv('WECHAT_ENABLED').lower() in ('true', '1', 'yes')

    def get_database_url(self) -> str:
        return self.database.url

    def get_llm_config(self) -> Dict[str, Any]:
        return asdict(self.llm)

    def get_server_config(self) -> Dict[str, Any]:
        return asdict(self.server)

    def get_feishu_config(self) -> Dict[str, Any]:
        return asdict(self.feishu)

    def get_all_config(self) -> Dict[str, Any]:
        return {
            'database': asdict(self.database),
            'llm': asdict(self.llm),
            'server': asdict(self.server),
            'feishu': asdict(self.feishu),
            'ai_accuracy': asdict(self.ai_accuracy),
            'system': asdict(self.system),
            'redis': asdict(self.redis),
            'auth': asdict(self.auth),
            'wechat': asdict(self.wechat),
        }

    def update_config(self, section: str, config_data: Dict[str, Any]):
        """更新配置节"""
        section_map = {
            'database': (self.database, DatabaseConfig),
            'llm': (self.llm, LLMConfig),
            'server': (self.server, ServerConfig),
            'feishu': (self.feishu, FeishuConfig),
            'ai_accuracy': (self.ai_accuracy, AIAccuracyConfig),
            'system': (self.system, SystemConfig),
            'redis': (self.redis, RedisConfig),
            'auth': (self.auth, AuthConfig),
            'wechat': (self.wechat, WeChatConfig),
        }
        if section not in section_map:
            raise ValueError(f"未知的配置节: {section}")

        _, cls = section_map[section]
        setattr(self, section, cls(**config_data))
        logger.info(f"配置节 {section} 更新成功")

    def validate_config(self) -> bool:
        """验证配置有效性"""
        if not self.database.url:
            logger.error("数据库URL未配置")
            return False
        if not self.llm.api_key:
            logger.warning("LLM API密钥未配置")
        logger.info("配置验证通过")
        return True


# 全局配置实例
_config_instance = None

def get_config() -> UnifiedConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = UnifiedConfig()
    return _config_instance

def reload_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = None
    return get_config()
