/**
 * Agent页面组件
 */

export default class Agent {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.init();
    }

    async init() {
        try {
            this.render();
            this.bindEvents();
            this.loadAgentStatus();
            this.loadActionHistory();
        } catch (error) {
            console.error('Agent init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">智能Agent</h1>
                    <p class="page-subtitle">AI助手自动监控和任务执行</p>
                </div>
            </div>

            <div class="row">
                <!-- Agent状态 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-robot me-2"></i>Agent状态
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="agent-status" class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">加载中...</span>
                                </div>
                                <div class="mt-2">加载Agent状态...</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 控制面板 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-sliders-h me-2"></i>控制面板
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button class="btn btn-success" id="start-monitoring-btn">
                                    <i class="fas fa-play me-2"></i>启动监控
                                </button>
                                <button class="btn btn-warning" id="stop-monitoring-btn">
                                    <i class="fas fa-stop me-2"></i>停止监控
                                </button>
                                <button class="btn btn-info" id="run-analysis-btn">
                                    <i class="fas fa-chart-line me-2"></i>运行分析
                                </button>
                                <button class="btn btn-primary" id="trigger-sample-btn">
                                    <i class="fas fa-magic me-2"></i>触发示例动作
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Agent对话 -->
            <div class="row mt-4">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-comments me-2"></i>Agent对话
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="chat-messages" class="chat-messages mb-3" style="height: 300px; overflow-y: auto;">
                                <div class="text-muted text-center">暂无对话记录</div>
                            </div>
                            <div class="input-group">
                                <input type="text" class="form-control" id="chat-input"
                                       placeholder="输入消息与Agent对话..." maxlength="500">
                                <button class="btn btn-primary" id="send-chat-btn">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 工具统计 -->
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-tools me-2"></i>工具统计
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="tools-stats" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>

                    <!-- LLM统计 -->
                    <div class="card mt-3">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-brain me-2"></i>LLM使用统计
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="llm-stats" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 执行历史 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-history me-2"></i>执行历史
                            </h5>
                            <button class="btn btn-sm btn-outline-danger" id="clear-history-btn">
                                <i class="fas fa-trash me-2"></i>清空历史
                            </button>
                        </div>
                        <div class="card-body">
                            <div id="action-history" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 控制按钮事件
        document.getElementById('start-monitoring-btn').addEventListener('click', () => {
            this.startMonitoring();
        });

        document.getElementById('stop-monitoring-btn').addEventListener('click', () => {
            this.stopMonitoring();
        });

        document.getElementById('run-analysis-btn').addEventListener('click', () => {
            this.runAnalysis();
        });

        document.getElementById('trigger-sample-btn').addEventListener('click', () => {
            this.triggerSampleActions();
        });

        // 对话事件
        document.getElementById('send-chat-btn').addEventListener('click', () => {
            this.sendChatMessage();
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // 清空历史
        document.getElementById('clear-history-btn').addEventListener('click', () => {
            this.clearHistory();
        });

        // 定期刷新状态
        this.statusInterval = setInterval(() => {
            this.loadAgentStatus();
        }, 5000);
    }

    async loadAgentStatus() {
        try {
            const response = await fetch('/api/agent/status');
            const data = await response.json();

            const statusDiv = document.getElementById('agent-status');
            if (data.success) {
                const status = data.status || 'unknown';
                const activeGoals = data.active_goals || 0;
                const availableTools = data.available_tools || 0;

                let statusClass = 'text-warning';
                let statusText = '未知状态';

                switch (status) {
                    case 'active':
                        statusClass = 'text-success';
                        statusText = '运行中';
                        break;
                    case 'inactive':
                        statusClass = 'text-secondary';
                        statusText = '未激活';
                        break;
                    case 'error':
                        statusClass = 'text-danger';
                        statusText = '错误';
                        break;
                }

                statusDiv.innerHTML = `
                    <div class="mb-3">
                        <i class="fas fa-circle ${statusClass} me-2"></i>
                        <span class="h5 mb-0 ${statusClass}">${statusText}</span>
                    </div>
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="h4 mb-1">${activeGoals}</div>
                            <small class="text-muted">活跃目标</small>
                        </div>
                        <div class="col-6">
                            <div class="h4 mb-1">${availableTools}</div>
                            <small class="text-muted">可用工具</small>
                        </div>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle text-warning fa-2x mb-2"></i>
                        <div>Agent服务不可用</div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载Agent状态失败:', error);
            document.getElementById('agent-status').innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-danger fa-2x mb-2"></i>
                    <div>加载状态失败</div>
                </div>
            `;
        }
    }

    async loadActionHistory() {
        try {
            const response = await fetch('/api/agent/action-history?limit=20');
            const data = await response.json();

            const historyDiv = document.getElementById('action-history');
            if (data.success && data.history.length > 0) {
                let html = '<div class="table-responsive"><table class="table table-sm">';
                html += '<thead><tr><th>时间</th><th>动作</th><th>状态</th><th>详情</th></tr></thead><tbody>';

                data.history.forEach(action => {
                    const timestamp = new Date(action.timestamp).toLocaleString();
                    const statusClass = action.success ? 'text-success' : 'text-danger';
                    const statusText = action.success ? '成功' : '失败';

                    html += `<tr>
                        <td>${timestamp}</td>
                        <td>${action.action_type || '未知'}</td>
                        <td><span class="${statusClass}">${statusText}</span></td>
                        <td><small class="text-muted">${action.details || ''}</small></td>
                    </tr>`;
                });

                html += '</tbody></table></div>';
                historyDiv.innerHTML = html;
            } else {
                historyDiv.innerHTML = '<div class="text-muted text-center">暂无执行历史</div>';
            }
        } catch (error) {
            console.error('加载执行历史失败:', error);
            document.getElementById('action-history').innerHTML = '<div class="text-danger text-center">加载历史失败</div>';
        }
    }

    async loadToolsStats() {
        try {
            const response = await fetch('/api/agent/tools/stats');
            const data = await response.json();

            const statsDiv = document.getElementById('tools-stats');
            if (data.success) {
                const tools = data.tools || [];
                const performance = data.performance || {};

                let html = `<div class="mb-2"><strong>工具数量:</strong> ${tools.length}</div>`;

                if (tools.length > 0) {
                    html += '<div class="small"><strong>可用工具:</strong></div><ul class="list-unstyled small">';
                    tools.slice(0, 5).forEach(tool => {
                        html += `<li>• ${tool.name}</li>`;
                    });
                    if (tools.length > 5) {
                        html += `<li class="text-muted">... 还有 ${tools.length - 5} 个工具</li>`;
                    }
                    html += '</ul>';
                }

                statsDiv.innerHTML = html;
            } else {
                statsDiv.innerHTML = '<div class="text-muted">获取工具统计失败</div>';
            }
        } catch (error) {
            console.error('加载工具统计失败:', error);
            document.getElementById('tools-stats').innerHTML = '<div class="text-danger">加载失败</div>';
        }
    }

    async loadLLMStats() {
        try {
            const response = await fetch('/api/agent/llm-stats');
            const data = await response.json();

            const statsDiv = document.getElementById('llm-stats');
            if (data.success) {
                const stats = data.stats || {};
                let html = '';

                if (stats.total_requests) {
                    html += `<div class="mb-1"><strong>总请求数:</strong> ${stats.total_requests}</div>`;
                }
                if (stats.success_rate !== undefined) {
                    html += `<div class="mb-1"><strong>成功率:</strong> ${(stats.success_rate * 100).toFixed(1)}%</div>`;
                }
                if (stats.average_response_time) {
                    html += `<div class="mb-1"><strong>平均响应时间:</strong> ${stats.average_response_time.toFixed(2)}s</div>`;
                }

                if (!html) {
                    html = '<div class="text-muted">暂无统计数据</div>';
                }

                statsDiv.innerHTML = html;
            } else {
                statsDiv.innerHTML = '<div class="text-muted">获取LLM统计失败</div>';
            }
        } catch (error) {
            console.error('加载LLM统计失败:', error);
            document.getElementById('llm-stats').innerHTML = '<div class="text-danger">加载失败</div>';
        }
    }

    async startMonitoring() {
        try {
            const response = await fetch('/api/agent/monitoring/start', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('监控已启动', 'success');
                }
                this.loadAgentStatus();
            } else {
                if (window.showToast) {
                    window.showToast(data.message || '启动监控失败', 'error');
                }
            }
        } catch (error) {
            console.error('启动监控失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async stopMonitoring() {
        try {
            const response = await fetch('/api/agent/monitoring/stop', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('监控已停止', 'success');
                }
                this.loadAgentStatus();
            } else {
                if (window.showToast) {
                    window.showToast(data.message || '停止监控失败', 'error');
                }
            }
        } catch (error) {
            console.error('停止监控失败:', error);
            if (window.showToast) {
                    window.showToast('网络错误', 'error');
            }
        }
    }

    async runAnalysis() {
        try {
            const response = await fetch('/api/agent/intelligent-analysis', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('智能分析完成', 'success');
                }
                this.loadActionHistory();
            } else {
                if (window.showToast) {
                    window.showToast('分析失败', 'error');
                }
            }
        } catch (error) {
            console.error('运行分析失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async triggerSampleActions() {
        try {
            const response = await fetch('/api/agent/trigger-sample', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('示例动作已触发', 'success');
                }
                this.loadActionHistory();
            } else {
                if (window.showToast) {
                    window.showToast('触发示例动作失败', 'error');
                }
            }
        } catch (error) {
            console.error('触发示例动作失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) {
            return;
        }

        // 添加用户消息到界面
        this.addMessageToChat('user', message);
        input.value = '';

        try {
            const response = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    context: { user_id: 'admin' }
                })
            });

            const data = await response.json();

            if (data.success) {
                // 添加Agent回复到界面
                this.addMessageToChat('agent', data.response);
            } else {
                this.addMessageToChat('agent', '抱歉，处理您的请求时出现错误。');
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessageToChat('agent', '网络错误，请稍后重试。');
        }
    }

    addMessageToChat(sender, message) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender === 'user' ? 'text-end' : ''}`;

        const time = new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="d-inline-block p-2 mb-2 rounded ${sender === 'user' ? 'bg-primary text-white' : 'bg-light'}">
                <div class="small">${message}</div>
                <div class="small opacity-75">${time}</div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async clearHistory() {
        if (!confirm('确定要清空所有执行历史吗？')) {
            return;
        }

        try {
            const response = await fetch('/api/agent/clear-history', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('历史已清空', 'success');
                }
                this.loadActionHistory();
            } else {
                if (window.showToast) {
                    window.showToast('清空历史失败', 'error');
                }
            }
        } catch (error) {
            console.error('清空历史失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    showError(error) {
        this.container.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                            <h4>页面加载失败</h4>
                            <p class="text-muted">${error.message || '未知错误'}</p>
                            <button class="btn btn-primary" onclick="location.reload()">
                                <i class="fas fa-redo me-2"></i>重新加载
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    destroy() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
    }
}
