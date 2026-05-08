/**
 * 系统设置页面组件
 */

export default class Settings {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.init();
    }

    async init() {
        this.render();
        this.bindEvents();
        this.loadSettings();
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">系统设置</h1>
                    <p class="page-subtitle">系统配置与管理</p>
                </div>
            </div>

            <div class="row">
                <!-- 系统信息 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-info-circle me-2"></i>系统信息
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="system-info" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 数据库状态 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-database me-2"></i>数据库状态
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="db-status" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 系统设置 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-sliders-h me-2"></i>系统配置
                            </h5>
                        </div>
                        <div class="card-body">
                            <form id="system-settings-form">
                                <!-- 预警规则设置 -->
                                <div class="mb-4">
                                    <h6>预警规则设置</h6>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">默认检查间隔 (秒)</label>
                                                <input type="number" class="form-control" id="check-interval" min="30" max="3600">
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">默认冷却时间 (秒)</label>
                                                <input type="number" class="form-control" id="cooldown" min="60" max="86400">
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- LLM配置 -->
                                <div class="mb-4">
                                    <h6>LLM配置</h6>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">API提供商</label>
                                                <select class="form-select" id="llm-provider">
                                                    <option value="openai">OpenAI</option>
                                                    <option value="qwen">通义千问</option>
                                                    <option value="claude">Claude</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">默认模型</label>
                                                <input type="text" class="form-control" id="default-model" placeholder="gpt-3.5-turbo">
                                            </div>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">API密钥</label>
                                        <input type="password" class="form-control" id="api-key" placeholder="输入API密钥">
                                    </div>
                                </div>

                                <!-- 其他设置 -->
                                <div class="mb-4">
                                    <h6>其他设置</h6>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="form-check mb-3">
                                                <input class="form-check-input" type="checkbox" id="enable-analytics">
                                                <label class="form-check-label" for="enable-analytics">
                                                    启用数据分析
                                                </label>
                                            </div>
                                            <div class="form-check mb-3">
                                                <input class="form-check-input" type="checkbox" id="enable-websocket">
                                                <label class="form-check-label" for="enable-websocket">
                                                    启用WebSocket实时通信
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check mb-3">
                                                <input class="form-check-input" type="checkbox" id="enable-pwa">
                                                <label class="form-check-label" for="enable-pwa">
                                                    启用PWA离线支持
                                                </label>
                                            </div>
                                            <div class="form-check mb-3">
                                                <input class="form-check-input" type="checkbox" id="enable-error-reporting">
                                                <label class="form-check-label" for="enable-error-reporting">
                                                    启用错误报告
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-save me-2"></i>保存设置
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 系统操作 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-tools me-2"></i>系统操作
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>数据管理</h6>
                                    <div class="d-grid gap-2">
                                        <button class="btn btn-warning" id="backup-data-btn">
                                            <i class="fas fa-download me-2"></i>备份数据
                                        </button>
                                        <button class="btn btn-danger" id="clear-cache-btn">
                                            <i class="fas fa-trash me-2"></i>清理缓存
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6>系统维护</h6>
                                    <div class="d-grid gap-2">
                                        <button class="btn btn-info" id="check-health-btn">
                                            <i class="fas fa-heartbeat me-2"></i>健康检查
                                        </button>
                                        <button class="btn btn-secondary" id="restart-services-btn">
                                            <i class="fas fa-redo me-2"></i>重启服务
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 设置表单提交
        const settingsForm = document.getElementById('system-settings-form');
        settingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });

        // 系统操作按钮
        document.getElementById('backup-data-btn').addEventListener('click', () => {
            this.backupData();
        });

        document.getElementById('clear-cache-btn').addEventListener('click', () => {
            this.clearCache();
        });

        document.getElementById('check-health-btn').addEventListener('click', () => {
            this.checkHealth();
        });

        document.getElementById('restart-services-btn').addEventListener('click', () => {
            this.restartServices();
        });
    }

    async loadSettings() {
        try {
            // 加载系统信息
            const healthResponse = await fetch('/api/health');
            const healthData = await healthResponse.json();

            const systemInfoDiv = document.getElementById('system-info');
            if (healthData) {
                systemInfoDiv.innerHTML = `
                    <div class="mb-2"><strong>版本:</strong> ${healthData.version || '1.0.0'}</div>
                    <div class="mb-2"><strong>运行时间:</strong> ${this.formatUptime(healthData.uptime || 0)}</div>
                    <div class="mb-2"><strong>健康评分:</strong> ${healthData.health_score || 0}/100</div>
                    <div class="mb-2"><strong>活跃会话:</strong> ${healthData.active_sessions || 0}</div>
                    <div class="mb-2"><strong>处理中的工单:</strong> ${healthData.processing_workorders || 0}</div>
                `;
            }

            // 加载数据库状态
            const dbStatusDiv = document.getElementById('db-status');
            if (healthData.db_status) {
                const dbStatus = healthData.db_status;
                dbStatusDiv.innerHTML = `
                    <div class="mb-2"><strong>状态:</strong> <span class="text-${dbStatus.connection_ok ? 'success' : 'danger'}">${dbStatus.connection_ok ? '正常' : '异常'}</span></div>
                    <div class="mb-2"><strong>类型:</strong> ${dbStatus.type || '未知'}</div>
                    <div class="mb-2"><strong>版本:</strong> ${dbStatus.version || '未知'}</div>
                    <div class="mb-2"><strong>连接数:</strong> ${dbStatus.active_connections || 0}</div>
                `;
            } else {
                dbStatusDiv.innerHTML = '<div class="text-muted">无法获取数据库状态</div>';
            }

            // 加载配置设置 (这里应该从后端API获取)
            this.loadConfigSettings();

        } catch (error) {
            console.error('加载设置失败:', error);
            document.getElementById('system-info').innerHTML = '<div class="text-danger">加载失败</div>';
            document.getElementById('db-status').innerHTML = '<div class="text-danger">加载失败</div>';
        }
    }

    async loadConfigSettings() {
        // 这里应该从后端API加载配置设置
        // 暂时设置一些默认值
        try {
            document.getElementById('check-interval').value = '300';
            document.getElementById('cooldown').value = '3600';
            document.getElementById('llm-provider').value = 'qwen';
            document.getElementById('default-model').value = 'qwen-turbo';
            document.getElementById('enable-analytics').checked = true;
            document.getElementById('enable-websocket').checked = true;
            document.getElementById('enable-pwa').checked = true;
            document.getElementById('enable-error-reporting').checked = false;
        } catch (error) {
            console.error('加载配置设置失败:', error);
        }
    }

    async saveSettings() {
        const settings = {
            alert_rules: {
                check_interval: parseInt(document.getElementById('check-interval').value),
                cooldown: parseInt(document.getElementById('cooldown').value)
            },
            llm: {
                provider: document.getElementById('llm-provider').value,
                model: document.getElementById('default-model').value,
                api_key: document.getElementById('api-key').value
            },
            features: {
                analytics: document.getElementById('enable-analytics').checked,
                websocket: document.getElementById('enable-websocket').checked,
                pwa: document.getElementById('enable-pwa').checked,
                error_reporting: document.getElementById('enable-error-reporting').checked
            }
        };

        try {
            // 这里应该调用后端API保存设置
            console.log('保存设置:', settings);

            if (window.showToast) {
                window.showToast('设置保存成功', 'success');
            }
        } catch (error) {
            console.error('保存设置失败:', error);
            if (window.showToast) {
                window.showToast('设置保存失败', 'error');
            }
        }
    }

    async backupData() {
        try {
            // 这里应该调用后端备份API
            console.log('开始备份数据...');

            if (window.showToast) {
                window.showToast('数据备份功能开发中', 'info');
            }
        } catch (error) {
            console.error('备份数据失败:', error);
            if (window.showToast) {
                window.showToast('备份失败', 'error');
            }
        }
    }

    async clearCache() {
        if (confirm('确定要清理所有缓存吗？')) {
            try {
                // 清理本地存储
                localStorage.clear();
                sessionStorage.clear();

                // 清理Service Worker缓存
                if ('caches' in window) {
                    const cacheNames = await caches.keys();
                    await Promise.all(
                        cacheNames.map(cacheName => caches.delete(cacheName))
                    );
                }

                if (window.showToast) {
                    window.showToast('缓存清理完成', 'success');
                }

                // 刷新页面
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } catch (error) {
                console.error('清理缓存失败:', error);
                if (window.showToast) {
                    window.showToast('清理缓存失败', 'error');
                }
            }
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            if (data) {
                const healthScore = data.health_score || 0;
                const status = healthScore >= 80 ? 'success' : healthScore >= 60 ? 'warning' : 'error';
                const message = `系统健康评分: ${healthScore}/100`;

                if (window.showToast) {
                    window.showToast(message, status);
                }
            } else {
                if (window.showToast) {
                    window.showToast('健康检查失败', 'error');
                }
            }
        } catch (error) {
            console.error('健康检查失败:', error);
            if (window.showToast) {
                window.showToast('健康检查失败', 'error');
            }
        }
    }

    async restartServices() {
        if (confirm('确定要重启系统服务吗？这可能会暂时中断服务。')) {
            try {
                // 这里应该调用后端重启API
                console.log('重启服务...');

                if (window.showToast) {
                    window.showToast('服务重启功能开发中', 'info');
                }
            } catch (error) {
                console.error('重启服务失败:', error);
                if (window.showToast) {
                    window.showToast('重启失败', 'error');
                }
            }
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (days > 0) {
            return `${days}天 ${hours}小时 ${minutes}分钟`;
        } else if (hours > 0) {
            return `${hours}小时 ${minutes}分钟`;
        } else {
            return `${minutes}分钟`;
        }
    }
}