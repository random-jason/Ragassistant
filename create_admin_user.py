# -*- coding: utf-8 -*-
"""
创建或修复默认管理员用户
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import db_manager
from src.core.models import User
# from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text, inspect

print("=" * 60)
print("创建/修复管理员用户")
print("=" * 60)

try:
    with db_manager.get_session() as session:
        # 检查表结构
        inspector = inspect(db_manager.engine)
        if 'users' not in inspector.get_table_names():
            print("错误: users表不存在，请先运行 python init_database.py")
            sys.exit(1)

        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"users表字段: {existing_columns}")

        # 检查是否存在admin用户
        admin_user = session.query(User).filter(User.username == 'admin').first()

        if admin_user:
            print(f"\n找到admin用户 (ID: {admin_user.id})")
            print(f"  邮箱: {admin_user.email}")
            print(f"  角色: {admin_user.role}")
            print(f"  激活状态: {admin_user.is_active}")

            # 验证密码
            password_ok = admin_user.check_password('admin123')
            print(f"  密码验证: {'正确' if password_ok else '错误'}")

            if not password_ok:
                print("\n密码不匹配，正在更新密码...")
                admin_user.set_password('admin123')
                admin_user.is_active = True
                if hasattr(admin_user, 'region'):
                    admin_user.region = None
                session.commit()
                print("密码已更新为: admin123")

            if not admin_user.is_active:
                print("用户未激活，正在激活...")
                admin_user.is_active = True
                session.commit()
                print("用户已激活")

            # 最终验证
            test_password = admin_user.check_password('admin123')
            if test_password and admin_user.is_active:
                print("\n管理员用户已就绪！")
                print("  用户名: admin")
                print("  密码: admin123")
                print("  状态: 已激活")
            else:
                print("\n警告: 用户状态异常")
                print(f"  密码正确: {test_password}")
                print(f"  已激活: {admin_user.is_active}")
        else:
            print("\n未找到admin用户，正在创建...")

            # 创建用户对象来生成密码哈希
            temp_user = User()
            temp_user.set_password('admin123')
            password_hash = temp_user.password_hash

            # 检查表结构，使用SQL直接插入避免字段不匹配
            try:
                # 先尝试使用模型创建
                new_admin = User(
                    username='admin',
                    email='admin@example.com',
                    name='系统管理员',
                    password_hash=password_hash,
                    role='admin',
                    is_active=True
                )
                if 'region' in existing_columns:
                    new_admin.region = None
                session.add(new_admin)
                session.commit()
                print("使用模型创建成功")
            except Exception as model_error:
                print(f"模型创建失败: {model_error}")
                print("尝试使用SQL直接插入...")
                session.rollback()

                # 使用SQL直接插入
                insert_fields = ['username', 'email', 'name', 'password_hash', 'role']
                insert_values = {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'name': '系统管理员',
                    'password_hash': password_hash,
                    'role': 'admin'
                }

                if 'is_active' in existing_columns:
                    insert_fields.append('is_active')
                    insert_values['is_active'] = True

                if 'region' in existing_columns:
                    insert_fields.append('region')
                    insert_values['region'] = None

                fields_str = ', '.join(insert_fields)
                values_str = ', '.join([f":{k}" for k in insert_fields])

                sql = f"""
                    INSERT INTO users ({fields_str})
                    VALUES ({values_str})
                """

                session.execute(text(sql), insert_values)
                session.commit()
                print("使用SQL创建成功")

            # 验证创建结果
            verify_user = session.query(User).filter(User.username == 'admin').first()
            if verify_user:
                test_password = verify_user.check_password('admin123')
                print(f"\n验证结果:")
                print(f"  用户ID: {verify_user.id}")
                print(f"  密码正确: {test_password}")
                print(f"  已激活: {verify_user.is_active}")

                if test_password and verify_user.is_active:
                    print("\n管理员用户创建成功！")
                    print("  用户名: admin")
                    print("  密码: admin123")
                else:
                    print("\n警告: 用户创建成功但状态异常")

        # 创建其他示例用户
        for username, name, email, password, role, region in [
            ('overseas_ops', '海外运维', 'overseas@example.com', 'ops123', 'overseas_ops', 'overseas'),
            ('domestic_ops', '国内运维', 'domestic@example.com', 'ops123', 'domestic_ops', 'domestic')
        ]:
            ops_user = session.query(User).filter(User.username == username).first()
            if not ops_user:
                print(f"\n创建{username}用户...")
                try:
                    new_user = User(
                        username=username,
                        name=name,
                        email=email,
                        role=role,
                        is_active=True
                    )
                    new_user.set_password(password)
                    if 'region' in existing_columns:
                        new_user.region = region
                    session.add(new_user)
                    session.commit()
                    print(f"  {username}用户创建成功")
                except Exception as e:
                    print(f"  {username}用户创建失败: {e}")
                    session.rollback()

        print("\n" + "=" * 60)
        print("操作完成！")
        print("=" * 60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
