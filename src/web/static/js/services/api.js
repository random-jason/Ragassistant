/**
 * 统一API服务
 * 提供所有API调用的统一接口
 */

class ApiService {
    constructor() {
        this.baseURL = '';
        this.defaultTimeout = 30000; // 30秒超时
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: options.timeout || this.defaultTimeout,
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error(`API请求失败: ${endpoint}`, error);
            throw error;
        }
    }

    // 健康检查相关
    async getHealth() {
        return this.request('/api/health');
    }

    // 预警相关
    async getAlerts() {
        return this.request('/api/alerts');
    }

    async createAlert(alertData) {
        return this.request('/api/alerts', {
            method: 'POST',
            body: JSON.stringify(alertData)
        });
    }

    async updateAlert(alertId, alertData) {
        return this.request(`/api/alerts/${alertId}`, {
            method: 'PUT',
            body: JSON.stringify(alertData)
        });
    }

    async deleteAlert(alertId) {
        return this.request(`/api/alerts/${alertId}`, {
            method: 'DELETE'
        });
    }

    // 规则相关
    async getRules() {
        return this.request('/api/rules');
    }

    async createRule(ruleData) {
        return this.request('/api/rules', {
            method: 'POST',
            body: JSON.stringify(ruleData)
        });
    }

    async updateRule(ruleId, ruleData) {
        return this.request(`/api/rules/${ruleId}`, {
            method: 'PUT',
            body: JSON.stringify(ruleData)
        });
    }

    async deleteRule(ruleId) {
        return this.request(`/api/rules/${ruleId}`, {
            method: 'DELETE'
        });
    }

    // 监控相关
    async getMonitorStatus() {
        return this.request('/api/monitor/status');
    }

    async startMonitoring() {
        return this.request('/api/monitor/start', {
            method: 'POST'
        });
    }

    async stopMonitoring() {
        return this.request('/api/monitor/stop', {
            method: 'POST'
        });
    }

    // Agent相关
    async getAgentStatus() {
        return this.request('/api/agent/status');
    }

    async toggleAgent(enabled) {
        return this.request('/api/agent/toggle', {
            method: 'POST',
            body: JSON.stringify({ enabled })
        });
    }

    async getAgentHistory(limit = 50) {
        return this.request(`/api/agent/action-history?limit=${limit}`);
    }

    // 对话相关
    async createChatSession(data) {
        return this.request('/api/chat/session', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async sendChatMessage(data) {
        return this.request('/api/chat/message', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getChatHistory(sessionId) {
        return this.request(`/api/chat/history/${sessionId}`);
    }
}

// 创建全局API服务实例
const apiService = new ApiService();
