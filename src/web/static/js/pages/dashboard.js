/**
 * 仪表板页面组件
 */

import { api } from '../core/api.js';
import { formatDate, formatRelativeTime } from '../core/utils.js';
import store from '../core/store.js';

export default class Dashboard {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.charts = {};
        this.init();
    }

    async init() {
        try {
            this.render();
            await this.loadData();
            this.bindEvents();
        } catch (error) {
            console.error('Dashboard init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-container">
                <div class="page-header">
                    <div>
                        <h1 class="page-title">仪表板</h1>
                        <p class="page-subtitle">系统概览与实时监控</p>
                    </div>
                    <div class="page-actions">
                        <button class="btn btn-primary" id="refresh-dashboard">
                            <i class="fas fa-sync-alt me-2"></i>刷新
                        </button>
                    </div>
                </div>

                <div class="page-content">

            <!-- 统计卡片 -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stat-card success">
                        <div class="stat-content">
                            <div class="stat-number" id="resolved-orders">0</div>
                            <div class="stat-label">今日已解决工单</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card warning">
                        <div class="stat-content">
                            <div class="stat-number" id="pending-orders">0</div>
                            <div class="stat-label">待处理工单</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card info">
                        <div class="stat-content">
                            <div class="stat-number" id="active-alerts">0</div>
                            <div class="stat-label">活跃预警</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="stat-content">
                            <div class="stat-number" id="satisfaction-rate">0%</div>
                            <div class="stat-label">满意度</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 图表区域 -->
            <div class="row mb-4">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">工单趋势</h5>
                            <select class="form-select form-select-sm" id="trend-period" style="width: auto;">
                                <option value="7">最近7天</option>
                                <option value="30" selected>最近30天</option>
                                <option value="90">最近90天</option>
                            </select>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="orders-trend-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">工单分类分布</h5>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="category-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 最新活动 -->
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">最新工单</h5>
                            <a href="/workorders" class="btn btn-sm btn-outline-primary">查看全部</a>
                        </div>
                        <div class="card-body">
                            <div class="list-group list-group-flush" id="recent-workorders">
                                <div class="text-center py-3">
                                    <div class="spinner spinner-sm"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">最新预警</h5>
                            <a href="/alerts" class="btn btn-sm btn-outline-primary">查看全部</a>
                        </div>
                        <div class="card-body">
                            <div class="list-group list-group-flush" id="recent-alerts">
                                <div class="text-center py-3">
                                    <div class="spinner spinner-sm"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            </div>
        `;
    }

    async loadData() {
        try {
            // 加载仪表板数据
            const [analytics, recentWorkorders, recentAlerts, health] = await Promise.all([
                api.monitor.analytics({ days: 30 }),
                api.workorders.list({ page: 1, per_page: 5, sort: 'created_at', order: 'desc' }),
                api.alerts.list({ page: 1, per_page: 5, sort: 'created_at', order: 'desc' }),
                api.system.health()
            ]);

            // 更新统计数据
            this.updateStats(analytics, health);

            // 更新图表
            this.updateCharts(analytics);

            // 更新最新工单列表
            this.updateRecentWorkorders(recentWorkorders.workorders || []);

            // 更新最新预警列表
            this.updateRecentAlerts(recentAlerts.alerts || []);

        } catch (error) {
            console.error('Load dashboard data error:', error);
            this.showError(error);
        }
    }

    updateStats(analytics, health) {
        // 更新统计卡片
        const stats = analytics.data || {};

        document.getElementById('resolved-orders').textContent = stats.resolved_orders || 0;
        document.getElementById('pending-orders').textContent = health.open_workorders || 0;
        document.getElementById('active-alerts').textContent = Object.values(health.active_alerts_by_level || {}).reduce((a, b) => a + b, 0);

        const satisfaction = stats.satisfaction_avg ? (stats.satisfaction_avg * 100).toFixed(1) : 0;
        document.getElementById('satisfaction-rate').textContent = `${satisfaction}%`;
    }

    updateCharts(analytics) {
        const data = analytics.data || {};

        // 更新工单趋势图
        this.updateTrendChart(data.trend || []);

        // 更新分类分布图
        this.updateCategoryChart(data.categories || {});
    }

    updateTrendChart(trendData) {
        const ctx = document.getElementById('orders-trend-chart');
        if (!ctx) return;

        // 销毁旧图表
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.map(item => item.date),
                datasets: [{
                    label: '工单数',
                    data: trendData.map(item => item.count),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateCategoryChart(categoryData) {
        const ctx = document.getElementById('category-chart');
        if (!ctx) return;

        // 销毁旧图表
        if (this.charts.category) {
            this.charts.category.destroy();
        }

        const labels = Object.keys(categoryData);
        const data = Object.values(categoryData);

        this.charts.category = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    updateRecentWorkorders(workorders) {
        const container = document.getElementById('recent-workorders');
        if (!container) return;

        if (!workorders.length) {
            container.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>暂无工单</p>
                </div>
            `;
            return;
        }

        container.innerHTML = workorders.map(workorder => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <a href="/workorders/${workorder.id}" class="text-decoration-none">
                                ${workorder.title}
                            </a>
                        </h6>
                        <small class="text-muted">
                            ${workorder.category || '未分类'} •
                            ${formatRelativeTime(workorder.created_at)}
                        </small>
                    </div>
                    <span class="badge bg-${this.getStatusColor(workorder.status)}">
                        ${this.getStatusText(workorder.status)}
                    </span>
                </div>
            </div>
        `).join('');
    }

    updateRecentAlerts(alerts) {
        const container = document.getElementById('recent-alerts');
        if (!container) return;

        if (!alerts.length) {
            container.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="fas fa-check-circle fa-2x mb-2"></i>
                    <p>暂无预警</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${alert.message}</h6>
                        <small class="text-muted">
                            ${alert.rule_name} •
                            ${formatRelativeTime(alert.created_at)}
                        </small>
                    </div>
                    <span class="badge bg-${this.getLevelColor(alert.level)}">
                        ${alert.level}
                    </span>
                </div>
            </div>
        `).join('');
    }

    getStatusColor(status) {
        const colors = {
            'open': 'danger',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary'
        };
        return colors[status] || 'secondary';
    }

    getStatusText(status) {
        const texts = {
            'open': '待处理',
            'in_progress': '处理中',
            'resolved': '已解决',
            'closed': '已关闭'
        };
        return texts[status] || status;
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
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
            });
        }

        // 趋势周期选择
        const periodSelect = document.getElementById('trend-period');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.changeTrendPeriod(e.target.value);
            });
        }

        // 定时刷新（每5分钟）
        this.refreshTimer = setInterval(() => {
            this.refresh();
        }, 5 * 60 * 1000);
    }

    async refresh() {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
        }

        try {
            await this.loadData();
        } catch (error) {
            console.error('Refresh error:', error);
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                const icon = refreshBtn.querySelector('i');
                icon.classList.remove('fa-spin');
            }
        }
    }

    async changeTrendPeriod(days) {
        try {
            const analytics = await api.monitor.analytics({ days: parseInt(days) });
            this.updateTrendChart(analytics.data?.trend || []);
        } catch (error) {
            console.error('Change trend period error:', error);
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

    destroy() {
        // 清理图表
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });

        // 清理定时器
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }
}