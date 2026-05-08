// AI Helpdesk 预警管理系统前端脚本

class AlertManager {
    constructor() {
        this.alerts = [];
        this.rules = [];
        this.health = {};
        this.monitorStatus = 'unknown';
        this.refreshInterval = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }

    bindEvents() {
        // 监控控制按钮
        document.getElementById('start-monitor').addEventListener('click', () => this.startMonitoring());
        document.getElementById('stop-monitor').addEventListener('click', () => this.stopMonitoring());
        document.getElementById('check-alerts').addEventListener('click', () => this.checkAlerts());
        document.getElementById('refresh-alerts').addEventListener('click', () => this.loadAlerts());

        // 规则管理
        document.getElementById('save-rule').addEventListener('click', () => this.saveRule());
        document.getElementById('update-rule').addEventListener('click', () => this.updateRule());

        // 预警过滤和排序
        document.getElementById('alert-filter').addEventListener('change', () => this.updateAlertsDisplay());
        document.getElementById('alert-sort').addEventListener('change', () => this.updateAlertsDisplay());

        // 自动刷新
        setInterval(() => {
            this.loadHealth();
            this.loadMonitorStatus();
        }, 5000);
    }

    async loadInitialData() {
        await Promise.all([
            this.loadHealth(),
            this.loadAlerts(),
            this.loadRules(),
            this.loadMonitorStatus()
        ]);
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadAlerts();
        }, 10000); // 每10秒刷新一次预警
    }

    async loadHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            this.health = data;
            this.updateHealthDisplay();
        } catch (error) {
            console.error('加载健康状态失败:', error);
        }
    }

    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();
            this.alerts = data;
            this.updateAlertsDisplay();
            this.updateAlertStatistics();
        } catch (error) {
            console.error('加载预警失败:', error);
        }
    }

    async loadRules() {
        try {
            const response = await fetch('/api/rules');
            const data = await response.json();
            this.rules = data;
            this.updateRulesDisplay();
        } catch (error) {
            console.error('加载规则失败:', error);
        }
    }

    async loadMonitorStatus() {
        try {
            const response = await fetch('/api/monitor/status');
            const data = await response.json();
            this.monitorStatus = data.monitor_status;
            this.updateMonitorStatusDisplay();
        } catch (error) {
            console.error('加载监控状态失败:', error);
        }
    }

    updateHealthDisplay() {
        const healthScore = this.health.health_score || 0;
        const healthStatus = this.health.status || 'unknown';
        
        const scoreElement = document.getElementById('health-score-text');
        const circleElement = document.getElementById('health-score-circle');
        const statusElement = document.getElementById('health-status');
        
        if (scoreElement) scoreElement.textContent = Math.round(healthScore);
        if (statusElement) statusElement.textContent = this.getHealthStatusText(healthStatus);
        
        if (circleElement) {
            circleElement.className = `score-circle ${healthStatus}`;
        }
    }

    updateAlertsDisplay() {
        const container = document.getElementById('alerts-container');
        
        if (this.alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h5>暂无活跃预警</h5>
                    <p>系统运行正常，没有需要处理的预警</p>
                </div>
            `;
            return;
        }

        // 应用过滤和排序
        let filteredAlerts = this.filterAndSortAlerts(this.alerts);

        const alertsHtml = filteredAlerts.map(alert => {
            const dataStr = alert.data ? JSON.stringify(alert.data, null, 2) : '无数据';
            return `
                <div class="alert-card ${alert.level}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="d-flex align-items-center mb-2">
                                    <span class="alert-level ${alert.level}">${this.getLevelText(alert.level)}</span>
                                    <span class="ms-2 text-muted fw-bold">${alert.rule_name || '未知规则'}</span>
                                    <span class="ms-auto text-muted small">${this.formatTime(alert.created_at)}</span>
                                </div>
                                <div class="alert-message">${alert.message}</div>
                                <div class="alert-meta">
                                    类型: ${this.getTypeText(alert.alert_type)} | 
                                    级别: ${this.getLevelText(alert.level)}
                                </div>
                                <div class="alert-data">${dataStr}</div>
                            </div>
                            <div class="ms-3">
                                <button class="btn btn-sm btn-outline-success" onclick="alertManager.resolveAlert(${alert.id})">
                                    <i class="fas fa-check me-1"></i>解决
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = alertsHtml;
    }

    updateRulesDisplay() {
        const tbody = document.getElementById('rules-table');
        
        if (this.rules.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">暂无规则</td>
                </tr>
            `;
            return;
        }

        const rulesHtml = this.rules.map(rule => `
            <tr>
                <td>${rule.name}</td>
                <td>${this.getTypeText(rule.alert_type)}</td>
                <td><span class="alert-level ${rule.level}">${this.getLevelText(rule.level)}</span></td>
                <td>${rule.threshold}</td>
                <td><span class="rule-status ${rule.enabled ? 'enabled' : 'disabled'}">${rule.enabled ? '启用' : '禁用'}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="alertManager.editRule('${rule.name}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="alertManager.deleteRule('${rule.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = rulesHtml;
    }

    updateAlertStatistics() {
        const stats = this.alerts.reduce((acc, alert) => {
            acc[alert.level] = (acc[alert.level] || 0) + 1;
            acc.total = (acc.total || 0) + 1;
            return acc;
        }, {});

        document.getElementById('critical-alerts').textContent = stats.critical || 0;
        document.getElementById('warning-alerts').textContent = stats.warning || 0;
        document.getElementById('info-alerts').textContent = stats.info || 0;
        document.getElementById('total-alerts').textContent = stats.total || 0;
    }

    updateMonitorStatusDisplay() {
        const statusElement = document.getElementById('monitor-status');
        const icon = statusElement.querySelector('i');
        const text = statusElement.querySelector('span') || statusElement;
        
        let statusText = '';
        let statusClass = '';
        
        switch (this.monitorStatus) {
            case 'running':
                statusText = '监控运行中';
                statusClass = 'text-success';
                icon.className = 'fas fa-circle text-success';
                break;
            case 'stopped':
                statusText = '监控已停止';
                statusClass = 'text-danger';
                icon.className = 'fas fa-circle text-danger';
                break;
            default:
                statusText = '监控状态未知';
                statusClass = 'text-warning';
                icon.className = 'fas fa-circle text-warning';
        }
        
        if (text.textContent) {
            text.textContent = statusText;
        } else {
            statusElement.innerHTML = `<i class="fas fa-circle ${statusClass}"></i> ${statusText}`;
        }
    }

    async startMonitoring() {
        try {
            const response = await fetch('/api/monitor/start', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('监控服务已启动', 'success');
                this.loadMonitorStatus();
            } else {
                this.showNotification(data.message || '启动监控失败', 'error');
            }
        } catch (error) {
            console.error('启动监控失败:', error);
            this.showNotification('启动监控失败', 'error');
        }
    }

    async stopMonitoring() {
        try {
            const response = await fetch('/api/monitor/stop', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('监控服务已停止', 'success');
                this.loadMonitorStatus();
            } else {
                this.showNotification(data.message || '停止监控失败', 'error');
            }
        } catch (error) {
            console.error('停止监控失败:', error);
            this.showNotification('停止监控失败', 'error');
        }
    }

    async checkAlerts() {
        try {
            const response = await fetch('/api/check-alerts', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`检查完成，发现 ${data.count} 个预警`, 'info');
                this.loadAlerts();
            } else {
                this.showNotification('检查预警失败', 'error');
            }
        } catch (error) {
            console.error('检查预警失败:', error);
            this.showNotification('检查预警失败', 'error');
        }
    }

    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('预警已解决', 'success');
                this.loadAlerts();
            } else {
                this.showNotification(data.message || '解决预警失败', 'error');
            }
        } catch (error) {
            console.error('解决预警失败:', error);
            this.showNotification('解决预警失败', 'error');
        }
    }

    async saveRule() {
        const formData = {
            name: document.getElementById('rule-name').value,
            description: document.getElementById('rule-description').value,
            alert_type: document.getElementById('rule-type').value,
            level: document.getElementById('rule-level').value,
            threshold: parseFloat(document.getElementById('rule-threshold').value),
            condition: document.getElementById('rule-condition').value,
            enabled: document.getElementById('rule-enabled').checked,
            check_interval: parseInt(document.getElementById('rule-interval').value),
            cooldown: parseInt(document.getElementById('rule-cooldown').value)
        };

        try {
            const response = await fetch('/api/rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('规则创建成功', 'success');
                this.hideModal('ruleModal');
                this.loadRules();
                this.resetRuleForm();
            } else {
                this.showNotification(data.message || '创建规则失败', 'error');
            }
        } catch (error) {
            console.error('创建规则失败:', error);
            this.showNotification('创建规则失败', 'error');
        }
    }

    async deleteRule(ruleName) {
        if (!confirm(`确定要删除规则 "${ruleName}" 吗？`)) {
            return;
        }

        try {
            const response = await fetch(`/api/rules/${ruleName}`, { method: 'DELETE' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('规则删除成功', 'success');
                this.loadRules();
            } else {
                this.showNotification(data.message || '删除规则失败', 'error');
            }
        } catch (error) {
            console.error('删除规则失败:', error);
            this.showNotification('删除规则失败', 'error');
        }
    }

    filterAndSortAlerts(alerts) {
        // 应用过滤
        const filter = document.getElementById('alert-filter').value;
        let filtered = alerts;
        
        if (filter !== 'all') {
            filtered = alerts.filter(alert => alert.level === filter);
        }
        
        // 应用排序
        const sort = document.getElementById('alert-sort').value;
        filtered.sort((a, b) => {
            switch (sort) {
                case 'time-desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'time-asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'level-desc':
                    const levelOrder = { 'critical': 4, 'error': 3, 'warning': 2, 'info': 1 };
                    return (levelOrder[b.level] || 0) - (levelOrder[a.level] || 0);
                case 'level-asc':
                    const levelOrderAsc = { 'critical': 4, 'error': 3, 'warning': 2, 'info': 1 };
                    return (levelOrderAsc[a.level] || 0) - (levelOrderAsc[b.level] || 0);
                default:
                    return 0;
            }
        });
        
        return filtered;
    }

    editRule(ruleName) {
        // 查找规则数据
        const rule = this.rules.find(r => r.name === ruleName);
        if (!rule) {
            this.showNotification('规则不存在', 'error');
            return;
        }
        
        // 填充编辑表单
        document.getElementById('edit-rule-name-original').value = rule.name;
        document.getElementById('edit-rule-name').value = rule.name;
        document.getElementById('edit-rule-type').value = rule.alert_type;
        document.getElementById('edit-rule-level').value = rule.level;
        document.getElementById('edit-rule-threshold').value = rule.threshold;
        document.getElementById('edit-rule-description').value = rule.description || '';
        document.getElementById('edit-rule-condition').value = rule.condition;
        document.getElementById('edit-rule-interval').value = rule.check_interval;
        document.getElementById('edit-rule-cooldown').value = rule.cooldown;
        document.getElementById('edit-rule-enabled').checked = rule.enabled;
        
        // 显示编辑模态框
        const modal = new bootstrap.Modal(document.getElementById('editRuleModal'));
        modal.show();
    }

    async updateRule() {
        const originalName = document.getElementById('edit-rule-name-original').value;
        const formData = {
            name: document.getElementById('edit-rule-name').value,
            description: document.getElementById('edit-rule-description').value,
            alert_type: document.getElementById('edit-rule-type').value,
            level: document.getElementById('edit-rule-level').value,
            threshold: parseFloat(document.getElementById('edit-rule-threshold').value),
            condition: document.getElementById('edit-rule-condition').value,
            enabled: document.getElementById('edit-rule-enabled').checked,
            check_interval: parseInt(document.getElementById('edit-rule-interval').value),
            cooldown: parseInt(document.getElementById('edit-rule-cooldown').value)
        };

        try {
            const response = await fetch(`/api/rules/${originalName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('规则更新成功', 'success');
                this.hideModal('editRuleModal');
                this.loadRules();
            } else {
                this.showNotification(data.message || '更新规则失败', 'error');
            }
        } catch (error) {
            console.error('更新规则失败:', error);
            this.showNotification('更新规则失败', 'error');
        }
    }

    resetRuleForm() {
        document.getElementById('rule-form').reset();
        document.getElementById('rule-interval').value = '300';
        document.getElementById('rule-cooldown').value = '3600';
        document.getElementById('rule-enabled').checked = true;
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    getLevelText(level) {
        const levelMap = {
            'critical': '严重',
            'error': '错误',
            'warning': '警告',
            'info': '信息'
        };
        return levelMap[level] || level;
    }

    getTypeText(type) {
        const typeMap = {
            'performance': '性能',
            'quality': '质量',
            'volume': '量级',
            'system': '系统',
            'business': '业务'
        };
        return typeMap[type] || type;
    }

    getHealthStatusText(status) {
        const statusMap = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差',
            'critical': '严重',
            'unknown': '未知'
        };
        return statusMap[status] || status;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1分钟内
            return '刚刚';
        } else if (diff < 3600000) { // 1小时内
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) { // 1天内
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleDateString();
        }
    }
}

// 初始化应用
let alertManager;
document.addEventListener('DOMContentLoaded', () => {
    alertManager = new AlertManager();
});
