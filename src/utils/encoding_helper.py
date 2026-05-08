# -*- coding: utf-8 -*-
"""
编码辅助工具
提供UTF-8编码相关的辅助函数
"""

import sys
import io
import os


def setup_utf8_output():
    """设置标准输出为UTF-8编码（Windows系统）"""
    if sys.platform == 'win32':
        try:
            # 设置标准输出编码
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
            # 设置控制台代码页为UTF-8
            os.system('chcp 65001 >nul 2>&1')
        except Exception:
            pass


def safe_print(*args, **kwargs):
    """安全的UTF-8打印函数"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果输出失败，尝试使用ASCII安全版本
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                try:
                    safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                except:
                    safe_args.append(repr(arg))
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


def read_file_utf8(file_path: str) -> str:
    """读取UTF-8编码的文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file_utf8(file_path: str, content: str):
    """写入UTF-8编码的文件"""
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

