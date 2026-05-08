# -*- coding: utf-8 -*-
"""
性能监控工具
监控系统性能，识别瓶颈，提供优化建议
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil

from .performance_config import PerformanceConfig

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.query_times = deque(maxlen=1000)
        self.api_response_times = deque(maxlen=1000)
        self.cache_hit_rates = defaultdict(list)
        self.system_metrics = deque(maxlen=100)
        
        self.monitoring_enabled = True
        self.monitor_thread = None
        self.start_monitoring()
    
    def start_monitoring(self):
        """启动性能监控"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.monitoring_enabled = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_enabled = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                self._collect_system_metrics()
                self._analyze_performance()
                time.sleep(PerformanceConfig.MONITORING_INTERVAL)
            except Exception as e:
                logger.error(f"性能监控异常: {e}")
                time.sleep(10)
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            metrics = {
                'timestamp': datetime.now(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'active_connections': len(psutil.net_connections()),
                'query_count': len(self.query_times),
                'api_count': len(self.api_response_times)
            }
            self.system_metrics.append(metrics)
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def _analyze_performance(self):
        """分析性能"""
        try:
            # 分析查询性能
            if self.query_times:
                avg_query_time = sum(self.query_times) / len(self.query_times)
                slow_queries = [t for t in self.query_times if t > PerformanceConfig.SLOW_QUERY_THRESHOLD]
                
                if len(slow_queries) > len(self.query_times) * 0.1:  # 超过10%的查询是慢查询
                    logger.warning(f"检测到慢查询: 平均{avg_query_time:.2f}s, 慢查询比例{len(slow_queries)/len(self.query_times)*100:.1f}%")
            
            # 分析API性能
            if self.api_response_times:
                avg_api_time = sum(self.api_response_times) / len(self.api_response_times)
                if avg_api_time > 2.0:  # 平均API响应时间超过2秒
                    logger.warning(f"API响应时间较慢: 平均{avg_api_time:.2f}s")
            
            # 分析缓存性能
            for cache_name, hit_rates in self.cache_hit_rates.items():
                if hit_rates:
                    avg_hit_rate = sum(hit_rates) / len(hit_rates)
                    if avg_hit_rate < 0.5:  # 缓存命中率低于50%
                        logger.warning(f"缓存命中率较低: {cache_name} {avg_hit_rate*100:.1f}%")
        
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
    
    def record_query_time(self, query_name: str, duration: float):
        """记录查询时间"""
        self.query_times.append(duration)
        
        if PerformanceConfig.PERFORMANCE_LOG_ENABLED:
            if duration > PerformanceConfig.SLOW_QUERY_THRESHOLD:
                logger.warning(f"慢查询: {query_name} 耗时 {duration:.2f}s")
            else:
                logger.debug(f"查询: {query_name} 耗时 {duration:.2f}s")
    
    def record_api_response_time(self, api_name: str, duration: float):
        """记录API响应时间"""
        self.api_response_times.append(duration)
        
        if PerformanceConfig.PERFORMANCE_LOG_ENABLED:
            if duration > 2.0:
                logger.warning(f"慢API: {api_name} 耗时 {duration:.2f}s")
            else:
                logger.debug(f"API: {api_name} 耗时 {duration:.2f}s")
    
    def record_cache_hit(self, cache_name: str, hit: bool):
        """记录缓存命中"""
        hit_rate = 1.0 if hit else 0.0
        self.cache_hit_rates[cache_name].append(hit_rate)
        
        # 保持最近100次记录
        if len(self.cache_hit_rates[cache_name]) > 100:
            self.cache_hit_rates[cache_name] = self.cache_hit_rates[cache_name][-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'query_performance': self._get_query_performance(),
                'api_performance': self._get_api_performance(),
                'cache_performance': self._get_cache_performance(),
                'system_performance': self._get_system_performance(),
                'recommendations': self._get_optimization_recommendations()
            }
            return report
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return {'error': str(e)}
    
    def _get_query_performance(self) -> Dict[str, Any]:
        """获取查询性能"""
        if not self.query_times:
            return {'status': 'no_data'}
        
        avg_time = sum(self.query_times) / len(self.query_times)
        max_time = max(self.query_times)
        slow_queries = len([t for t in self.query_times if t > PerformanceConfig.SLOW_QUERY_THRESHOLD])
        
        return {
            'total_queries': len(self.query_times),
            'avg_time': round(avg_time, 3),
            'max_time': round(max_time, 3),
            'slow_queries': slow_queries,
            'slow_query_rate': round(slow_queries / len(self.query_times) * 100, 1)
        }
    
    def _get_api_performance(self) -> Dict[str, Any]:
        """获取API性能"""
        if not self.api_response_times:
            return {'status': 'no_data'}
        
        avg_time = sum(self.api_response_times) / len(self.api_response_times)
        max_time = max(self.api_response_times)
        slow_apis = len([t for t in self.api_response_times if t > 2.0])
        
        return {
            'total_requests': len(self.api_response_times),
            'avg_time': round(avg_time, 3),
            'max_time': round(max_time, 3),
            'slow_requests': slow_apis,
            'slow_request_rate': round(slow_apis / len(self.api_response_times) * 100, 1)
        }
    
    def _get_cache_performance(self) -> Dict[str, Any]:
        """获取缓存性能"""
        cache_stats = {}
        for cache_name, hit_rates in self.cache_hit_rates.items():
            if hit_rates:
                avg_hit_rate = sum(hit_rates) / len(hit_rates)
                cache_stats[cache_name] = {
                    'hit_rate': round(avg_hit_rate * 100, 1),
                    'total_requests': len(hit_rates)
                }
        
        return cache_stats if cache_stats else {'status': 'no_data'}
    
    def _get_system_performance(self) -> Dict[str, Any]:
        """获取系统性能"""
        if not self.system_metrics:
            return {'status': 'no_data'}
        
        latest = self.system_metrics[-1]
        return {
            'cpu_percent': latest['cpu_percent'],
            'memory_percent': latest['memory_percent'],
            'disk_percent': latest['disk_percent'],
            'active_connections': latest['active_connections']
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        # 查询性能建议
        if self.query_times:
            avg_query_time = sum(self.query_times) / len(self.query_times)
            if avg_query_time > 1.0:
                recommendations.append("考虑优化数据库查询，添加索引或使用缓存")
        
        # API性能建议
        if self.api_response_times:
            avg_api_time = sum(self.api_response_times) / len(self.api_response_times)
            if avg_api_time > 2.0:
                recommendations.append("考虑优化API响应时间，使用异步处理或缓存")
        
        # 缓存性能建议
        for cache_name, hit_rates in self.cache_hit_rates.items():
            if hit_rates:
                avg_hit_rate = sum(hit_rates) / len(hit_rates)
                if avg_hit_rate < 0.5:
                    recommendations.append(f"优化{cache_name}缓存策略，提高命中率")
        
        # 系统资源建议
        if self.system_metrics:
            latest = self.system_metrics[-1]
            if latest['cpu_percent'] > 80:
                recommendations.append("CPU使用率过高，考虑优化计算密集型操作")
            if latest['memory_percent'] > 80:
                recommendations.append("内存使用率过高，考虑清理缓存或优化内存使用")
        
        return recommendations

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
