/**
 * 预警管理组件
 * 专门处理预警相关的功能
 */

class AlertManager {
    constructor() {
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
        this.bindButton('start-monitor', () => this.startMonitoring());
        this.bindButton('stop-monitor', () => this.stopMonitoring());
        this.bindButton('check-alerts', () => this.checkAlerts());
        this.bindButton('refresh-alerts', () => this.loadAlerts());

        // 预警过滤和排序
        this.bindSelect('alert-filter', () => this.updateAlertsDisplay());
        this.bindSelect('alert-sort', () => this.updateAlertsDisplay());
    }

    bindButton(id, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('click', handler);
        }
    }

    bindSelect(id, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', handler);
        }
    }

    async loadInitialData() {
        store.setLoading(true);
        try {
            await Promise.all([
                this.loadAlerts(),
                this.loadRules(),
                this.loadMonitorStatus()
            ]);
        } catch (error) {
            console.error('加载初始数据失败:', error);
            notificationManager.error('加载数据失败，请刷新页面重试');
        } finally {
            store.setLoading(false);
        }
    }

    startAutoRefresh() {
        // 清除现有定时器
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        // 每10秒刷新一次预警
        this.refreshInterval = setInterval(() => {
            this.loadAlerts();
        }, 10000);
    }

    // 监控控制方法
    async startMonitoring() {
        try {
            store.setLoading(true);
            const result = await apiService.startMonitoring();

            if (result.success) {
                notificationManager.success('监控已启动');
                await this.loadMonitorStatus();
            } else {
                notificationManager.error(result.message || '启动监控失败');
            }
        } catch (error) {
            console.error('启动监控失败:', error);
            notificationManager.error('启动监控失败');
        } finally {
            store.setLoading(false);
        }
    }

    async stopMonitoring() {
        try {
            store.setLoading(true);
            const result = await apiService.stopMonitoring();

            if (result.success) {
                notificationManager.success('监控已停止');
                await this.loadMonitorStatus();
            } else {
                notificationManager.error(result.message || '停止监控失败');
            }
        } catch (error) {
            console.error('停止监控失败:', error);
            notificationManager.error('停止监控失败');
        } finally {
            store.setLoading(false);
        }
    }

    async checkAlerts() {
        try {
            store.setLoading(true);
            await this.loadAlerts();
            notificationManager.success('预警检查完成');
        } catch (error) {
            console.error('检查预警失败:', error);
            notificationManager.error('检查预警失败');
        } finally {
            store.setLoading(false);
        }
    }

    // 数据加载方法
    async loadAlerts() {
        try {
            const data = await apiService.getAlerts();
            store.updateAlerts(data);
            this.updateAlertsDisplay();
        } catch (error) {
            console.error('加载预警失败:', error);
        }
    }

    async loadRules() {
        try {
            const data = await apiService.getRules();
            store.updateRules(data);
            this.updateRulesDisplay();
        } catch (error) {
            console.error('加载规则失败:', error);
        }
    }

    async loadMonitorStatus() {
        try {
            const data = await apiService.getMonitorStatus();
            store.updateMonitorStatus(data.monitor_status);
            this.updateMonitorStatusDisplay();
        } catch (error) {
            console.error('加载监控状态失败:', error);
        }
    }

    // 显示更新方法
    updateAlertsDisplay() {
        const alerts = store.getSortedAlerts('timestamp', 'desc');
        const container = document.getElementById('alerts-container');

        if (!container) return;

        if (alerts.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-4"><i class="fas fa-info-circle fa-2x mb-2"></i><br>暂无预警</div>';
            return;
        }

        container.innerHTML = alerts.map(alert => this.createAlertElement(alert)).join('');
    }

    createAlertElement(alert) {
        const levelClass = this.getLevelClass(alert.level);
        const typeText = this.getTypeText(alert.alert_type);
        const levelText = this.getLevelText(alert.level);
        const timeText = this.formatTime(alert.timestamp);

        return `
            <div class="alert-item card mb-2 border-${levelClass}">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <span class="badge bg-${levelClass} me-2">${levelText}</span>
                                <span class="badge bg-secondary">${typeText}</span>
                                <small class="text-muted ms-2">${timeText}</small>
                            </div>
                            <h6 class="card-title mb-1">${alert.title}</h6>
                            <p class="card-text small text-muted mb-2">${alert.description}</p>
                            <div class="alert-actions">
                                <button class="btn btn-sm btn-outline-primary me-1" onclick="alertManager.acknowledgeAlert('${alert.id}')">
                                    <i class="fas fa-check"></i> 确认
                                </button>
                                <button class="btn btn-sm btn-outline-info" onclick="alertManager.viewAlertDetail('${alert.id}')">
                                    <i class="fas fa-eye"></i> 详情
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updateRulesDisplay() {
        const rules = store.getState().rules;
        const container = document.getElementById('rules-container');

        if (!container) return;

        if (rules.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-4"><i class="fas fa-list fa-2x mb-2"></i><br>暂无规则</div>';
            return;
        }

        container.innerHTML = rules.map(rule => this.createRuleElement(rule)).join('');
    }

    createRuleElement(rule) {
        const enabledText = rule.enabled ? '<span class="badge bg-success">启用</span>' : '<span class="badge bg-secondary">禁用</span>';

        return `
            <tr>
                <td>${rule.name}</td>
                <td>${rule.alert_type}</td>
                <td>${rule.level}</td>
                <td>${rule.threshold}</td>
                <td>${enabledText}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="alertManager.editRule('${rule.name}')">
                        <i class="fas fa-edit"></i> 编辑
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="alertManager.deleteRule('${rule.name}')">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `;
    }

    updateMonitorStatusDisplay() {
        const status = store.getState().monitorStatus;
        const element = document.getElementById('monitor-status');

        if (!element) return;

        const statusConfig = {
            'running': { icon: 'text-success', text: '运行中' },
            'stopped': { icon: 'text-danger', text: '已停止' },
            'unknown': { icon: 'text-warning', text: '未知' }
        };

        const config = statusConfig[status] || statusConfig.unknown;

        element.innerHTML = `
            <i class="fas fa-circle ${config.icon}"></i> 监控状态: ${config.text}
        `;
    }

    // 工具方法
    getLevelClass(level) {
        const levelMap = {
            'critical': 'danger',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return levelMap[level] || 'secondary';
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

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
        return date.toLocaleDateString();
    }

    // 预警操作方法
    async acknowledgeAlert(alertId) {
        try {
            await apiService.updateAlert(alertId, { acknowledged: true });
            notificationManager.success('预警已确认');
            await this.loadAlerts();
        } catch (error) {
            console.error('确认预警失败:', error);
            notificationManager.error('确认预警失败');
        }
    }

    viewAlertDetail(alertId) {
        // 这里可以实现查看详情的逻辑
        notificationManager.info('详情查看功能开发中');
    }

    // 规则操作方法
    editRule(ruleName) {
        const rule = store.getState().rules.find(r => r.name === ruleName);
        if (!rule) {
            notificationManager.error('规则不存在');
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

    async deleteRule(ruleName) {
        if (!confirm(`确定要删除规则 "${ruleName}" 吗？`)) return;

        try {
            await apiService.deleteRule(ruleName);
            notificationManager.success('规则删除成功');
            await this.loadRules();
        } catch (error) {
            console.error('删除规则失败:', error);
            notificationManager.error('删除规则失败');
        }
    }
}
