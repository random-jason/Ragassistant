# -*- coding: utf-8 -*-
"""
认证蓝图
处理用户登录、注册、注销等功能
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from src.core.auth_manager import auth_manager
from src.web.error_handlers import handle_api_errors, create_error_response, create_success_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
@handle_api_errors
def login():
    """用户登录"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    username = data['username']
    password = data['password']
    remember = data.get('remember', False)

    # 认证用户
    user_data = auth_manager.authenticate_user(username, password)

    if user_data:
        # 生成token
        token = auth_manager.generate_token(user_data)

        # 存储到session
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']
        session['user_info'] = user_data
        session['token'] = token

        if remember:
            session.permanent = True

        # 构建响应
        response_data = {
            "success": True,
            "message": "登录成功",
            "user": {
                "id": user_data['id'],
                "username": user_data['username'],
                "name": user_data['name'],
                "email": user_data['email'],
                "role": user_data['role']
            },
            "token": token
        }

        return jsonify(response_data)
    else:
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401


@auth_bp.route('/logout', methods=['POST'])
@handle_api_errors
def logout():
    """用户注销"""
    # 清除session
    session.clear()

    return jsonify(create_success_response(message="注销成功"))


@auth_bp.route('/status')
@handle_api_errors
def get_auth_status():
    """获取认证状态"""
    if 'user_id' in session and 'user_info' in session:
        return jsonify({
            "authenticated": True,
            "user": session['user_info'],
            "token": session.get('token')
        })
    else:
        return jsonify({
            "authenticated": False,
            "user": None,
            "token": None
        })


@auth_bp.route('/register', methods=['POST'])
@handle_api_errors
def register():
    """用户注册（仅管理员可用）"""
    # 检查当前用户是否为管理员
    if not session.get('user_info') or session['user_info'].get('role') != 'admin':
        return create_error_response("权限不足", 403)

    data = request.get_json()

    required_fields = ['username', 'password', 'name']
    if not all(data.get(field) for field in required_fields):
        return create_error_response("缺少必要字段", 400)

    user = auth_manager.create_user(
        username=data['username'],
        password=data['password'],
        name=data['name'],
        email=data.get('email'),
        role=data.get('role', 'user')
    )

    if not user:
        return create_error_response("用户创建失败，用户名可能已存在", 400)

    return jsonify(create_success_response(
        data={
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "role": user.role
        },
        message="用户创建成功"
    ))


@auth_bp.route('/user/profile')
@handle_api_errors
def get_user_profile():
    """获取用户信息"""
    if 'user_info' not in session:
        return create_error_response("未登录", 401)

    return jsonify(create_success_response(data=session['user_info']))


@auth_bp.route('/user/profile', methods=['PUT'])
@handle_api_errors
def update_user_profile():
    """更新用户信息"""
    if 'user_info' not in session:
        return create_error_response("未登录", 401)

    data = request.get_json()
    user_id = session['user_info']['id']

    # 这里应该实现用户信息的更新逻辑
    # 暂时只返回成功响应

    return jsonify(create_success_response(message="用户信息更新成功"))
