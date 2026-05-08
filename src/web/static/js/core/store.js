/**
 * 全局状态管理
 * 集中管理应用状态，避免状态分散
 */

class Store {
    constructor() {
        this.state = {
            // 预警相关
            alerts: [],
            alertFilters: {
                level: 'all',
                type: 'all',
                status: 'all'
            },
            alertStats: {
                total: 0,
                critical: 0,
                warning: 0,
                info: 0
            },

            // 规则相关
            rules: [],

            // 系统状态
            health: {},
            monitorStatus: 'unknown',

            // Agent相关
            agentStatus: {
                status: 'inactive',
                active_goals: 0,
                available_tools: 0
            },
            agentHistory: [],

            // UI状态
            loading: false,
            notifications: []
        };

        this.listeners = [];
        this.debounceTimers = new Map();
    }

    // 获取状态
    getState() {
        return { ...this.state };
    }

    // 更新状态
    setState(updates) {
        const prevState = { ...this.state };
        this.state = { ...this.state, ...updates };

        // 通知监听器
        this.notifyListeners(prevState, this.state);
    }

    // 订阅状态变化
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    // 通知监听器
    notifyListeners(prevState, newState) {
        this.listeners.forEach(listener => {
            try {
                listener(prevState, newState);
            } catch (error) {
                console.error('状态监听器错误:', error);
            }
        });
    }

    // 防抖更新状态
    setStateDebounced(updates, delay = 300) {
        const key = JSON.stringify(updates);

        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }

        this.debounceTimers.set(key, setTimeout(() => {
            this.setState(updates);
            this.debounceTimers.delete(key);
        }, delay));
    }

    // 预警相关方法
    updateAlerts(alerts) {
        this.setState({ alerts });

        // 更新统计信息
        const stats = {
            total: alerts.length,
            critical: alerts.filter(a => a.level === 'critical').length,
            warning: alerts.filter(a => a.level === 'warning').length,
            info: alerts.filter(a => a.level === 'info').length
        };
        this.setState({ alertStats: stats });
    }

    updateAlertFilters(filters) {
        this.setState({ alertFilters: { ...this.state.alertFilters, ...filters } });
    }

    // 规则相关方法
    updateRules(rules) {
        this.setState({ rules });
    }

    // 系统状态相关方法
    updateHealth(health) {
        this.setState({ health });
    }

    updateMonitorStatus(status) {
        this.setState({ monitorStatus: status });
    }

    // Agent相关方法
    updateAgentStatus(status) {
        this.setState({ agentStatus: status });
    }

    updateAgentHistory(history) {
        this.setState({ agentHistory: history });
    }

    // UI状态相关方法
    setLoading(loading) {
        this.setState({ loading });
    }

    // 通知相关方法
    addNotification(notification) {
        const notifications = [...this.state.notifications, {
            id: Date.now(),
            timestamp: new Date(),
            ...notification
        }];
        this.setState({ notifications });

        // 3秒后自动移除
        setTimeout(() => {
            this.removeNotification(notification.id || notifications[notifications.length - 1].id);
        }, 3000);
    }

    removeNotification(id) {
        const notifications = this.state.notifications.filter(n => n.id !== id);
        this.setState({ notifications });
    }

    // 获取过滤后的预警
    getFilteredAlerts() {
        const { alerts, alertFilters } = this.state;

        return alerts.filter(alert => {
            if (alertFilters.level !== 'all' && alert.level !== alertFilters.level) return false;
            if (alertFilters.type !== 'all' && alert.alert_type !== alertFilters.type) return false;
            if (alertFilters.status !== 'all' && alert.status !== alertFilters.status) return false;
            return true;
        });
    }

    // 获取排序后的预警
    getSortedAlerts(sortBy = 'timestamp', sortOrder = 'desc') {
        const filtered = this.getFilteredAlerts();

        return filtered.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            if (sortBy === 'timestamp') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }

            if (sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }
}

// 创建全局状态管理实例
const store = new Store();