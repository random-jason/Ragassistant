# -*- coding: utf-8 -*-
"""
数据库查询优化器
提供查询优化、批量操作、连接池管理等功能
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from contextlib import contextmanager

from .cache_manager import cache_manager, cache_result
from .database import db_manager
from .models import Conversation, WorkOrder, Alert, KnowledgeEntry

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
    
    @cache_result(ttl=60)  # 缓存1分钟，提高响应速度
    def get_conversations_paginated(self, page: int = 1, per_page: int = 10, 
                                   search: str = '', user_id: str = '', 
                                   date_filter: str = '') -> Dict[str, Any]:
        """分页获取对话记录（优化版）"""
        start_time = time.time()
        
        try:
            with db_manager.get_session() as session:
                # 构建基础查询
                query = session.query(Conversation)
                
                # 应用过滤条件
                if search:
                    query = query.filter(
                        Conversation.user_message.contains(search) |
                        Conversation.assistant_response.contains(search)
                    )
                
            # Conversation模型没有user_id字段，跳过用户过滤
            # if user_id:
            #     query = query.filter(Conversation.user_id == user_id)
                
                if date_filter:
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    if date_filter == 'today':
                        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif date_filter == 'week':
                        start_date = now - timedelta(days=7)
                    elif date_filter == 'month':
                        start_date = now - timedelta(days=30)
                    else:
                        start_date = None
                    
                    if start_date:
                        query = query.filter(Conversation.timestamp >= start_date)
                
                # 获取总数（使用索引优化）
                total = query.count()
                
                # 分页查询（使用索引）
                conversations = query.order_by(
                    Conversation.timestamp.desc()
                ).offset((page - 1) * per_page).limit(per_page).all()
                
                # 统计数据（批量查询）
                stats = self._get_conversation_stats(session)
                
                # 分页信息
                pagination = {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page,
                    'total': total
                }
                
                # 转换数据格式
                conversation_list = []
                for conv in conversations:
                    conversation_list.append({
                        'id': conv.id,
                        'user_message': conv.user_message,
                        'assistant_response': conv.assistant_response,
                        'timestamp': conv.timestamp.isoformat() if conv.timestamp else None,
                        'confidence_score': conv.confidence_score,
                        'work_order_id': conv.work_order_id
                    })
                
                # 记录查询时间
                query_time = time.time() - start_time
                self._record_query_time('get_conversations_paginated', query_time)
                
                return {
                    'success': True,
                    'conversations': conversation_list,
                    'pagination': pagination,
                    'stats': stats,
                    'query_time': query_time
                }
                
        except Exception as e:
            logger.error(f"分页查询对话失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_conversation_stats(self, session: Session) -> Dict[str, Any]:
        """获取对话统计信息（批量查询优化）"""
        try:
            from datetime import datetime
            
            # 使用单个查询获取多个统计信息
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 批量查询统计信息
            stats_query = session.query(
                func.count(Conversation.id).label('total'),
                func.avg(Conversation.confidence_score).label('avg_response_time')
            ).first()
            
            today_count = session.query(Conversation).filter(
                Conversation.timestamp >= today_start
            ).count()
            
            return {
                'total': stats_query.total or 0,
                'today': today_count,
                'avg_response_time': round(stats_query.avg_response_time or 0, 2),
                'active_users': 1  # Conversation模型没有user_id，暂时设为1
            }
        except Exception as e:
            logger.error(f"获取对话统计失败: {e}")
            return {'total': 0, 'today': 0, 'avg_response_time': 0, 'active_users': 0}
    
    @cache_result(ttl=30)  # 缓存30秒，提高响应速度
    def get_workorders_optimized(self, status_filter: str = '', 
                                priority_filter: str = '') -> List[Dict[str, Any]]:
        """优化版工单查询"""
        start_time = time.time()
        
        try:
            with db_manager.get_session() as session:
                query = session.query(WorkOrder)
                
                if status_filter and status_filter != 'all':
                    query = query.filter(WorkOrder.status == status_filter)
                
                if priority_filter and priority_filter != 'all':
                    query = query.filter(WorkOrder.priority == priority_filter)
                
                # 使用索引排序
                workorders = query.order_by(
                    WorkOrder.created_at.desc()
                ).limit(100).all()  # 限制返回数量
                
                result = []
                for wo in workorders:
                    result.append({
                        "id": wo.id,
                        "order_id": wo.order_id,
                        "title": wo.title,
                        "description": wo.description,
                        "category": wo.category,
                        "priority": wo.priority,
                        "status": wo.status,
                        "created_at": wo.created_at.isoformat() if wo.created_at else None,
                        "updated_at": wo.updated_at.isoformat() if wo.updated_at else None,
                        "resolution": wo.resolution,
                        "satisfaction_score": wo.satisfaction_score
                    })
                
                query_time = time.time() - start_time
                self._record_query_time('get_workorders_optimized', query_time)
                
                return result
                
        except Exception as e:
            logger.error(f"优化工单查询失败: {e}")
            return []
    
    def batch_insert_conversations(self, conversations: List[Dict[str, Any]]) -> bool:
        """批量插入对话记录"""
        try:
            with db_manager.get_session() as session:
                # 批量插入
                conversation_objects = []
                for conv_data in conversations:
                    conv = Conversation(**conv_data)
                    conversation_objects.append(conv)
                
                session.add_all(conversation_objects)
                session.commit()
                
                # 清除相关缓存
                cache_manager.delete('get_conversations_paginated')
                
                logger.info(f"批量插入 {len(conversations)} 条对话记录")
                return True
                
        except Exception as e:
            logger.error(f"批量插入对话记录失败: {e}")
            return False
    
    def batch_update_workorders(self, updates: List[Tuple[int, Dict[str, Any]]]) -> bool:
        """批量更新工单"""
        try:
            with db_manager.get_session() as session:
                for workorder_id, update_data in updates:
                    workorder = session.query(WorkOrder).filter(
                        WorkOrder.id == workorder_id
                    ).first()
                    
                    if workorder:
                        for key, value in update_data.items():
                            setattr(workorder, key, value)
                
                session.commit()
                
                # 清除相关缓存
                cache_manager.delete('get_workorders_optimized')
                
                logger.info(f"批量更新 {len(updates)} 个工单")
                return True
                
        except Exception as e:
            logger.error(f"批量更新工单失败: {e}")
            return False
    
    def get_analytics_optimized(self, days: int = 30) -> Dict[str, Any]:
        """优化版分析数据查询"""
        start_time = time.time()
        
        try:
            with db_manager.get_session() as session:
                from datetime import datetime, timedelta
                
                end_time = datetime.now()
                start_time_query = end_time - timedelta(days=days-1)
                
                # 批量查询所有需要的数据
                # 修改：查询所有工单，不限制时间范围
                workorders = session.query(WorkOrder).all()
                
                # 修改：查询所有预警和对话，不限制时间范围
                alerts = session.query(Alert).all()
                
                conversations = session.query(Conversation).all()
                
                # 处理数据
                analytics = self._process_analytics_data(workorders, alerts, conversations, days)
                
                query_time = time.time() - start_time
                self._record_query_time('get_analytics_optimized', query_time)
                
                return analytics
                
        except Exception as e:
            logger.error(f"优化分析查询失败: {e}")
            return {}
    
    def _process_analytics_data(self, workorders, alerts, conversations, days):
        """处理分析数据"""
        from collections import defaultdict, Counter
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days-1)
        
        # 趋势数据
        day_keys = [(start_time + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
        wo_by_day = Counter([(wo.created_at.strftime('%Y-%m-%d') if wo.created_at else end_time.strftime('%Y-%m-%d')) for wo in workorders])
        alert_by_day = Counter([(al.created_at.strftime('%Y-%m-%d') if al.created_at else end_time.strftime('%Y-%m-%d')) for al in alerts])
        
        trend = [{
            'date': d,
            'workorders': int(wo_by_day.get(d, 0)),
            'alerts': int(alert_by_day.get(d, 0))
        } for d in day_keys]
        
        # 工单统计
        total = len(workorders)
        status_counts = Counter([wo.status for wo in workorders])
        category_counts = Counter([wo.category for wo in workorders])
        priority_counts = Counter([wo.priority for wo in workorders])
        
        
        # 处理状态映射（支持中英文状态）
        status_mapping = {
            'open': ['open', '待处理', '新建', 'new'],
            'in_progress': ['in_progress', '处理中', '进行中', 'progress', 'processing', 'analysising', 'analyzing'],
            'resolved': ['resolved', '已解决', '已完成'],
            'closed': ['closed', '已关闭', '关闭']
        }
        
        # 统计各状态的数量
        mapped_counts = {'open': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0}
        
        for status, count in status_counts.items():
            if status is None:
                continue
            status_lower = str(status).lower()
            mapped = False
            for mapped_status, possible_values in status_mapping.items():
                if status_lower in [v.lower() for v in possible_values]:
                    mapped_counts[mapped_status] += count
                    mapped = True
                    break
            
            if not mapped:
                logger.warning(f"未映射的状态: '{status}' (数量: {count})")
        
        
        resolved_count = mapped_counts['resolved']
        
        workorders_stats = {
            'total': total,
            'open': mapped_counts['open'],
            'in_progress': mapped_counts['in_progress'],
            'resolved': mapped_counts['resolved'],
            'closed': mapped_counts['closed'],
            'by_category': dict(category_counts),
            'by_priority': dict(priority_counts)
        }
        
        # 满意度统计
        scores = [float(wo.satisfaction_score) for wo in workorders if wo.satisfaction_score is not None]
        avg_satisfaction = round(sum(scores)/len(scores), 1) if scores else 0
        dist = Counter([str(int(round(s))) for s in scores]) if scores else {}
        
        satisfaction_stats = {
            'average': avg_satisfaction,
            'distribution': {k: int(v) for k, v in dist.items()}
        }
        
        # 预警统计
        level_counts = Counter([al.level for al in alerts])
        active_alerts = len([al for al in alerts if al.is_active])
        resolved_alerts = len([al for al in alerts if not al.is_active and al.resolved_at])
        
        alerts_stats = {
            'total': len(alerts),
            'active': active_alerts,
            'resolved': resolved_alerts,
            'by_level': {k: int(v) for k, v in level_counts.items()}
        }
        
        # 性能指标
        resp_times = [float(c.response_time) for c in conversations if c.response_time is not None]
        avg_resp = round(sum(resp_times)/len(resp_times), 2) if resp_times else 0
        throughput = len(conversations)
        
        critical = level_counts.get('critical', 0)
        error_rate = round((critical / alerts_stats['total']) * 100, 2) if alerts_stats['total'] > 0 else 0
        
        performance_stats = {
            'response_time': avg_resp,
            'uptime': 99.0,
            'error_rate': error_rate,
            'throughput': throughput
        }
        
        return {
            'trend': trend,
            'workorders': workorders_stats,
            'satisfaction': satisfaction_stats,
            'alerts': alerts_stats,
            'performance': performance_stats,
            'summary': {
                'total_workorders': total,
                'resolution_rate': round((resolved_count/total)*100, 1) if total > 0 else 0,
                'avg_satisfaction': avg_satisfaction,
                'active_alerts': active_alerts
            }
        }
    
    def _record_query_time(self, query_name: str, query_time: float):
        """记录查询时间"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = []
        
        self.query_stats[query_name].append(query_time)
        
        # 保持最近100次记录
        if len(self.query_stats[query_name]) > 100:
            self.query_stats[query_name] = self.query_stats[query_name][-100:]
        
    
    def get_query_performance_report(self) -> Dict[str, Any]:
        """获取查询性能报告"""
        report = {}
        
        for query_name, times in self.query_stats.items():
            if times:
                report[query_name] = {
                    'count': len(times),
                    'avg_time': round(sum(times) / len(times), 3),
                    'max_time': round(max(times), 3),
                    'min_time': round(min(times), 3),
                    'slow_queries': len([t for t in times if t > self.slow_query_threshold])
                }
        
        return report
    
    def optimize_database_indexes(self) -> bool:
        """优化数据库索引"""
        try:
            with db_manager.get_session() as session:
                # 创建常用查询的索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_conversations_work_order_id ON conversations(work_order_id)",
                    "CREATE INDEX IF NOT EXISTS idx_workorders_status ON work_orders(status)",
                    "CREATE INDEX IF NOT EXISTS idx_workorders_priority ON work_orders(priority)",
                    "CREATE INDEX IF NOT EXISTS idx_workorders_created_at ON work_orders(created_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_is_active ON alerts(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC)"
                ]
                
                for index_sql in indexes:
                    try:
                        session.execute(text(index_sql))
                    except Exception as e:
                        logger.warning(f"创建索引失败: {e}")
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"数据库索引优化失败: {e}")
            return False
    
    def clear_all_caches(self) -> bool:
        """清除所有缓存"""
        try:
            cache_manager.clear()
            logger.info("所有缓存已清除")
            return True
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False


# 全局查询优化器实例
query_optimizer = QueryOptimizer()
