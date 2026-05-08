/**
 * 重构后的主应用文件
 * 使用模块化架构整合所有功能
 */

// 全局变量声明
let alertManager;
let healthMonitor;
let agentMonitor;

// DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 初始化各个管理器
        alertManager = new AlertManager();
        healthMonitor = new HealthMonitor();
        agentMonitor = new AgentMonitor();

        // 启动自动刷新
        healthMonitor.startMonitoring();

        console.log('AI Helpdesk 应用初始化完成');
    } catch (error) {
        console.error('应用初始化失败:', error);
        notificationManager.error('应用初始化失败，请刷新页面重试');
    }
});

// 健康监控组件
class HealthMonitor {
    constructor() {
        this.interval = null;
    }

    startMonitoring() {
        // 每5秒检查一次健康状态和监控状态
        this.interval = setInterval(async () => {
            try {
                const [healthData, monitorData] = await Promise.all([
                    apiService.getHealth(),
                    apiService.getMonitorStatus()
                ]);

                store.updateHealth(healthData);
                store.updateMonitorStatus(monitorData.monitor_status);
            } catch (error) {
                console.error('健康检查失败:', error);
            }
        }, 5000);
    }

    stopMonitoring() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Agent监控组件
class AgentMonitor {
    constructor() {
        this.interval = null;
        this.init();
    }

    init() {
        // 监听Agent相关按钮
        this.bindAgentControls();
        this.loadAgentStatus();
    }

    bindAgentControls() {
        const toggleBtn = document.getElementById('toggle-agent');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleAgent());
        }
    }

    async loadAgentStatus() {
        try {
            const status = await apiService.getAgentStatus();
            store.updateAgentStatus(status);
            this.updateAgentDisplay();
        } catch (error) {
            console.error('加载Agent状态失败:', error);
        }
    }

    async toggleAgent() {
        try {
            const currentStatus = store.getState().agentStatus;
            const enabled = currentStatus.status === 'inactive';

            const result = await apiService.toggleAgent(enabled);

            if (result.success) {
                notificationManager.success(`Agent已${enabled ? '启用' : '禁用'}`);
                await this.loadAgentStatus();
            } else {
                notificationManager.error(result.message || '操作失败');
            }
        } catch (error) {
            console.error('切换Agent状态失败:', error);
            notificationManager.error('操作失败');
        }
    }

    updateAgentDisplay() {
        const status = store.getState().agentStatus;
        const statusElement = document.getElementById('agent-status');

        if (statusElement) {
            const statusText = status.status === 'active' ? '运行中' : '未运行';
            const statusClass = status.status === 'active' ? 'text-success' : 'text-secondary';

            statusElement.innerHTML = `
                <i class="fas fa-robot me-1 ${statusClass}"></i>
                Agent: ${statusText}
                <small class="text-muted">(${status.active_goals} 个活跃目标, ${status.available_tools} 个工具)</small>
            `;
        }
    }
}

// 导出全局对象供HTML访问
window.alertManager = alertManager;
window.apiService = apiService;
window.store = store;
window.notificationManager = notificationManager;
