# -*- coding: utf-8 -*-
"""
AI调用成功率监控模块
监控AI API调用的成功率和性能指标
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import time

from ..core.database import db_manager
from ..core.models import Alert
from ..core.redis_manager import redis_manager
from ..config.unified_config import get_config

logger = logging.getLogger(__name__)

@dataclass
class APICall:
    """API调用记录"""
    timestamp: datetime
    user_id: str
    work_order_id: Optional[int]
    model_name: str
    endpoint: str
    success: bool
    response_time: float
    status_code: Optional[int]
    error_message: Optional[str]
    input_length: int
    output_length: int

class AISuccessMonitor:
    """AI调用成功率监控器"""
    
    def __init__(self):
        # 监控阈值
        self.thresholds = {
            "success_rate_min": 0.95,           # 最低成功率95%
            "avg_response_time_max": 10.0,       # 最大平均响应时间10秒
            "error_rate_max": 0.05,              # 最大错误率5%
            "consecutive_failures_max": 5,       # 最大连续失败次数
            "hourly_failures_max": 10            # 每小时最大失败次数
        }
        
        # 性能等级定义
        self.performance_levels = {
            "excellent": {"success_rate": 0.98, "response_time": 2.0},
            "good": {"success_rate": 0.95, "response_time": 5.0},
            "fair": {"success_rate": 0.90, "response_time": 8.0},
            "poor": {"success_rate": 0.85, "response_time": 12.0}
        }
    
    def _get_redis_client(self):
        """获取Redis客户端"""
        return redis_manager.get_connection()
    
    def record_api_call(
        self,
        user_id: str,
        work_order_id: Optional[int],
        model_name: str,
        endpoint: str,
        success: bool,
        response_time: float,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        input_length: int = 0,
        output_length: int = 0
    ) -> APICall:
        """记录API调用"""
        try:
            api_call = APICall(
                timestamp=datetime.now(),
                user_id=user_id,
                work_order_id=work_order_id,
                model_name=model_name,
                endpoint=endpoint,
                success=success,
                response_time=response_time,
                status_code=status_code,
                error_message=error_message,
                input_length=input_length,
                output_length=output_length
            )
            
            # 保存到Redis
            self._save_to_redis(api_call)
            
            # 检查阈值
            self._check_thresholds(api_call)
            
            logger.info(f"API调用记录: {model_name} - {'成功' if success else '失败'}")
            return api_call
            
        except Exception as e:
            logger.error(f"记录API调用失败: {e}")
            return None
    
    def _save_to_redis(self, api_call: APICall):
        """保存到Redis"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return
        
        try:
            timestamp = api_call.timestamp.timestamp()
            call_data = {
                "user_id": api_call.user_id,
                "work_order_id": api_call.work_order_id,
                "model_name": api_call.model_name,
                "endpoint": api_call.endpoint,
                "success": api_call.success,
                "response_time": api_call.response_time,
                "status_code": api_call.status_code,
                "error_message": api_call.error_message,
                "input_length": api_call.input_length,
                "output_length": api_call.output_length
            }
            
            # 保存到多个键
            redis_client.zadd(
                "api_calls:daily",
                {json.dumps(call_data, ensure_ascii=False): timestamp}
            )
            
            redis_client.zadd(
                f"api_calls:model:{api_call.model_name}",
                {json.dumps(call_data, ensure_ascii=False): timestamp}
            )
            
            redis_client.zadd(
                f"api_calls:user:{api_call.user_id}",
                {json.dumps(call_data, ensure_ascii=False): timestamp}
            )
            
            # 设置过期时间（保留30天）
            redis_client.expire("api_calls:daily", 30 * 24 * 3600)
            
        except Exception as e:
            logger.error(f"保存API调用到Redis失败: {e}")
    
    def _check_thresholds(self, api_call: APICall):
        """检查阈值并触发预警"""
        try:
            # 检查连续失败
            consecutive_failures = self._get_consecutive_failures(api_call.model_name)
            if consecutive_failures >= self.thresholds["consecutive_failures_max"]:
                self._trigger_alert(
                    "consecutive_failures",
                    f"模型 {api_call.model_name} 连续失败 {consecutive_failures} 次",
                    "critical"
                )
            
            # 检查每小时失败次数
            hourly_failures = self._get_hourly_failures(api_call.timestamp)
            if hourly_failures >= self.thresholds["hourly_failures_max"]:
                self._trigger_alert(
                    "high_hourly_failures",
                    f"每小时失败次数过多: {hourly_failures}",
                    "warning"
                )
            
            # 检查成功率
            success_rate = self._get_recent_success_rate(api_call.model_name, hours=1)
            if success_rate < self.thresholds["success_rate_min"]:
                self._trigger_alert(
                    "low_success_rate",
                    f"模型 {api_call.model_name} 成功率过低: {success_rate:.2%}",
                    "warning"
                )
            
            # 检查响应时间
            avg_response_time = self._get_avg_response_time(api_call.model_name, hours=1)
            if avg_response_time > self.thresholds["avg_response_time_max"]:
                self._trigger_alert(
                    "slow_response",
                    f"模型 {api_call.model_name} 响应时间过长: {avg_response_time:.2f}秒",
                    "warning"
                )
            
        except Exception as e:
            logger.error(f"检查阈值失败: {e}")
    
    def _get_consecutive_failures(self, model_name: str) -> int:
        """获取连续失败次数"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0
            
            # 获取最近的调用记录
            recent_calls = redis_client.zrevrange(
                f"api_calls:model:{model_name}",
                0,
                9,  # 最近10次调用
                withscores=True
            )
            
            consecutive_failures = 0
            for call_data, _ in recent_calls:
                try:
                    call = json.loads(call_data)
                    if not call.get("success", True):
                        consecutive_failures += 1
                    else:
                        break
                except json.JSONDecodeError:
                    continue
            
            return consecutive_failures
            
        except Exception as e:
            logger.error(f"获取连续失败次数失败: {e}")
            return 0
    
    def _get_hourly_failures(self, timestamp: datetime) -> int:
        """获取每小时失败次数"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0
            
            hour_start = timestamp.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            start_time = hour_start.timestamp()
            end_time = hour_end.timestamp()
            
            calls = redis_client.zrangebyscore(
                "api_calls:daily",
                start_time,
                end_time,
                withscores=True
            )
            
            failures = 0
            for call_data, _ in calls:
                try:
                    call = json.loads(call_data)
                    if not call.get("success", True):
                        failures += 1
                except json.JSONDecodeError:
                    continue
            
            return failures
            
        except Exception as e:
            logger.error(f"获取每小时失败次数失败: {e}")
            return 0
    
    def _get_recent_success_rate(self, model_name: str, hours: int = 1) -> float:
        """获取最近成功率"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0.0
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            calls = redis_client.zrangebyscore(
                f"api_calls:model:{model_name}",
                start_time,
                end_time,
                withscores=True
            )
            
            if not calls:
                return 1.0  # 没有调用记录时认为成功率100%
            
            successful_calls = 0
            total_calls = len(calls)
            
            for call_data, _ in calls:
                try:
                    call = json.loads(call_data)
                    if call.get("success", True):
                        successful_calls += 1
                except json.JSONDecodeError:
                    continue
            
            return successful_calls / total_calls if total_calls > 0 else 0.0
            
        except Exception as e:
            logger.error(f"获取成功率失败: {e}")
            return 0.0
    
    def _get_avg_response_time(self, model_name: str, hours: int = 1) -> float:
        """获取平均响应时间"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return 0.0
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            calls = redis_client.zrangebyscore(
                f"api_calls:model:{model_name}",
                start_time,
                end_time,
                withscores=True
            )
            
            if not calls:
                return 0.0
            
            total_time = 0.0
            count = 0
            
            for call_data, _ in calls:
                try:
                    call = json.loads(call_data)
                    response_time = call.get("response_time", 0)
                    if response_time > 0:
                        total_time += response_time
                        count += 1
                except json.JSONDecodeError:
                    continue
            
            return total_time / count if count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"获取平均响应时间失败: {e}")
            return 0.0
    
    def _trigger_alert(self, alert_type: str, message: str, severity: str):
        """触发预警"""
        try:
            alert = Alert(
                rule_name=f"AI成功率监控_{alert_type}",
                alert_type=alert_type,
                level=severity,
                severity=severity,
                message=message,
                is_active=True,
                created_at=datetime.now()
            )
            
            with db_manager.get_session() as session:
                session.add(alert)
                session.commit()
            
            logger.warning(f"AI成功率监控预警: {message}")
            
        except Exception as e:
            logger.error(f"触发AI成功率监控预警失败: {e}")
    
    def get_model_performance(self, model_name: str, hours: int = 24) -> Dict[str, Any]:
        """获取模型性能指标"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return {}
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            calls = redis_client.zrangebyscore(
                f"api_calls:model:{model_name}",
                start_time,
                end_time,
                withscores=True
            )
            
            if not calls:
                return {
                    "model_name": model_name,
                    "total_calls": 0,
                    "success_rate": 0.0,
                    "avg_response_time": 0.0,
                    "error_rate": 0.0,
                    "performance_level": "unknown"
                }
            
            stats = {
                "total_calls": len(calls),
                "successful_calls": 0,
                "failed_calls": 0,
                "total_response_time": 0.0,
                "response_times": [],
                "errors": defaultdict(int)
            }
            
            for call_data, _ in calls:
                try:
                    call = json.loads(call_data)
                    
                    if call.get("success", True):
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1
                        error_msg = call.get("error_message", "unknown")
                        stats["errors"][error_msg] += 1
                    
                    response_time = call.get("response_time", 0)
                    if response_time > 0:
                        stats["total_response_time"] += response_time
                        stats["response_times"].append(response_time)
                    
                except json.JSONDecodeError:
                    continue
            
            # 计算指标
            success_rate = stats["successful_calls"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
            avg_response_time = stats["total_response_time"] / len(stats["response_times"]) if stats["response_times"] else 0
            error_rate = stats["failed_calls"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
            
            # 确定性能等级
            performance_level = self._determine_performance_level(success_rate, avg_response_time)
            
            return {
                "model_name": model_name,
                "total_calls": stats["total_calls"],
                "successful_calls": stats["successful_calls"],
                "failed_calls": stats["failed_calls"],
                "success_rate": round(success_rate, 4),
                "avg_response_time": round(avg_response_time, 2),
                "error_rate": round(error_rate, 4),
                "performance_level": performance_level,
                "top_errors": dict(list(stats["errors"].items())[:5])  # 前5个错误
            }
            
        except Exception as e:
            logger.error(f"获取模型性能失败: {e}")
            return {}
    
    def _determine_performance_level(self, success_rate: float, avg_response_time: float) -> str:
        """确定性能等级"""
        for level, thresholds in self.performance_levels.items():
            if success_rate >= thresholds["success_rate"] and avg_response_time <= thresholds["response_time"]:
                return level
        return "poor"
    
    def get_system_performance(self, hours: int = 24) -> Dict[str, Any]:
        """获取系统整体性能"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return {}
            
            end_time = datetime.now().timestamp()
            start_time = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            calls = redis_client.zrangebyscore(
                "api_calls:daily",
                start_time,
                end_time,
                withscores=True
            )
            
            if not calls:
                return {
                    "total_calls": 0,
                    "success_rate": 0.0,
                    "avg_response_time": 0.0,
                    "unique_users": 0,
                    "model_distribution": {}
                }
            
            stats = {
                "total_calls": len(calls),
                "successful_calls": 0,
                "failed_calls": 0,
                "total_response_time": 0.0,
                "unique_users": set(),
                "model_distribution": defaultdict(int),
                "hourly_distribution": defaultdict(int)
            }
            
            for call_data, timestamp in calls:
                try:
                    call = json.loads(call_data)
                    
                    if call.get("success", True):
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1
                    
                    response_time = call.get("response_time", 0)
                    if response_time > 0:
                        stats["total_response_time"] += response_time
                    
                    stats["unique_users"].add(call.get("user_id", ""))
                    stats["model_distribution"][call.get("model_name", "unknown")] += 1
                    
                    # 按小时统计
                    hour = datetime.fromtimestamp(timestamp).strftime("%H:00")
                    stats["hourly_distribution"][hour] += 1
                    
                except json.JSONDecodeError:
                    continue
            
            # 计算指标
            success_rate = stats["successful_calls"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
            avg_response_time = stats["total_response_time"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
            
            return {
                "total_calls": stats["total_calls"],
                "successful_calls": stats["successful_calls"],
                "failed_calls": stats["failed_calls"],
                "success_rate": round(success_rate, 4),
                "avg_response_time": round(avg_response_time, 2),
                "unique_users": len(stats["unique_users"]),
                "model_distribution": dict(stats["model_distribution"]),
                "hourly_distribution": dict(stats["hourly_distribution"])
            }
            
        except Exception as e:
            logger.error(f"获取系统性能失败: {e}")
            return {}
    
    def get_performance_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取性能趋势"""
        try:
            trend_data = []
            
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i)
                day_start = datetime.combine(date, datetime.min.time())
                day_end = datetime.combine(date, datetime.max.time())
                
                start_time = day_start.timestamp()
                end_time = day_end.timestamp()
                
                redis_client = self._get_redis_client()
                if not redis_client:
                    trend_data.append({
                        "date": date.isoformat(),
                        "total_calls": 0,
                        "success_rate": 0.0,
                        "avg_response_time": 0.0
                    })
                    continue
                
                calls = redis_client.zrangebyscore(
                    "api_calls:daily",
                    start_time,
                    end_time,
                    withscores=True
                )
                
                if not calls:
                    trend_data.append({
                        "date": date.isoformat(),
                        "total_calls": 0,
                        "success_rate": 0.0,
                        "avg_response_time": 0.0
                    })
                    continue
                
                successful_calls = 0
                total_response_time = 0.0
                
                for call_data, _ in calls:
                    try:
                        call = json.loads(call_data)
                        if call.get("success", True):
                            successful_calls += 1
                        
                        response_time = call.get("response_time", 0)
                        if response_time > 0:
                            total_response_time += response_time
                            
                    except json.JSONDecodeError:
                        continue
                
                success_rate = successful_calls / len(calls) if calls else 0
                avg_response_time = total_response_time / len(calls) if calls else 0
                
                trend_data.append({
                    "date": date.isoformat(),
                    "total_calls": len(calls),
                    "success_rate": round(success_rate, 4),
                    "avg_response_time": round(avg_response_time, 2)
                })
            
            return list(reversed(trend_data))
            
        except Exception as e:
            logger.error(f"获取性能趋势失败: {e}")
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
                "api_calls:daily",
                0,
                cutoff_time
            )
            
            # 清理模型数据
            model_keys = redis_client.keys("api_calls:model:*")
            for key in model_keys:
                redis_client.zremrangebyscore(key, 0, cutoff_time)
            
            # 清理用户数据
            user_keys = redis_client.keys("api_calls:user:*")
            for key in user_keys:
                redis_client.zremrangebyscore(key, 0, cutoff_time)
            
            logger.info(f"清理AI成功率监控数据成功: 数量={removed_count}")
            return removed_count
            
        except Exception as e:
            logger.error(f"清理AI成功率监控数据失败: {e}")
            return 0
