/**
 * WebSocket管理模块
 */

import { defaultConfig, storage, debounce } from './utils.js';
import store from './store.js';

// WebSocket配置
const config = {
    ...defaultConfig,
    reconnectInterval: 3000, // 重连间隔
    maxReconnectAttempts: 5, // 最大重连次数
    heartbeatInterval: 30000, // 心跳间隔
    heartbeatTimeout: 5000, // 心跳超时
    messageQueue: [], // 消息队列
    debug: false // 调试模式
};

// WebSocket状态枚举
export const WebSocketState = {
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3
};

// WebSocket管理器类
class WebSocketManager {
    constructor(url = config.wsUrl) {
        this.url = url;
        this.ws = null;
        this.state = WebSocketState.CLOSED;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        this.heartbeatTimeoutTimer = null;
        this.messageHandlers = new Map();
        this.readyStateHandlers = [];
        this.messageId = 0;
        this.pendingRequests = new Map();

        // 绑定方法
        this.onOpen = this.onOpen.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onMessage = this.onMessage.bind(this);
        this.onError = this.onError.bind(this);
    }

    // 连接WebSocket
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.log('WebSocket already connected');
            return;
        }

        // 清除之前的重连定时器
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        this.log('Connecting to WebSocket...');
        this.setState(WebSocketState.CONNECTING);

        try {
            // 构建WebSocket URL，添加认证信息
            const token = storage.get('authToken');
            const wsUrl = token ? `${this.url}?token=${token}` : this.url;

            this.ws = new WebSocket(wsUrl);

            // 绑定事件处理器
            this.ws.onopen = this.onOpen;
            this.ws.onclose = this.onClose;
            this.ws.onmessage = this.onMessage;
            this.ws.onerror = this.onError;

        } catch (error) {
            this.log('WebSocket connection error:', error);
            this.handleError(error);
        }
    }

    // 断开连接
    disconnect() {
        this.log('Disconnecting WebSocket...');
        this.setState(WebSocketState.CLOSING);

        // 停止重连
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // 停止心跳
        this.stopHeartbeat();

        // 关闭连接
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.setState(WebSocketState.CLOSED);
    }

    // 发送消息
    send(type, data = {}, options = {}) {
        return new Promise((resolve, reject) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                const message = {
                    id: this.messageId++,
                    type,
                    data,
                    timestamp: Date.now()
                };

                // 如果需要响应，保存回调
                if (options.expectResponse) {
                    this.pendingRequests.set(message.id, {
                        resolve,
                        reject,
                        timeout: setTimeout(() => {
                            this.pendingRequests.delete(message.id);
                            reject(new Error('Request timeout'));
                        }, options.timeout || 30000)
                    });
                }

                // 发送消息
                this.ws.send(JSON.stringify(message));
                this.log('Sent message:', message);

                // 如果不需要响应，立即解决
                if (!options.expectResponse) {
                    resolve(message.id);
                }
            } else {
                // 连接未就绪，加入队列
                config.messageQueue.push({ type, data, options, resolve, reject });
                reject(new Error('WebSocket not connected'));
            }
        });
    }

    // 注册消息处理器
    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }

    // 取消注册消息处理器
    off(type, handler) {
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    // 注册状态变化处理器
    onReadyStateChange(handler) {
        this.readyStateHandlers.push(handler);
    }

    // 事件处理器
    onOpen() {
        this.log('WebSocket connected');
        this.setState(WebSocketState.OPEN);
        this.reconnectAttempts = 0;

        // 启动心跳
        this.startHeartbeat();

        // 发送队列中的消息
        this.flushMessageQueue();

        // 通知状态变化
        this.notifyReadyStateChange();

        // 更新store状态
        store.commit('SET_WS_CONNECTED', true);
    }

    onClose(event) {
        this.log('WebSocket closed:', event);
        this.setState(WebSocketState.CLOSED);

        // 停止心跳
        this.stopHeartbeat();

        // 拒绝所有待处理的请求
        this.pendingRequests.forEach(({ reject, timeout }) => {
            clearTimeout(timeout);
            reject(new Error('WebSocket closed'));
        });
        this.pendingRequests.clear();

        // 通知状态变化
        this.notifyReadyStateChange();

        // 更新store状态
        store.commit('SET_WS_CONNECTED', false);

        // 自动重连
        if (!event.wasClean && this.reconnectAttempts < config.maxReconnectAttempts) {
            this.reconnect();
        }
    }

    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.log('Received message:', message);

            // 处理响应消息
            if (message.id && this.pendingRequests.has(message.id)) {
                const { resolve, reject, timeout } = this.pendingRequests.get(message.id);
                clearTimeout(timeout);
                this.pendingRequests.delete(message.id);

                if (message.error) {
                    reject(new Error(message.error));
                } else {
                    resolve(message.data);
                }
                return;
            }

            // 处理业务消息
            const handlers = this.messageHandlers.get(message.type);
            if (handlers) {
                handlers.forEach(handler => {
                    try {
                        handler(message.data, message);
                    } catch (error) {
                        this.log('Handler error:', error);
                    }
                });
            } else {
                this.log('No handler for message type:', message.type);
            }

            // 处理心跳响应
            if (message.type === 'pong') {
                this.handlePong();
            }

        } catch (error) {
            this.log('Message parse error:', error);
        }
    }

    onError(error) {
        this.log('WebSocket error:', error);
        this.handleError(error);
    }

    // 重连
    reconnect() {
        if (this.reconnectAttempts >= config.maxReconnectAttempts) {
            this.log('Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        this.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, config.reconnectInterval);
    }

    // 启动心跳
    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            this.send('ping').catch(error => {
                this.log('Heartbeat error:', error);
            });

            // 设置心跳超时
            this.heartbeatTimeoutTimer = setTimeout(() => {
                this.log('Heartbeat timeout');
                this.disconnect();
                this.reconnect();
            }, config.heartbeatTimeout);
        }, config.heartbeatInterval);
    }

    // 停止心跳
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }
    }

    // 处理pong响应
    handlePong() {
        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }
    }

    // 清空消息队列
    flushMessageQueue() {
        while (config.messageQueue.length > 0) {
            const { type, data, options, resolve, reject } = config.messageQueue.shift();
            this.send(type, data, options).then(resolve).catch(reject);
        }
    }

    // 设置状态
    setState(state) {
        this.state = state;
        this.notifyReadyStateChange();
    }

    // 通知状态变化
    notifyReadyStateChange() {
        this.readyStateHandlers.forEach(handler => {
            try {
                handler(this.state);
            } catch (error) {
                this.log('ReadyState handler error:', error);
            }
        });
    }

    // 处理错误
    handleError(error) {
        this.log('WebSocket error:', error);

        // 显示错误提示
        store.dispatch('showToast', {
            type: 'error',
            message: 'WebSocket连接失败'
        });
    }

    // 日志输出
    log(...args) {
        if (config.debug) {
            console.log('[WebSocket]', ...args);
        }
    }

    // 获取连接状态
    getReadyState() {
        return this.state;
    }

    // 检查是否已连接
    isConnected() {
        return this.state === WebSocket.OPEN;
    }
}

// 创建全局WebSocket实例
export const wsManager = new WebSocketManager();

// 扩展WebSocket管理器，添加业务方法
wsManager.on('connected', (data) => {
    store.dispatch('showToast', {
        type: 'success',
        message: 'WebSocket已连接'
    });
});

wsManager.on('disconnected', (data) => {
    store.dispatch('showToast', {
        type: 'warning',
        message: 'WebSocket已断开'
    });
});

// 业务方法封装
export const wsApi = {
    // 创建会话
    createSession: (data) => wsManager.send('create_session', data, { expectResponse: true }),

    // 发送消息
    sendMessage: (data) => wsManager.send('send_message', data, { expectResponse: true }),

    // 获取历史记录
    getHistory: (sessionId) => wsManager.send('get_history', { session_id: sessionId }, { expectResponse: true }),

    // 创建工单
    createWorkOrder: (data) => wsManager.send('create_work_order', data, { expectResponse: true }),

    // 获取工单状态
    getWorkOrderStatus: (workOrderId) => wsManager.send('get_work_order_status', { work_order_id: workOrderId }, { expectResponse: true }),

    // 结束会话
    endSession: (sessionId) => wsManager.send('end_session', { session_id: sessionId }, { expectResponse: true })
};

// 初始化WebSocket连接
export function initWebSocket() {
    // 页面可见时连接
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && !wsManager.isConnected()) {
            wsManager.connect();
        }
    });

    // 窗口获得焦点时检查连接
    window.addEventListener('focus', () => {
        if (!wsManager.isConnected()) {
            wsManager.connect();
        }
    });

    // 页面卸载时断开连接
    window.addEventListener('beforeunload', () => {
        wsManager.disconnect();
    });

    // 网络状态变化时重连
    window.addEventListener('online', () => {
        if (!wsManager.isConnected()) {
            wsManager.connect();
        }
    });

    // 自动连接
    wsManager.connect();
}

// 导出配置和管理器
export { config };
export default wsManager;