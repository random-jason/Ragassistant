# -*- coding: utf-8 -*-
"""
工单同步服务
实现飞书多维表格与本地工单系统的双向同步
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.integrations.feishu_client import FeishuClient
from src.integrations.ai_suggestion_service import AISuggestionService
from src.integrations.flexible_field_mapper import FlexibleFieldMapper
from src.core.database import db_manager
from src.core.models import WorkOrder

# 工单状态和优先级枚举
class WorkOrderStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"

class WorkOrderPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

logger = logging.getLogger(__name__)

class WorkOrderSyncService:
    """工单同步服务"""
    
    def __init__(self, feishu_client: FeishuClient, app_token: str, table_id: str):
        """
        初始化同步服务
        
        Args:
            feishu_client: 飞书客户端
            app_token: 多维表格应用token
            table_id: 表格ID
        """
        self.feishu_client = feishu_client
        self.app_token = app_token
        self.table_id = table_id
        self.ai_service = AISuggestionService()
        
        # 初始化灵活字段映射器
        self.field_mapper = FlexibleFieldMapper()
        
        # 保留原有的字段映射作为默认配置（向后兼容）
        self.field_mapping = {
            # 核心字段
            "TR Number": "order_id",
            "TR Description": "description",  # 问题描述
            "Type of problem": "category",
            "TR Level": "priority",
            "TR Status": "status",
            "Source": "source",
            "Date creation": "created_at",
            "处理过程": "resolution",  # 处理过程历史记录（存储完整历史到resolution字段）
            "TR tracking": "resolution",
            
            # 扩展字段
            "Created by": "created_by",
            "Module（模块）": "module",
            "Wilfulness（责任人）": "wilfulness",
            "Date of close TR": "date_of_close",
            "父记录": "parent_record",
            "Has it been updated on the same day": "has_updated_same_day",
            "Operating time": "operating_time",
            
            # AI建议字段
            "AI建议": "ai_suggestion",
            "Issue Start Time": "updated_at"
        }
        
        # 将原有映射添加到灵活映射器中
        self._init_flexible_mapper()
        
        # 状态映射
        self.status_mapping = {
            "close": WorkOrderStatus.CLOSED,
            "temporary close": WorkOrderStatus.IN_PROGRESS,
            "OTA": WorkOrderStatus.IN_PROGRESS,
            "open": WorkOrderStatus.PENDING,
            "pending": WorkOrderStatus.PENDING,
            "completed": WorkOrderStatus.COMPLETED
        }
        
        # 优先级映射
        self.priority_mapping = {
            "Low": WorkOrderPriority.LOW,
            "Medium": WorkOrderPriority.MEDIUM,
            "High": WorkOrderPriority.HIGH,
            "Urgent": WorkOrderPriority.URGENT
        }
    
    def _init_flexible_mapper(self):
        """初始化灵活映射器，将原有映射添加到其中"""
        for feishu_field, local_field in self.field_mapping.items():
            self.field_mapper.add_field_mapping(feishu_field, local_field)
    
    def get_field_discovery_report(self, feishu_fields: Dict[str, Any]) -> Dict[str, Any]:
        """获取字段发现报告"""
        return self.field_mapper.discover_fields(feishu_fields)
    
    def add_field_mapping(self, feishu_field: str, local_field: str, 
                         aliases: List[str] = None, patterns: List[str] = None,
                         priority: int = 3) -> bool:
        """添加字段映射"""
        return self.field_mapper.add_field_mapping(feishu_field, local_field, aliases, patterns, priority)
    
    def remove_field_mapping(self, feishu_field: str) -> bool:
        """移除字段映射"""
        return self.field_mapper.remove_field_mapping(feishu_field)
    
    def get_mapping_status(self) -> Dict[str, Any]:
        """获取映射状态"""
        return self.field_mapper.get_mapping_status()
    
    def sync_from_feishu(self, generate_ai_suggestions: bool = True, limit: int = 10) -> Dict[str, Any]:
        """
        从飞书同步工单数据到本地系统
        
        Args:
            generate_ai_suggestions: 是否生成AI建议
            limit: 处理记录数量限制
            
        Returns:
            同步结果统计
        """
        try:
            logger.info("开始从飞书同步工单数据...")
            
            # 获取飞书表格记录
            records = self.feishu_client.get_table_records(self.app_token, self.table_id, page_size=limit)
            
            if records.get("code") != 0:
                raise Exception(f"获取飞书记录失败: {records.get('msg', '未知错误')}")
            
            items = records.get("data", {}).get("items", [])
            logger.info(f"从飞书获取 {len(items)} 条记录")
            
            # 生成AI建议
            if generate_ai_suggestions:
                logger.info("开始生成AI建议...")
                
                # 调试：记录第一条记录的结构
                if items and len(items) > 0:
                    logger.info(f"第一条记录结构示例: record_id={items[0].get('record_id')}, 有fields字段={('fields' in items[0])}")
                    if 'fields' in items[0]:
                        logger.info(f"第一条记录的fields示例: {list(items[0]['fields'].keys())[:5]}")
                        logger.info(f"第一条记录的AI建议字段内容: {items[0].get('fields', {}).get('AI建议', '无')[:50] if items[0].get('fields', {}).get('AI建议') else '无'}")
                
                items = self.ai_service.batch_generate_suggestions(items, limit)
                
                # 将AI建议更新回飞书表格
                for item in items:
                    if "ai_suggestion" in item:
                        try:
                            self.feishu_client.update_table_record(
                                self.app_token, 
                                self.table_id, 
                                item["record_id"],
                                {"AI建议": item["ai_suggestion"]}
                            )
                            logger.info(f"更新飞书记录 {item['record_id']} 的AI建议")
                        except Exception as e:
                            logger.error(f"更新飞书AI建议失败: {e}")
            
            synced_count = 0
            updated_count = 0
            created_count = 0
            errors = []
            
            with db_manager.get_session() as session:
                for record in items:
                    try:
                        # 解析飞书记录
                        parsed_fields = self.feishu_client.parse_record_fields(record)
                        feishu_id = record.get("record_id")
                        
                        # 查找本地是否存在对应记录
                        existing_workorder = session.query(WorkOrder).filter(
                            WorkOrder.feishu_record_id == feishu_id
                        ).first()
                        
                        workorder_data = self._convert_feishu_to_local(parsed_fields)
                        workorder_data["feishu_record_id"] = feishu_id
                        
                        # 过滤掉WorkOrder模型不支持的字段（防止dict参数错误）
                        valid_fields = {}
                        for key, value in workorder_data.items():
                            if hasattr(WorkOrder, key):
                                # 确保值不是dict、list等复杂类型
                                if isinstance(value, (dict, list)):
                                    logger.warning(f"字段 '{key}' 包含复杂类型 {type(value).__name__}，跳过")
                                    continue
                                valid_fields[key] = value
                        
                        if existing_workorder:
                            # 更新现有记录
                            for key, value in valid_fields.items():
                                if key != "feishu_record_id":
                                    setattr(existing_workorder, key, value)
                            existing_workorder.updated_at = datetime.now()
                            updated_count += 1
                        else:
                            # 创建新记录
                            valid_fields["created_at"] = datetime.now()
                            valid_fields["updated_at"] = datetime.now()
                            new_workorder = WorkOrder(**valid_fields)
                            session.add(new_workorder)
                            created_count += 1
                        
                        synced_count += 1
                        
                    except Exception as e:
                        error_msg = f"处理记录 {record.get('record_id', 'unknown')} 失败: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                session.commit()
            
            result = {
                "success": True,
                "total_records": len(items),
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "ai_suggestions_generated": generate_ai_suggestions,
                "errors": errors
            }
            
            logger.info(f"飞书同步完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"飞书同步失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_to_feishu(self, workorder_id: int) -> Dict[str, Any]:
        """将本地工单同步到飞书"""
        try:
            with db_manager.get_session() as session:
                workorder = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
                if not workorder:
                    return {"success": False, "error": "工单不存在"}
                
                feishu_fields = self._convert_local_to_feishu(workorder)
                
                if workorder.feishu_record_id:
                    result = self.feishu_client.update_table_record(
                        self.app_token, self.table_id, workorder.feishu_record_id, feishu_fields
                    )
                else:
                    result = self.feishu_client.create_table_record(
                        self.app_token, self.table_id, feishu_fields
                    )
                    
                    if result.get("code") == 0:
                        workorder.feishu_record_id = result["data"]["record"]["record_id"]
                        session.commit()
                
                if result.get("code") == 0:
                    return {"success": True, "message": "同步成功"}
                else:
                    return {"success": False, "error": result.get("msg", "同步失败")}
                    
        except Exception as e:
            logger.error(f"同步到飞书失败: {e}")
            return {"success": False, "error": str(e)}
    
    def create_workorder_from_feishu_record(self, record_id: str) -> Dict[str, Any]:
        """从飞书单条记录创建工单"""
        try:
            logger.info(f"从飞书记录 {record_id} 创建工单")
            
            feishu_data = self.feishu_client.get_table_record(
                self.app_token, 
                self.table_id, 
                record_id
            )
            
            if feishu_data.get("code") != 0:
                return {
                    "success": False,
                    "message": f"获取飞书记录失败: {feishu_data.get('msg', '未知错误')}"
                }
            
            record = feishu_data.get("data", {}).get("record")
            if not record:
                return {
                    "success": False,
                    "message": "飞书记录不存在"
                }
            
            fields = record.get("fields", {})
            local_data = self._convert_feishu_to_local(fields)
            local_data["feishu_record_id"] = record_id
            
            existing_workorder = self._find_existing_workorder(record_id)
            
            if existing_workorder:
                return {
                    "success": False,
                    "message": f"工单已存在: {existing_workorder.order_id}"
                }
            
            workorder = self._create_workorder(local_data)
            
            return {
                "success": True,
                "message": f"工单创建成功: {local_data.get('order_id')}",
                "workorder_id": workorder.id,
                "order_id": local_data.get('order_id')
            }
            
        except Exception as e:
            logger.error(f"从飞书记录创建工单失败: {e}")
            return {
                "success": False,
                "message": f"创建工单失败: {str(e)}"
            }
    
    def _find_existing_workorder(self, feishu_record_id: str) -> Optional[WorkOrder]:
        """查找已存在的工单"""
        try:
            with db_manager.get_session() as session:
                return session.query(WorkOrder).filter(
                    WorkOrder.feishu_record_id == feishu_record_id
                ).first()
        except Exception as e:
            logger.error(f"查找现有工单失败: {e}")
            return None
    
    def _create_workorder(self, local_data: Dict[str, Any]) -> WorkOrder:
        """创建新工单"""
        try:
            with db_manager.get_session() as session:
                # 只使用WorkOrder模型支持的字段
                valid_data = {}
                for key, value in local_data.items():
                    if hasattr(WorkOrder, key):
                        # 确保值不是dict、list等复杂类型
                        if isinstance(value, (dict, list)):
                            logger.warning(f"字段 '{key}' 包含复杂类型 {type(value).__name__}，跳过")
                            continue
                        valid_data[key] = value
                
                workorder = WorkOrder(**valid_data)
                session.add(workorder)
                session.commit()
                session.refresh(workorder)
                logger.info(f"创建工单成功: {workorder.order_id}")
                return workorder
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            raise
    
    def _update_workorder(self, workorder: WorkOrder, local_data: Dict[str, Any]) -> WorkOrder:
        """更新现有工单"""
        try:
            with db_manager.get_session() as session:
                workorder.title = local_data.get("title", workorder.title)
                workorder.description = local_data.get("description", workorder.description)
                workorder.category = local_data.get("category", workorder.category)
                workorder.priority = local_data.get("priority", workorder.priority)
                workorder.status = local_data.get("status", workorder.status)
                workorder.updated_at = local_data.get("updated_at", workorder.updated_at)
                workorder.resolution = local_data.get("solution", workorder.resolution)
                workorder.assignee = local_data.get("assignee", workorder.assignee)
                workorder.solution = local_data.get("solution", workorder.solution)
                workorder.ai_suggestion = local_data.get("ai_suggestion", workorder.ai_suggestion)
                
                session.commit()
                session.refresh(workorder)
                logger.info(f"更新工单成功: {workorder.order_id}")
                return workorder
        except Exception as e:
            logger.error(f"更新工单失败: {e}")
            raise
    
    def _update_feishu_ai_suggestion(self, record_id: str, ai_suggestion: str) -> bool:
        """更新飞书表格中的AI建议"""
        try:
            result = self.feishu_client.update_table_record(
                self.app_token,
                self.table_id,
                record_id,
                {"AI建议": ai_suggestion}
            )
            logger.info(f"更新飞书AI建议结果: {result}")
            return result.get("code") == 0
        except Exception as e:
            logger.error(f"更新飞书AI建议失败: {e}")
            return False

    def _convert_feishu_to_local(self, feishu_fields: Dict[str, Any]) -> Dict[str, Any]:
        """将飞书字段转换为本地工单字段"""
        logger.info(f"开始转换飞书字段: {feishu_fields}")
        
        local_data, conversion_stats = self.field_mapper.convert_fields(feishu_fields)
        
        logger.info(f"字段转换统计: 总字段 {conversion_stats['total_fields']}, "
                   f"已映射 {conversion_stats['mapped_fields']}, "
                   f"未映射 {len(conversion_stats['unmapped_fields'])}")
        
        if conversion_stats['unmapped_fields']:
            logger.warning(f"未映射字段: {conversion_stats['unmapped_fields']}")
            for field in conversion_stats['unmapped_fields']:
                suggestions = conversion_stats['mapping_details'][field].get('suggestions', [])
                if suggestions:
                    logger.info(f"字段 '{field}' 的建议映射: {suggestions[0] if suggestions else '无'}")
        
        # 特殊字段处理
        for local_field, value in local_data.items():
            if local_field == "status" and value in self.status_mapping:
                local_data[local_field] = self.status_mapping[value]
            elif local_field == "priority" and value in self.priority_mapping:
                local_data[local_field] = self.priority_mapping[value]
            elif local_field in ["created_at", "updated_at", "date_of_close"] and value:
                try:
                    if isinstance(value, (int, float)):
                        local_data[local_field] = datetime.fromtimestamp(value / 1000)
                    else:
                        local_data[local_field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"时间字段转换失败: {e}, 使用当前时间")
                    local_data[local_field] = datetime.now()
        
        # 生成标题：使用TR Description作为标题
        tr_description = feishu_fields.get("TR Description", "")
        if tr_description:
            # 标题直接使用问题描述，如果太长则截断
            if len(tr_description) > 200:
                local_data["title"] = tr_description[:197] + "..."
            else:
                local_data["title"] = tr_description
        else:
            # 如果没有描述，使用TR Number
            tr_number = feishu_fields.get("TR Number", "")
            if tr_number:
                local_data["title"] = f"{tr_number} - TR工单"
            else:
                local_data["title"] = "TR工单"
        
        # 处理"处理过程"字段：提取最新一条作为solution
        # "处理过程"字段已映射到resolution，这里需要：
        # 1. resolution存储完整的"处理过程"历史
        # 2. solution存储"处理过程"的最新一条
        process_history = local_data.get("resolution", "")
        if process_history and isinstance(process_history, str):
            # 按换行分割，获取最后一行（最新一条）
            process_lines = [line.strip() for line in process_history.split('\n') if line.strip()]
            if process_lines:
                # 最新一条作为solution
                local_data["solution"] = process_lines[-1]
                # 完整历史保留在resolution（已在字段映射中设置）
            else:
                local_data["solution"] = ""
        else:
            local_data["solution"] = ""
        
        # 设置默认值
        if "status" not in local_data:
            local_data["status"] = WorkOrderStatus.PENDING
        if "priority" not in local_data:
            local_data["priority"] = WorkOrderPriority.MEDIUM
        if "category" not in local_data:
            local_data["category"] = "Remote control"
            
        return local_data
    
    def _convert_local_to_feishu(self, workorder: WorkOrder) -> Dict[str, Any]:
        """将本地工单字段转换为飞书字段"""
        feishu_fields = {}
        
        reverse_mapping = {v: k for k, v in self.field_mapping.items()}
        
        for local_field, feishu_field in reverse_mapping.items():
            value = getattr(workorder, local_field, None)
            if value is not None:
                if local_field == "status":
                    reverse_status = {v: k for k, v in self.status_mapping.items()}
                    value = reverse_status.get(value, str(value))
                elif local_field == "priority":
                    reverse_priority = {v: k for k, v in self.priority_mapping.items()}
                    value = reverse_priority.get(value, str(value))
                elif local_field in ["created_at", "updated_at"] and isinstance(value, datetime):
                    value = value.isoformat()
                
                feishu_fields[feishu_field] = value
        
        return feishu_fields
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态统计"""
        try:
            with db_manager.get_session() as session:
                total_local = session.query(WorkOrder).count()
                synced_count = session.query(WorkOrder).filter(
                    WorkOrder.feishu_record_id.isnot(None)
                ).count()
                
                return {
                    "total_local_workorders": total_local,
                    "synced_workorders": synced_count,
                    "unsynced_workorders": total_local - synced_count
                }
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {"error": str(e)}
