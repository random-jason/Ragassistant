// HTTP版本实时对话前端脚本

class ChatHttpClient {
    constructor() {
        this.sessionId = null;
        this.messageCount = 0;
        this.apiBase = '/api/chat';
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateConnectionStatus(true);
    }

    bindEvents() {
        // 开始对话
        document.getElementById('start-chat').addEventListener('click', () => this.startChat());
        
        // 结束对话
        document.getElementById('end-chat').addEventListener('click', () => this.endChat());
        
        // 发送消息
        document.getElementById('send-button').addEventListener('click', () => this.sendMessage());
        
        // 回车发送
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // 创建工单
        document.getElementById('create-work-order').addEventListener('click', () => this.showWorkOrderModal());
        document.getElementById('create-work-order-btn').addEventListener('click', () => this.createWorkOrder());
        
        // 快速操作按钮
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const message = e.target.getAttribute('data-message');
                document.getElementById('message-input').value = message;
                this.sendMessage();
            });
        });
    }

    async startChat() {
        try {
            // 创建会话
            const userId = document.getElementById('user-id').value || 'anonymous';
            const workOrderId = document.getElementById('work-order-id').value || null;
            
            const response = await this.sendRequest('POST', '/session', {
                user_id: userId,
                work_order_id: workOrderId ? parseInt(workOrderId) : null
            });
            
            if (response.success) {
                this.sessionId = response.session_id;
                this.updateSessionInfo();
                this.enableChat();
                this.addSystemMessage('对话已开始，请描述您的问题。');
            } else {
                this.showError('创建会话失败');
            }
            
        } catch (error) {
            console.error('启动对话失败:', error);
            this.showError('启动对话失败: ' + error.message);
        }
    }

    async endChat() {
        try {
            if (this.sessionId) {
                await this.sendRequest('DELETE', `/session/${this.sessionId}`);
            }
            
            this.sessionId = null;
            this.disableChat();
            this.addSystemMessage('对话已结束。');
            
        } catch (error) {
            console.error('结束对话失败:', error);
        }
    }

    async sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message || !this.sessionId) {
            return;
        }
        
        // 清空输入框
        input.value = '';
        
        // 添加用户消息
        this.addMessage('user', message);
        
        // 显示打字指示器
        this.showTypingIndicator();
        
        try {
            const response = await this.sendRequest('POST', '/message', {
                session_id: this.sessionId,
                message: message
            });
            
            this.hideTypingIndicator();
            
            if (response.success) {
                // 添加助手回复
                this.addMessage('assistant', response.content, {
                    knowledge_used: response.knowledge_used,
                    confidence_score: response.confidence_score,
                    work_order_id: response.work_order_id
                });
                
                // 更新工单ID
                if (response.work_order_id) {
                    document.getElementById('work-order-id').value = response.work_order_id;
                }
                
            } else {
                this.addMessage('assistant', '抱歉，我暂时无法处理您的问题。请稍后再试。');
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('发送消息失败:', error);
            this.addMessage('assistant', '发送消息失败，请检查网络连接。');
        }
    }

    async createWorkOrder() {
        const title = document.getElementById('wo-title').value;
        const description = document.getElementById('wo-description').value;
        const category = document.getElementById('wo-category').value;
        const priority = document.getElementById('wo-priority').value;
        
        if (!title || !description) {
            this.showError('请填写工单标题和描述');
            return;
        }
        
        try {
            const response = await this.sendRequest('POST', '/work-order', {
                session_id: this.sessionId,
                title: title,
                description: description,
                category: category,
                priority: priority
            });
            
            if (response.success) {
                const workOrderId = response.work_order_id;
                document.getElementById('work-order-id').value = workOrderId;
                this.addSystemMessage(`工单创建成功！工单号: ${response.order_id}`);
                
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('workOrderModal'));
                modal.hide();
                
                // 清空表单
                document.getElementById('work-order-form').reset();
                
            } else {
                this.showError('创建工单失败: ' + (response.error || '未知错误'));
            }
            
        } catch (error) {
            console.error('创建工单失败:', error);
            this.showError('创建工单失败: ' + error.message);
        }
    }

    async sendRequest(method, endpoint, data = null) {
        const url = this.apiBase + endpoint;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        return await response.json();
    }

    addMessage(role, content, metadata = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // 如果是第一条消息，清空欢迎信息
        if (this.messageCount === 0) {
            messagesContainer.innerHTML = '';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : 'A';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = content;
        
        // 添加时间戳
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        contentDiv.appendChild(timeDiv);
        
        // 添加元数据
        if (metadata.knowledge_used && metadata.knowledge_used.length > 0) {
            const knowledgeDiv = document.createElement('div');
            knowledgeDiv.className = 'knowledge-info';
            knowledgeDiv.innerHTML = `<i class="fas fa-lightbulb me-1"></i>基于 ${metadata.knowledge_used.length} 条知识库信息生成`;
            contentDiv.appendChild(knowledgeDiv);
        }
        
        if (metadata.confidence_score) {
            const confidenceDiv = document.createElement('div');
            confidenceDiv.className = 'confidence-score';
            confidenceDiv.textContent = `置信度: ${(metadata.confidence_score * 100).toFixed(1)}%`;
            contentDiv.appendChild(confidenceDiv);
        }
        
        if (metadata.work_order_id) {
            const workOrderDiv = document.createElement('div');
            workOrderDiv.className = 'work-order-info';
            workOrderDiv.innerHTML = `<i class="fas fa-ticket-alt me-1"></i>关联工单: ${metadata.work_order_id}`;
            contentDiv.appendChild(workOrderDiv);
        }
        
        if (role === 'user') {
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messageCount++;
    }

    addSystemMessage(content) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'text-center text-muted py-2';
        messageDiv.innerHTML = `<small><i class="fas fa-info-circle me-1"></i>${content}</small>`;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        document.getElementById('typing-indicator').classList.add('show');
    }

    hideTypingIndicator() {
        document.getElementById('typing-indicator').classList.remove('show');
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.className = 'connection-status connected';
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>HTTP连接';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusElement.innerHTML = '<i class="fas fa-circle me-1"></i>连接断开';
        }
    }

    updateSessionInfo() {
        const sessionInfo = document.getElementById('session-info');
        sessionInfo.innerHTML = `
            <div><strong>会话ID:</strong> ${this.sessionId}</div>
            <div><strong>消息数:</strong> ${this.messageCount}</div>
            <div><strong>状态:</strong> 活跃</div>
        `;
    }

    enableChat() {
        document.getElementById('start-chat').disabled = true;
        document.getElementById('end-chat').disabled = false;
        document.getElementById('message-input').disabled = false;
        document.getElementById('send-button').disabled = false;
    }

    disableChat() {
        document.getElementById('start-chat').disabled = false;
        document.getElementById('end-chat').disabled = true;
        document.getElementById('message-input').disabled = true;
        document.getElementById('send-button').disabled = true;
    }

    showWorkOrderModal() {
        if (!this.sessionId) {
            this.showError('请先开始对话');
            return;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('workOrderModal'));
        modal.show();
    }

    showError(message) {
        this.addSystemMessage(`<span class="text-danger">错误: ${message}</span>`);
    }
}

// 初始化聊天客户端
document.addEventListener('DOMContentLoaded', () => {
    window.chatClient = new ChatHttpClient();
});
