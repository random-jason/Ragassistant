# -*- coding: utf-8 -*-
"""
系统优化模块
包含性能优化、安全优化、流量保护、成本优化、稳定性优化
"""

import os
import logging
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import redis

from ..config.unified_config import get_config
from .database import db_manager

logger = logging.getLogger(__name__)

class SystemOptimizer:
    """系统优化器"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
        
        # 性能监控
        self.performance_metrics = deque(maxlen=1000)
        self.request_counts = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        
        # 流量控制
        self.rate_limits = {
            "per_minute": 60,      # 每分钟最大请求数
            "per_hour": 1000,      # 每小时最大请求数
            "per_day": 10000       # 每天最大请求数
        }
        
        # 成本控制
        self.cost_limits = {
            "daily": 100.0,        # 每日成本限制（元）
            "hourly": 20.0,        # 每小时成本限制（元）
            "per_request": 0.1     # 单次请求成本限制（元）
        }
        
        # 安全设置
        self.security_settings = {
            "max_input_length": 10000,     # 最大输入长度
            "max_output_length": 5000,     # 最大输出长度
            "blocked_keywords": ["恶意", "攻击", "病毒"],  # 屏蔽关键词
            "max_concurrent_users": 50     # 最大并发用户数（调整为更合理的值）
        }
        
        # 延迟启动监控线程（避免启动时阻塞）
        threading.Timer(5.0, self._start_monitoring).start()
    
    def _init_redis(self):
        """初始化Redis连接（延迟连接）"""
        self.redis_client = None
        self.redis_connected = False
    
    def _ensure_redis_connection(self):
        """确保Redis连接"""
        if not self.redis_connected:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    password=os.getenv("REDIS_PASSWORD", ""),
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True
                )
                self.redis_client.ping()
                self.redis_connected = True
            except Exception as e:
                logger.debug(f"系统优化Redis连接失败: {e}")
                self.redis_client = None
    
    def _start_monitoring(self):
        """启动监控线程"""
        try:
            # 检查是否启用系统监控
            enable_monitoring = get_config().system.monitoring_enabled
            if not enable_monitoring:
                logger.info("系统监控已禁用")
                return
                
            monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
            monitor_thread.start()
        except Exception as e:
            logger.error(f"启动监控线程失败: {e}")
    
    def _monitor_system(self):
        """系统监控循环"""
        while True:
            try:
                self._collect_metrics()
                self._check_performance()
                self._check_security()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"系统监控异常: {e}")
                time.sleep(60)
    
    def _collect_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络IO
            network = psutil.net_io_counters()
            
            # 只统计与我们的应用相关的连接（避免统计系统所有连接）
            app_connections = 0
            try:
                # 获取当前进程的网络连接
                current_process = psutil.Process()
                app_connections = len(current_process.connections())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 如果无法获取当前进程连接，使用一个合理的估算值
                app_connections = 5  # 默认估算值
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "active_connections": app_connections
            }
            
            self.performance_metrics.append(metrics)
            
            # 保存到Redis
            if self.redis_client:
                self.redis_client.lpush(
                    "system_metrics",
                    str(metrics)
                )
                self.redis_client.ltrim("system_metrics", 0, 999)  # 保留最近1000条
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def _check_performance(self):
        """检查性能指标"""
        try:
            if len(self.performance_metrics) < 5:
                return
            
            recent_metrics = list(self.performance_metrics)[-5:]
            
            # 检查CPU使用率
            avg_cpu = sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
            if avg_cpu > 80:
                self._trigger_performance_alert("high_cpu", f"CPU使用率过高: {avg_cpu:.1f}%")
            
            # 检查内存使用率
            avg_memory = sum(m["memory_percent"] for m in recent_metrics) / len(recent_metrics)
            if avg_memory > 85:
                self._trigger_performance_alert("high_memory", f"内存使用率过高: {avg_memory:.1f}%")
            
            # 检查磁盘使用率
            avg_disk = sum(m["disk_percent"] for m in recent_metrics) / len(recent_metrics)
            if avg_disk > 90:
                self._trigger_performance_alert("high_disk", f"磁盘使用率过高: {avg_disk:.1f}%")
            
        except Exception as e:
            logger.error(f"检查性能指标失败: {e}")
    
    def _check_security(self):
        """检查安全指标"""
        try:
            # 检查并发连接数（使用滑动窗口避免误报）
            if len(self.performance_metrics) >= 3:  # 至少需要3个数据点
                recent_metrics = list(self.performance_metrics)[-3:]  # 最近3个数据点
                avg_connections = sum(m.get("active_connections", 0) for m in recent_metrics) / len(recent_metrics)
                
                # 只有当平均连接数持续过高时才触发预警
                if avg_connections > self.security_settings["max_concurrent_users"]:
                    self._trigger_security_alert("high_connections", f"平均并发连接数过高: {avg_connections:.1f}")
            
        except Exception as e:
            logger.error(f"检查安全指标失败: {e}")
    
    def _trigger_performance_alert(self, alert_type: str, message: str):
        """触发性能预警"""
        try:
            from ..core.models import Alert
            
            with db_manager.get_session() as session:
                alert = Alert(
                    rule_name=f"性能监控_{alert_type}",
                    alert_type=alert_type,
                    level="warning",
                    severity="medium",
                    message=message,
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(alert)
                session.commit()
            
            logger.warning(f"性能预警: {message}")
            
        except Exception as e:
            logger.error(f"触发性能预警失败: {e}")
    
    def _trigger_security_alert(self, alert_type: str, message: str):
        """触发安全预警"""
        try:
            from ..core.models import Alert
            
            with db_manager.get_session() as session:
                alert = Alert(
                    rule_name=f"安全监控_{alert_type}",
                    alert_type=alert_type,
                    level="error",
                    severity="high",
                    message=message,
                    is_active=True,
                    created_at=datetime.now()
                )
                session.add(alert)
                session.commit()
            
            logger.warning(f"安全预警: {message}")
            
        except Exception as e:
            logger.error(f"触发安全预警失败: {e}")
    
    def check_rate_limit(self, user_id: str) -> bool:
        """检查用户请求频率限制"""
        try:
            if not self.redis_client:
                return True  # Redis不可用时允许请求
            
            now = datetime.now()
            minute_key = f"rate_limit:{user_id}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:{user_id}:{now.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:{user_id}:{now.strftime('%Y%m%d')}"
            
            # 检查每分钟限制
            minute_count = self.redis_client.get(minute_key) or 0
            if int(minute_count) >= self.rate_limits["per_minute"]:
                logger.warning(f"用户 {user_id} 触发每分钟频率限制")
                return False
            
            # 检查每小时限制
            hour_count = self.redis_client.get(hour_key) or 0
            if int(hour_count) >= self.rate_limits["per_hour"]:
                logger.warning(f"用户 {user_id} 触发每小时频率限制")
                return False
            
            # 检查每日限制
            day_count = self.redis_client.get(day_key) or 0
            if int(day_count) >= self.rate_limits["per_day"]:
                logger.warning(f"用户 {user_id} 触发每日频率限制")
                return False
            
            # 增加计数
            self.redis_client.incr(minute_key)
            self.redis_client.incr(hour_key)
            self.redis_client.incr(day_key)
            
            # 设置过期时间
            self.redis_client.expire(minute_key, 60)
            self.redis_client.expire(hour_key, 3600)
            self.redis_client.expire(day_key, 86400)
            
            return True
            
        except Exception as e:
            logger.error(f"检查频率限制失败: {e}")
            return True  # 出错时允许请求
    
    def check_input_security(self, user_input: str) -> Dict[str, Any]:
        """检查输入安全性"""
        try:
            result = {
                "is_safe": True,
                "blocked_keywords": [],
                "length_check": True,
                "message": "输入安全"
            }
            
            # 检查长度
            if len(user_input) > self.security_settings["max_input_length"]:
                result["is_safe"] = False
                result["length_check"] = False
                result["message"] = f"输入长度超过限制: {len(user_input)} > {self.security_settings['max_input_length']}"
                return result
            
            # 检查屏蔽关键词
            blocked_keywords = []
            for keyword in self.security_settings["blocked_keywords"]:
                if keyword in user_input:
                    blocked_keywords.append(keyword)
            
            if blocked_keywords:
                result["is_safe"] = False
                result["blocked_keywords"] = blocked_keywords
                result["message"] = f"包含屏蔽关键词: {', '.join(blocked_keywords)}"
            
            return result
            
        except Exception as e:
            logger.error(f"检查输入安全性失败: {e}")
            return {
                "is_safe": True,
                "blocked_keywords": [],
                "length_check": True,
                "message": "安全检查异常，允许通过"
            }
    
    def check_cost_limit(self, estimated_cost: float) -> bool:
        """检查成本限制"""
        try:
            if not self.redis_client:
                return True  # Redis不可用时允许请求
            
            now = datetime.now()
            hour_key = f"cost_limit:{now.strftime('%Y%m%d%H')}"
            day_key = f"cost_limit:{now.strftime('%Y%m%d')}"
            
            # 检查单次请求成本
            if estimated_cost > self.cost_limits["per_request"]:
                logger.warning(f"单次请求成本超限: {estimated_cost:.4f} > {self.cost_limits['per_request']}")
                return False
            
            # 检查每小时成本
            hour_cost = float(self.redis_client.get(hour_key) or 0)
            if hour_cost + estimated_cost > self.cost_limits["hourly"]:
                logger.warning(f"每小时成本超限: {hour_cost + estimated_cost:.4f} > {self.cost_limits['hourly']}")
                return False
            
            # 检查每日成本
            day_cost = float(self.redis_client.get(day_key) or 0)
            if day_cost + estimated_cost > self.cost_limits["daily"]:
                logger.warning(f"每日成本超限: {day_cost + estimated_cost:.4f} > {self.cost_limits['daily']}")
                return False
            
            # 增加成本计数
            self.redis_client.incrbyfloat(hour_key, estimated_cost)
            self.redis_client.incrbyfloat(day_key, estimated_cost)
            
            # 设置过期时间
            self.redis_client.expire(hour_key, 3600)
            self.redis_client.expire(day_key, 86400)
            
            return True
            
        except Exception as e:
            logger.error(f"检查成本限制失败: {e}")
            return True  # 出错时允许请求
    
    def optimize_response_time(self, response_time: float) -> Dict[str, Any]:
        """优化响应时间"""
        try:
            self.response_times.append(response_time)
            
            # 计算平均响应时间
            if len(self.response_times) >= 10:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                
                optimization_suggestions = []
                
                if avg_response_time > 5.0:
                    optimization_suggestions.append("考虑增加缓存层")
                
                if avg_response_time > 10.0:
                    optimization_suggestions.append("考虑优化数据库查询")
                
                if avg_response_time > 15.0:
                    optimization_suggestions.append("考虑使用异步处理")
                
                return {
                    "avg_response_time": avg_response_time,
                    "suggestions": optimization_suggestions,
                    "performance_level": self._get_performance_level(avg_response_time)
                }
            
            return {
                "avg_response_time": response_time,
                "suggestions": [],
                "performance_level": "insufficient_data"
            }
            
        except Exception as e:
            logger.error(f"优化响应时间失败: {e}")
            return {}
    
    def _get_performance_level(self, response_time: float) -> str:
        """获取性能等级"""
        if response_time < 2.0:
            return "excellent"
        elif response_time < 5.0:
            return "good"
        elif response_time < 10.0:
            return "fair"
        else:
            return "poor"
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            if not self.performance_metrics:
                return {"status": "no_data"}
            
            latest_metrics = self.performance_metrics[-1]
            
            # 计算趋势
            if len(self.performance_metrics) >= 5:
                recent_cpu = [m["cpu_percent"] for m in list(self.performance_metrics)[-5:]]
                recent_memory = [m["memory_percent"] for m in list(self.performance_metrics)[-5:]]
                
                cpu_trend = "stable"
                if recent_cpu[-1] > recent_cpu[0] + 10:
                    cpu_trend = "increasing"
                elif recent_cpu[-1] < recent_cpu[0] - 10:
                    cpu_trend = "decreasing"
                
                memory_trend = "stable"
                if recent_memory[-1] > recent_memory[0] + 5:
                    memory_trend = "increasing"
                elif recent_memory[-1] < recent_memory[0] - 5:
                    memory_trend = "decreasing"
            else:
                cpu_trend = "insufficient_data"
                memory_trend = "insufficient_data"
            
            return {
                "status": "healthy",
                "cpu_percent": latest_metrics["cpu_percent"],
                "memory_percent": latest_metrics["memory_percent"],
                "disk_percent": latest_metrics["disk_percent"],
                "active_connections": latest_metrics["active_connections"],
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "timestamp": latest_metrics["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def cleanup_old_metrics(self, days: int = 7) -> int:
        """清理旧指标数据"""
        try:
            if not self.redis_client:
                return 0
            
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            # 清理系统指标
            removed_count = self.redis_client.zremrangebyscore(
                "system_metrics",
                0,
                cutoff_time
            )
            
            # 清理频率限制数据
            rate_limit_keys = self.redis_client.keys("rate_limit:*")
            for key in rate_limit_keys:
                self.redis_client.delete(key)
            
            # 清理成本限制数据
            cost_limit_keys = self.redis_client.keys("cost_limit:*")
            for key in cost_limit_keys:
                self.redis_client.delete(key)
            
            logger.info(f"清理系统优化数据成功: 数量={removed_count}")
            return removed_count
            
        except Exception as e:
            logger.error(f"清理系统优化数据失败: {e}")
            return 0
