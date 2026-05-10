# -*- coding: utf-8 -*-
"""
AI Helpdesk 综合管理平台
"""

import sys
import os
import logging
import threading
import signal
import asyncio
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/dashboard.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def start_websocket_server():
    """启动WebSocket服务器"""
    try:
        from src.web.websocket_server import WebSocketServer
        # 修复：使用 0.0.0.0 而不是 localhost，允许外部连接
        server = WebSocketServer(host="0.0.0.0", port=8765)
        server.run()
    except Exception as e:
        print(f"WebSocket服务器启动失败: {e}")

def check_database_connection():
    """检查数据库连接"""
    try:
        from src.core.database import db_manager
        if db_manager.check_connection():
            print("✓ 数据库连接正常")
            return True
        else:
            print("✗ 数据库连接失败，请检查数据库配置和网络连接。")
            return False
    except Exception as e:
        print(f"✗ 数据库连接检查出错: {e}")
        return False

def signal_handler(sig, frame):
    """优雅关闭信号处理器"""
    print("\n正在停止服务...")
    print("感谢使用 AI Helpdesk！")
    sys.exit(0)

def main():
    """主函数"""
    print("=" * 60)
    print("AI Helpdesk - 综合管理平台")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    # 注册信号处理器用于优雅关闭
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 检查必要目录
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        logger.info("正在启动 AI Helpdesk 综合管理平台...")

        # 检查数据库连接
        if not check_database_connection():
            logger.error("数据库连接失败，退出启动")
            print("请根据日志检查数据库配置和网络连接。")
            sys.exit(1)

        # 跳过系统检查，直接启动（避免重复初始化）
        logger.info("跳过系统检查，直接启动服务...")

        # 导入并启动Flask应用
        from src.web.app import app
        
        print()
        print("访问地址:")
        print("  主页: http://localhost:5000")
        print("  预警管理: http://localhost:5000/alerts")
        print("  实时对话: http://localhost:5000/chat")
        print("  WebSocket: ws://0.0.0.0:8765")
        print()
        print("按 Ctrl+C 停止服务")
        print("=" * 60)
        
        # 在单独线程中启动WebSocket服务器
        websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
        websocket_thread.start()
        
        # 启动Flask应用
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        logger.info("用户手动停止服务")
    except Exception as e:
        print(f"启动失败: {e}")
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
