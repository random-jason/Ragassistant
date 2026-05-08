from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base
from .cache_manager import cache_manager, cache_query
from ..config.unified_config import get_config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化数据库连接"""
        try:
            config = get_config()
            db_config = {
                "url": config.database.url,
                "echo": config.server.debug,
            }
            
            # 根据数据库类型选择不同的连接参数
            if "mysql" in db_config["url"]:
                # MySQL配置 - 优化连接池和重连机制
                self.engine = create_engine(
                    db_config["url"],
                    echo=db_config["echo"],
                    pool_size=10,  # 连接池大小
                    max_overflow=20,  # 溢出连接数
                    pool_pre_ping=True,  # 连接前检查连接是否有效
                    pool_recycle=280,  # 4分40秒后回收连接，避免防火墙切断长连接
                    pool_timeout=30,  # 连接池超时（秒）
                    connect_args={
                        "charset": "utf8mb4",
                        "autocommit": False,
                        "connect_timeout": 10,  # 连接超时，快速失败
                        "read_timeout": 30,  # 读取超时
                        "write_timeout": 30,  # 写入超时
                        "max_allowed_packet": 64*1024*1024,  # 64MB
                    }
                )
            else:
                # SQLite配置 - 优化性能
                self.engine = create_engine(
                    db_config["url"],
                    echo=db_config["echo"],
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20,  # 连接超时
                        "isolation_level": None  # 自动提交模式
                    }
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            try:
                session.close()
            except Exception as close_error:
                logger.warning(f"关闭数据库会话时出错: {close_error}")

    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False

    def reconnect(self) -> bool:
        """重新连接数据库"""
        try:
            if self.engine:
                self.engine.dispose()
            self._initialize_database()
            logger.info("数据库重新连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库重新连接失败: {e}")
            return False
    
    def get_session_direct(self) -> Session:
        """直接获取数据库会话"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """关闭数据库会话"""
        if session:
            session.close()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    @cache_query(ttl=60)  # 缓存1分钟
    def get_cached_query(self, query_key: str, query_func, *args, **kwargs):
        """执行带缓存的查询"""
        return query_func(*args, **kwargs)
    
    def invalidate_cache_pattern(self, pattern: str):
        """根据模式清除缓存"""
        try:
            cache_manager.delete(pattern)
            logger.info(f"缓存已清除: {pattern}")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        return cache_manager.get_stats()

# 全局数据库管理器实例
db_manager = DatabaseManager()
