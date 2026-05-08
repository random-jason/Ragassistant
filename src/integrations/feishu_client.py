# -*- coding: utf-8 -*-
"""
飞书API客户端
支持多维表格数据读取和更新
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from src.config.unified_config import get_config

logger = logging.getLogger(__name__)

class FeishuClient:
    """飞书API客户端"""
    
    def __init__(self, app_id: str, app_secret: str, bot_webhook_url: Optional[str] = None):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.bot_webhook_url = bot_webhook_url
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.token_expires_at = 0
        
    def _get_access_token(self) -> str:
        """获取访问令牌 - 使用tenant_access_token"""
        # 检查当前token是否还有效（提前5分钟刷新）
        if self.access_token and time.time() < (self.token_expires_at - 300):
            logger.debug(f"使用缓存的访问令牌: {self.access_token[:20]}...")
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal/"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            logger.info(f"正在获取飞书tenant_access_token，应用ID: {self.app_id}")
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"飞书API响应: {result}")
            
            if result.get("code") == 0:
                self.access_token = result["tenant_access_token"]
                # 设置过期时间，提前5分钟刷新
                expire_time = result.get("expire", 7200)  # 默认2小时
                self.token_expires_at = time.time() + expire_time
                
                logger.info(f"tenant_access_token获取成功: {self.access_token[:20]}...")
                logger.info(f"令牌有效期: {expire_time}秒，过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.token_expires_at))}")
                return self.access_token
            else:
                error_msg = f"获取tenant_access_token失败: {result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"获取飞书访问令牌失败: {e}")
            raise
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        headers = kwargs.get('headers', {})
        token = self._get_access_token()
        
        # 确保Authorization头格式正确：Bearer <token>
        headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        })
        kwargs['headers'] = headers
        
        try:
            logger.info(f"发送飞书API请求: {method} {url}")
            logger.info(f"请求头: Authorization: Bearer {token[:20]}...")
            
            response = requests.request(method, url, timeout=30, **kwargs)
            logger.info(f"飞书API响应状态码: {response.status_code}")
            
            # 处理403权限错误
            if response.status_code == 403:
                try:
                    error_data = response.json()
                    logger.error(f"飞书API权限错误: {error_data}")
                    raise Exception(f"飞书API权限不足: {error_data.get('msg', '未知权限错误')}")
                except:
                    logger.error(f"飞书API权限错误，无法解析响应内容")
                    raise Exception(f"飞书API权限不足，状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"飞书API响应内容: {result}")
            return result
        except Exception as e:
            logger.error(f"飞书API请求失败: {e}")
            logger.error(f"请求URL: {url}")
            logger.error(f"请求方法: {method}")
            logger.error(f"请求头: {headers}")
            raise
    
    def get_table_records(self, app_token: str, table_id: str, view_id: Optional[str] = None, 
                         page_size: int = 500, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取多维表格记录
        
        Args:
            app_token: 多维表格应用token
            table_id: 表格ID
            view_id: 视图ID（可选）
            page_size: 每页记录数
            page_token: 分页令牌
            
        Returns:
            包含记录数据的字典
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        
        params = {
            "page_size": page_size
        }
        if view_id:
            params["view_id"] = view_id
        if page_token:
            params["page_token"] = page_token
            
        return self._make_request("GET", url, params=params)
    
    def get_all_table_records(self, app_token: str, table_id: str, view_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取表格所有记录（自动分页）
        
        Args:
            app_token: 多维表格应用token
            table_id: 表格ID
            view_id: 视图ID（可选）
            
        Returns:
            所有记录的列表
        """
        all_records = []
        page_token = None
        
        while True:
            result = self.get_table_records(app_token, table_id, view_id, page_token=page_token)
            
            if result.get("code") != 0:
                raise Exception(f"获取表格记录失败: {result.get('msg', '未知错误')}")
            
            records = result.get("data", {}).get("items", [])
            all_records.extend(records)
            
            # 检查是否有下一页
            page_token = result.get("data", {}).get("page_token")
            if not page_token:
                break
                
        return all_records
    
    def update_table_record(self, app_token: str, table_id: str, record_id: str, 
                           fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新表格记录
        
        Args:
            app_token: 多维表格应用token
            table_id: 表格ID
            record_id: 记录ID
            fields: 要更新的字段
            
        Returns:
            更新结果
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        
        data = {
            "fields": fields
        }
        
        return self._make_request("PUT", url, json=data)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试飞书连接
        
        Returns:
            连接测试结果
        """
        try:
            # 尝试获取访问令牌
            token = self._get_access_token()
            
            # 验证token格式（应该以t-开头）
            if not token.startswith('t-'):
                logger.warning(f"获取的token格式异常，应该以't-'开头: {token[:20]}...")
            
            return {
                "success": True,
                "message": "飞书连接测试成功",
                "token_prefix": token[:20] + "...",
                "token_expires_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.token_expires_at))
            }
        except Exception as e:
            logger.error(f"飞书连接测试失败: {e}")
            return {
                "success": False,
                "message": f"飞书连接测试失败: {str(e)}"
            }
    
    def create_table_record(self, app_token: str, table_id: str, 
                           fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建表格记录
        
        Args:
            app_token: 多维表格应用token
            table_id: 表格ID
            fields: 记录字段
            
        Returns:
            创建结果
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        
        data = {
            "fields": fields
        }
        
        return self._make_request("POST", url, json=data)
    
    def get_table_record(self, app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """
        获取单条多维表格记录
        
        Args:
            app_token: 应用token
            table_id: 表格ID
            record_id: 记录ID
            
        Returns:
            记录数据
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        
        return self._make_request("GET", url)
    
    def get_table_fields(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """
        获取表格字段信息
        
        Args:
            app_token: 多维表格应用token
            table_id: 表格ID
            
        Returns:
            字段信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        
        return self._make_request("GET", url)
    
    def parse_record_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析记录字段，将飞书格式转换为标准格式
        
        Args:
            record: 飞书记录
            
        Returns:
            解析后的字段字典
        """
        fields = record.get("fields", {})
        parsed = {}
        
        for key, value in fields.items():
            if isinstance(value, dict):
                # 处理复杂字段类型
                if "text" in value:
                    parsed[key] = value["text"]
                elif "number" in value:
                    parsed[key] = value["number"]
                elif "date" in value:
                    parsed[key] = value["date"]
                elif "select" in value:
                    parsed[key] = value["select"]["name"] if isinstance(value["select"], dict) else value["select"]
                elif "multi_select" in value:
                    parsed[key] = [item["name"] if isinstance(item, dict) else item for item in value["multi_select"]]
                else:
                    parsed[key] = str(value)
            else:
                parsed[key] = value
                
        return parsed

    def send_bot_message(self, message: str, user_id: Optional[str] = None):
        """
        发送飞书机器人消息
        
        Args:
            message: 消息内容
            user_id: 用户ID（可选，用于@用户）
        """
        webhook_url = self.bot_webhook_url or Config.FEISHU_BOT_WEBHOOK_URL
        if not webhook_url:
            logger.warning("飞书机器人webhook URL未配置，跳过发送")
            return

        headers = {"Content-Type": "application/json"}
        
        # 基础消息内容
        content = {"text": message}
        
        # 如果有user_id，则@该用户
        if user_id:
            # 飞书的@格式为 <at user_id="ou_xxx"></at>
            # 注意：这里的user_id需要是open_id或union_id，取决于机器人配置
            # 为简化，这里假设user_id是open_id
            at_user = f'<at user_id="{user_id}"></at> '
            content["text"] = at_user + message

        data = {
            "msg_type": "text",
            "content": content
        }

        try:
            response = requests.post(webhook_url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                logger.info("飞书机器人消息发送成功")
            else:
                logger.error(f"飞书机器人消息发送失败: {result}")
        except Exception as e:
            logger.error(f"发送飞书机器人消息时出错: {e}")
