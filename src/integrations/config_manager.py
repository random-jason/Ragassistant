# -*- coding: utf-8 -*-
"""
配置管理器
管理飞书等外部系统的运行时配置，支持持久化存储和并发访问
初始值从统一配置(.env)加载，运行时修改可持久化到JSON文件
"""

import json
import threading
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from src.config.unified_config import get_config

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器（单例）"""

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

        self._config_lock = threading.RLock()
        self.config_file = Path("config/integrations_config.json")

        # 从统一配置初始化默认值
        unified = get_config()
        self.default_config = {
            "feishu": {
                "app_id": unified.feishu.app_id,
                "app_secret": unified.feishu.app_secret,
                "app_token": unified.feishu.app_token,
                "table_id": unified.feishu.table_id,
                "last_updated": None,
                "status": unified.feishu.status,
            },
            "system": {
                "sync_limit": unified.feishu.sync_limit,
                "ai_suggestions_enabled": True,
                "auto_sync_interval": unified.feishu.auto_sync_interval,
                "last_sync_time": None,
            }
        }

        self._load_config()
        self._initialized = True

    def _load_config(self):
        """加载持久化的运行时配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                self.config = self._merge(self.default_config, loaded)
            else:
                self.config = self.default_config.copy()
                self._save_config()
            logger.info("运行时配置加载成功")
        except Exception as e:
            logger.warning(f"运行时配置加载失败，使用默认值: {e}")
            self.config = self.default_config.copy()

    def _save_config(self):
        """持久化运行时配置"""
        try:
            with self._config_lock:
                self.config_file.parent.mkdir(exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存运行时配置失败: {e}")

    def _merge(self, default: Dict, loaded: Dict) -> Dict:
        result = default.copy()
        for key, value in loaded.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result

    def get_feishu_config(self) -> Dict[str, Any]:
        with self._config_lock:
            return self.config.get("feishu", {}).copy()

    def update_feishu_config(self, **kwargs) -> bool:
        try:
            with self._config_lock:
                feishu = self.config.setdefault("feishu", {})
                for key, value in kwargs.items():
                    if key in ("app_id", "app_secret", "app_token", "table_id"):
                        feishu[key] = value
                feishu["last_updated"] = datetime.now().isoformat()
                feishu["status"] = "active" if all([
                    feishu.get("app_id"), feishu.get("app_secret"),
                    feishu.get("app_token"), feishu.get("table_id")
                ]) else "inactive"
                self._save_config()
                return True
        except Exception as e:
            logger.error(f"飞书配置更新失败: {e}")
            return False

    def get_system_config(self) -> Dict[str, Any]:
        with self._config_lock:
            return self.config.get("system", {}).copy()

    def update_system_config(self, **kwargs) -> bool:
        try:
            with self._config_lock:
                system = self.config.setdefault("system", {})
                for key, value in kwargs.items():
                    if key in ("sync_limit", "ai_suggestions_enabled", "auto_sync_interval"):
                        system[key] = value
                self._save_config()
                return True
        except Exception as e:
            logger.error(f"系统配置更新失败: {e}")
            return False

    def test_feishu_connection(self) -> Dict[str, Any]:
        try:
            from .feishu_client import FeishuClient
            feishu = self.get_feishu_config()
            if not all([feishu.get("app_id"), feishu.get("app_secret")]):
                return {"success": False, "error": "飞书配置不完整"}
            client = FeishuClient(feishu["app_id"], feishu["app_secret"])
            token = client._get_access_token()
            if token:
                return {"success": True, "message": "飞书连接正常"}
            return {"success": False, "error": "无法获取访问令牌"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_config_summary(self) -> Dict[str, Any]:
        with self._config_lock:
            feishu = self.config.get("feishu", {})
            system = self.config.get("system", {})
            return {
                "feishu": {
                    "app_id": feishu.get("app_id", ""),
                    "app_token": feishu.get("app_token", ""),
                    "table_id": feishu.get("table_id", ""),
                    "status": feishu.get("status", "inactive"),
                    "last_updated": feishu.get("last_updated"),
                    "app_secret": "***" if feishu.get("app_secret") else ""
                },
                "system": system
            }

    def reset_config(self) -> bool:
        try:
            with self._config_lock:
                self.config = self.default_config.copy()
                self._save_config()
                return True
        except Exception as e:
            logger.error(f"配置重置失败: {e}")
            return False

    def export_config(self) -> str:
        with self._config_lock:
            return json.dumps(self.config, ensure_ascii=False, indent=2)

    def import_config(self, config_json: str) -> bool:
        try:
            imported = json.loads(config_json)
            with self._config_lock:
                self.config = self._merge(self.default_config, imported)
                self._save_config()
                return True
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False


config_manager = ConfigManager()
