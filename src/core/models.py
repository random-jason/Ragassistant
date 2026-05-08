from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

Base = declarative_base()

class WorkOrder(Base):
    """工单模型"""
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    resolution = Column(Text)
    satisfaction_score = Column(Float)

    # 飞书集成字段
    feishu_record_id = Column(String(100), unique=True, nullable=True)  # 飞书记录ID
    assignee = Column(String(100), nullable=True)  # 负责人
    solution = Column(Text, nullable=True)  # 解决方案
    ai_suggestion = Column(Text, nullable=True)  # AI建议

    # 扩展飞书字段
    source = Column(String(50), nullable=True)  # 来源（Mail, Telegram bot等）
    module = Column(String(100), nullable=True)  # 模块（local O&M, OTA等）
    created_by = Column(String(100), nullable=True)  # 创建人
    wilfulness = Column(String(100), nullable=True)  # 责任人
    date_of_close = Column(DateTime, nullable=True)  # 关闭日期
    parent_record = Column(String(100), nullable=True)  # 父记录
    has_updated_same_day = Column(String(50), nullable=True)  # 是否同日更新
    operating_time = Column(String(100), nullable=True)  # 操作时间

    # 工单分发和权限管理字段
    assigned_module = Column(String(50), nullable=True)  # 分配的模块
    module_owner = Column(String(100), nullable=True)  # 业务接口人/模块负责人
    dispatcher = Column(String(100), nullable=True)  # 分发人（运维人员）
    dispatch_time = Column(DateTime, nullable=True)  # 分发时间
    region = Column(String(50), nullable=True)  # 区域（overseas/domestic）- 用于区分海外/国内

    # 关联对话记录
    conversations = relationship("Conversation", back_populates="work_order")
    # 关联处理过程记录
    process_history = relationship("WorkOrderProcessHistory", back_populates="work_order", order_by="WorkOrderProcessHistory.process_time")

class Conversation(Base):
    """对话记录模型"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"))
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    confidence_score = Column(Float)
    knowledge_used = Column(Text)  # 使用的知识库条目
    response_time = Column(Float)  # 响应时间（秒）

    work_order = relationship("WorkOrder", back_populates="conversations")

class KnowledgeEntry(Base):
    """知识库条目模型"""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    confidence_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # 是否已验证
    verified_by = Column(String(100))  # 验证人
    verified_at = Column(DateTime)  # 验证时间
    vector_embedding = Column(Text)  # 向量嵌入的JSON字符串

class Analytics(Base):
    """分析统计模型"""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    total_orders = Column(Integer, default=0)
    resolved_orders = Column(Integer, default=0)
    avg_resolution_time = Column(Float, default=0.0)
    satisfaction_avg = Column(Float, default=0.0)
    knowledge_hit_rate = Column(Float, default=0.0)
    category_distribution = Column(Text)  # JSON格式的类别分布
    created_at = Column(DateTime, default=datetime.now)

class Alert(Base):
    """预警模型"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)
    level = Column(String(20), nullable=False)  # info, warning, error, critical
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    message = Column(Text, nullable=False)
    data = Column(Text)  # JSON格式的预警数据
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime)

class WorkOrderSuggestion(Base):
    """工单AI建议与人工描述表"""
    __tablename__ = "work_order_suggestions"

    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    ai_suggestion = Column(Text)
    human_resolution = Column(Text)
    ai_similarity = Column(Float)
    approved = Column(Boolean, default=False)
    use_human_resolution = Column(Boolean, default=False)  # 是否使用人工描述入库
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class WorkOrderProcessHistory(Base):
    """工单处理过程记录表"""
    __tablename__ = "work_order_process_history"

    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)

    # 处理人员信息
    processor_name = Column(String(100), nullable=False)  # 处理人员姓名
    processor_role = Column(String(50), nullable=True)  # 处理人员角色（运维、业务方等）
    processor_region = Column(String(50), nullable=True)  # 处理人员区域（overseas/domestic）

    # 处理内容
    process_content = Column(Text, nullable=False)  # 处理内容/操作描述
    action_type = Column(String(50), nullable=False)  # 操作类型（dispatch、process、close、reassign等）

    # 处理结果
    previous_status = Column(String(50), nullable=True)  # 处理前的状态
    new_status = Column(String(50), nullable=True)  # 处理后的状态
    assigned_module = Column(String(50), nullable=True)  # 分配的模块（如果是分发操作）

    # 时间戳
    process_time = Column(DateTime, default=datetime.now, nullable=False)  # 处理时间
    created_at = Column(DateTime, default=datetime.now)

    # 关联工单
    work_order = relationship("WorkOrder", back_populates="process_history")


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    name = Column(String(100), nullable=True)
    role = Column(String(20), default='user')  # admin, user, operator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self):
        """转换为字典格式（用于API响应）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
