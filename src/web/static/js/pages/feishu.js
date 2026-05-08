/**
 * 飞书同步页面组件
 */

export default class Feishu {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.init();
    }

    async init() {
        try {
            this.render();
            this.bindEvents();
            this.loadSyncStatus();
        } catch (error) {
            console.error('Feishu init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">飞书同步</h1>
                    <p class="page-subtitle">与飞书多维表格进行数据同步</p>
                </div>
            </div>

            <div class="row">
                <!-- 同步配置 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-cog me-2"></i>同步配置
                            </h5>
                        </div>
                        <div class="card-body">
                            <form id="feishu-config-form">
                                <div class="mb-3">
                                    <label for="app_id" class="form-label">App ID</label>
                                    <input type="text" class="form-control" id="app_id" name="app_id"
                                           placeholder="飞书应用的App ID">
                                </div>
                                <div class="mb-3">
                                    <label for="app_secret" class="form-label">App Secret</label>
                                    <input type="password" class="form-control" id="app_secret" name="app_secret"
                                           placeholder="飞书应用的App Secret">
                                </div>
                                <div class="mb-3">
                                    <label for="app_token" class="form-label">App Token</label>
                                    <input type="text" class="form-control" id="app_token" name="app_token"
                                           placeholder="多维表格的App Token">
                                </div>
                                <div class="mb-3">
                                    <label for="table_id" class="form-label">Table ID</label>
                                    <input type="text" class="form-control" id="table_id" name="table_id"
                                           placeholder="数据表的Table ID">
                                </div>
                                <div class="d-grid gap-2">
                                    <button type="submit" class="btn btn-primary" id="save-config-btn">
                                        <i class="fas fa-save me-2"></i>保存配置
                                    </button>
                                    <button type="button" class="btn btn-outline-secondary" id="test-connection-btn">
                                        <i class="fas fa-plug me-2"></i>测试连接
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- 同步状态 -->
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-info-circle me-2"></i>同步状态
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="sync-status" class="text-muted">
                                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                            </div>
                        </div>
                    </div>

                    <!-- 同步操作 -->
                    <div class="card mt-3">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-sync me-2"></i>同步操作
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button class="btn btn-success" id="sync-from-feishu-btn">
                                    <i class="fas fa-download me-2"></i>从飞书同步
                                </button>
                                <button class="btn btn-primary" id="preview-data-btn">
                                    <i class="fas fa-eye me-2"></i>预览飞书数据
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 字段映射 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-link me-2"></i>字段映射
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <button class="btn btn-outline-primary mb-3" id="discover-fields-btn">
                                        <i class="fas fa-search me-2"></i>发现字段
                                    </button>
                                    <div id="field-discovery-result"></div>
                                </div>
                                <div class="col-md-6">
                                    <button class="btn btn-outline-secondary mb-3" id="mapping-status-btn">
                                        <i class="fas fa-list me-2"></i>映射状态
                                    </button>
                                    <div id="mapping-status-result"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 数据预览 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-table me-2"></i>数据预览
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="data-preview" class="text-muted">
                                点击"预览飞书数据"查看数据
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 配置表单提交
        const configForm = document.getElementById('feishu-config-form');
        configForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfig();
        });

        // 测试连接
        document.getElementById('test-connection-btn').addEventListener('click', () => {
            this.testConnection();
        });

        // 从飞书同步
        document.getElementById('sync-from-feishu-btn').addEventListener('click', () => {
            this.syncFromFeishu();
        });

        // 预览数据
        document.getElementById('preview-data-btn').addEventListener('click', () => {
            this.previewData();
        });

        // 发现字段
        document.getElementById('discover-fields-btn').addEventListener('click', () => {
            this.discoverFields();
        });

        // 映射状态
        document.getElementById('mapping-status-btn').addEventListener('click', () => {
            this.getMappingStatus();
        });

        // 加载配置
        this.loadConfig();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/feishu-sync/config');
            const data = await response.json();

            if (data.success) {
                document.getElementById('app_id').value = data.config.app_id || '';
                document.getElementById('app_secret').value = data.config.app_secret || '';
                document.getElementById('app_token').value = data.config.app_token || '';
                document.getElementById('table_id').value = data.config.table_id || '';
            }
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    async saveConfig() {
        const formData = new FormData(document.getElementById('feishu-config-form'));
        const config = {
            app_id: formData.get('app_id'),
            app_secret: formData.get('app_secret'),
            app_token: formData.get('app_token'),
            table_id: formData.get('table_id')
        };

        try {
            const response = await fetch('/api/feishu-sync/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('配置保存成功', 'success');
                }
            } else {
                if (window.showToast) {
                    window.showToast(data.error || '配置保存失败', 'error');
                }
            }
        } catch (error) {
            console.error('保存配置失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async testConnection() {
        try {
            const response = await fetch('/api/feishu-sync/test-connection');
            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast('连接测试成功', 'success');
                }
                // 显示字段信息
                if (data.fields) {
                    console.log('飞书表格字段:', data.fields);
                }
            } else {
                if (window.showToast) {
                    window.showToast(data.message || '连接测试失败', 'error');
                }
            }
        } catch (error) {
            console.error('测试连接失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async loadSyncStatus() {
        try {
            const response = await fetch('/api/feishu-sync/status');
            const data = await response.json();

            const statusDiv = document.getElementById('sync-status');
            if (data.success) {
                const status = data.status;
                statusDiv.innerHTML = `
                    <div class="mb-2">
                        <strong>最后同步:</strong> ${status.last_sync || '从未同步'}
                    </div>
                    <div class="mb-2">
                        <strong>同步状态:</strong> ${status.is_syncing ? '同步中' : '空闲'}
                    </div>
                    <div class="mb-2">
                        <strong>总记录数:</strong> ${status.total_records || 0}
                    </div>
                `;
            } else {
                statusDiv.innerHTML = '<span class="text-danger">获取状态失败</span>';
            }
        } catch (error) {
            console.error('获取同步状态失败:', error);
            document.getElementById('sync-status').innerHTML = '<span class="text-danger">获取状态失败</span>';
        }
    }

    async syncFromFeishu() {
        try {
            const response = await fetch('/api/feishu-sync/sync-from-feishu', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    generate_ai_suggestions: true,
                    limit: 50
                })
            });

            const data = await response.json();

            if (data.success) {
                if (window.showToast) {
                    window.showToast(data.message, 'success');
                }
                this.loadSyncStatus(); // 重新加载状态
            } else {
                if (window.showToast) {
                    window.showToast(data.error || '同步失败', 'error');
                }
            }
        } catch (error) {
            console.error('同步失败:', error);
            if (window.showToast) {
                window.showToast('网络错误', 'error');
            }
        }
    }

    async previewData() {
        try {
            const response = await fetch('/api/feishu-sync/preview-feishu-data');
            const data = await response.json();

            const previewDiv = document.getElementById('data-preview');
            if (data.success && data.preview_data.length > 0) {
                let html = `<div class="table-responsive"><table class="table table-sm">`;
                html += '<thead><tr><th>记录ID</th><th>字段数据</th></tr></thead><tbody>';

                data.preview_data.forEach(item => {
                    html += `<tr>
                        <td>${item.record_id}</td>
                        <td><pre class="small">${JSON.stringify(item.fields, null, 2)}</pre></td>
                    </tr>`;
                });

                html += '</tbody></table></div>';
                previewDiv.innerHTML = html;
            } else {
                previewDiv.innerHTML = '<span class="text-muted">暂无数据</span>';
            }
        } catch (error) {
            console.error('预览数据失败:', error);
            document.getElementById('data-preview').innerHTML = '<span class="text-danger">预览失败</span>';
        }
    }

    async discoverFields() {
        try {
            const response = await fetch('/api/feishu-sync/field-mapping/discover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: 5 })
            });

            const data = await response.json();

            const resultDiv = document.getElementById('field-discovery-result');
            if (data.success) {
                const report = data.discovery_report;
                let html = '<h6>字段发现报告</h6>';

                if (Object.keys(report).length > 0) {
                    html += '<ul class="list-group list-group-flush">';
                    Object.entries(report).forEach(([field, info]) => {
                        html += `<li class="list-group-item">
                            <strong>${field}</strong>: ${info.suggestion || '未知'}
                            <br><small class="text-muted">置信度: ${(info.confidence * 100).toFixed(1)}%</small>
                        </li>`;
                    });
                    html += '</ul>';
                } else {
                    html += '<p class="text-muted">未发现可映射的字段</p>';
                }

                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = '<span class="text-danger">字段发现失败</span>';
            }
        } catch (error) {
            console.error('字段发现失败:', error);
            document.getElementById('field-discovery-result').innerHTML = '<span class="text-danger">字段发现失败</span>';
        }
    }

    async getMappingStatus() {
        try {
            const response = await fetch('/api/feishu-sync/field-mapping/status');
            const data = await response.json();

            const resultDiv = document.getElementById('mapping-status-result');
            if (data.success) {
                const status = data.status;
                let html = '<h6>映射状态</h6>';

                if (status.mappings && status.mappings.length > 0) {
                    html += '<ul class="list-group list-group-flush">';
                    status.mappings.forEach(mapping => {
                        html += `<li class="list-group-item">
                            <strong>${mapping.feishu_field}</strong> → ${mapping.local_field}
                            <br><small class="text-muted">优先级: ${mapping.priority}</small>
                        </li>`;
                    });
                    html += '</ul>';
                } else {
                    html += '<p class="text-muted">暂无字段映射</p>';
                }

                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = '<span class="text-danger">获取映射状态失败</span>';
            }
        } catch (error) {
            console.error('获取映射状态失败:', error);
            document.getElementById('mapping-status-result').innerHTML = '<span class="text-danger">获取映射状态失败</span>';
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
}
