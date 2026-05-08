# -*- coding: utf-8 -*-
"""
Token消耗监控模块
监控AI调用的Token使用情况和成本
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
from ..core.database import db_manager
from ..core.models import Conversation
from ..core.redis_manager import redis_manager
from ..config.unified_config import get_config

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token使用记录"""
    timestamp: datetime
    user_id: str
    work_order_id: Optional[int]
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    response_time: float
    success: bool
    error_message: Optional[str] = None

class TokenMonitor:
    """Token消耗监控器"""
    
    def __init__(self):
        # Token价格配置（每1000个token的价格，单位：元）
        self.token_prices = {
            "qwen-plus-latest": {
                "input": 0.002,   # 输入token价格
                "output": 0.006   # 输出token价格
            },
            "qwen-turbo": {
                "input": 0.0008,
                "output": 0.002
            },
            "qwen-max": {
                "input": 0.02,
                "output": 0.06
            }
        }
        
        # 监控阈值
        self.thresholds = {
            "daily_cost_limit": 100.0,      # 每日成本限制（元）
            "hourly_cost_limit": 20.0,      # 每小时成本限制（元）
            "token_limit_per_request": 10000,  # 单次请求token限制
            "error_rate_threshold": 0.1     # 错误率阈值
        }
    
    def _get_redis_client(self):
        """获取Redis客户端"""
        return redis_manager.get_connection()
    
    def record_token_usage(
        self,
        user_id: str,
        work_order_id: Optional[int],
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> TokenUsage:
        """记录Token使用情况"""
        try:
            total_tokens = input_tokens + output_tokens
            
            # 计算成本
            cost = self._calculate_cost(model_name, input_tokens, output_tokens)
            
            # 创建使用记录
            usage = TokenUsage(
                timestamp=datetime.now(),
                user_id=user_id,
                work_order_id=work_order_id,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=cost,
                response_time=response_time,
                success=success,
                error_message=error_message
            )
            
            # 保存到Redis
            self._save_to_redis(usage)
            
            # 检查阈值
            self._check_thresholds(usage)
            
            logger.info(f"Token使用记录: {total_tokens} tokens, 成本: {cost:.4f}元")
            return usage
            
        except Exception as e:
            logger.error(f"记录Token使用失败: {e}")
            return None
    
    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """计算Token成本"""
        if model_name not in self.token_prices:
            model_name = "qwen-plus-latest"  # 默认模型
        
        prices = self.token_prices[model_name]
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        return input_cost + output_cost
    
    def _save_to_redis(self, usage: TokenUsage):
        """保存到Redis"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return
        
        try:
            # 保存到时间序列
            timestamp = usage.timestamp.timestamp()
            usage_data = {
                "user_id": usage.user_id,
                "work_order_id": usage.work_order_id,
                "model_name": usage.model_name,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "cost": usage.cost,
                "response_time": usage.response_time,
                "success": usage.success,
                "error_message": usage.error_message
            }
            
            # 保存到多个键
            redis_client.zadd(
                "token_usage:daily",
                {json.dumps(usage_data, ensure_ascii=False): timestamp}
            )
            
            redis_client.zadd(
                f"token_usage:user:{usage.user_id}",
                {json.dumps(usage_data, ensure_ascii=False): timestamp}
            )
            
            if usage.work_order_id:
                redis_client.zadd(
                    f"token_usage:work_order:{usage.work_order_id}",
                    {json.dumps(usage_data, ensure_ascii=False): timestamp}
                )
            
            # 设置过期时间（保留30天）
            redis_client.expire("token_usage:daily", 30 * 24 * 3600)
            
        except Exception as e:
            logger.error(f"保存Token使用到Redis失败: {e}")
    
    def _check_thresholds(self, usage: TokenUsage):
        """检查阈值并触发预警"""
        try:
            # 检查单次请求token限制
            if usage.total_tokens > self.thresholds["token_limit_per_request"]:
                self._trigger_alert(
                    "high_token_usage",
                    f"单次请求Token使用过多: {usage.total_tokens}",
                    "warning"
                )
            
            # 检查今日成本
            daily_cost = self.get_daily_cost(usage.timestamp.date())
            if daily_cost > self.thresholds["daily_cost_limit"]:
                self._trigger_alert(
                    "daily_cost_exceeded",
                    f"今日成本超限: {daily_cost:.2f}元",
                    "critical"
                )
            
            # 检查每小时成本
            hourly_cost = self.get_hourly_cost(usage.timestamp)
            if hourly_cost > self.thresholds["hourly_cost_limit"]:
                self._trigger_alert(
                    "hourly_cost_exceeded",
                    f"每小时成本超限: {hourly_cost:.2f}元",
                    "warning"
                )
            
        except Exception as e:
            logger.error(f"检查阈值失败: {e}")
    
    def _trigger_alert(self, alert_type: str, message: str, severity: str):
        """触发预警"""
        try:
            from ..core.models import Alert
            
            with db_manager.get_session() as session:
                alert = Alert(
                    rule_name=f"Token监控_{alert_type}",
                    alert_type=alert_type,
                    level=severity,
                    severity=severity,
                    message=message,
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(alert)
                session.commit()
                
            logger.warning(f"Token监控预警: {message}")
            
        except Exception as e:
            logger.error(f"触发Token监控预警失败: {e}")
    
    def get_daily_cost(self, date: datetime.date) -> float:
        """获取指定日期的成本"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0.0
            
            start_time = datetime.combine(date, datetime.min.time()).timestamp()
            end_time = datetime.combine(date, datetime.max.time()).timestamp()
            
            # 从Redis获取当日数据
            usage_records = redis_client.zrangebyscore(
                "token_usage:daily",
                start_time,
                end_time,
                withscores=True
            )
            
            total_cost = 0.0
            for record_data, _ in usage_records:
                try:
                    record = json.loads(record_data)
                    total_cost += record.get("cost", 0)
                except json.JSONDecodeError:
                    continue
            
            return total_cost
            
        except Exception as e:
            logger.error(f"获取日成本失败: {e}")
            return 0.0
    
    def get_hourly_cost(self, timestamp: datetime) -> float:
        """获取指定小时的成本"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0.0
            
            # 获取当前小时的数据
            hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            start_time = hour_start.timestamp()
            end_time = hour_end.timestamp()
            
            usage_records = redis_client.zrangebyscore(
                "token_usage:daily",
                start_time,
                end_time,
                withscores=True
            )
            
            total_cost = 0.0
            for record_data, _ in usage_records:
                try:
                    record = json.loads(record_data)
                    total_cost += record.get("cost", 0)
                except json.JSONDecodeError:
                    continue
            
            return total_cost
            
        except Exception as e:
            logger.error(f"获取小时成本失败: {e}")
            return 0.0
    
    def get_user_token_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取用户Token使用统计"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return {}
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            usage_records = redis_client.zrangebyscore(
                f"token_usage:user:{user_id}",
                start_time,
                end_time,
                withscores=True
            )
            
            stats = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0.0,
                "model_usage": defaultdict(int),
                "daily_usage": defaultdict(lambda: {"tokens": 0, "cost": 0})
            }
            
            response_times = []
            
            for record_data, timestamp in usage_records:
                try:
                    record = json.loads(record_data)
                    
                    stats["total_tokens"] += record.get("total_tokens", 0)
                    stats["total_cost"] += record.get("cost", 0)
                    stats["total_requests"] += 1
                    
                    if record.get("success", True):
                        stats["successful_requests"] += 1
                    else:
                        stats["failed_requests"] += 1
                    
                    model_name = record.get("model_name", "unknown")
                    stats["model_usage"][model_name] += 1
                    
                    if record.get("response_time"):
                        response_times.append(record["response_time"])
                    
                    # 按日期统计
                    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    stats["daily_usage"][date_str]["tokens"] += record.get("total_tokens", 0)
                    stats["daily_usage"][date_str]["cost"] += record.get("cost", 0)
                    
                except json.JSONDecodeError:
                    continue
            
            # 计算平均响应时间
            if response_times:
                stats["avg_response_time"] = sum(response_times) / len(response_times)
            
            # 计算成功率
            if stats["total_requests"] > 0:
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["success_rate"] = 0
            
            return dict(stats)
            
        except Exception as e:
            logger.error(f"获取用户Token统计失败: {e}")
            return {}
    
    def get_system_token_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取系统Token使用统计"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return {}
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            usage_records = redis_client.zrangebyscore(
                "token_usage:daily",
                start_time,
                end_time,
                withscores=True
            )
            
            stats = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "unique_users": set(),
                "model_usage": defaultdict(int),
                "daily_usage": defaultdict(lambda: {"tokens": 0, "cost": 0, "requests": 0})
            }
            
            for record_data, timestamp in usage_records:
                try:
                    record = json.loads(record_data)
                    
                    stats["total_tokens"] += record.get("total_tokens", 0)
                    stats["total_cost"] += record.get("cost", 0)
                    stats["total_requests"] += 1
                    
                    if record.get("success", True):
                        stats["successful_requests"] += 1
                    else:
                        stats["failed_requests"] += 1
                    
                    stats["unique_users"].add(record.get("user_id", ""))
                    
                    model_name = record.get("model_name", "unknown")
                    stats["model_usage"][model_name] += 1
                    
                    # 按日期统计
                    date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    stats["daily_usage"][date_str]["tokens"] += record.get("total_tokens", 0)
                    stats["daily_usage"][date_str]["cost"] += record.get("cost", 0)
                    stats["daily_usage"][date_str]["requests"] += 1
                    
                except json.JSONDecodeError:
                    continue
            
            # 计算成功率
            if stats["total_requests"] > 0:
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["success_rate"] = 0
            
            stats["unique_users"] = len(stats["unique_users"])
            
            return dict(stats)
            
        except Exception as e:
            logger.error(f"获取系统Token统计失败: {e}")
            return {}
    
    def get_cost_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取成本趋势"""
        try:
            trend_data = []
            
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                daily_cost = self.get_daily_cost(date)
                
                trend_data.append({
                    "date": date.isoformat(),
                    "cost": daily_cost
                })
            
            return list(reversed(trend_data))
            
        except Exception as e:
            logger.error(f"获取成本趋势失败: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """清理旧数据"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0
            
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            # 清理每日数据
            removed_count = redis_client.zremrangebyscore(
                "token_usage:daily",
                0,
                cutoff_time
            )
            
            # 清理用户数据
            user_keys = redis_client.keys("token_usage:user:*")
            for key in user_keys:
                redis_client.zremrangebyscore(key, 0, cutoff_time)
            
            # 清理工单数据
            work_order_keys = redis_client.keys("token_usage:work_order:*")
            for key in work_order_keys:
                redis_client.zremrangebyscore(key, 0, cutoff_time)
            
            logger.info(f"清理Token监控数据成功: 数量={removed_count}")
            return removed_count
            
        except Exception as e:
            logger.error(f"清理Token监控数据失败: {e}")
            return 0
