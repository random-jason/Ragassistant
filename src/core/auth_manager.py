# -*- coding: utf-8 -*-
"""
认证管理器
处理用户登录、注册、会话管理等功能
"""

import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app

from src.core.database import db_manager
from src.core.models import User


class AuthManager:
    """认证管理器"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
        self.token_expiry = timedelta(hours=24)

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return self.hash_password(password) == password_hash

    def generate_token(self, user_data: dict) -> str:
        """生成JWT token"""
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """用户认证"""
        print(f"[DEBUG] 开始认证用户: {username}")
        with db_manager.get_session() as session:
            user = session.query(User).filter_by(username=username).first()
            print(f"[DEBUG] 找到用户: {user is not None}")

            if user and user.is_active and self.verify_password(password, user.password_hash):
                print(f"[DEBUG] 用户认证成功: {user.username}")

                # 立即访问所有需要的属性，确保在会话内
                user_id = user.id
                username_val = user.username
                password_hash_val = user.password_hash
                email_val = user.email
                name_val = user.name
                role_val = user.role
                is_active_val = user.is_active
                created_at_val = user.created_at
                last_login_val = datetime.now()

                print(f"[DEBUG] 访问用户属性成功: name={name_val}, role={role_val}")

                # 更新最后登录时间
                user.last_login = last_login_val
                session.commit()
                print("[DEBUG] 数据库更新成功")

                # 返回用户数据字典，避免SQLAlchemy会话绑定问题
                user_dict = {
                    'id': user_id,
                    'username': username_val,
                    'password_hash': password_hash_val,
                    'email': email_val,
                    'name': name_val,
                    'role': role_val,
                    'is_active': is_active_val,
                    'created_at': created_at_val,
                    'last_login': last_login_val
                }
                print(f"[DEBUG] 返回用户字典: {user_dict['username']}")
                return user_dict
            else:
                print("[DEBUG] 用户认证失败")
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        with db_manager.get_session() as session:
            return session.query(User).filter_by(id=user_id).first()

    def get_user_by_token(self, token: str) -> Optional[User]:
        """根据token获取用户"""
        payload = self.verify_token(token)
        if payload:
            return self.get_user_by_id(payload['user_id'])
        return None

    def create_user(self, username: str, password: str, name: str, email: str = None, role: str = 'user') -> Optional[User]:
        """创建新用户"""
        try:
            with db_manager.get_session() as session:
                # 检查用户名是否已存在
                existing_user = session.query(User).filter_by(username=username).first()
                if existing_user:
                    return None

                user = User(
                    username=username,
                    name=name,
                    email=email,
                    role=role,
                    is_active=True
                )
                user.set_password(password)

                session.add(user)
                session.commit()
                return user
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None

    def create_default_admin(self):
        """创建默认管理员用户"""
        admin = self.create_user('admin', 'admin123', '系统管理员', 'admin@example.com', 'admin')
        if admin:
            print("默认管理员用户已创建: admin/admin123")
        return admin


# 全局认证管理器实例
auth_manager = AuthManager()
