# -*- coding: utf-8 -*-
"""
通用装饰器
提供统一的错误处理、服务管理等装饰器
"""

from functools import wraps
from flask import jsonify
from src.web.service_manager import service_manager


def handle_errors(default_response=None):
    """统一错误处理装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if default_response:
                    return default_response
                return jsonify({"error": str(e)}), 500
        return decorated_function
    return decorator


def with_service(service_name):
    """服务注入装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 将服务管理器注入到函数参数中
            kwargs['service_manager'] = service_manager
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_json(required_fields=None):
    """JSON请求验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "请求必须是JSON格式"}), 400

                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return jsonify({"error": f"缺少必要字段: {', '.join(missing_fields)}"}), 400

                kwargs['data'] = data
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": "JSON格式错误"}), 400
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """响应缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import make_response
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response, status = response
            else:
                status = 200

            if hasattr(response, 'headers'):
                response.headers['Cache-Control'] = f'public, max-age={timeout}'
            return response
        return decorated_function
    return decorator
