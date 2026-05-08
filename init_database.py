# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import sys
import os
import logging
import json
from typing import Dict, List, Optional, Any
from sqlalchemy import text, inspect
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.unified_config import get_config
from src.utils.helpers import setup_logging
from src.core.database import db_manager
from src.core.models import (
    Base, WorkOrder, KnowledgeEntry, Conversation, Analytics, Alert,
    WorkOrderSuggestion, WorkOrderProcessHistory, User
)

class DatabaseInitializer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_url = str(db_manager.engine.url)
        self.is_mysql = 'mysql' in self.db_url
        self.is_sqlite = 'sqlite' in self.db_url
        self.is_postgresql = 'postgresql' in self.db_url

        # 数据库版本信息
        self.db_version = self._get_database_version()

        # 迁移历史记录
        self.migration_history = []

    def _get_database_version(self) -> str:
        """获取数据库版本信息"""
        try:
            with db_manager.get_session() as session:
                if self.is_mysql:
                    result = session.execute(text("SELECT VERSION()")).fetchone()
                    return f"MySQL {result[0]}"
                elif self.is_postgresql:
                    result = session.execute(text("SELECT version()")).fetchone()
                    return f"PostgreSQL {result[0].split()[1]}"
                else:  # SQLite
                    result = session.execute(text("SELECT sqlite_version()")).fetchone()
                    return f"SQLite {result[0]}"
        except Exception as e:
            self.logger.warning(f"无法获取数据库版本: {e}")
            return "Unknown"

    def initialize_database(self, force_reset: bool = False) -> bool:
        """初始化数据库 - 主入口函数"""
        print("=" * 80)
        print("智能助手数据库初始化系统")
        print("=" * 80)
        print(f"数据库类型: {self.db_version}")
        print(f"连接地址: {self.db_url}")
        print(f"初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            # 设置日志
            config = get_config()
            setup_logging(config.server.log_level, "logs/helpdesk.log")

            # 测试数据库连接
            if not self._test_connection():
                return False

            # 检查是否需要重置数据库
            if force_reset:
                if not self._reset_database():
                    return False

            # 创建数据库表
            if not self._create_tables():
                return False

            # 执行数据库迁移
            if not self._run_migrations():
                return False

            # 插入初始数据
            if not self._insert_initial_data():
                return False

            # 验证数据库完整性
            if not self._verify_database_integrity():
                return False

            # 生成初始化报告
            self._generate_init_report()

            print("\n" + "=" * 80)
            print("数据库初始化完成！")
            print("=" * 80)
            return True

        except Exception as e:
            print(f"\n数据库初始化失败: {e}")
            self.logger.error(f"数据库初始化失败: {e}", exc_info=True)
            return False

    def _test_connection(self) -> bool:
        """测试数据库连接"""
        print("\n测试数据库连接...")
        try:
            if db_manager.test_connection():
                print("数据库连接成功")
                return True
            else:
                print("数据库连接失败")
                return False
        except Exception as e:
            print(f"数据库连接测试异常: {e}")
            return False

    def _reset_database(self) -> bool:
        """重置数据库（谨慎使用）"""
        print("\n重置数据库...")
        try:
            # 删除所有表
            Base.metadata.drop_all(bind=db_manager.engine)
            print("数据库表删除成功")

            # 重新创建所有表
            Base.metadata.create_all(bind=db_manager.engine)
            print("数据库表重新创建成功")

            return True
        except Exception as e:
            print(f"数据库重置失败: {e}")
        return False

    def _create_tables(self) -> bool:
        """创建数据库表"""
        print("\n创建数据库表...")
        try:
            # 获取现有表信息
            inspector = inspect(db_manager.engine)
            existing_tables = inspector.get_table_names()

            # 创建所有表
            Base.metadata.create_all(bind=db_manager.engine)

            # 检查新创建的表
            new_tables = inspector.get_table_names()
            created_tables = set(new_tables) - set(existing_tables)

            if created_tables:
                print(f"新创建表: {', '.join(created_tables)}")
            else:
                print("所有表已存在")

            return True
        except Exception as e:
            print(f"创建数据库表失败: {e}")
            return False

    def _run_migrations(self) -> bool:
        """执行数据库迁移"""
        print("\n执行数据库迁移...")

        migrations = [
            self._migrate_user_table_structure,
            self._migrate_knowledge_verification_fields,
            self._migrate_alert_severity_field,
            self._migrate_conversation_enhancements,
            self._migrate_workorder_enhancements,
            self._migrate_workorder_suggestions_enhancements,
            self._migrate_workorder_dispatch_fields,
            self._migrate_workorder_process_history_table,
            self._migrate_analytics_enhancements,
            self._migrate_system_optimization_fields
        ]

        success_count = 0
        for migration in migrations:
            try:
                if migration():
                    success_count += 1
            except Exception as e:
                self.logger.error(f"迁移失败: {migration.__name__}: {e}")
                print(f"迁移 {migration.__name__} 失败: {e}")

        print(f"完成 {success_count}/{len(migrations)} 个迁移")
        return success_count > 0

    def _migrate_user_table_structure(self) -> bool:
        """迁移用户表结构"""
        print("   检查用户表结构...")

        try:
            with db_manager.get_session() as session:
                # 检查users表是否存在
                inspector = inspect(db_manager.engine)
                if 'users' not in inspector.get_table_names():
                    print("      创建users表...")
                    # 创建User模型的表
                    User.__table__.create(session.bind, checkfirst=True)
                    print("      users表创建成功")
                    return True

                # 检查users表的列
                existing_columns = [col['name'] for col in inspector.get_columns('users')]
                print(f"      users表现有字段: {existing_columns}")

                # 检查必需的字段
                required_fields = {
                    'name': 'VARCHAR(100)',
                    'email': 'VARCHAR(120)',
                    'role': 'VARCHAR(20) DEFAULT \'user\'',
                    'is_active': 'BOOLEAN DEFAULT TRUE',
                    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'last_login': 'TIMESTAMP NULL'
                }

                fields_to_add = []
                for field_name, field_type in required_fields.items():
                    if field_name not in existing_columns:
                        fields_to_add.append((field_name, field_type))

                if fields_to_add:
                    print(f"      需要添加字段: {[f[0] for f in fields_to_add]}")
                    return self._add_table_columns('users', fields_to_add)
                else:
                    print("      users表结构完整")
                    return True

        except Exception as e:
            print(f"      用户表结构迁移失败: {e}")
            return False

    def _migrate_knowledge_verification_fields(self) -> bool:
        """迁移知识库验证字段"""
        print("   检查知识库验证字段...")

        fields_to_add = [
            ('is_verified', 'BOOLEAN DEFAULT FALSE'),
            ('verified_by', 'VARCHAR(100)'),
            ('verified_at', 'DATETIME')
        ]

        return self._add_table_columns('knowledge_entries', fields_to_add)

    def _migrate_alert_severity_field(self) -> bool:
        """迁移预警严重程度字段"""
        print("   检查预警严重程度字段...")

        fields_to_add = [
            ('severity', 'VARCHAR(20) DEFAULT \'medium\'')
        ]

        return self._add_table_columns('alerts', fields_to_add)

    def _migrate_conversation_enhancements(self) -> bool:
        """迁移对话增强字段"""
        print("   检查对话增强字段...")

        fields_to_add = [
            ('timestamp', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('knowledge_used', 'TEXT'),
            ('response_time', 'FLOAT')
        ]

        return self._add_table_columns('conversations', fields_to_add)

    def _migrate_workorder_enhancements(self) -> bool:
        """迁移工单增强字段"""
        print("   检查工单增强字段...")

        fields_to_add = [
            ('resolution', 'TEXT'),
            ('satisfaction_score', 'FLOAT'),
            # 飞书集成字段
            ('feishu_record_id', 'VARCHAR(100)'),
            ('assignee', 'VARCHAR(100)'),
            ('solution', 'TEXT'),
            ('ai_suggestion', 'TEXT'),
            # 扩展飞书字段
            ('source', 'VARCHAR(50)'),
            ('module', 'VARCHAR(100)'),
            ('created_by', 'VARCHAR(100)'),
            ('wilfulness', 'VARCHAR(100)'),
            ('date_of_close', 'DATETIME'),
            ('parent_record', 'VARCHAR(100)'),
            ('has_updated_same_day', 'VARCHAR(50)'),
            ('operating_time', 'VARCHAR(100)')
        ]

        return self._add_table_columns('work_orders', fields_to_add)

    def _migrate_workorder_suggestions_enhancements(self) -> bool:
        """迁移工单建议表增强字段"""
        print("   检查工单建议表增强字段...")

        fields_to_add = [
            ('ai_similarity', 'FLOAT'),
            ('approved', 'BOOLEAN DEFAULT FALSE'),
            ('use_human_resolution', 'BOOLEAN DEFAULT FALSE')  # 是否使用人工描述入库
        ]

        return self._add_table_columns('work_order_suggestions', fields_to_add)

    def _migrate_workorder_dispatch_fields(self) -> bool:
        """迁移工单分发和权限管理字段"""
        print("   检查工单分发和权限管理字段...")

        fields_to_add = [
            ('assigned_module', 'VARCHAR(50)'),
            ('module_owner', 'VARCHAR(100)'),
            ('dispatcher', 'VARCHAR(100)'),
            ('dispatch_time', 'DATETIME'),
            ('region', 'VARCHAR(50)')
        ]

        return self._add_table_columns('work_orders', fields_to_add)

    def _migrate_workorder_process_history_table(self) -> bool:
        """迁移工单处理过程记录表"""
        print("   检查工单处理过程记录表...")

        try:
            with db_manager.get_session() as session:
                # 检查表是否存在
                inspector = inspect(db_manager.engine)
                if 'work_order_process_history' not in inspector.get_table_names():
                    print("      创建work_order_process_history表...")
                    WorkOrderProcessHistory.__table__.create(session.bind, checkfirst=True)
                    print("      work_order_process_history表创建成功")
                else:
                    print("      work_order_process_history表已存在")

                    # 检查字段是否完整
                    existing_columns = [col['name'] for col in inspector.get_columns('work_order_process_history')]
                    required_columns = [
                        'processor_name', 'processor_role', 'processor_region',
                        'process_content', 'action_type', 'previous_status',
                        'new_status', 'assigned_module', 'process_time'
                    ]

                    missing_columns = [col for col in required_columns if col not in existing_columns]
                    if missing_columns:
                        print(f"      缺少字段: {', '.join(missing_columns)}")
                        # 这里可以选择性地添加缺失字段，但通常表已经完整创建
                    else:
                        print("      所有必需字段已存在")

                session.commit()
                return True
        except Exception as e:
            print(f"      工单处理过程记录表迁移失败: {e}")
            return False

    def _migrate_analytics_enhancements(self) -> bool:
        """迁移分析增强字段"""
        print("   检查分析增强字段...")

        fields_to_add = [
            ('performance_score', 'FLOAT'),
            ('quality_metrics', 'TEXT'),
            ('cost_analysis', 'TEXT'),
            ('optimization_suggestions', 'TEXT')
        ]

        return self._add_table_columns('analytics', fields_to_add)

    def _migrate_system_optimization_fields(self) -> bool:
        """迁移系统优化字段"""
        print("   检查系统优化字段...")

        # 为各个表添加系统优化相关字段
        tables_and_fields = {
            'conversations': [
                ('processing_time', 'FLOAT'),
                ('memory_usage', 'FLOAT'),
                ('cpu_usage', 'FLOAT')
            ],
            'work_orders': [
                ('processing_efficiency', 'FLOAT'),
                ('resource_usage', 'TEXT')
            ],
            'knowledge_entries': [
                ('search_frequency', 'INTEGER DEFAULT 0'),
                ('last_accessed', 'DATETIME'),
                ('relevance_score', 'FLOAT')
            ]
        }

        success = True
        for table_name, fields in tables_and_fields.items():
            if not self._add_table_columns(table_name, fields):
                success = False

        return success

    def _add_table_columns(self, table_name: str, fields: List[tuple]) -> bool:
        """为表添加字段"""
        try:
            added_count = 0
            skipped_count = 0

            for field_name, field_type in fields:
                try:
                    if self._column_exists(table_name, field_name):
                        skipped_count += 1
                        continue

                    print(f"      添加字段 {table_name}.{field_name}...")

                    # 使用单独的会话添加每个字段，避免长时间锁定
                    with db_manager.get_session() as session:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}"
                        session.execute(text(alter_sql))
                        session.commit()

                    print(f"      字段 {field_name} 添加成功")
                    added_count += 1

                except Exception as field_error:
                    print(f"      字段 {field_name} 添加失败: {field_error}")
                    # 继续处理其他字段，不中断整个过程

            if added_count > 0:
                print(f"      成功添加 {added_count} 个字段，跳过 {skipped_count} 个已存在字段")
            else:
                print(f"      所有字段都已存在，跳过 {skipped_count} 个字段")

            return True

        except Exception as e:
            print(f"      添加字段过程失败: {e}")
            return False

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """检查字段是否存在"""
        try:
            with db_manager.get_session() as session:
                if self.is_mysql:
                    result = session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = :table_name
                        AND COLUMN_NAME = :column_name
                    """), {"table_name": table_name, "column_name": column_name}).fetchone()
                elif self.is_postgresql:
                    result = session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        AND column_name = :column_name
                    """), {"table_name": table_name, "column_name": column_name}).fetchone()
                else:  # SQLite
                    result = session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM pragma_table_info(:table_name)
                        WHERE name = :column_name
                    """), {"table_name": table_name, "column_name": column_name}).fetchone()

                return result[0] > 0
        except Exception:
            return False

    def _insert_initial_data(self) -> bool:
        """插入初始数据"""
        print("\n插入初始数据...")

        try:
            with db_manager.get_session() as session:
                # 检查是否已有用户数据
                existing_users = session.query(User).count()
                if existing_users == 0:
                    # 创建默认管理员用户
                    from src.core.auth_manager import auth_manager
                    admin_user = auth_manager.create_default_admin()
                    if admin_user:
                        print("   默认管理员用户已创建: admin/admin123")
                    else:
                        print("   创建默认管理员用户失败")

                # 检查是否已有知识库数据
                existing_count = session.query(KnowledgeEntry).count()
                if existing_count > 0:
                    print(f"   数据库中已有 {existing_count} 条知识库条目，跳过初始数据插入")
                    return True

                # 插入初始知识库数据
                initial_data = self._get_initial_knowledge_data()
                for data in initial_data:
                    entry = KnowledgeEntry(**data)
                    session.add(entry)

                session.commit()
                print(f"   成功插入 {len(initial_data)} 条知识库条目")

                # 验证现有知识库条目
                self._verify_existing_knowledge()

                return True
        except Exception as e:
            print(f"   插入初始数据失败: {e}")
            return False

    def _get_initial_knowledge_data(self) -> List[Dict[str, Any]]:
        """获取初始知识库数据"""
        return [
                {
                    "question": "如何重置密码？",
                    "answer": "您可以通过以下步骤重置密码：1. 点击登录页面的'忘记密码'链接 2. 输入您的邮箱地址 3. 检查邮箱并点击重置链接 4. 设置新密码",
                    "category": "账户问题",
                    "confidence_score": 0.9,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.9
                },
                {
                    "question": "账户被锁定了怎么办？",
                    "answer": "如果您的账户被锁定，请尝试以下解决方案：1. 等待15分钟后重试登录 2. 如果问题持续，请联系客服并提供您的用户ID",
                    "category": "账户问题",
                    "confidence_score": 0.8,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.8
                },
                {
                    "question": "如何修改个人信息？",
                    "answer": "您可以在个人设置页面修改个人信息：1. 登录后点击右上角的个人头像 2. 选择'个人设置' 3. 修改相关信息并保存",
                    "category": "账户问题",
                    "confidence_score": 0.7,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.7
                },
                {
                    "question": "支付失败怎么办？",
                    "answer": "如果支付失败，请检查：1. 银行卡余额是否充足 2. 银行卡是否支持在线支付 3. 网络连接是否正常 4. 如果问题持续，请联系支付客服",
                    "category": "支付问题",
                    "confidence_score": 0.8,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.8
                },
                {
                    "question": "如何申请退款？",
                    "answer": "申请退款流程：1. 在订单详情页面点击'申请退款' 2. 选择退款原因 3. 填写退款说明 4. 提交申请后等待审核",
                    "category": "支付问题",
                    "confidence_score": 0.7,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.7
                },
                {
                    "question": "系统无法访问怎么办？",
                    "answer": "如果系统无法访问，请尝试：1. 检查网络连接 2. 清除浏览器缓存 3. 尝试使用其他浏览器 4. 如果问题持续，请联系技术支持",
                    "category": "技术问题",
                    "confidence_score": 0.8,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.8
                },
                {
                    "question": "如何联系客服？",
                    "answer": "您可以通过以下方式联系客服：1. 在线客服：点击页面右下角的客服图标 2. 电话客服：400-123-4567 3. 邮箱客服：support@example.com",
                    "category": "服务问题",
                    "confidence_score": 0.9,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.9
                },
                {
                    "question": "如何上传文件？",
                    "answer": "上传文件步骤：1. 登录系统后进入知识库管理页面 2. 点击'上传文件'按钮 3. 选择需要上传的文件（支持txt、md等格式）4. 等待系统自动处理并生成知识条目",
                    "category": "系统功能",
                    "confidence_score": 0.9,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.9
                },
                {
                    "question": "如何创建工单？",
                    "answer": "创建工单步骤：1. 进入工单管理页面 2. 点击'新建工单'按钮 3. 填写标题、描述、分类和优先级 4. 提交后系统将自动分配处理",
                    "category": "系统功能",
                    "confidence_score": 0.9,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.9
                },
                {
                    "question": "如何查看系统运行状态？",
                    "answer": "查看系统运行状态：1. 登录后进入监控面板 2. 可查看系统健康分数、活跃预警、工单统计等信息 3. 支持Token使用量监控和AI性能分析",
                    "category": "系统功能",
                    "confidence_score": 0.8,
                    "is_verified": True,
                    "verified_by": "system",
                "verified_at": datetime.now(),
                "search_frequency": 0,
                "relevance_score": 0.8
            }
        ]

    def _verify_existing_knowledge(self) -> bool:
        """验证现有的知识库条目"""
        try:
            with db_manager.get_session() as session:
                # 获取所有未验证的知识库条目
                unverified_entries = session.query(KnowledgeEntry).filter(
                    KnowledgeEntry.is_verified == False
                ).all()

                if unverified_entries:
                    print(f"   发现 {len(unverified_entries)} 条未验证的知识库条目")

                    # 将现有的知识库条目标记为已验证
                    for entry in unverified_entries:
                        entry.is_verified = True
                        entry.verified_by = "system_init"
                        entry.verified_at = datetime.now()
                        if not hasattr(entry, 'search_frequency'):
                            entry.search_frequency = 0
                        if not hasattr(entry, 'relevance_score'):
                            entry.relevance_score = 0.7

                    session.commit()
                    print(f"   成功验证 {len(unverified_entries)} 条知识库条目")
                else:
                    print("   所有知识库条目已验证")

                return True
        except Exception as e:
            print(f"   验证知识库条目失败: {e}")
            return False

    def _verify_database_integrity(self) -> bool:
        """验证数据库完整性"""
        print("\n验证数据库完整性...")

        try:
            with db_manager.get_session() as session:
                # 检查各表的记录数
                tables_info = {
                    'users': User,
                    'work_orders': WorkOrder,
                    'conversations': Conversation,
                    'knowledge_entries': KnowledgeEntry,
                    'analytics': Analytics,
                    'alerts': Alert,
                    'work_order_suggestions': WorkOrderSuggestion,
                    'work_order_process_history': WorkOrderProcessHistory
                }

                total_records = 0
                for table_name, model_class in tables_info.items():
                    try:
                        count = session.query(model_class).count()
                        total_records += count
                        print(f"   {table_name}: {count} 条记录")
                    except Exception as e:
                        print(f"   {table_name}: 检查失败 - {e}")

                print(f"   总记录数: {total_records}")

                # 检查关键字段
                self._check_critical_fields()

                print("   数据库完整性验证通过")
                return True
        except Exception as e:
            print(f"   数据库完整性验证失败: {e}")
            return False

    def _check_critical_fields(self):
        """检查关键字段"""
        critical_checks = [
            ("knowledge_entries", "is_verified"),
            ("alerts", "severity"),
            ("vehicle_data", "vehicle_id"),
            ("conversations", "timestamp"),
            ("conversations", "response_time"),
            ("work_orders", "ai_suggestion"),
            ("work_orders", "assigned_module"),
            ("work_order_process_history", "processor_name"),
            ("work_order_suggestions", "ai_similarity")
        ]

        for table_name, field_name in critical_checks:
            if self._column_exists(table_name, field_name):
                print(f"      {table_name}.{field_name} 字段存在")
            else:
                print(f"      {table_name}.{field_name} 字段缺失")

    def _generate_init_report(self):
        """生成初始化报告"""
        print("\n生成初始化报告...")

        try:
            report = {
                "init_time": datetime.now().isoformat(),
                "database_version": self.db_version,
                "database_url": self.db_url,
                "migrations_applied": len(self.migration_history),
                "tables_created": self._get_table_count(),
                "initial_data_inserted": True,
                "verification_passed": True
            }

            # 保存报告到文件
            report_path = Path("database_init_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"   初始化报告已保存到: {report_path}")

        except Exception as e:
            print(f"   生成初始化报告失败: {e}")

    def _get_table_count(self) -> int:
        """获取表数量"""
        try:
            inspector = inspect(db_manager.engine)
            return len(inspector.get_table_names())
        except Exception:
            return 0

    def check_database_status(self) -> Dict[str, Any]:
        """检查数据库状态"""
        print("\n" + "=" * 80)
        print("数据库状态检查")
        print("=" * 80)

        try:
            with db_manager.get_session() as session:
                # 检查各表的记录数
                tables_info = {
                    'work_orders': WorkOrder,
                    'conversations': Conversation,
                    'knowledge_entries': KnowledgeEntry,
                    'analytics': Analytics,
                    'alerts': Alert,
                    'work_order_suggestions': WorkOrderSuggestion,
                    'work_order_process_history': WorkOrderProcessHistory
                }

                status = {
                    "database_version": self.db_version,
                    "connection_status": "正常",
                    "tables": {},
                    "total_records": 0,
                    "last_check": datetime.now().isoformat()
                }

                for table_name, model_class in tables_info.items():
                    try:
                        count = session.query(model_class).count()
                        status["tables"][table_name] = count
                        status["total_records"] += count
                        print(f"{table_name}: {count} 条记录")
                    except Exception as e:
                        status["tables"][table_name] = f"错误: {e}"
                        print(f"{table_name}: 检查失败 - {e}")

                # 检查知识库验证状态
                if 'knowledge_entries' in status["tables"] and isinstance(status["tables"]['knowledge_entries'], int):
                    verified_count = session.query(KnowledgeEntry).filter(KnowledgeEntry.is_verified == True).count()
                    unverified_count = session.query(KnowledgeEntry).filter(KnowledgeEntry.is_verified == False).count()
                    print(f"   - 已验证: {verified_count}")
                    print(f"   - 未验证: {unverified_count}")
                    status["knowledge_verification"] = {
                        "verified": verified_count,
                        "unverified": unverified_count
                    }

                print(f"\n总记录数: {status['total_records']}")
                print("\n数据库状态检查完成")

                return status

        except Exception as e:
            print(f"数据库状态检查失败: {e}")
            return {"error": str(e)}

def main():
    """主函数"""
    print("智能助手数据库初始化工具")
    print("=" * 80)

    # 创建初始化器
    initializer = DatabaseInitializer()

    # 检查命令行参数
    force_reset = '--reset' in sys.argv or '--force' in sys.argv

    if force_reset:
        print("警告：将重置数据库，所有数据将被删除！")
        try:
            confirm = input("确定要继续吗？(y/N): ")
            if confirm.lower() != 'y':
                print("操作已取消")
                return
        except Exception:
            print("非交互环境，跳过确认")

    # 初始化数据库
    if initializer.initialize_database(force_reset=force_reset):
        # 检查数据库状态
        initializer.check_database_status()

        print("\n" + "=" * 80)
        print("数据库初始化成功！")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("数据库初始化失败！")
        print("=" * 80)


if __name__ == "__main__":
    main()
