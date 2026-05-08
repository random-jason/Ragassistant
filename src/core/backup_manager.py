# -*- coding: utf-8 -*-
"""
数据库备份管理器
提供MySQL到SQLite的备份功能
"""

import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .models import Base, WorkOrder, Conversation, KnowledgeEntry, Alert, Analytics, WorkOrderSuggestion
from .database import db_manager

logger = logging.getLogger(__name__)

class BackupManager:
    """数据库备份管理器"""
    
    def __init__(self, backup_db_path: str = "helpdesk.db"):
        self.backup_db_path = backup_db_path
        self.backup_engine = None
        self.BackupSessionLocal = None
        self._initialize_backup_db()
    
    def _initialize_backup_db(self):
        """初始化备份数据库"""
        try:
            # 创建SQLite备份数据库连接
            self.backup_engine = create_engine(
                f"sqlite:///{self.backup_db_path}",
                echo=False,
                connect_args={"check_same_thread": False}
            )
            
            self.BackupSessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.backup_engine
            )
            
            # 创建备份数据库表
            Base.metadata.create_all(bind=self.backup_engine)
            logger.info(f"备份数据库初始化成功: {self.backup_db_path}")
            
        except Exception as e:
            logger.error(f"备份数据库初始化失败: {e}")
            raise
    
    @contextmanager
    def get_backup_session(self):
        """获取备份数据库会话"""
        session = self.BackupSessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"备份数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def get_backup_session_direct(self):
        """直接获取备份数据库会话"""
        return self.BackupSessionLocal()
    
    def backup_all_data(self) -> Dict[str, Any]:
        """备份所有数据到SQLite"""
        backup_result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "backup_file": self.backup_db_path,
            "tables": {},
            "errors": []
        }
        
        try:
            # 清空备份数据库
            self._clear_backup_database()
            
            # 备份各个表
            tables_to_backup = [
                ("work_orders", WorkOrder),
                ("conversations", Conversation),
                ("knowledge_entries", KnowledgeEntry),

                ("alerts", Alert),
                ("analytics", Analytics),
                ("work_order_suggestions", WorkOrderSuggestion)
            ]
            
            for table_name, model_class in tables_to_backup:
                try:
                    count = self._backup_table(model_class, table_name)
                    backup_result["tables"][table_name] = count
                    logger.info(f"备份表 {table_name}: {count} 条记录")
                except Exception as e:
                    error_msg = f"备份表 {table_name} 失败: {str(e)}"
                    backup_result["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # 计算备份文件大小
            if os.path.exists(self.backup_db_path):
                backup_result["backup_size"] = os.path.getsize(self.backup_db_path)
            
            logger.info(f"数据备份完成: {backup_result}")
            
        except Exception as e:
            backup_result["success"] = False
            backup_result["errors"].append(f"备份过程失败: {str(e)}")
            logger.error(f"数据备份失败: {e}")
        
        return backup_result
    
    def _clear_backup_database(self):
        """清空备份数据库"""
        try:
            with self.get_backup_session() as backup_session:
                # 删除所有表的数据
                for table in Base.metadata.tables.values():
                    backup_session.execute(text(f"DELETE FROM {table.name}"))
                backup_session.commit()
                logger.info("备份数据库已清空")
        except Exception as e:
            logger.error(f"清空备份数据库失败: {e}")
            raise
    
    def _backup_table(self, model_class, table_name: str) -> int:
        """备份单个表的数据"""
        count = 0
        
        try:
            # 从MySQL读取数据
            with db_manager.get_session() as mysql_session:
                records = mysql_session.query(model_class).all()
                
                # 写入SQLite备份数据库
                with self.get_backup_session() as backup_session:
                    for record in records:
                        # 创建新记录对象
                        backup_record = model_class()
                        
                        # 复制所有字段
                        for column in model_class.__table__.columns:
                            if hasattr(record, column.name):
                                setattr(backup_record, column.name, getattr(record, column.name))
                        
                        backup_session.add(backup_record)
                        count += 1
                    
                    backup_session.commit()
        
        except Exception as e:
            logger.error(f"备份表 {table_name} 失败: {e}")
            raise
        
        return count
    
    def restore_from_backup(self, table_name: str = None) -> Dict[str, Any]:
        """从备份恢复数据到MySQL"""
        restore_result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "restored_tables": {},
            "errors": []
        }
        
        try:
            if not os.path.exists(self.backup_db_path):
                raise FileNotFoundError(f"备份文件不存在: {self.backup_db_path}")
            
            # 确定要恢复的表
            tables_to_restore = [
                ("work_orders", WorkOrder),
                ("conversations", Conversation),
                ("knowledge_entries", KnowledgeEntry),

                ("alerts", Alert),
                ("analytics", Analytics),
                ("work_order_suggestions", WorkOrderSuggestion)
            ]
            
            if table_name:
                tables_to_restore = [(tn, mc) for tn, mc in tables_to_restore if tn == table_name]
            
            for table_name, model_class in tables_to_restore:
                try:
                    count = self._restore_table(model_class, table_name)
                    restore_result["restored_tables"][table_name] = count
                    logger.info(f"恢复表 {table_name}: {count} 条记录")
                except Exception as e:
                    error_msg = f"恢复表 {table_name} 失败: {str(e)}"
                    restore_result["errors"].append(error_msg)
                    logger.error(error_msg)
            
        except Exception as e:
            restore_result["success"] = False
            restore_result["errors"].append(f"恢复过程失败: {str(e)}")
            logger.error(f"数据恢复失败: {e}")
        
        return restore_result
    
    def _restore_table(self, model_class, table_name: str) -> int:
        """恢复单个表的数据"""
        count = 0
        
        try:
            # 从SQLite备份读取数据
            with self.get_backup_session() as backup_session:
                records = backup_session.query(model_class).all()
                
                # 写入MySQL数据库
                with db_manager.get_session() as mysql_session:
                    # 清空目标表
                    mysql_session.query(model_class).delete()
                    
                    for record in records:
                        # 创建新记录对象
                        mysql_record = model_class()
                        
                        # 复制所有字段
                        for column in model_class.__table__.columns:
                            if hasattr(record, column.name):
                                setattr(mysql_record, column.name, getattr(record, column.name))
                        
                        mysql_session.add(mysql_record)
                        count += 1
                    
                    mysql_session.commit()
        
        except Exception as e:
            logger.error(f"恢复表 {table_name} 失败: {e}")
            raise
        
        return count
    
    def get_backup_info(self) -> Dict[str, Any]:
        """获取备份信息"""
        info = {
            "backup_file": self.backup_db_path,
            "exists": os.path.exists(self.backup_db_path),
            "size": 0,
            "last_modified": None,
            "table_counts": {}
        }
        
        if info["exists"]:
            info["size"] = os.path.getsize(self.backup_db_path)
            info["last_modified"] = datetime.fromtimestamp(
                os.path.getmtime(self.backup_db_path)
            ).isoformat()
            
            # 统计备份数据库中的记录数
            try:
                with self.get_backup_session() as session:
                    tables = [
                        ("work_orders", WorkOrder),
                        ("conversations", Conversation),
                        ("knowledge_entries", KnowledgeEntry),
        
                        ("alerts", Alert),
                        ("analytics", Analytics),
                        ("work_order_suggestions", WorkOrderSuggestion)
                    ]
                    
                    for table_name, model_class in tables:
                        try:
                            count = session.query(model_class).count()
                            info["table_counts"][table_name] = count
                        except Exception:
                            info["table_counts"][table_name] = 0
            except Exception as e:
                logger.error(f"获取备份信息失败: {e}")
        
        return info

# 全局备份管理器实例
backup_manager = BackupManager()
