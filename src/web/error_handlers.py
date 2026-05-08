# -*- coding: utf-8 -*-
"""
错误处理装饰器和工具
提供统一的错误处理模式
"""

import logging
from functools import wraps
from typing import Callable, Any, Dict
from flask import jsonify

logger = logging.getLogger(__name__)


def handle_api_errors(func: Callable) -> Callable:
    """API错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"参数错误 {func.__name__}: {e}")
            return jsonify({"error": f"参数错误: {str(e)}"}), 400
        except PermissionError as e:
            logger.warning(f"权限错误 {func.__name__}: {e}")
            return jsonify({"error": f"权限不足: {str(e)}"}), 403
        except FileNotFoundError as e:
            logger.warning(f"文件未找到 {func.__name__}: {e}")
            return jsonify({"error": f"文件未找到: {str(e)}"}), 404
        except Exception as e:
            logger.error(f"未处理错误 {func.__name__}: {e}")
            return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500
    return wrapper


def handle_database_errors(func: Callable) -> Callable:
    """数据库错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"数据库错误 {func.__name__}: {e}")
            return jsonify({"error": f"数据库操作失败: {str(e)}"}), 500
    return wrapper


def handle_service_errors(func: Callable) -> Callable:
    """服务错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"服务错误 {func.__name__}: {e}")
            return jsonify({"error": "服务暂时不可用"}), 503
    return wrapper


def create_error_response(message: str, status_code: int = 500, details: str = None) -> tuple:
    """创建标准错误响应"""
    response = {"error": message}
    if details:
        response["details"] = details
    logger.error(f"错误响应: {message} - {details}")
    return jsonify(response), status_code


def create_success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """创建标准成功响应"""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response
