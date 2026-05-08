# -*- coding: utf-8 -*-
"""
WebSocket实时通信服务器
提供实时对话功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol

from ..dialogue.realtime_chat import RealtimeChatManager

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket服务器"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.chat_manager = RealtimeChatManager()
        self.connected_clients: Set[WebSocketServerProtocol] = set()

    async def register_client(self, websocket: WebSocketServerProtocol):
        """注册客户端"""
        self.connected_clients.add(websocket)
        logger.info(f"客户端连接: {websocket.remote_address}")

    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """注销客户端"""
        self.connected_clients.discard(websocket)
        logger.info(f"客户端断开: {websocket.remote_address}")

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            message_id = data.get("messageId")  # 获取消息ID

            if message_type == "create_session":
                await self._handle_create_session(websocket, data, message_id)
            elif message_type == "send_message":
                await self._handle_send_message(websocket, data, message_id)
            elif message_type == "get_history":
                await self._handle_get_history(websocket, data, message_id)
            elif message_type == "create_work_order":
                await self._handle_create_work_order(websocket, data, message_id)
            elif message_type == "get_work_order_status":
                await self._handle_get_work_order_status(websocket, data, message_id)
            elif message_type == "end_session":
                await self._handle_end_session(websocket, data, message_id)
            else:
                await self._send_error(websocket, "未知消息类型", message_id)

        except json.JSONDecodeError:
            await self._send_error(websocket, "JSON格式错误")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await self._send_error(websocket, f"处理消息失败: {str(e)}")

    async def _handle_create_session(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理创建会话请求"""
        user_id = data.get("user_id", "anonymous")
        work_order_id = data.get("work_order_id")

        session_id = self.chat_manager.create_session(user_id, work_order_id)

        response = {
            "type": "session_created",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _handle_send_message(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理发送消息请求"""
        session_id = data.get("session_id")
        message = data.get("message")

        if not session_id or not message:
            await self._send_error(websocket, "缺少必要参数", message_id)
            return

        # 处理消息
        result = self.chat_manager.process_message(session_id, message)

        response = {
            "type": "message_response",
            "session_id": session_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _handle_get_history(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理获取历史记录请求"""
        session_id = data.get("session_id")

        if not session_id:
            await self._send_error(websocket, "缺少会话ID", message_id)
            return

        history = self.chat_manager.get_session_history(session_id)

        response = {
            "type": "history_response",
            "session_id": session_id,
            "history": history,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _handle_create_work_order(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理创建工单请求"""
        session_id = data.get("session_id")
        title = data.get("title")
        description = data.get("description")
        category = data.get("category", "技术问题")
        priority = data.get("priority", "medium")

        if not session_id or not title or not description:
            await self._send_error(websocket, "缺少必要参数", message_id)
            return

        result = self.chat_manager.create_work_order(session_id, title, description, category, priority)

        response = {
            "type": "work_order_created",
            "session_id": session_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _handle_get_work_order_status(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理获取工单状态请求"""
        work_order_id = data.get("work_order_id")

        if not work_order_id:
            await self._send_error(websocket, "缺少工单ID", message_id)
            return

        result = self.chat_manager.get_work_order_status(work_order_id)

        response = {
            "type": "work_order_status",
            "work_order_id": work_order_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _handle_end_session(self, websocket: WebSocketServerProtocol, data: Dict, message_id: str = None):
        """处理结束会话请求"""
        session_id = data.get("session_id")

        if not session_id:
            await self._send_error(websocket, "缺少会话ID", message_id)
            return

        success = self.chat_manager.end_session(session_id)

        response = {
            "type": "session_ended",
            "session_id": session_id,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str, message_id: str = None):
        """发送错误消息"""
        response = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }

        if message_id:
            response["messageId"] = message_id

        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        # 检查连接头
        # 兼容不同版本的websockets库
        if hasattr(websocket, 'request') and hasattr(websocket.request, 'headers'):
            headers = websocket.request.headers
        else:
            headers = getattr(websocket, 'request_headers', {})

        connection = headers.get("Connection", "").lower()

        # 处理不同的连接头格式
        if "upgrade" not in connection and "keep-alive" in connection:
            logger.warning(f"收到非标准连接头: {connection}")
            # 对于keep-alive连接头，我们仍然接受连接
        elif "upgrade" not in connection:
            logger.warning(f"连接头不包含upgrade: {connection}")
            await websocket.close(code=1002, reason="Invalid connection header")
            return

        await self.register_client(websocket)

        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket连接错误: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """启动WebSocket服务器"""
        logger.info(f"启动WebSocket服务器: ws://{self.host}:{self.port}")

        # 添加CORS支持
        async def handle_client_with_cors(websocket):
            # 兼容不同版本的websockets库
            # 新版本使用websocket.request.path，旧版本使用websocket.path
            if hasattr(websocket, 'request') and hasattr(websocket.request, 'path'):
                path = websocket.request.path
                headers = websocket.request.headers
            else:
                path = getattr(websocket, 'path', '/')
                headers = getattr(websocket, 'request_headers', {})

            # 设置CORS头
            # 注意: 这里仅做逻辑处理，实际CORS头需要在握手阶段(process_request)处理
            # 但process_request返回响应会中断WebSocket连接，所以通常在Nginx层处理CORS
            if hasattr(headers, 'get') and headers.get("Origin"):
                pass
                
            await self.handle_client(websocket, path)

        async with websockets.serve(
            handle_client_with_cors,
            self.host,
            self.port,
            # 添加额外的服务器选项
            process_request=self._process_request
        ):
            await asyncio.Future()  # 保持服务器运行

    def _process_request(self, connection, request):
        """
        处理HTTP请求，支持CORS
        兼容旧版签名: (path, request_headers)
        兼容新版签名: (connection, request)
        """
        # 检查是否是WebSocket升级请求
        # request 可能是 Headers 对象(旧版) 或 Request 对象(新版)
        try:
            if hasattr(request, 'headers') and hasattr(request.headers, 'get'):
                # 新版 websockets (request 是 Request 对象)
                upgrade_header = request.headers.get("Upgrade", "").lower()
            elif hasattr(request, 'get'):
                # 旧版 websockets (request 是 Headers 对象)
                upgrade_header = request.get("Upgrade", "").lower()
            else:
                upgrade_header = ""
        except Exception as e:
            logger.error(f"解析请求头失败: {e}")
            upgrade_header = ""

        if upgrade_header == "websocket":
            return None  # 允许WebSocket连接

        # 对于非WebSocket请求，返回简单的HTML页面
        return (
            200,
            [("Content-Type", "text/html; charset=utf-8")],
            b"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>WebSocket Server</title>
            </head>
            <body>
                <h1>WebSocket Server is running</h1>
                <p>This is a WebSocket server. Please use a WebSocket client to connect.</p>
                <p>WebSocket URL: ws://localhost:8765</p>
            </body>
            </html>
            """
        )

    def run(self):
        """运行服务器"""
        asyncio.run(self.start_server())

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 启动服务器
    server = WebSocketServer()
    server.run()
