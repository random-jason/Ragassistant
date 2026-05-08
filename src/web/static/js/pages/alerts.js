/**
 * 预警管理页面组件
 */

import { api } from '../core/api.js';
import { formatDate, formatRelativeTime } from '../core/utils.js';
import { confirm, alert } from '../components/modal.js';
import store from '../core/store.js';

export default class Alerts {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.filters = {
            level: '',
            status: '',
            type: '',
            page: 1,
            per_page: 10
        };
        this.init();
    }

    async init() {
        try {
            this.render();
            await this.loadData();
            this.bindEvents();
        } catch (error) {
            console.error('Alerts page init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">预警管理</h1>
                    <p class="page-subtitle">系统预警规则与实时监控</p>
                </div>
                <div class="page-actions">
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#ruleModal">
                        <i class="fas fa-plus me-2"></i>添加规则
                    </button>
                    <button class="btn btn-success" id="check-alerts">
                        <i class="fas fa-search me-2"></i>检查预警
                    </button>
                </div>
            </div>

            <!-- 预警统计 -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stat-card danger">
                        <div class="stat-content">
                            <div class="stat-number" id="critical-alerts">0</div>
                            <div class="stat-label">严重预警</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card warning">
                        <div class="stat-content">
                            <div class="stat-number" id="warning-alerts">0</div>
                            <div class="stat-label">警告预警</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card info">
                        <div class="stat-content">
                            <div class="stat-number" id="info-alerts">0</div>
                            <div class="stat-label">信息预警</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="stat-content">
                            <div class="stat-number" id="total-alerts">0</div>
                            <div class="stat-label">总预警数</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 监控控制 -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">监控控制</h5>
                </div>
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <span class="me-3">监控状态：</span>
                                <span class="status-indicator" id="monitor-status">
                                    <span id="monitor-text">检查中...</span>
                                </span>
                            </div>
                        </div>
                        <div class="col-md-6 text-end">
                            <button class="btn btn-success me-2" id="start-monitor">
                                <i class="fas fa-play me-1"></i>启动监控
                            </button>
                            <button class="btn btn-danger" id="stop-monitor">
                                <i class="fas fa-stop me-1"></i>停止监控
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 预警规则 -->
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">预警规则</h5>
                    <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#ruleModal">
                        <i class="fas fa-plus me-1"></i>添加规则
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>规则名称</th>
                                    <th>类型</th>
                                    <th>级别</th>
                                    <th>阈值</th>
                                    <th>状态</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="rules-table">
                                <tr>
                                    <td colspan="6" class="text-center">
                                        <div class="spinner spinner-sm"></div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 预警列表 -->
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">预警历史</h5>
                </div>
                <div class="card-body">
                    <!-- 筛选器 -->
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <select class="form-select" id="filter-level">
                                <option value="">所有级别</option>
                                <option value="critical">严重</option>
                                <option value="error">错误</option>
                                <option value="warning">警告</option>
                                <option value="info">信息</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" id="filter-status">
                                <option value="">所有状态</option>
                                <option value="active">活跃</option>
                                <option value="resolved">已解决</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="filter-search" placeholder="搜索预警...">
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-secondary w-100" id="reset-filters">
                                重置
                            </button>
                        </div>
                    </div>

                    <!-- 预警列表 -->
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>时间</th>
                                    <th>级别</th>
                                    <th>规则</th>
                                    <th>消息</th>
                                    <th>状态</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="alerts-table">
                                <tr>
                                    <td colspan="6" class="text-center">
                                        <div class="spinner spinner-sm"></div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- 分页 -->
                    <nav class="mt-3">
                        <ul class="pagination justify-content-center" id="pagination">
                            <!-- 分页将在这里生成 -->
                        </ul>
                    </nav>
                </div>
            </div>
        `;

        // 渲染规则模态框
        this.renderRuleModal();
    }

    renderRuleModal() {
        const modalHTML = `
            <div class="modal fade" id="ruleModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">添加预警规则</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="rule-form">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">规则名称</label>
                                            <input type="text" class="form-control" name="name" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">预警类型</label>
                                            <select class="form-select" name="alert_type" required>
                                                <option value="performance">性能预警</option>
                                                <option value="quality">质量预警</option>
                                                <option value="volume">量级预警</option>
                                                <option value="system">系统预警</option>
                                                <option value="business">业务预警</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">预警级别</label>
                                            <select class="form-select" name="level" required>
                                                <option value="info">信息</option>
                                                <option value="warning">警告</option>
                                                <option value="error">错误</option>
                                                <option value="critical">严重</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">阈值</label>
                                            <input type="number" class="form-control" name="threshold" step="0.01" required>
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">规则描述</label>
                                    <textarea class="form-control" name="description" rows="2"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">条件表达式</label>
                                    <input type="text" class="form-control" name="condition"
                                           placeholder="例如: satisfaction_avg < threshold" required>
                                </div>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">检查间隔(秒)</label>
                                            <input type="number" class="form-control" name="check_interval" value="300">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">冷却时间(秒)</label>
                                            <input type="number" class="form-control" name="cooldown" value="3600">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <div class="form-check mt-4">
                                                <input class="form-check-input" type="checkbox" name="enabled" checked>
                                                <label class="form-check-label">启用规则</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="save-rule">保存规则</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    async loadData() {
        try {
            // 并行加载数据
            const [alertsRes, rulesRes, statistics, monitorStatus] = await Promise.all([
                api.alerts.list(this.filters),
                api.rules.list(),
                api.alerts.statistics(),
                api.monitor.status()
            ]);

            // 更新统计数据
            this.updateStatistics(statistics);

            // 更新监控状态
            this.updateMonitorStatus(monitorStatus);

            // 更新规则列表
            this.updateRulesList(rulesRes);

            // 更新预警列表
            this.updateAlertsList(alertsRes);

        } catch (error) {
            console.error('Load alerts data error:', error);
            this.showError(error);
        }
    }

    updateStatistics(statistics) {
        document.getElementById('critical-alerts').textContent = statistics.critical || 0;
        document.getElementById('warning-alerts').textContent = statistics.warning || 0;
        document.getElementById('info-alerts').textContent = statistics.info || 0;
        document.getElementById('total-alerts').textContent = statistics.total || 0;
    }

    updateMonitorStatus(status) {
        const statusEl = document.getElementById('monitor-status');
        const textEl = document.getElementById('monitor-text');

        if (status.status === 'running') {
            statusEl.className = 'status-indicator online';
            textEl.textContent = '监控运行中';
        } else {
            statusEl.className = 'status-indicator offline';
            textEl.textContent = '监控已停止';
        }
    }

    updateRulesList(rules) {
        const tbody = document.getElementById('rules-table');
        if (!tbody) return;

        if (!rules || rules.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">暂无预警规则</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = rules.map(rule => `
            <tr>
                <td>${rule.name}</td>
                <td><span class="badge bg-secondary">${rule.alert_type}</span></td>
                <td><span class="badge bg-${this.getLevelColor(rule.level)}">${rule.level}</span></td>
                <td>${rule.threshold}</td>
                <td>
                    <span class="status-indicator ${rule.enabled ? 'online' : 'offline'}">
                        ${rule.enabled ? '启用' : '禁用'}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="alerage.editRule('${rule.name}')">
                            编辑
                        </button>
                        <button class="btn btn-outline-danger" onclick="alerage.deleteRule('${rule.name}')">
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updateAlertsList(response) {
        const tbody = document.getElementById('alerts-table');
        if (!tbody) return;

        const alerts = response.alerts || [];

        if (alerts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">暂无预警记录</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = alerts.map(alert => `
            <tr>
                <td>${formatDate(alert.created_at, 'MM-DD HH:mm')}</td>
                <td><span class="badge bg-${this.getLevelColor(alert.level)}">${alert.level}</span></td>
                <td>${alert.rule_name}</td>
                <td>${alert.message}</td>
                <td>
                    <span class="status-indicator ${alert.is_active ? 'online' : 'offline'}">
                        ${alert.is_active ? '活跃' : '已解决'}
                    </span>
                </td>
                <td>
                    ${alert.is_active ? `
                        <button class="btn btn-sm btn-success" onclick="alerage.resolveAlert('${alert.id}')">
                            解决
                        </button>
                    ` : '-'}
                </td>
            </tr>
        `).join('');

        // 更新分页
        this.updatePagination(response);
    }

    updatePagination(response) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        const { page = 1, total_pages = 1 } = response;

        if (total_pages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = '';

        // 上一页
        if (page > 1) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${page - 1}">上一页</a>
            </li>`;
        }

        // 页码
        for (let i = Math.max(1, page - 2); i <= Math.min(total_pages, page + 2); i++) {
            html += `<li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }

        // 下一页
        if (page < total_pages) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${page + 1}">下一页</a>
            </li>`;
        }

        pagination.innerHTML = html;
    }

    getLevelColor(level) {
        const colors = {
            'critical': 'danger',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return colors[level] || 'secondary';
    }

    bindEvents() {
        // 监控控制
        document.getElementById('start-monitor')?.addEventListener('click', () => {
            this.startMonitor();
        });

        document.getElementById('stop-monitor')?.addEventListener('click', () => {
            this.stopMonitor();
        });

        document.getElementById('check-alerts')?.addEventListener('click', () => {
            this.checkAlerts();
        });

        // 规则表单
        document.getElementById('save-rule')?.addEventListener('click', () => {
            this.saveRule();
        });

        // 筛选器
        document.getElementById('filter-level')?.addEventListener('change', (e) => {
            this.filters.level = e.target.value;
            this.filters.page = 1;
            this.loadAlerts();
        });

        document.getElementById('filter-status')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value === 'active' ? 'active' :
                e.target.value === 'resolved' ? 'resolved' : '';
            this.filters.page = 1;
            this.loadAlerts();
        });

        document.getElementById('filter-search')?.addEventListener('input',
            this.debounce((e) => {
                this.filters.search = e.target.value;
                this.filters.page = 1;
                this.loadAlerts();
            }, 300)
        );

        document.getElementById('reset-filters')?.addEventListener('click', () => {
            this.resetFilters();
        });

        // 分页
        document.getElementById('pagination')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('page-link')) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page) {
                    this.filters.page = page;
                    this.loadAlerts();
                }
            }
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async startMonitor() {
        try {
            await api.monitor.start();
            await this.loadData();
            store.dispatch('showToast', {
                type: 'success',
                message: '监控已启动'
            });
        } catch (error) {
            console.error('Start monitor error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '启动监控失败'
            });
        }
    }

    async stopMonitor() {
        try {
            await api.monitor.stop();
            await this.loadData();
            store.dispatch('showToast', {
                type: 'success',
                message: '监控已停止'
            });
        } catch (error) {
            console.error('Stop monitor error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '停止监控失败'
            });
        }
    }

    async checkAlerts() {
        try {
            const result = await api.monitor.checkAlerts();
            await this.loadData();
            store.dispatch('showToast', {
                type: 'success',
                message: `检查完成，发现 ${result.alerts_count || 0} 个新预警`
            });
        } catch (error) {
            console.error('Check alerts error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '检查预警失败'
            });
        }
    }

    async saveRule() {
        const form = document.getElementById('rule-form');
        const formData = new FormData(form);
        const saveBtn = document.getElementById('save-rule');
        const isEditing = saveBtn.dataset.editing === 'true';

        const data = {
            name: formData.get('name'),
            alert_type: formData.get('alert_type'),
            level: formData.get('level'),
            threshold: parseFloat(formData.get('threshold')),
            description: formData.get('description'),
            condition: formData.get('condition'),
            check_interval: parseInt(formData.get('check_interval')),
            cooldown: parseInt(formData.get('cooldown')),
            enabled: formData.has('enabled')
        };

        try {
            if (isEditing) {
                // 更新规则
                const originalName = saveBtn.dataset.originalName;
                await api.rules.update(originalName, data);
                store.dispatch('showToast', {
                    type: 'success',
                    message: '规则更新成功'
                });
            } else {
                // 创建规则
                await api.rules.create(data);
                store.dispatch('showToast', {
                    type: 'success',
                    message: '规则创建成功'
                });
            }

            await this.loadData();

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('ruleModal'));
            modal.hide();

            // 重置表单和按钮状态
            form.reset();
            form.querySelector('[name="name"]').disabled = false;
            saveBtn.textContent = '保存规则';
            saveBtn.dataset.editing = 'false';
            delete saveBtn.dataset.originalName;
            document.querySelector('#ruleModal .modal-title').textContent = '添加预警规则';

        } catch (error) {
            console.error('Save rule error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: (isEditing ? '更新' : '创建') + '规则失败'
            });
        }
    }

    async editRule(name) {
        try {
            // 获取规则详情
            const rules = await api.rules.list();
            const rule = rules.find(r => r.name === name);

            if (!rule) {
                throw new Error('规则不存在');
            }

            // 填充表单
            const form = document.getElementById('rule-form');
            form.querySelector('[name="name"]').value = rule.name;
            form.querySelector('[name="name"]').disabled = true; // 规则名称不可编辑
            form.querySelector('[name="alert_type"]').value = rule.alert_type;
            form.querySelector('[name="level"]').value = rule.level;
            form.querySelector('[name="threshold"]').value = rule.threshold;
            form.querySelector('[name="description"]').value = rule.description || '';
            form.querySelector('[name="condition"]').value = rule.condition || '';
            form.querySelector('[name="check_interval"]').value = rule.check_interval || 300;
            form.querySelector('[name="cooldown"]').value = rule.cooldown || 3600;
            form.querySelector('[name="enabled"]').checked = rule.enabled;

            // 修改模态框标题和按钮
            document.querySelector('#ruleModal .modal-title').textContent = '编辑预警规则';
            const saveBtn = document.getElementById('save-rule');
            saveBtn.textContent = '更新规则';
            saveBtn.dataset.editing = 'true';
            saveBtn.dataset.originalName = name;

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('ruleModal'));
            modal.show();

        } catch (error) {
            console.error('Load rule error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '加载规则失败: ' + (error.message || '未知错误')
            });
        }
    }

    async deleteRule(name) {
        const confirmed = await confirm({
            title: '删除规则',
            message: `确定要删除规则 "${name}" 吗？`
        });

        if (!confirmed) return;

        try {
            await api.rules.delete(name);
            await this.loadData();
            store.dispatch('showToast', {
                type: 'success',
                message: '规则已删除'
            });
        } catch (error) {
            console.error('Delete rule error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '删除规则失败'
            });
        }
    }

    async resolveAlert(alertId) {
        try {
            await api.alerts.resolve(alertId, { resolved_by: 'admin', resolution: '手动解决' });
            await this.loadAlerts();
            store.dispatch('showToast', {
                type: 'success',
                message: '预警已解决'
            });
        } catch (error) {
            console.error('Resolve alert error:', error);
            store.dispatch('showToast', {
                type: 'error',
                message: '解决预警失败'
            });
        }
    }

    resetFilters() {
        this.filters = {
            level: '',
            status: '',
            search: '',
            page: 1,
            per_page: 10
        };

        // 重置筛选器UI
        document.getElementById('filter-level').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-search').value = '';

        // 重新加载数据
        this.loadAlerts();
    }

    async loadAlerts() {
        try {
            const response = await api.alerts.list(this.filters);
            this.updateAlertsList(response);
        } catch (error) {
            console.error('Load alerts error:', error);
        }
    }

    showError(error) {
        this.container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">加载失败</h4>
                <p>${error.message || '未知错误'}</p>
                <hr>
                <button class="btn btn-outline-danger" onclick="location.reload()">
                    重新加载
                </button>
            </div>
        `;
    }
}

// 暴露到全局供内联事件使用
window.alerage = null;