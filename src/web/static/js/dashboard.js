// AI Helpdesk 综合管理平台前端脚本

// 多语言支持
const translations = {
    zh: {
        // 导航栏
        'nav-title': 'AI Helpdesk',
        'nav-health-checking': '检查中...',
        'nav-health-normal': '系统正常',
        'nav-health-warning': '系统警告',
        'nav-health-error': '系统错误',
        
        // 侧边栏
        'sidebar-dashboard': '仪表板',
        'sidebar-workorders': '工单管理',
        'sidebar-conversations': '智能对话',
        'sidebar-agent': 'Agent管理',
        'sidebar-alerts': '预警管理',
        'sidebar-knowledge': '知识库',
        'sidebar-analytics': '数据分析',
        'sidebar-feishu-sync': '飞书同步',
        'sidebar-conversation-history': '对话历史',
        'sidebar-token-monitor': 'Token监控',
        'sidebar-ai-monitor': 'AI监控',
        'sidebar-system-optimizer': '系统优化',
        'sidebar-system': '系统设置',
        
        // 预警管理页面
        'alerts-critical': '严重预警',
        'alerts-warning': '警告预警',
        'alerts-info': '信息预警',
        'alerts-total': '总预警数',
        'alerts-active': '活跃预警',
        'alerts-resolve': '解决',
        
        // 设置页面
        'settings-title': '系统设置',
        'settings-basic': '基础设置',
        'settings-system-info': '系统信息',
        'settings-log-config': '日志配置',
        'settings-current-port': '当前服务端口',
        'settings-websocket-port': 'WebSocket端口',
        'settings-log-level': '日志级别',
        'settings-save': '保存设置',
        'settings-save-success': '设置保存成功',
        'settings-save-failed': '保存设置失败',
        'settings-port-note': '服务端口配置需要在配置文件中修改，前端页面仅显示当前状态。',
        'settings-log-note': '调整系统日志的详细程度'
    },
    en: {
        // Navigation
        'nav-title': 'AI Helpdesk',
        'nav-health-checking': 'Checking...',
        'nav-health-normal': 'System Normal',
        'nav-health-warning': 'System Warning',
        'nav-health-error': 'System Error',
        
        // Sidebar
        'sidebar-dashboard': 'Dashboard',
        'sidebar-workorders': 'Work Orders',
        'sidebar-conversations': 'Smart Chat',
        'sidebar-agent': 'Agent Management',
        'sidebar-alerts': 'Alert Management',
        'sidebar-knowledge': 'Knowledge Base',
        'sidebar-analytics': 'Analytics',
        'sidebar-feishu-sync': 'Feishu Sync',
        'sidebar-conversation-history': 'Conversation History',
        'sidebar-token-monitor': 'Token Monitor',
        'sidebar-ai-monitor': 'AI Monitor',
        'sidebar-system-optimizer': 'System Optimizer',
        'sidebar-system': 'System Settings',
        
        // Alert Management page
        'alerts-critical': 'Critical Alerts',
        'alerts-warning': 'Warning Alerts',
        'alerts-info': 'Info Alerts',
        'alerts-total': 'Total Alerts',
        'alerts-active': 'Active Alerts',
        'alerts-resolve': 'Resolve',
        
        // Settings page
        'settings-title': 'System Settings',
        'settings-basic': 'Basic Settings',
        'settings-system-info': 'System Information',
        'settings-log-config': 'Log Configuration',
        'settings-current-port': 'Current Service Port',
        'settings-websocket-port': 'WebSocket Port',
        'settings-log-level': 'Log Level',
        'settings-save': 'Save Settings',
        'settings-save-success': 'Settings saved successfully',
        'settings-save-failed': 'Failed to save settings',
        'settings-port-note': 'Service port configuration needs to be modified in configuration files. Frontend only displays current status.',
        'settings-log-note': 'Adjust the detail level of system logs'
    }
};

// 全局语言切换函数
function switchLanguage(lang) {
    localStorage.setItem('preferred-language', lang);
    document.documentElement.lang = lang;
    
    // 更新按钮状态
    document.getElementById('lang-zh').classList.toggle('active', lang === 'zh');
    document.getElementById('lang-en').classList.toggle('active', lang === 'en');
    
    // 更新页面文本
    updatePageLanguage(lang);
}

// 更新页面语言
function updatePageLanguage(lang) {
    const t = translations[lang];
    if (!t) return;
    
    // 更新所有带有 data-i18n 属性的元素
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (t[key]) {
            // 检查元素是否包含图标（i标签）
            const icon = element.querySelector('i');
            if (icon) {
                // 如果包含图标，只更新文本部分
                const textNodes = Array.from(element.childNodes).filter(node => 
                    node.nodeType === Node.TEXT_NODE || (node.nodeType === Node.ELEMENT_NODE && node.tagName !== 'I')
                );
                // 保留图标，更新其他文本内容
                element.innerHTML = icon.outerHTML + ' ' + t[key];
            } else {
                // 如果没有图标，直接更新文本内容
                element.textContent = t[key];
            }
        }
    });
    
    // 更新导航栏标题（特殊处理，因为包含图标）
    const navBrand = document.querySelector('.navbar-brand');
    if (navBrand) {
        const icon = navBrand.querySelector('i');
        if (icon) {
            navBrand.innerHTML = `<i class="fas fa-robot me-2"></i>${t['nav-title']}`;
        }
    }
    
    // 更新当前标签页标题
    const currentTabTitle = document.getElementById('current-tab-title');
    if (currentTabTitle) {
        const currentTab = document.querySelector('.nav-link.active');
        if (currentTab) {
            const tabKey = currentTab.getAttribute('data-i18n');
            if (tabKey && t[tabKey]) {
                // 检查当前标签是否包含图标
                const icon = currentTab.querySelector('i');
                if (icon) {
                    currentTabTitle.innerHTML = icon.outerHTML + ' ' + t[tabKey];
                } else {
                    currentTabTitle.textContent = t[tabKey];
                }
            }
        }
    }
}

class HelpdeskDashboard {
    constructor() {
        this.currentTab = 'dashboard';
        this.charts = {};
        this.refreshIntervals = {};
        this.websocket = null;
        this.sessionId = null;
        this.isAgentMode = true;
        this.currentLanguage = localStorage.getItem('preferred-language') || 'zh';
        
        // 优化：添加前端缓存
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30秒缓存
        
        // 智能更新机制
        this.lastUpdateTimes = {
            alerts: 0,
            workorders: 0,
            health: 0,
            analytics: 0
        };
        
        this.updateThresholds = {
            alerts: 10000,      // 10秒
            workorders: 30000,  // 30秒
            health: 30000,     // 30秒
            analytics: 60000   // 60秒
        };
        
        this.isPageVisible = true;
        
        // 分页配置
        this.paginationConfig = {
            defaultPageSize: 10,
            pageSizeOptions: [5, 10, 20, 50],
            maxVisiblePages: 5
        };
        
        this.init();
        this.restorePageState();
        this.initLanguage();
        this.initSmartUpdate();
        
        // 添加页面卸载时的清理逻辑
        window.addEventListener('beforeunload', () => {
            this.destroyAllCharts();
            this.cleanupConnections();
        });
    }
    
    initLanguage() {
        // 初始化语言设置
        document.documentElement.lang = this.currentLanguage;
        document.getElementById('lang-zh').classList.toggle('active', this.currentLanguage === 'zh');
        document.getElementById('lang-en').classList.toggle('active', this.currentLanguage === 'en');
        updatePageLanguage(this.currentLanguage);
    }

    async generateAISuggestion(workorderId) {
        const button = document.querySelector(`button[onclick="dashboard.generateAISuggestion(${workorderId})"]`);
        const textarea = document.getElementById(`aiSuggestion_${workorderId}`);
        
        try {
            // 添加加载状态
            if (button) {
                button.classList.add('btn-loading');
                button.disabled = true;
            }
            if (textarea) {
                textarea.classList.add('ai-loading');
                textarea.value = '正在生成AI建议，请稍候...';
            }
            
            const resp = await fetch(`/api/workorders/${workorderId}/ai-suggestion`, { method: 'POST' });
            const data = await resp.json();
            
            if (data.success) {
                if (textarea) {
                    textarea.value = data.suggestion || '';
                    textarea.classList.remove('ai-loading');
                    textarea.classList.add('success-animation');
                    
                    // 移除成功动画类
                    setTimeout(() => {
                        textarea.classList.remove('success-animation');
                    }, 600);
                }
                this.showNotification('AI建议已生成', 'success');
            } else {
                throw new Error(data.error || '生成失败');
            }
        } catch (e) {
            console.error('生成AI建议失败:', e);
            if (textarea) {
                textarea.value = 'AI建议生成失败，请重试';
                textarea.classList.remove('ai-loading');
            }
            this.showNotification('生成AI建议失败: ' + e.message, 'error');
        } finally {
            // 移除加载状态
            if (button) {
                button.classList.remove('btn-loading');
                button.disabled = false;
            }
        }
    }

    async saveHumanResolution(workorderId) {
        try {
            const text = document.getElementById(`humanResolution_${workorderId}`).value.trim();
            if (!text) { this.showNotification('请输入人工描述', 'warning'); return; }
            const resp = await fetch(`/api/workorders/${workorderId}/human-resolution`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ human_resolution: text })
            });
            const data = await resp.json();
            if (data.success) {
                const simEl = document.getElementById(`aiSim_${workorderId}`);
                const apprEl = document.getElementById(`aiApproved_${workorderId}`);
                const approveBtn = document.getElementById(`approveBtn_${workorderId}`);
                const percent = Math.round((data.similarity || 0) * 100);
                
                // 更新相似度显示，使用语义相似度
                if (simEl) { 
                    simEl.innerHTML = `<i class="fas fa-percentage"></i>语义相似度: ${percent}%`; 
                    
                    // 使用新的CSS类
                    if (percent >= 90) {
                        simEl.className = 'similarity-badge high';
                    } else if (percent >= 80) {
                        simEl.className = 'similarity-badge medium';
                    } else {
                        simEl.className = 'similarity-badge low';
                    }
                    
                    simEl.title = this.getSimilarityExplanation(percent);
                }
                
                // 更新审批状态
                if (apprEl) { 
                    if (data.use_human_resolution) {
                        apprEl.textContent = '将使用人工描述入库';
                        apprEl.className = 'status-badge human-resolution';
                    } else if (data.approved) {
                        apprEl.textContent = '已自动审批';
                        apprEl.className = 'status-badge approved';
                    } else {
                        apprEl.textContent = '未审批';
                        apprEl.className = 'status-badge pending';
                    }
                }
                
                // 更新审批按钮状态
                if (approveBtn) {
                    const canApprove = data.approved || data.use_human_resolution;
                    approveBtn.disabled = !canApprove;
                    
                    if (data.use_human_resolution) {
                        approveBtn.textContent = '使用人工描述入库';
                        approveBtn.className = 'approve-btn';
                        approveBtn.title = 'AI准确率低于90%，将使用人工描述入库';
                    } else if (data.approved) {
                        approveBtn.textContent = '已自动审批';
                        approveBtn.className = 'approve-btn approved';
                        approveBtn.title = 'AI建议与人工描述高度一致';
                    } else {
                        approveBtn.textContent = '审批入库';
                        approveBtn.className = 'approve-btn';
                        approveBtn.title = '手动审批入库';
                    }
                }
                
                // 显示更详细的反馈信息
                const message = this.getSimilarityMessage(percent, data.approved, data.use_human_resolution);
                this.showNotification(message, data.approved ? 'success' : data.use_human_resolution ? 'warning' : 'info');
            } else {
                throw new Error(data.error || '保存失败');
            }
        } catch (e) {
            console.error('保存人工描述失败:', e);
            this.showNotification('保存人工描述失败: ' + e.message, 'error');
        }
    }

    async approveToKnowledge(workorderId) {
        try {
            const resp = await fetch(`/api/workorders/${workorderId}/approve-to-knowledge`, { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                const contentType = data.used_content === 'human_resolution' ? '人工描述' : 'AI建议';
                const confidence = Math.round((data.confidence_score || 0) * 100);
                this.showNotification(`已入库为知识条目！使用${contentType}，置信度: ${confidence}%`, 'success');
            } else {
                throw new Error(data.error || '入库失败');
            }
        } catch (e) {
            console.error('入库失败:', e);
            this.showNotification('入库失败: ' + e.message, 'error');
        }
    }
    init() {
        this.bindEvents();
        // 优化：并行加载初始数据，提高响应速度
        this.loadInitialDataAsync();
        this.startAutoRefresh();
        this.initCharts();
    }
    
    async loadInitialDataAsync() {
        // 并行加载多个数据源
        try {
            await Promise.all([
                this.loadDashboard(),
                this.loadWorkOrders(),
                this.loadConversationHistory(),
                this.loadKnowledgeBase()
            ]);
        } catch (error) {
            console.error('并行加载数据失败:', error);
            // 回退到串行加载
            await this.loadInitialData();
        }
    }
    
    // 优化：添加缓存方法
    getCachedData(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    // 统一分页组件
    createPaginationComponent(data, containerId, loadFunction, itemName = '条记录') {
        const paginationContainer = document.getElementById(containerId);
        if (!paginationContainer) return;
        
        // 调试信息
        console.log(`分页数据 (${containerId}):`, data);
        
        const { page, total_pages, total, per_page } = data;
        
        // 检查必要字段
        if (page === undefined || total_pages === undefined || total === undefined || per_page === undefined) {
            console.error(`分页数据不完整 (${containerId}):`, { page, total_pages, total, per_page });
            paginationContainer.innerHTML = '<div class="text-tertiary text-sm">分页数据加载中...</div>';
            return;
        }
        
        if (total_pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHtml = `
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <span class="text-secondary text-sm me-3">共 ${total} ${itemName}，第 ${page} / ${total_pages} 页</span>
                    <div class="d-flex align-items-center">
                        <label class="form-label text-sm font-medium me-2 mb-0">每页显示:</label>
                        <select class="form-select form-select-sm text-sm" style="width: auto;" onchange="dashboard.changePageSize('${containerId}', this.value, '${loadFunction}')">
        `;
        
        // 每页显示条数选择器
        this.paginationConfig.pageSizeOptions.forEach(size => {
            const selected = size === per_page ? 'selected' : '';
            paginationHtml += `<option value="${size}" ${selected}>${size}</option>`;
        });
        
        paginationHtml += `
                        </select>
                    </div>
                </div>
                <nav>
                    <ul class="pagination pagination-sm mb-0">
        `;
        
        // 上一页
        if (page > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="dashboard.loadPage('${loadFunction}', ${page - 1}, '${containerId}')">上一页</a></li>`;
        }
        
        // 页码
        const startPage = Math.max(1, page - Math.floor(this.paginationConfig.maxVisiblePages / 2));
        const endPage = Math.min(total_pages, startPage + this.paginationConfig.maxVisiblePages - 1);
        
        // 如果开始页码大于1，显示第一页和省略号
        if (startPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="dashboard.loadPage('${loadFunction}', 1, '${containerId}')">1</a></li>`;
            if (startPage > 2) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        // 显示页码范围
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === page ? 'active' : '';
            paginationHtml += `<li class="page-item ${activeClass}"><a class="page-link" href="#" onclick="dashboard.loadPage('${loadFunction}', ${i}, '${containerId}')">${i}</a></li>`;
        }
        
        // 如果结束页码小于总页数，显示省略号和最后一页
        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="dashboard.loadPage('${loadFunction}', ${total_pages}, '${containerId}')">${total_pages}</a></li>`;
        }
        
        // 下一页
        if (page < total_pages) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="dashboard.loadPage('${loadFunction}', ${page + 1}, '${containerId}')">下一页</a></li>`;
        }
        
        paginationHtml += `
                    </ul>
                </nav>
            </div>
        `;
        
        paginationContainer.innerHTML = paginationHtml;
    }

    // 加载指定页面
    loadPage(loadFunction, page, containerId) {
        const pageSize = this.getPageSize(containerId);
        if (loadFunction === 'loadAlerts') {
            this.loadAlerts(page, true);
        } else if (loadFunction === 'loadWorkOrders') {
            this.loadWorkOrders(page, true);
        } else if (loadFunction === 'loadKnowledge') {
            this.loadKnowledge(page);
        } else if (loadFunction === 'loadConversationHistory') {
            this.loadConversationHistory(page);
        }
    }

    // 改变每页显示条数
    changePageSize(containerId, pageSize, loadFunction) {
        // 保存页面大小到localStorage
        localStorage.setItem(`pageSize_${containerId}`, pageSize);
        
        // 重新加载第一页
        if (loadFunction === 'loadAlerts') {
            this.loadAlerts(1, true);
        } else if (loadFunction === 'loadWorkOrders') {
            this.loadWorkOrders(1, true);
        } else if (loadFunction === 'loadKnowledge') {
            this.loadKnowledge(1);
        } else if (loadFunction === 'loadConversationHistory') {
            this.loadConversationHistory(1);
        }
    }

    // 获取页面大小
    getPageSize(containerId) {
        const saved = localStorage.getItem(`pageSize_${containerId}`);
        return saved ? parseInt(saved) : this.paginationConfig.defaultPageSize;
    }
    
    setCachedData(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    clearCache() {
        this.cache.clear();
    }

    bindEvents() {
        // 标签页切换
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });

        // 对话控制
        document.getElementById('start-chat').addEventListener('click', () => this.startChat());
        document.getElementById('end-chat').addEventListener('click', () => this.endChat());
        document.getElementById('create-work-order').addEventListener('click', () => this.showCreateWorkOrderModal());
        document.getElementById('send-button').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // 快速操作按钮
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.dataset.message;
                document.getElementById('message-input').value = message;
                this.sendMessage();
            });
        });

        // Agent控制
        document.getElementById('agent-mode-toggle').addEventListener('change', (e) => {
            this.toggleAgentMode(e.target.checked);
        });

        // Agent对话功能
        document.getElementById('send-agent-message').addEventListener('click', () => this.sendAgentMessage());
        document.getElementById('clear-agent-chat').addEventListener('click', () => this.clearAgentChat());
        document.getElementById('agent-message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendAgentMessage();
            }
        });

        // Agent控制按钮
        document.getElementById('trigger-sample-action').addEventListener('click', () => this.triggerSampleAction());
        document.getElementById('clear-agent-history').addEventListener('click', () => this.clearAgentHistory());
        document.getElementById('start-agent-monitoring').addEventListener('click', () => this.startAgentMonitoring());
        document.getElementById('stop-agent-monitoring').addEventListener('click', () => this.stopAgentMonitoring());
        document.getElementById('proactive-monitoring').addEventListener('click', () => this.proactiveMonitoring());
        document.getElementById('intelligent-analysis').addEventListener('click', () => this.intelligentAnalysis());

        // 预警管理
        document.getElementById('refresh-alerts').addEventListener('click', () => this.loadAlerts());
        document.getElementById('alert-filter').addEventListener('change', () => this.updateAlertsDisplay());

        // 统计数字点击事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clickable-stat')) {
                const type = e.target.dataset.type;
                const status = e.target.dataset.status || e.target.dataset.level;
                this.showStatPreview(type, status);
            }
        });

        // 知识库管理
        document.getElementById('search-knowledge').addEventListener('click', () => this.searchKnowledge());
        document.getElementById('knowledge-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchKnowledge();
        });

        // 工单管理
        document.getElementById('refresh-workorders').addEventListener('click', () => this.loadWorkOrders());
        document.getElementById('workorder-status-filter').addEventListener('change', () => this.loadWorkOrders());
        document.getElementById('workorder-priority-filter').addEventListener('change', () => this.loadWorkOrders());

        // 模态框
        document.getElementById('create-work-order-btn').addEventListener('click', () => this.createWorkOrder());
        document.getElementById('add-knowledge-btn').addEventListener('click', () => this.addKnowledge());
        document.getElementById('upload-file-btn').addEventListener('click', () => this.uploadFile());

        // 置信度滑块
        document.getElementById('knowledge-confidence').addEventListener('input', (e) => {
            document.getElementById('confidence-value').textContent = e.target.value;
        });
        document.getElementById('file-confidence').addEventListener('input', (e) => {
            document.getElementById('file-confidence-value').textContent = e.target.value;
        });

        // 处理方式选择
        document.getElementById('process-method').addEventListener('change', (e) => {
            const manualDiv = document.getElementById('manual-question-div');
            if (e.target.value === 'manual') {
                manualDiv.style.display = 'block';
            } else {
                manualDiv.style.display = 'none';
            }
        });

        // 系统设置
        document.getElementById('system-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSystemSettings();
        });

        // API测试按钮事件
        const testApiBtn = document.getElementById('test-api-connection');
        if (testApiBtn) {
            testApiBtn.addEventListener('click', () => this.testApiConnection());
        }
        
        const testModelBtn = document.getElementById('test-model-response');
        if (testModelBtn) {
            testModelBtn.addEventListener('click', () => this.testModelResponse());
        }
        
        // 重启服务按钮事件
        const restartBtn = document.getElementById('restart-service');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                if (confirm('确定要重启服务吗？这将中断当前连接。')) {
                    this.showNotification('重启服务功能待实现', 'info');
                }
            });
        }
    }

    switchTab(tabName) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 显示对应内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });
        document.getElementById(`${tabName}-tab`).style.display = 'block';

        this.currentTab = tabName;
        
        // 如果切换到分析页面，重新初始化图表
        if (tabName === 'analytics') {
            // 延迟一点时间确保DOM已更新
            setTimeout(() => {
                this.initializeCharts();
            }, 100);
        }
        
        // 保存当前页面状态
        this.savePageState();

        // 加载对应数据
        switch(tabName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'chat':
                this.loadChatData();
                break;
            case 'agent':
                this.loadAgentData();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
            case 'knowledge':
                this.loadKnowledge();
                break;
            case 'workorders':
                this.loadWorkOrders();
                break;
            case 'conversation-history':
                this.loadConversationHistory();
                break;
            case 'token-monitor':
                this.loadTokenMonitor();
                break;
            case 'ai-monitor':
                this.loadAIMonitor();
                break;
            case 'system-optimizer':
                this.loadSystemOptimizer();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    savePageState() {
        const state = {
            currentTab: this.currentTab,
            timestamp: Date.now()
        };
        localStorage.setItem('helpdesk_dashboard_state', JSON.stringify(state));
    }

    restorePageState() {
        try {
            const savedState = localStorage.getItem('helpdesk_dashboard_state');
            if (savedState) {
                const state = JSON.parse(savedState);
                // 如果状态保存时间不超过1小时，则恢复
                if (Date.now() - state.timestamp < 3600000) {
                    this.switchTab(state.currentTab);
                }
            }
        } catch (error) {
            console.warn('恢复页面状态失败:', error);
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadHealth(),
            this.loadDashboardData(),
            this.loadSystemInfo()
        ]);
    }

    // 初始化智能更新机制
    initSmartUpdate() {
        // 页面可见性检测
        document.addEventListener('visibilitychange', () => {
            this.isPageVisible = !document.hidden;
            if (this.isPageVisible) {
                // 页面重新可见时，立即更新数据
                this.smartRefresh();
            }
        });

        // 尝试连接WebSocket获取实时更新
        this.initWebSocketConnection();

        // 智能定时刷新
        this.startSmartRefresh();
    }

    // 初始化WebSocket连接
    initWebSocketConnection() {
        try {
            const wsUrl = `ws://localhost:8765/dashboard`;
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                // 发送订阅消息
                this.websocket.send(JSON.stringify({
                    type: 'subscribe',
                    topics: ['alerts', 'workorders', 'health']
                }));
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleRealtimeUpdate(data);
                } catch (error) {
                    console.error('WebSocket消息解析失败:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket连接已关闭');
                // 5秒后重连
                setTimeout(() => {
                    if (this.isPageVisible) {
                        this.initWebSocketConnection();
                    }
                }, 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket连接错误:', error);
            };
        } catch (error) {
            console.log('WebSocket连接失败，使用轮询模式:', error);
        }
    }

    // 处理实时更新
    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'alert_update':
                // 直接更新预警统计，无需API调用
                this.updateAlertStatistics(data.alerts);
                this.lastUpdateTimes.alerts = Date.now();
                break;
            case 'workorder_update':
                // 更新工单统计
                if (this.currentTab === 'workorders') {
                    this.loadWorkOrders();
                }
                this.lastUpdateTimes.workorders = Date.now();
                break;
            case 'health_update':
                // 更新健康状态
                this.updateHealthDisplay(data.health);
                this.lastUpdateTimes.health = Date.now();
                break;
        }
    }

    // 智能刷新机制
    startSmartRefresh() {
        // 每5秒检查一次是否需要更新
        this.refreshIntervals.smart = setInterval(() => {
            if (this.isPageVisible) {
                this.smartRefresh();
            }
        }, 5000);
    }

    // 智能刷新逻辑
    smartRefresh() {
        const now = Date.now();
        
        // 如果最近有用户操作，跳过自动更新
        if (now - this.lastUpdateTimes.alerts < 5000) { // 5秒内不自动更新
            return;
        }
        
        // 检查预警数据是否需要更新
        if (now - this.lastUpdateTimes.alerts > this.updateThresholds.alerts) {
            this.refreshAlertStats();
            this.lastUpdateTimes.alerts = now;
        }
        
        // 检查健康状态是否需要更新
        if (now - this.lastUpdateTimes.health > this.updateThresholds.health) {
            this.loadHealth();
            this.lastUpdateTimes.health = now;
        }
        
        // 检查分析数据是否需要更新
        if (now - this.lastUpdateTimes.analytics > this.updateThresholds.analytics) {
            this.loadAnalytics();
            this.lastUpdateTimes.analytics = now;
        }
        
        // 根据当前标签页决定是否更新工单数据
        if (this.currentTab === 'workorders' && 
            now - this.lastUpdateTimes.workorders > this.updateThresholds.workorders) {
            this.loadWorkOrders();
            this.lastUpdateTimes.workorders = now;
        }
    }

    startAutoRefresh() {
        // 保留原有的刷新机制作为备用
        this.refreshIntervals.health = setInterval(() => {
            if (this.isPageVisible) {
                this.loadHealth();
            }
        }, 30000);

        this.refreshIntervals.currentTab = setInterval(() => {
            if (this.isPageVisible) {
                this.refreshCurrentTab();
            }
        }, 30000);
    }

    refreshCurrentTab() {
        switch(this.currentTab) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
            case 'agent':
                this.loadAgentData();
                break;
        }
    }

    // 刷新预警统计（优化版）
    async refreshAlertStats() {
        try {
            // 检查缓存
            const cacheKey = 'alerts_stats';
            const cachedData = this.cache.get(cacheKey);
            const now = Date.now();
            
            if (cachedData && (now - cachedData.timestamp) < this.cacheTimeout) {
                // 使用缓存数据
                this.updateAlertStatistics(cachedData.data);
                return;
            }
            
            const response = await fetch('/api/alerts?per_page=1000'); // 获取全部数据
            const data = await response.json();
            
            if (data.alerts) {
                // 更新缓存
                this.cache.set(cacheKey, {
                    data: data.alerts,
                    timestamp: now
                });
                
                this.updateAlertStatistics(data.alerts);
            }
        } catch (error) {
            console.error('刷新预警统计失败:', error);
            // 静默处理错误，避免频繁的错误日志
        }
    }

    // 更新健康状态显示
    updateHealthDisplay(healthData) {
        if (healthData.status) {
            const statusElement = document.getElementById('health-status');
            if (statusElement) {
                statusElement.textContent = healthData.status;
                statusElement.className = `badge ${this.getHealthBadgeClass(healthData.status)}`;
            }
        }
        
        if (healthData.details) {
            const detailsElement = document.getElementById('health-details');
            if (detailsElement) {
                detailsElement.innerHTML = healthData.details;
            }
        }
    }

    async loadHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            this.updateHealthDisplay(data);
        } catch (error) {
            console.error('加载健康状态失败:', error);
        }
    }

    updateHealthDisplay(health) {
        const healthScore = health.health_score || 0;
        const healthStatus = health.status || 'unknown';
        
        // 更新健康指示器
        const healthDot = document.getElementById('health-dot');
        const healthStatusText = document.getElementById('health-status');
        const systemHealthDot = document.getElementById('system-health-dot');
        const systemHealthText = document.getElementById('system-health-text');
        const healthProgress = document.getElementById('health-progress');
        
        if (healthDot) {
            healthDot.className = `health-dot ${healthStatus}`;
        }
        if (healthStatusText) {
            healthStatusText.textContent = this.getHealthStatusText(healthStatus);
        }
        if (systemHealthDot) {
            systemHealthDot.className = `health-dot ${healthStatus}`;
        }
        if (systemHealthText) {
            systemHealthText.textContent = this.getHealthStatusText(healthStatus);
        }
        if (healthProgress) {
            healthProgress.style.width = `${healthScore * 100}%`;
            healthProgress.className = `progress-bar ${this.getHealthColor(healthScore)}`;
        }

        // 更新内存和CPU使用率
        const memoryUsage = health.memory_usage || 0;
        const memoryProgress = document.getElementById('memory-progress');
        if (memoryProgress) {
            memoryProgress.style.width = `${memoryUsage}%`;
        }

        const cpuUsage = health.cpu_usage || 0;
        const cpuProgress = document.getElementById('cpu-progress');
        if (cpuProgress) {
            cpuProgress.style.width = `${cpuUsage}%`;
        }
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

    getHealthColor(score) {
        if (score >= 0.8) return 'bg-success';
        if (score >= 0.6) return 'bg-info';
        if (score >= 0.4) return 'bg-warning';
        return 'bg-danger';
    }

    async loadDashboardData() {
        try {
            const [sessionsResponse, alertsResponse, workordersResponse, knowledgeResponse] = await Promise.all([
                fetch('/api/chat/sessions'),
                fetch('/api/alerts?per_page=1000'), // 获取全部预警数据
                fetch('/api/workorders'),
                fetch('/api/knowledge/stats')
            ]);

            const sessions = await sessionsResponse.json();
            const alerts = await alertsResponse.json();
            const workorders = await workordersResponse.json();
            const knowledge = await knowledgeResponse.json();

            // 更新统计卡片
            document.getElementById('total-sessions').textContent = sessions.sessions?.length || 0;
            document.getElementById('total-alerts').textContent = alerts.alerts?.length || 0;
            document.getElementById('total-workorders').textContent = workorders.workorders?.filter(w => w.status === 'open').length || 0;
            document.getElementById('knowledge-count').textContent = knowledge.total_entries || 0;
            
            // 更新预警统计数字
            if (alerts.alerts) {
                this.updateAlertStatistics(alerts.alerts);
            }
            
            // 更新知识库详细统计
            document.getElementById('knowledge-total').textContent = knowledge.total_entries || 0;
            document.getElementById('knowledge-active').textContent = knowledge.active_entries || 0;
            const confidencePercent = Math.round((knowledge.average_confidence || 0) * 100);
            document.getElementById('knowledge-confidence').style.width = `${confidencePercent}%`;
            document.getElementById('knowledge-confidence').setAttribute('aria-valuenow', confidencePercent);
            document.getElementById('knowledge-confidence').textContent = `${confidencePercent}%`;

            // 更新性能图表
            await this.updatePerformanceChart(sessions, alerts, workorders);
            
            // 更新系统健康状态
            await this.updateSystemHealth();
            
            // 加载分析数据并更新统计卡片
            await this.loadAnalytics();

        } catch (error) {
            console.error('加载仪表板数据失败:', error);
        }
    }



    initCharts() {
        // 性能趋势图
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '工单数量',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4
                    }, {
                        label: '预警数量',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // 分析图表
        const analyticsCtx = document.getElementById('analyticsChart');
        if (analyticsCtx) {
            this.charts.analytics = new Chart(analyticsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '满意度',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4
                    }, {
                        label: '解决时间(小时)',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // 类别分布图
        const categoryCtx = document.getElementById('categoryChart');
        if (categoryCtx) {
            this.charts.category = new Chart(categoryCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#007bff',
                            '#28a745',
                            '#ffc107',
                            '#dc3545',
                            '#17a2b8'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    async updatePerformanceChart(sessions, alerts, workorders) {
        if (!this.charts.performance) return;

        try {
            // 获取真实的分析数据
            const response = await fetch('/api/analytics?days=7&dimension=performance');
            const analyticsData = await response.json();
            
            if (analyticsData.trend && analyticsData.trend.length > 0) {
                // 使用真实数据
                const labels = analyticsData.trend.map(item => {
                    const date = new Date(item.date);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                });
                
                const workorderData = analyticsData.trend.map(item => item.workorders || 0);
                const alertData = analyticsData.trend.map(item => item.alerts || 0);
                
                this.charts.performance.data.labels = labels;
                this.charts.performance.data.datasets[0].data = workorderData;
                this.charts.performance.data.datasets[1].data = alertData;
                this.charts.performance.update();
            } else {
                // 如果没有真实数据，显示提示
                this.charts.performance.data.labels = ['暂无数据'];
                this.charts.performance.data.datasets[0].data = [0];
                this.charts.performance.data.datasets[1].data = [0];
                this.charts.performance.update();
            }
        } catch (error) {
            console.error('获取性能趋势数据失败:', error);
            // 出错时显示空数据
            this.charts.performance.data.labels = ['数据加载失败'];
            this.charts.performance.data.datasets[0].data = [0];
            this.charts.performance.data.datasets[1].data = [0];
            this.charts.performance.update();
        }
    }

    // 更新系统健康状态显示
    async updateSystemHealth() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            
            // 更新健康分数
            const healthScore = Math.max(0, 100 - (settings.memory_usage_percent || 0) - (settings.cpu_usage_percent || 0));
            const healthProgress = document.getElementById('health-progress');
            const healthDot = document.getElementById('system-health-dot');
            const healthText = document.getElementById('system-health-text');
            
            if (healthProgress) {
                healthProgress.style.width = `${healthScore}%`;
                healthProgress.setAttribute('aria-valuenow', healthScore);
            }
            
            if (healthDot) {
                healthDot.className = 'health-dot';
                if (healthScore >= 80) healthDot.classList.add('excellent');
                else if (healthScore >= 60) healthDot.classList.add('good');
                else if (healthScore >= 40) healthDot.classList.add('fair');
                else if (healthScore >= 20) healthDot.classList.add('poor');
                else healthDot.classList.add('critical');
            }
            
            if (healthText) {
                const statusText = healthScore >= 80 ? '优秀' : 
                                 healthScore >= 60 ? '良好' : 
                                 healthScore >= 40 ? '一般' : 
                                 healthScore >= 20 ? '较差' : '严重';
                healthText.textContent = `${statusText} (${healthScore}%)`;
            }
            
            // 更新内存使用
            const memoryProgress = document.getElementById('memory-progress');
            if (memoryProgress && settings.memory_usage_percent !== undefined) {
                memoryProgress.style.width = `${settings.memory_usage_percent}%`;
                memoryProgress.setAttribute('aria-valuenow', settings.memory_usage_percent);
            }
            
            // 更新CPU使用
            const cpuProgress = document.getElementById('cpu-progress');
            if (cpuProgress && settings.cpu_usage_percent !== undefined) {
                cpuProgress.style.width = `${settings.cpu_usage_percent}%`;
                cpuProgress.setAttribute('aria-valuenow', settings.cpu_usage_percent);
            }
            
        } catch (error) {
            console.error('更新系统健康状态失败:', error);
        }
    }

    // 对话功能
    async startChat() {
        try {
            const userId = document.getElementById('user-id').value;
            const workOrderId = document.getElementById('work-order-id').value;

            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    work_order_id: workOrderId ? parseInt(workOrderId) : null
                })
            });

            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                document.getElementById('start-chat').disabled = true;
                document.getElementById('end-chat').disabled = false;
                document.getElementById('message-input').disabled = false;
                document.getElementById('send-button').disabled = false;
                document.getElementById('session-info').textContent = `会话ID: ${this.sessionId}`;
                document.getElementById('connection-status').className = 'badge bg-success';
                document.getElementById('connection-status').innerHTML = '<i class="fas fa-circle me-1"></i>已连接';
                
                this.showNotification('对话已开始', 'success');
            } else {
                this.showNotification('开始对话失败', 'error');
            }
        } catch (error) {
            console.error('开始对话失败:', error);
            this.showNotification('开始对话失败', 'error');
        }
    }

    async endChat() {
        try {
            if (!this.sessionId) return;

            const response = await fetch(`/api/chat/session/${this.sessionId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                this.sessionId = null;
                document.getElementById('start-chat').disabled = false;
                document.getElementById('end-chat').disabled = true;
                document.getElementById('message-input').disabled = true;
                document.getElementById('send-button').disabled = true;
                document.getElementById('session-info').textContent = '未开始对话';
                document.getElementById('connection-status').className = 'badge bg-secondary';
                document.getElementById('connection-status').innerHTML = '<i class="fas fa-circle me-1"></i>未连接';
                
                this.showNotification('对话已结束', 'info');
            } else {
                this.showNotification('结束对话失败', 'error');
            }
        } catch (error) {
            console.error('结束对话失败:', error);
            this.showNotification('结束对话失败', 'error');
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message || !this.sessionId) return;

        // 显示用户消息
        this.addMessage('user', message);
        messageInput.value = '';

        // 显示占位提示：小奇正在查询中
        const typingId = this.showTypingIndicator();

        // 发送消息到服务器
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            const data = await response.json();
            if (data.success) {
                this.updateTypingIndicator(typingId, data.response, data.knowledge_used);
            } else {
                this.updateTypingIndicator(typingId, '抱歉，处理您的消息时出现了错误。', null, true);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.updateTypingIndicator(typingId, '网络连接错误，请稍后重试。', null, true);
        }
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const id = `typing-${Date.now()}`;
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.id = id;
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div>小奇正在查询中，请稍后…</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return id;
    }

    updateTypingIndicator(typingId, content, knowledgeUsed = null, isError = false) {
        const node = document.getElementById(typingId);
        if (!node) {
            // 回退：若占位不存在则直接追加
            this.addMessage('assistant', content, knowledgeUsed, isError);
            return;
        }
        const contentDiv = node.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.innerHTML = `
                <div>${content}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            `;
            if (knowledgeUsed && knowledgeUsed.length > 0) {
                const knowledgeDiv = document.createElement('div');
                knowledgeDiv.className = 'knowledge-info';
                knowledgeDiv.innerHTML = `
                    <i class="fas fa-lightbulb me-1"></i>
                    使用了知识库: ${knowledgeUsed.map(k => k.question || k.source || '实时数据').join(', ')}
                `;
                contentDiv.appendChild(knowledgeDiv);
            }
            if (isError) {
                contentDiv.style.borderLeft = '4px solid #dc3545';
            } else {
                contentDiv.style.borderLeft = '';
            }
        }
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addMessage(role, content, knowledgeUsed = null, isError = false) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // 移除欢迎消息
        const welcomeMsg = messagesContainer.querySelector('.text-center');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div>${content}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;

        if (knowledgeUsed && knowledgeUsed.length > 0) {
            const knowledgeDiv = document.createElement('div');
            knowledgeDiv.className = 'knowledge-info';
            knowledgeDiv.innerHTML = `
                <i class="fas fa-lightbulb me-1"></i>
                使用了知识库: ${knowledgeUsed.map(k => k.question).join(', ')}
            `;
            contentDiv.appendChild(knowledgeDiv);
        }

        if (isError) {
            contentDiv.style.borderLeft = '4px solid #dc3545';
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // 滚动到底部
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Agent功能
    async toggleAgentMode(enabled) {
        try {
            const response = await fetch('/api/agent/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled })
            });

            const data = await response.json();
            if (data.success) {
                this.isAgentMode = enabled;
                this.showNotification(`Agent模式已${enabled ? '启用' : '禁用'}`, 'success');
                this.loadAgentData();
            } else {
                this.showNotification('切换Agent模式失败', 'error');
            }
        } catch (error) {
            console.error('切换Agent模式失败:', error);
            this.showNotification('切换Agent模式失败', 'error');
        }
    }

    async loadAgentData() {
        try {
            const [statusResp, toolsResp] = await Promise.all([
                fetch('/api/agent/status'),
                fetch('/api/agent/tools/stats')
            ]);
            const data = await statusResp.json();
            const toolsData = await toolsResp.json();
            
            if (data.success) {
                document.getElementById('agent-current-state').textContent = data.status || '未知';
                document.getElementById('agent-active-goals').textContent = data.active_goals || 0;
                const tools = (toolsData.success ? toolsData.tools : (data.tools || [])) || [];
                document.getElementById('agent-available-tools').textContent = tools.length || 0;
                
                // 更新工具列表（使用真实统计）
                this.updateToolsList(tools);
                
                // 更新执行历史
                this.updateAgentExecutionHistory(data.execution_history || []);
            }
        } catch (error) {
            console.error('加载Agent数据失败:', error);
        }
    }

    updateToolsList(tools) {
        const toolsList = document.getElementById('tools-list');
        if (!tools || tools.length === 0) {
            toolsList.innerHTML = '<div class="empty-state"><i class="fas fa-tools"></i><p>暂无工具</p></div>';
            return;
        }

        const toolsHtml = tools.map(tool => {
            const usage = tool.usage_count || 0;
            const success = Math.round((tool.success_rate || 0) * 100);
            const meta = tool.metadata || {};
            return `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <strong>${tool.name}</strong>
                        ${meta.description ? `<div class="text-muted small">${meta.description}</div>` : ''}
                        <small class="text-muted">使用次数: ${usage}</small>
                    </div>
                    <div>
                        <span class="badge ${success >= 80 ? 'bg-success' : success >= 50 ? 'bg-warning' : 'bg-secondary'}">${success}%</span>
                        <button class="btn btn-sm btn-outline-primary ms-2" data-tool="${tool.name}" title="执行工具">
                            <i class="fas fa-play"></i>
                            <span class="ms-1">执行</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        toolsList.innerHTML = toolsHtml;

        // 绑定执行事件
        toolsList.querySelectorAll('button[data-tool]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const tool = btn.getAttribute('data-tool');
                // 简单参数输入（可扩展为动态表单）
                let params = {};
                try {
                    const input = prompt('请输入执行参数(JSON)：', '{}');
                    if (input) params = JSON.parse(input);
                } catch (e) {
                    this.showNotification('参数格式错误，应为JSON', 'warning');
                    return;
                }
                try {
                    const resp = await fetch('/api/agent/tools/execute', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tool, parameters: params })
                    });
                    const res = await resp.json();
                    if (res.success) {
                        this.showNotification(`工具 ${tool} 执行成功`, 'success');
                        await this.loadAgentData();
                    } else {
                        this.showNotification(res.error || `工具 ${tool} 执行失败`, 'error');
                    }
                } catch (err) {
                    console.error('执行工具失败:', err);
                    this.showNotification('执行工具失败: ' + err.message, 'error');
                }
            });
        });

        // 追加自定义工具注册入口
        const addDiv = document.createElement('div');
        addDiv.className = 'mt-3';
        addDiv.innerHTML = `
            <div class="input-group input-group-sm">
                <input type="text" id="custom-tool-name" class="form-control" placeholder="自定义工具名称">
                <input type="text" id="custom-tool-desc" class="form-control" placeholder="描述(可选)">
                <button class="btn btn-outline-primary" id="register-tool-btn">注册</button>
            </div>
        `;
        toolsList.appendChild(addDiv);
        document.getElementById('register-tool-btn').addEventListener('click', async () => {
            const name = document.getElementById('custom-tool-name').value.trim();
            const description = document.getElementById('custom-tool-desc').value.trim();
            if (!name) { this.showNotification('请输入工具名称', 'warning'); return; }
            try {
                const resp = await fetch('/api/agent/tools/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description })
                });
                const res = await resp.json();
                if (res.success) {
                    this.showNotification('工具注册成功', 'success');
                    this.loadAgentData();
                } else {
                    this.showNotification(res.error || '工具注册失败', 'error');
                }
            } catch (e) {
                console.error('注册工具失败:', e);
                this.showNotification('注册工具失败', 'error');
            }
        });
    }

    updateExecutionHistory(history) {
        const historyContainer = document.getElementById('agent-execution-history');
        if (history.length === 0) {
            historyContainer.innerHTML = '<div class="empty-state"><i class="fas fa-history"></i><p>暂无执行历史</p></div>';
            return;
        }

        const historyHtml = history.slice(-5).map(item => `
            <div class="border-bottom pb-2 mb-2">
                <div class="d-flex justify-content-between">
                    <strong>${item.type || '未知任务'}</strong>
                    <small class="text-muted">${new Date(item.timestamp).toLocaleString()}</small>
                </div>
                <div class="text-muted small">${item.description || '无描述'}</div>
                <div class="mt-1">
                    <span class="badge ${item.success ? 'bg-success' : 'bg-danger'}">
                        ${item.success ? '成功' : '失败'}
                    </span>
                </div>
            </div>
        `).join('');

        historyContainer.innerHTML = historyHtml;
    }

    async startAgentMonitoring() {
        try {
            const response = await fetch('/api/agent/monitoring/start', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Agent监控已启动', 'success');
            } else {
                this.showNotification('启动Agent监控失败', 'error');
            }
        } catch (error) {
            console.error('启动Agent监控失败:', error);
            this.showNotification('启动Agent监控失败', 'error');
        }
    }

    async stopAgentMonitoring() {
        try {
            const response = await fetch('/api/agent/monitoring/stop', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Agent监控已停止', 'success');
            } else {
                this.showNotification('停止Agent监控失败', 'error');
            }
        } catch (error) {
            console.error('停止Agent监控失败:', error);
            this.showNotification('停止Agent监控失败', 'error');
        }
    }

    async proactiveMonitoring() {
        try {
            const response = await fetch('/api/agent/proactive-monitoring', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`主动监控完成，发现 ${data.proactive_actions?.length || 0} 个行动机会`, 'info');
            } else {
                this.showNotification('主动监控失败', 'error');
            }
        } catch (error) {
            console.error('主动监控失败:', error);
            this.showNotification('主动监控失败', 'error');
        }
    }

    async intelligentAnalysis() {
        try {
            const response = await fetch('/api/agent/intelligent-analysis', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('智能分析完成', 'success');
                // 更新分析图表
                this.updateAnalyticsChart(data.analysis);
            } else {
                this.showNotification('智能分析失败', 'error');
            }
        } catch (error) {
            console.error('智能分析失败:', error);
            this.showNotification('智能分析失败', 'error');
        }
    }

    updateAnalyticsChart(analysis) {
        if (!this.charts.analytics || !analysis) return;

        // 更新分析图表数据
        const labels = analysis.trends?.dates || [];
        const satisfactionData = analysis.trends?.satisfaction || [];
        const resolutionTimeData = analysis.trends?.resolution_time || [];

        this.charts.analytics.data.labels = labels;
        this.charts.analytics.data.datasets[0].data = satisfactionData;
        this.charts.analytics.data.datasets[1].data = resolutionTimeData;
        this.charts.analytics.update();
    }

    // 预警管理
    async loadAlerts(page = 1, forceRefresh = false) {
        const cacheKey = `alerts_page_${page}`;
        
        if (!forceRefresh && this.cache.has(cacheKey)) {
            const cachedData = this.cache.get(cacheKey);
            this.updateAlertsDisplay(cachedData.alerts);
            this.updateAlertsPagination(cachedData);
            this.updateAlertStatistics(cachedData.alerts); // 添加统计更新
            return;
        }

        try {
            const pageSize = this.getPageSize('alerts-pagination');
            const response = await fetch(`/api/alerts?page=${page}&per_page=${pageSize}`);
            const data = await response.json();
            
            this.cache.set(cacheKey, data);
            this.updateAlertsDisplay(data.alerts);
            this.updateAlertsPagination(data);
            this.updateAlertStatistics(data.alerts); // 添加统计更新
        } catch (error) {
            console.error('加载预警失败:', error);
            this.showNotification('加载预警失败', 'error');
        }
    }

    updateAlertsDisplay(alerts) {
        const container = document.getElementById('alerts-container');
        
        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h5>暂无活跃预警</h5>
                    <p>系统运行正常，没有需要处理的预警</p>
                </div>
            `;
            return;
        }

        // 添加预警列表的批量操作头部
        const headerHtml = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center">
                    <input type="checkbox" id="select-all-alerts" class="form-check-input me-2" onchange="dashboard.toggleSelectAllAlerts()">
                    <label for="select-all-alerts" class="form-check-label">全选</label>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-danger" id="batch-delete-alerts" onclick="dashboard.batchDeleteAlerts()" disabled>
                        <i class="fas fa-trash me-1"></i>批量删除
                    </button>
                </div>
            </div>
        `;

        const alertsHtml = alerts.map(alert => `
            <div class="alert-item ${alert.level}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="d-flex align-items-start">
                        <input type="checkbox" class="form-check-input me-2 alert-checkbox" value="${alert.id}" onchange="dashboard.updateBatchDeleteAlertsButton()">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <span class="badge bg-${this.getAlertColor(alert.level)} me-2">${this.getLevelText(alert.level)}</span>
                                <span class="fw-bold">${alert.rule_name || '未知规则'}</span>
                                <span class="ms-auto text-muted small">${this.formatTime(alert.created_at)}</span>
                            </div>
                            <div class="alert-message mb-2">${alert.message}</div>
                            <div class="alert-meta text-muted small">
                                类型: ${this.getTypeText(alert.alert_type)} | 
                                级别: ${this.getLevelText(alert.level)}
                            </div>
                        </div>
                    </div>
                    <div class="ms-3">
                        <button class="btn btn-sm btn-outline-success" onclick="dashboard.resolveAlert(${alert.id})" title="解决预警">
                            <i class="fas fa-check"></i>
                            <span class="d-none d-md-inline ms-1">解决</span>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = headerHtml + alertsHtml;
    }

    updateAlertsPagination(data) {
        this.createPaginationComponent(data, 'alerts-pagination', 'loadAlerts', '条预警');
    }

    updateAlertStatistics(alerts) {
        // 如果传入的是分页数据，需要重新获取全部数据来计算统计
        if (alerts && alerts.length > 0) {
            // 检查是否是分页数据（通常分页数据少于50条）
            const pageSize = this.getPageSize('alerts-pagination');
            if (alerts.length <= pageSize) {
                // 可能是分页数据，需要获取全部数据
                this.updateAlertStatisticsFromAPI();
                return;
            }
        }
        
        // 使用传入的数据计算统计
        const stats = (alerts || []).reduce((acc, alert) => {
            acc[alert.level] = (acc[alert.level] || 0) + 1;
            acc.total = (acc.total || 0) + 1;
            return acc;
        }, {});

        document.getElementById('critical-alerts').textContent = stats.critical || 0;
        document.getElementById('warning-alerts').textContent = stats.warning || 0;
        document.getElementById('info-alerts').textContent = stats.info || 0;
        document.getElementById('total-alerts-count').textContent = stats.total || 0;
    }

    // 从API获取全部预警数据来计算统计
    async updateAlertStatisticsFromAPI() {
        try {
            // 获取全部预警数据（不分页）
            const response = await fetch('/api/alerts?per_page=1000'); // 获取大量数据
            const data = await response.json();
            
            if (data.alerts) {
                const stats = data.alerts.reduce((acc, alert) => {
                    acc[alert.level] = (acc[alert.level] || 0) + 1;
                    acc.total = (acc.total || 0) + 1;
                    return acc;
                }, {});

                document.getElementById('critical-alerts').textContent = stats.critical || 0;
                document.getElementById('warning-alerts').textContent = stats.warning || 0;
                document.getElementById('info-alerts').textContent = stats.info || 0;
                document.getElementById('total-alerts-count').textContent = stats.total || 0;
                
                // 更新缓存
                this.cache.set('alerts_stats', {
                    data: data.alerts,
                    timestamp: Date.now()
                });
            }
        } catch (error) {
            console.error('获取全部预警统计失败:', error);
        }
    }

    // 预警批量删除功能
    toggleSelectAllAlerts() {
        const selectAllCheckbox = document.getElementById('select-all-alerts');
        const alertCheckboxes = document.querySelectorAll('.alert-checkbox');
        
        alertCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        
        this.updateBatchDeleteAlertsButton();
    }

    updateBatchDeleteAlertsButton() {
        const selectedCheckboxes = document.querySelectorAll('.alert-checkbox:checked');
        const batchDeleteBtn = document.getElementById('batch-delete-alerts');
        
        if (batchDeleteBtn) {
            batchDeleteBtn.disabled = selectedCheckboxes.length === 0;
            batchDeleteBtn.textContent = selectedCheckboxes.length > 0 
                ? `批量删除 (${selectedCheckboxes.length})` 
                : '批量删除';
        }
    }

    async batchDeleteAlerts() {
        const selectedCheckboxes = document.querySelectorAll('.alert-checkbox:checked');
        const selectedIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
        
        if (selectedIds.length === 0) {
            this.showNotification('请选择要删除的预警', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${selectedIds.length} 个预警吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch('/api/batch-delete/alerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ids: selectedIds })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                
                // 清除所有相关缓存
                this.cache.delete('alerts');
                this.cache.delete('alerts_stats');
                
                // 立即更新统计数字，避免跳动
                await this.updateStatsAfterDelete(selectedIds.length);
                
                // 重新加载预警列表
                await this.loadAlerts();
                
                // 重置批量删除按钮状态
                this.updateBatchDeleteAlertsButton();
            } else {
                this.showNotification(data.error || '批量删除失败', 'error');
            }
        } catch (error) {
            console.error('批量删除预警失败:', error);
            this.showNotification('批量删除预警失败', 'error');
        }
    }

    // 删除后更新统计数字（平滑更新）
    async updateStatsAfterDelete(deletedCount) {
        try {
            // 直接调用API获取最新统计，不依赖页面显示数据
            await this.updateAlertStatisticsFromAPI();
            
            // 更新最后更新时间，避免智能更新机制干扰
            this.lastUpdateTimes.alerts = Date.now();
            
        } catch (error) {
            console.error('更新删除后统计失败:', error);
            // 如果计算失败，直接刷新
            await this.refreshAlertStats();
        }
    }

    // 获取当前显示的预警数据
    getCurrentDisplayedAlerts() {
        const alertElements = document.querySelectorAll('.alert-item');
        const alerts = [];
        
        alertElements.forEach(element => {
            const level = element.querySelector('.alert-level')?.textContent?.trim();
            if (level) {
                alerts.push({ level: level.toLowerCase() });
            }
        });
        
        return alerts;
    }

    // 计算预警统计
    calculateAlertStats(alerts) {
        const stats = { critical: 0, warning: 0, info: 0, total: 0 };
        
        alerts.forEach(alert => {
            const level = alert.level.toLowerCase();
            if (stats.hasOwnProperty(level)) {
                stats[level]++;
            }
            stats.total++;
        });
        
        return stats;
    }

    // 平滑更新预警统计数字
    smoothUpdateAlertStats(newStats) {
        // 获取当前显示的数字
        const currentCritical = parseInt(document.getElementById('critical-alerts')?.textContent || '0');
        const currentWarning = parseInt(document.getElementById('warning-alerts')?.textContent || '0');
        const currentInfo = parseInt(document.getElementById('info-alerts')?.textContent || '0');
        const currentTotal = parseInt(document.getElementById('total-alerts-count')?.textContent || '0');
        
        // 平滑过渡到新数字
        this.animateNumberChange('critical-alerts', currentCritical, newStats.critical);
        this.animateNumberChange('warning-alerts', currentWarning, newStats.warning);
        this.animateNumberChange('info-alerts', currentInfo, newStats.info);
        this.animateNumberChange('total-alerts-count', currentTotal, newStats.total);
    }

    // 数字变化动画
    animateNumberChange(elementId, from, to) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const duration = 300; // 300ms动画
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // 使用缓动函数
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.round(from + (to - from) * easeOut);
            
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // 解决预警后更新统计数字
    async updateStatsAfterResolve(alertId) {
        try {
            // 直接调用API获取最新统计，不依赖页面显示数据
            await this.updateAlertStatisticsFromAPI();
            
            // 更新最后更新时间，避免智能更新机制干扰
            this.lastUpdateTimes.alerts = Date.now();
            
        } catch (error) {
            console.error('更新解决后统计失败:', error);
            // 如果计算失败，直接刷新
            await this.refreshAlertStats();
        }
    }

    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('预警已解决', 'success');
                
                // 清除缓存
                this.cache.delete('alerts');
                this.cache.delete('alerts_stats');
                
                // 立即更新统计数字
                await this.updateStatsAfterResolve(alertId);
                
                // 重新加载预警列表
                this.loadAlerts();
            } else {
                this.showNotification('解决预警失败', 'error');
            }
        } catch (error) {
            console.error('解决预警失败:', error);
            this.showNotification('解决预警失败', 'error');
        }
    }

    // 知识库管理
    async loadKnowledge(page = 1) {
        try {
            const pageSize = this.getPageSize('knowledge-pagination');
            const response = await fetch(`/api/knowledge?page=${page}&per_page=${pageSize}`);
            const data = await response.json();
            
            if (data.knowledge) {
                this.updateKnowledgeDisplay(data.knowledge);
                this.updateKnowledgePagination(data);
            } else {
                // 兼容旧格式
                this.updateKnowledgeDisplay(data);
            }
        } catch (error) {
            console.error('加载知识库失败:', error);
        }
    }

    updateKnowledgeDisplay(knowledge) {
        const container = document.getElementById('knowledge-list');
        
        if (knowledge.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-database"></i><p>暂无知识条目</p></div>';
            return;
        }

        // 添加知识库列表的批量操作头部
        const headerHtml = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center">
                    <input type="checkbox" id="select-all-knowledge" class="form-check-input me-2" onchange="dashboard.toggleSelectAllKnowledge()">
                    <label for="select-all-knowledge" class="form-check-label">全选</label>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-danger" id="batch-delete-knowledge" onclick="dashboard.batchDeleteKnowledge()" disabled>
                        <i class="fas fa-trash me-1"></i>批量删除
                    </button>
                </div>
            </div>
        `;

        const knowledgeHtml = knowledge.map(item => `
            <div class="knowledge-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="d-flex align-items-start">
                        <input type="checkbox" class="form-check-input me-2 knowledge-checkbox" value="${item.id}" onchange="dashboard.updateBatchDeleteKnowledgeButton()">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${item.question}</h6>
                            <p class="text-muted mb-2">${item.answer}</p>
                            <div class="d-flex gap-3">
                                <small class="text-muted">分类: ${item.category}</small>
                                <small class="text-muted">置信度: ${Math.round(item.confidence_score * 100)}%</small>
                                <small class="text-muted">使用次数: ${item.usage_count || 0}</small>
                                <span class="badge ${item.is_verified ? 'bg-success' : 'bg-warning'}">
                                    ${item.is_verified ? '已验证' : '未验证'}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="ms-3">
                        <div class="btn-group" role="group">
                            ${item.is_verified ? 
                                `<button class="btn btn-sm btn-outline-warning" onclick="dashboard.unverifyKnowledge(${item.id})" title="取消验证">
                                    <i class="fas fa-times-circle"></i>
                                    <span class="d-none d-md-inline ms-1">取消验证</span>
                                </button>` :
                                `<button class="btn btn-sm btn-outline-success" onclick="dashboard.verifyKnowledge(${item.id})" title="验证">
                                    <i class="fas fa-check-circle"></i>
                                    <span class="d-none d-md-inline ms-1">验证</span>
                                </button>`
                            }
                            <button class="btn btn-sm btn-outline-danger" onclick="dashboard.deleteKnowledge(${item.id})" title="删除">
                                <i class="fas fa-trash"></i>
                                <span class="d-none d-md-inline ms-1">删除</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = headerHtml + knowledgeHtml;
    }

    updateKnowledgePagination(data) {
        this.createPaginationComponent(data, 'knowledge-pagination', 'loadKnowledge', '条知识');
    }

    async searchKnowledge() {
        const query = document.getElementById('knowledge-search').value.trim();
        if (!query) {
            this.loadKnowledge();
            return;
        }

        try {
            const response = await fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.updateKnowledgeDisplay(results);
        } catch (error) {
            console.error('搜索知识库失败:', error);
        }
    }

    async addKnowledge() {
        const question = document.getElementById('knowledge-question').value.trim();
        const answer = document.getElementById('knowledge-answer').value.trim();
        const category = document.getElementById('knowledge-category').value;
        const confidence = parseFloat(document.getElementById('knowledge-confidence').value);

        if (!question || !answer) {
            this.showNotification('请填写完整信息', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/knowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question,
                    answer,
                    category,
                    confidence_score: confidence
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('知识添加成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('addKnowledgeModal')).hide();
                document.getElementById('knowledge-form').reset();
                this.loadKnowledge();
            } else {
                this.showNotification('添加知识失败', 'error');
            }
        } catch (error) {
            console.error('添加知识失败:', error);
            this.showNotification('添加知识失败', 'error');
        }
    }

    async uploadFile() {
        const fileInput = document.getElementById('file-input');
        const processMethod = document.getElementById('process-method').value;
        const category = document.getElementById('file-category').value;
        const confidence = parseFloat(document.getElementById('file-confidence').value);
        const manualQuestion = document.getElementById('manual-question').value.trim();

        if (!fileInput.files[0]) {
            this.showNotification('请选择文件', 'warning');
            return;
        }

        if (processMethod === 'manual' && !manualQuestion) {
            this.showNotification('请指定问题', 'warning');
            return;
        }

        // 显示进度条
        const progressDiv = document.getElementById('upload-progress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        const statusText = document.getElementById('upload-status');
        
        progressDiv.style.display = 'block';
        progressBar.style.width = '0%';
        statusText.textContent = '正在上传文件...';

        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('process_method', processMethod);
            formData.append('category', category);
            formData.append('confidence_score', confidence);
            if (manualQuestion) {
                formData.append('manual_question', manualQuestion);
            }

            // 模拟进度更新
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 20;
                if (progress > 90) progress = 90;
                progressBar.style.width = progress + '%';
                
                if (progress < 30) {
                    statusText.textContent = '正在上传文件...';
                } else if (progress < 60) {
                    statusText.textContent = '正在解析文件内容...';
                } else if (progress < 90) {
                    statusText.textContent = '正在生成知识库...';
                }
            }, 500);

            const response = await fetch('/api/knowledge/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            statusText.textContent = '处理完成！';

            const data = await response.json();
            
            setTimeout(() => {
                progressDiv.style.display = 'none';
                
                if (data.success) {
                    this.showNotification(`文件处理成功，生成了 ${data.knowledge_count || 0} 条知识`, 'success');
                    bootstrap.Modal.getInstance(document.getElementById('uploadFileModal')).hide();
                    document.getElementById('file-upload-form').reset();
                    this.loadKnowledge();
                } else {
                    this.showNotification(data.error || '文件处理失败', 'error');
                }
            }, 1000);

        } catch (error) {
            console.error('文件上传失败:', error);
            progressDiv.style.display = 'none';
            this.showNotification('文件上传失败', 'error');
        }
    }

    async verifyKnowledge(knowledgeId) {
        try {
            const response = await fetch(`/api/knowledge/verify/${knowledgeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    verified_by: 'admin'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('知识库验证成功', 'success');
                this.loadKnowledge();
            } else {
                this.showNotification('知识库验证失败', 'error');
            }
        } catch (error) {
            console.error('验证知识库失败:', error);
            this.showNotification('验证知识库失败', 'error');
        }
    }

    async unverifyKnowledge(knowledgeId) {
        try {
            const response = await fetch(`/api/knowledge/unverify/${knowledgeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('取消验证成功', 'success');
                this.loadKnowledge();
            } else {
                this.showNotification('取消验证失败', 'error');
            }
        } catch (error) {
            console.error('取消验证失败:', error);
            this.showNotification('取消验证失败', 'error');
        }
    }

    async deleteKnowledge(knowledgeId) {
        if (!confirm('确定要删除这条知识库条目吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/knowledge/delete/${knowledgeId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('知识库删除成功', 'success');
                this.loadKnowledge();
            } else {
                this.showNotification('知识库删除失败', 'error');
            }
        } catch (error) {
            console.error('删除知识库失败:', error);
            this.showNotification('删除知识库失败', 'error');
        }
    }

    // 知识库批量删除功能
    toggleSelectAllKnowledge() {
        const selectAllCheckbox = document.getElementById('select-all-knowledge');
        const knowledgeCheckboxes = document.querySelectorAll('.knowledge-checkbox');
        
        knowledgeCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        
        this.updateBatchDeleteKnowledgeButton();
    }

    updateBatchDeleteKnowledgeButton() {
        const selectedCheckboxes = document.querySelectorAll('.knowledge-checkbox:checked');
        const batchDeleteBtn = document.getElementById('batch-delete-knowledge');
        
        if (batchDeleteBtn) {
            batchDeleteBtn.disabled = selectedCheckboxes.length === 0;
            batchDeleteBtn.textContent = selectedCheckboxes.length > 0 
                ? `批量删除 (${selectedCheckboxes.length})` 
                : '批量删除';
        }
    }

    async batchDeleteKnowledge() {
        const selectedCheckboxes = document.querySelectorAll('.knowledge-checkbox:checked');
        const selectedIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
        
        if (selectedIds.length === 0) {
            this.showNotification('请选择要删除的知识库条目', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${selectedIds.length} 个知识库条目吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch('/api/batch-delete/knowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ids: selectedIds })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                
                // 清除缓存并强制刷新
                this.cache.delete('knowledge');
                await this.loadKnowledge();
                
                // 重置批量删除按钮状态
                this.updateBatchDeleteKnowledgeButton();
            } else {
                this.showNotification(data.error || '批量删除失败', 'error');
            }
        } catch (error) {
            console.error('批量删除知识库条目失败:', error);
            this.showNotification('批量删除知识库条目失败', 'error');
        }
    }

    // 工单管理
    async loadWorkOrders(page = 1, forceRefresh = false) {
        const cacheKey = `workorders_page_${page}`;
        
        if (!forceRefresh && this.cache.has(cacheKey)) {
            const cachedData = this.cache.get(cacheKey);
            this.updateWorkOrdersDisplay(cachedData.workorders);
            this.updateWorkOrdersPagination(cachedData);
            // 不在这里更新统计，因为分页数据不完整
            return;
        }

        try {
            const statusFilter = document.getElementById('workorder-status-filter')?.value || 'all';
            const priorityFilter = document.getElementById('workorder-priority-filter')?.value || 'all';
            
            let url = '/api/workorders';
            const params = new URLSearchParams();
            params.append('page', page);
            const pageSize = this.getPageSize('workorders-pagination');
            params.append('per_page', pageSize.toString());
            if (statusFilter !== 'all') params.append('status', statusFilter);
            if (priorityFilter !== 'all') params.append('priority', priorityFilter);
            
            // 添加强制刷新参数
            if (forceRefresh) {
                params.append('_t', Date.now().toString());
            }
            
            if (params.toString()) url += '?' + params.toString();

            const response = await fetch(url, {
                cache: forceRefresh ? 'no-cache' : 'default',
                headers: forceRefresh ? {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                } : {}
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateWorkOrdersDisplay(data.workorders);
            this.updateWorkOrdersPagination(data);
            // 不在这里更新统计，因为分页数据不完整
            
            // 更新缓存
            this.cache.set(cacheKey, data);
            
        } catch (error) {
            console.error('加载工单失败:', error);
            this.showNotification('加载工单失败: ' + error.message, 'error');
        }
    }

    updateWorkOrdersDisplay(workorders) {
        const container = document.getElementById('workorders-list');
        
        if (workorders.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-tasks"></i><p>暂无工单</p></div>';
            return;
        }

        // 添加工单列表的批量操作头部
        const headerHtml = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="d-flex align-items-center">
                    <input type="checkbox" id="select-all-workorders" class="form-check-input me-2" onchange="dashboard.toggleSelectAllWorkorders()">
                    <label for="select-all-workorders" class="form-check-label">全选</label>
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-danger" id="batch-delete-workorders" onclick="dashboard.batchDeleteWorkorders()" disabled>
                        <i class="fas fa-trash me-1"></i>批量删除
                    </button>
                </div>
            </div>
        `;

        const workordersHtml = workorders.map(workorder => `
            <div class="work-order-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="d-flex align-items-start">
                        <input type="checkbox" class="form-check-input me-2 workorder-checkbox" value="${workorder.id}" onchange="dashboard.updateBatchDeleteButton()">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${workorder.title}</h6>
                            <p class="text-muted mb-2">${workorder.description ? workorder.description.substring(0, 100) + (workorder.description.length > 100 ? '...' : '') : '无处理过程'}</p>
                            <div class="d-flex gap-3">
                                <span class="badge bg-${this.getPriorityColor(workorder.priority)}">${this.getPriorityText(workorder.priority)}</span>
                                <span class="badge bg-${this.getStatusColor(workorder.status)}">${this.getStatusText(workorder.status)}</span>
                                <small class="text-muted">分类: ${workorder.category}</small>
                                <small class="text-muted">创建时间: ${new Date(workorder.created_at).toLocaleString()}</small>
                            </div>
                        </div>
                    </div>
                    <div class="ms-3">
                        <div class="btn-group" role="group">
                            <button class="btn btn-sm btn-outline-info" onclick="dashboard.viewWorkOrderDetails(${workorder.id})" title="查看详情">
                                <i class="fas fa-eye"></i>
                                <span class="d-none d-md-inline ms-1">查看</span>
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="dashboard.updateWorkOrder(${workorder.id})" title="编辑">
                                <i class="fas fa-edit"></i>
                                <span class="d-none d-md-inline ms-1">编辑</span>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="dashboard.deleteWorkOrder(${workorder.id})" title="删除">
                                <i class="fas fa-trash"></i>
                                <span class="d-none d-md-inline ms-1">删除</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = headerHtml + workordersHtml;
    }

    updateWorkOrdersPagination(data) {
        this.createPaginationComponent(data, 'workorders-pagination', 'loadWorkOrders', '个工单');
    }

    updateWorkOrderStatistics(workorders) {
        const stats = workorders.reduce((acc, wo) => {
            acc.total = (acc.total || 0) + 1;
            acc[wo.status] = (acc[wo.status] || 0) + 1;
            return acc;
        }, {});

        // 状态映射
        const statusMapping = {
            'open': ['open', '待处理', '新建', 'new'],
            'in_progress': ['in_progress', '处理中', '进行中', 'progress', 'processing'],
            'resolved': ['resolved', '已解决', '已完成'],
            'closed': ['closed', '已关闭', '关闭']
        };

        // 统计各状态的数量
        const mapped_counts = {'open': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0};

        for (const [status, count] of Object.entries(stats)) {
            if (status === 'total') continue;
            
            const status_lower = String(status).toLowerCase();
            let mapped = false;
            
            for (const [mapped_status, possible_values] of Object.entries(statusMapping)) {
                if (possible_values.some(v => v.toLowerCase() === status_lower)) {
                    mapped_counts[mapped_status] += count;
                    mapped = true;
                    break;
                }
            }
            
            if (!mapped) {
                console.warn(`未映射的状态: '${status}' (数量: ${count})`);
            }
        }

        document.getElementById('workorders-total').textContent = stats.total || 0;
        document.getElementById('workorders-open').textContent = mapped_counts['open'];
        document.getElementById('workorders-progress').textContent = mapped_counts['in_progress'];
        document.getElementById('workorders-resolved').textContent = mapped_counts['resolved'];
        
        console.log('工单统计更新:', {
            total: stats.total,
            open: mapped_counts['open'],
            in_progress: mapped_counts['in_progress'],
            resolved: mapped_counts['resolved'],
            closed: mapped_counts['closed']
        });
    }

    // 工单批量删除功能
    toggleSelectAllWorkorders() {
        const selectAllCheckbox = document.getElementById('select-all-workorders');
        const workorderCheckboxes = document.querySelectorAll('.workorder-checkbox');
        
        workorderCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        
        this.updateBatchDeleteButton();
    }

    updateBatchDeleteButton() {
        const selectedCheckboxes = document.querySelectorAll('.workorder-checkbox:checked');
        const batchDeleteBtn = document.getElementById('batch-delete-workorders');
        
        if (batchDeleteBtn) {
            batchDeleteBtn.disabled = selectedCheckboxes.length === 0;
            batchDeleteBtn.textContent = selectedCheckboxes.length > 0 
                ? `批量删除 (${selectedCheckboxes.length})` 
                : '批量删除';
        }
    }

    async batchDeleteWorkorders() {
        const selectedCheckboxes = document.querySelectorAll('.workorder-checkbox:checked');
        const selectedIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
        
        if (selectedIds.length === 0) {
            this.showNotification('请选择要删除的工单', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${selectedIds.length} 个工单吗？此操作不可撤销。`)) {
            return;
        }

        try {
            const response = await fetch('/api/batch-delete/workorders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ids: selectedIds })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                
                // 清除缓存并强制刷新
                this.cache.delete('workorders');
                await this.loadWorkOrders(true); // 强制刷新
                await this.loadAnalytics();
                
                // 重置批量删除按钮状态
                this.updateBatchDeleteButton();
            } else {
                this.showNotification(data.error || '批量删除失败', 'error');
            }
        } catch (error) {
            console.error('批量删除工单失败:', error);
            this.showNotification('批量删除工单失败', 'error');
        }
    }

    async createWorkOrder() {
        const title = document.getElementById('wo-title').value.trim();
        const description = document.getElementById('wo-description').value.trim();
        const category = document.getElementById('wo-category').value;
        const priority = document.getElementById('wo-priority').value;

        if (!title || !description) {
            this.showNotification('请填写完整信息', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/workorders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    description,
                    category,
                    priority
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('工单创建成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('createWorkOrderModal')).hide();
                document.getElementById('work-order-form').reset();
                // 立即刷新工单列表和统计
                await this.loadWorkOrders();
                await this.loadAnalytics();
            } else {
                this.showNotification('创建工单失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('创建工单失败:', error);
            this.showNotification('创建工单失败', 'error');
        }
    }

    async viewWorkOrderDetails(workorderId) {
        try {
            const response = await fetch(`/api/workorders/${workorderId}`);
            const workorder = await response.json();
            
            if (workorder.error) {
                this.showNotification('获取工单详情失败', 'error');
                return;
            }
            
            this.showWorkOrderDetailsModal(workorder);
        } catch (error) {
            console.error('获取工单详情失败:', error);
            this.showNotification('获取工单详情失败', 'error');
        }
    }

    showWorkOrderDetailsModal(workorder) {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal fade" id="workOrderDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">工单详情 - ${workorder.order_id || workorder.id}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <h6>基本信息</h6>
                                    <table class="table table-sm">
                                        <tr>
                                            <td><strong>工单号:</strong></td>
                                            <td>${workorder.order_id || workorder.id}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>标题:</strong></td>
                                            <td>${workorder.title}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>分类:</strong></td>
                                            <td>${workorder.category}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>优先级:</strong></td>
                                            <td><span class="badge bg-${this.getPriorityColor(workorder.priority)}">${this.getPriorityText(workorder.priority)}</span></td>
                                        </tr>
                                        <tr>
                                            <td><strong>状态:</strong></td>
                                            <td><span class="badge bg-${this.getStatusColor(workorder.status)}">${this.getStatusText(workorder.status)}</span></td>
                                        </tr>
                                        <tr>
                                            <td><strong>创建时间:</strong></td>
                                            <td>${new Date(workorder.created_at).toLocaleString()}</td>
                                        </tr>
                                        <tr>
                                            <td><strong>更新时间:</strong></td>
                                            <td>${new Date(workorder.updated_at).toLocaleString()}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h6>问题描述</h6>
                                    <div class="border p-3 rounded">
                                        ${workorder.title || '无问题描述'}
                                    </div>
                                    ${workorder.description ? `
                                        <h6 class="mt-3">处理过程</h6>
                                        <div class="border p-3 rounded bg-light">
                                            ${workorder.description}
                                        </div>
                                    ` : ''}
                                    ${workorder.resolution ? `
                                        <h6 class="mt-3">解决方案</h6>
                                        <div class="border p-3 rounded bg-light">
                                            ${workorder.resolution}
                                        </div>
                                    ` : ''}
                                    ${workorder.satisfaction_score ? `
                                        <h6 class="mt-3">满意度评分</h6>
                                        <div class="border p-3 rounded">
                                            <div class="progress">
                                                <div class="progress-bar" style="width: ${workorder.satisfaction_score * 100}%"></div>
                                            </div>
                                            <small class="text-muted">${workorder.satisfaction_score}/5.0</small>
                                        </div>
                                    ` : ''}
                                    <div class="ai-suggestion-section">
                                        <div class="ai-suggestion-header">
                                            <h6 class="ai-suggestion-title">
                                                <i class="fas fa-robot"></i>AI建议与人工描述
                                            </h6>
                                            <button class="generate-ai-btn" onclick="dashboard.generateAISuggestion(${workorder.id})">
                                                <i class="fas fa-magic me-1"></i>生成AI建议
                                            </button>
                                        </div>
                                        
                                        <div class="ai-suggestion-content">
                                            <label class="form-label fw-bold text-primary mb-2">
                                                <i class="fas fa-brain me-1"></i>AI建议
                                            </label>
                                            <textarea id="aiSuggestion_${workorder.id}" class="form-control" rows="4" placeholder="点击上方按钮生成AI建议..." readonly></textarea>
                                        </div>
                                        
                                        <div class="human-resolution-content">
                                            <label class="form-label fw-bold text-warning mb-2">
                                                <i class="fas fa-user-edit me-1"></i>人工描述
                                            </label>
                                            <textarea id="humanResolution_${workorder.id}" class="form-control" rows="3" placeholder="请填写人工处理描述..."></textarea>
                                        </div>
                                        
                                        <div class="similarity-indicator">
                                            <button class="save-human-btn" onclick="dashboard.saveHumanResolution(${workorder.id})">
                                                <i class="fas fa-save me-1"></i>保存人工描述并评估
                                            </button>
                                            <span id="aiSim_${workorder.id}" class="similarity-badge bg-secondary">
                                                <i class="fas fa-percentage"></i>相似度: --
                                            </span>
                                            <span id="aiApproved_${workorder.id}" class="status-badge pending">未审批</span>
                                        </div>
                                        
                                        <div class="action-buttons">
                                            <button id="approveBtn_${workorder.id}" class="approve-btn" onclick="dashboard.approveToKnowledge(${workorder.id})" disabled>
                                                <i class="fas fa-check me-1"></i>审批入库
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            ${workorder.conversations && workorder.conversations.length > 0 ? `
                                <h6>对话记录</h6>
                                <div class="conversation-history" style="max-height: 300px; overflow-y: auto;">
                                    ${workorder.conversations.map(conv => `
                                        <div class="border-bottom pb-2 mb-2">
                                            <div class="d-flex justify-content-between">
                                                <small class="text-muted">${new Date(conv.timestamp).toLocaleString()}</small>
                                            </div>
                                            <div class="mb-1">
                                                <strong>用户:</strong> ${conv.user_message}
                                            </div>
                                            <div>
                                                <strong>助手:</strong> ${conv.assistant_response}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            <button type="button" class="btn btn-primary" onclick="dashboard.updateWorkOrder(${workorder.id})">编辑工单</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框
        const existingModal = document.getElementById('workOrderDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新的模态框到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('workOrderDetailsModal'));
        modal.show();
        
        // 模态框关闭时移除DOM元素
        document.getElementById('workOrderDetailsModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    async updateWorkOrder(workorderId) {
        try {
            // 获取工单详情
            const response = await fetch(`/api/workorders/${workorderId}`);
            const workorder = await response.json();
            
            if (workorder.id) {
                this.showEditWorkOrderModal(workorder);
            } else {
                throw new Error(workorder.error || '获取工单详情失败');
            }
        } catch (error) {
            console.error('获取工单详情失败:', error);
            this.showNotification('获取工单详情失败: ' + error.message, 'error');
        }
    }

    async deleteWorkOrder(workorderId) {
        console.log('deleteWorkOrder called with ID:', workorderId);
        
        if (!confirm('确定要删除这个工单吗？此操作不可撤销。')) {
            console.log('用户取消了删除操作');
            return;
        }

        try {
            console.log('发送删除请求到:', `/api/workorders/${workorderId}`);
            const response = await fetch(`/api/workorders/${workorderId}`, {
                method: 'DELETE'
            });

            console.log('删除响应状态:', response.status);
            const data = await response.json();
            console.log('删除响应数据:', data);
            
            if (data.success) {
                this.showNotification('工单删除成功', 'success');
                // 立即刷新工单列表和统计
                await this.loadWorkOrders();
                await this.loadAnalytics();
            } else {
                this.showNotification('删除工单失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('删除工单失败:', error);
            this.showNotification('删除工单失败: ' + error.message, 'error');
        }
    }

    showEditWorkOrderModal(workorder) {
        // 创建编辑工单模态框
        const modalHtml = `
            <div class="modal fade" id="editWorkOrderModal" tabindex="-1" aria-labelledby="editWorkOrderModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editWorkOrderModalLabel">编辑工单 #${workorder.id}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editWorkOrderForm">
                                <div class="row">
                                    <div class="col-md-8">
                                        <div class="mb-3">
                                            <label for="editTitle" class="form-label">标题 *</label>
                                            <input type="text" class="form-control" id="editTitle" value="${workorder.title}" required>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label for="editPriority" class="form-label">优先级</label>
                                            <select class="form-select" id="editPriority">
                                                <option value="low" ${workorder.priority === 'low' ? 'selected' : ''}>低</option>
                                                <option value="medium" ${workorder.priority === 'medium' ? 'selected' : ''}>中</option>
                                                <option value="high" ${workorder.priority === 'high' ? 'selected' : ''}>高</option>
                                                <option value="urgent" ${workorder.priority === 'urgent' ? 'selected' : ''}>紧急</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editCategory" class="form-label">分类</label>
                                            <select class="form-select" id="editCategory">
                                                <option value="技术问题" ${workorder.category === '技术问题' ? 'selected' : ''}>技术问题</option>
                                                <option value="业务问题" ${workorder.category === '业务问题' ? 'selected' : ''}>业务问题</option>
                                                <option value="系统故障" ${workorder.category === '系统故障' ? 'selected' : ''}>系统故障</option>
                                                <option value="功能需求" ${workorder.category === '功能需求' ? 'selected' : ''}>功能需求</option>
                                                <option value="其他" ${workorder.category === '其他' ? 'selected' : ''}>其他</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editStatus" class="form-label">状态</label>
                                            <select class="form-select" id="editStatus">
                                                <option value="open" ${workorder.status === 'open' ? 'selected' : ''}>待处理</option>
                                                <option value="in_progress" ${workorder.status === 'in_progress' ? 'selected' : ''}>处理中</option>
                                                <option value="resolved" ${workorder.status === 'resolved' ? 'selected' : ''}>已解决</option>
                                                <option value="closed" ${workorder.status === 'closed' ? 'selected' : ''}>已关闭</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="editDescription" class="form-label">处理过程 *</label>
                                    <textarea class="form-control" id="editDescription" rows="4" required>${workorder.description}</textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="editResolution" class="form-label">解决方案</label>
                                    <textarea class="form-control" id="editResolution" rows="3" placeholder="请输入解决方案...">${workorder.resolution || ''}</textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editSatisfactionScore" class="form-label">满意度评分 (1-5)</label>
                                            <input type="number" class="form-control" id="editSatisfactionScore" min="1" max="5" value="${workorder.satisfaction_score || ''}">
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" onclick="dashboard.saveWorkOrder(${workorder.id})">保存修改</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框
        const existingModal = document.getElementById('editWorkOrderModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新模态框到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('editWorkOrderModal'));
        modal.show();
        
        // 模态框关闭时清理
        document.getElementById('editWorkOrderModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    async saveWorkOrder(workorderId) {
        try {
            // 获取表单数据
            const formData = {
                title: document.getElementById('editTitle').value,
                description: document.getElementById('editDescription').value,
                category: document.getElementById('editCategory').value,
                priority: document.getElementById('editPriority').value,
                status: document.getElementById('editStatus').value,
                resolution: document.getElementById('editResolution').value,
                satisfaction_score: parseInt(document.getElementById('editSatisfactionScore').value) || null
            };
            
            // 验证必填字段
            if (!formData.title.trim() || !formData.description.trim()) {
                this.showNotification('标题和描述不能为空', 'error');
                return;
            }
            
            // 发送更新请求
            const response = await fetch(`/api/workorders/${workorderId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('工单更新成功', 'success');
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('editWorkOrderModal'));
                modal.hide();
                // 刷新工单列表和统计
                await this.loadWorkOrders();
                await this.loadAnalytics();
            } else {
                throw new Error(result.error || '更新工单失败');
            }
        } catch (error) {
            console.error('更新工单失败:', error);
            this.showNotification('更新工单失败: ' + error.message, 'error');
        }
    }

    // 工单导入功能
    showImportModal() {
        // 显示导入模态框
        const modal = new bootstrap.Modal(document.getElementById('importWorkOrderModal'));
        modal.show();
        
        // 重置表单
        document.getElementById('excel-file-input').value = '';
        document.getElementById('import-progress').classList.add('d-none');
        document.getElementById('import-result').classList.add('d-none');
    }

    async downloadTemplate() {
        try {
            // 直接请求文件接口，避免浏览器跨源/权限限制
            const resp = await fetch('/api/workorders/import/template/file');
            if (!resp.ok) throw new Error('下载接口返回错误');
            const blob = await resp.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = '工单导入模板.xlsx';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(blobUrl);
            this.showNotification('模板下载成功', 'success');
        } catch (error) {
            console.error('下载模板失败:', error);
            this.showNotification('下载模板失败: ' + error.message, 'error');
        }
    }

    async importWorkOrders() {
        const fileInput = document.getElementById('excel-file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showNotification('请选择要导入的Excel文件', 'error');
            return;
        }
        
        // 验证文件类型
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            this.showNotification('只支持Excel文件(.xlsx, .xls)', 'error');
            return;
        }
        
        // 验证文件大小
        if (file.size > 16 * 1024 * 1024) {
            this.showNotification('文件大小不能超过16MB', 'error');
            return;
        }
        
        // 显示进度条
        document.getElementById('import-progress').classList.remove('d-none');
        document.getElementById('import-result').classList.add('d-none');
        
        try {
            // 创建FormData
            const formData = new FormData();
            formData.append('file', file);
            
            // 发送导入请求
            const response = await fetch('/api/workorders/import', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 显示成功消息
                document.getElementById('import-progress').classList.add('d-none');
                document.getElementById('import-result').classList.remove('d-none');
                document.getElementById('import-success-message').textContent = 
                    `成功导入 ${result.imported_count} 个工单`;
                
                this.showNotification(result.message, 'success');
                
                // 刷新工单列表
                this.loadWorkOrders();
                
                // 3秒后关闭模态框
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('importWorkOrderModal'));
                    modal.hide();
                }, 3000);
                
            } else {
                throw new Error(result.error || '导入工单失败');
            }
            
        } catch (error) {
            console.error('导入工单失败:', error);
            document.getElementById('import-progress').classList.add('d-none');
            this.showNotification('导入工单失败: ' + error.message, 'error');
        }
    }

    // 对话历史管理
    async loadConversationHistory(page = 1) {
        try {
            const pageSize = this.getPageSize('conversations-pagination');
            const response = await fetch(`/api/conversations?page=${page}&per_page=${pageSize}`);
            const data = await response.json();
            
            if (data.conversations) {
                this.renderConversationList(data.conversations || []);
                this.updateConversationPagination(data);
                this.updateConversationStats(data.stats || {});
            } else {
                throw new Error(data.error || '加载对话历史失败');
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
            this.showNotification('加载对话历史失败: ' + error.message, 'error');
        }
    }

    renderConversationList(conversations) {
        const container = document.getElementById('conversation-list');
        if (!conversations || conversations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>暂无对话记录</p>
                </div>
            `;
            return;
        }

        const html = conversations.map(conv => `
            <div class="card mb-3 conversation-item" data-conversation-id="${conv.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h6 class="mb-1">用户: ${conv.user_id || '匿名'}</h6>
                            <small class="text-muted">${new Date(conv.timestamp).toLocaleString()}</small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="dashboard.viewConversation(${conv.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="dashboard.deleteConversation(${conv.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="conversation-preview">
                        <p class="mb-1"><strong>用户:</strong> ${conv.user_message?.substring(0, 100)}${conv.user_message?.length > 100 ? '...' : ''}</p>
                        <p class="mb-0"><strong>助手:</strong> ${conv.assistant_response?.substring(0, 100)}${conv.assistant_response?.length > 100 ? '...' : ''}</p>
                    </div>
                    <div class="mt-2">
                        <span class="badge bg-secondary">响应时间: ${conv.response_time || 0}ms</span>
                        ${conv.work_order_id ? `<span class="badge bg-info">工单: ${conv.work_order_id}</span>` : ''}
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    updateConversationPagination(data) {
        this.createPaginationComponent(data, 'conversations-pagination', 'loadConversationHistory', '条对话');
    }

    updateConversationStats(stats) {
        document.getElementById('conversation-total').textContent = stats.total || 0;
        document.getElementById('conversation-today').textContent = stats.today || 0;
        document.getElementById('conversation-avg-response').textContent = `${stats.avg_response_time || 0}ms`;
        document.getElementById('conversation-active-users').textContent = stats.active_users || 0;
    }

    async refreshConversationHistory() {
        // 先尝试触发一次合并迁移（幂等，重复调用也安全）
        try {
            await fetch('/api/conversations/migrate-merge', { method: 'POST' });
        } catch (e) { /* 忽略迁移失败 */ }
        await this.loadConversationHistory();
        this.showNotification('对话历史已刷新', 'success');
    }

    async clearAllConversations() {
        if (!confirm('确定要清空所有对话历史吗？此操作不可恢复！')) {
            return;
        }

        try {
            const response = await fetch('/api/conversations/clear', { method: 'DELETE' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('对话历史已清空', 'success');
                await this.loadConversationHistory();
            } else {
                throw new Error(data.error || '清空对话历史失败');
            }
        } catch (error) {
            console.error('清空对话历史失败:', error);
            this.showNotification('清空对话历史失败: ' + error.message, 'error');
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm('确定要删除这条对话记录吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/conversations/${conversationId}`, { method: 'DELETE' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('对话记录已删除', 'success');
                await this.loadConversationHistory();
            } else {
                throw new Error(data.error || '删除对话记录失败');
            }
        } catch (error) {
            console.error('删除对话记录失败:', error);
            this.showNotification('删除对话记录失败: ' + error.message, 'error');
        }
    }

    async viewConversation(conversationId) {
        try {
            const response = await fetch(`/api/conversations/${conversationId}`);
            const data = await response.json();
            
            if (data.success) {
                data.user_id = data.user_id || '匿名';
                this.showConversationModal(data);
            } else {
                throw new Error(data.error || '获取对话详情失败');
            }
        } catch (error) {
            console.error('获取对话详情失败:', error);
            this.showNotification('获取对话详情失败: ' + error.message, 'error');
        }
    }

    showConversationModal(conversation) {
        const modalHtml = `
            <div class="modal fade" id="conversationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">对话详情</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>用户:</strong> ${conversation.user_id || '匿名'}<br>
                                <strong>时间:</strong> ${new Date(conversation.timestamp).toLocaleString()}<br>
                                <strong>响应时间:</strong> ${conversation.response_time || 0}ms
                            </div>
                            <div class="mb-3">
                                <h6>用户消息:</h6>
                                <div class="border p-3 rounded">${conversation.user_message || ''}</div>
                            </div>
                            <div class="mb-3">
                                <h6>助手回复:</h6>
                                <div class="border p-3 rounded">${conversation.assistant_response || ''}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框
        const existingModal = document.getElementById('conversationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('conversationModal'));
        modal.show();
    }

    async filterConversations() {
        const search = document.getElementById('conversation-search').value;
        const userFilter = document.getElementById('conversation-user-filter').value;
        const dateFilter = document.getElementById('conversation-date-filter').value;
        
        try {
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (userFilter) params.append('user_id', userFilter);
            if (dateFilter) params.append('date_filter', dateFilter);
            
            const response = await fetch(`/api/conversations?${params.toString()}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderConversationList(data.conversations || []);
                this.renderConversationPagination(data.pagination || {});
            } else {
                throw new Error(data.error || '筛选对话失败');
            }
        } catch (error) {
            console.error('筛选对话失败:', error);
            this.showNotification('筛选对话失败: ' + error.message, 'error');
        }
    }

    // Token监控
    async loadTokenMonitor() {
        try {
            const response = await fetch('/api/token-monitor/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateTokenStats(data);
                this.loadTokenChart();
                this.loadTokenRecords();
            } else {
                throw new Error(data.error || '加载Token监控数据失败');
            }
        } catch (error) {
            console.error('加载Token监控数据失败:', error);
            this.showNotification('加载Token监控数据失败: ' + error.message, 'error');
        }
    }

    updateTokenStats(stats) {
        document.getElementById('token-today').textContent = stats.today_tokens || 0;
        document.getElementById('token-month').textContent = stats.month_tokens || 0;
        document.getElementById('token-cost').textContent = `¥${stats.total_cost || 0}`;
        document.getElementById('token-budget').textContent = `¥${stats.budget_limit || 1000}`;
    }

    async loadTokenChart() {
        try {
            const response = await fetch('/api/token-monitor/chart');
            const data = await response.json();
            
            if (data.success) {
                this.renderTokenChart(data);
            }
        } catch (error) {
            console.error('加载Token图表失败:', error);
        }
    }

    renderTokenChart(data) {
        const ctx = document.getElementById('tokenChart').getContext('2d');
        
        if (this.charts.tokenChart) {
            this.charts.tokenChart.destroy();
        }
        
        this.charts.tokenChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Token消耗',
                    data: data.tokens || [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }, {
                    label: '成本',
                    data: data.costs || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Token数量'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '成本 (元)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }

    async loadTokenRecords() {
        try {
            const response = await fetch('/api/token-monitor/records');
            const data = await response.json();
            
            if (data.success) {
                this.renderTokenRecords(data.records || []);
            }
        } catch (error) {
            console.error('加载Token记录失败:', error);
        }
    }

    renderTokenRecords(records) {
        const tbody = document.getElementById('token-records');
        
        if (!records || records.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">暂无记录</td>
                </tr>
            `;
            return;
        }

        const html = records.map(record => `
            <tr>
                <td>${new Date(record.timestamp).toLocaleString()}</td>
                <td>${record.user_id || '匿名'}</td>
                <td>${record.model || 'qwen-turbo'}</td>
                <td>${record.input_tokens || 0}</td>
                <td>${record.output_tokens || 0}</td>
                <td>${record.total_tokens || 0}</td>
                <td>¥${record.cost || 0}</td>
                <td>${record.response_time || 0}ms</td>
            </tr>
        `).join('');

        tbody.innerHTML = html;
    }

    async saveTokenSettings() {
        const dailyThreshold = document.getElementById('daily-threshold').value;
        const monthlyBudget = document.getElementById('monthly-budget').value;
        const enableAlerts = document.getElementById('enable-alerts').checked;

        try {
            const response = await fetch('/api/token-monitor/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    daily_threshold: parseInt(dailyThreshold),
                    monthly_budget: parseFloat(monthlyBudget),
                    enable_alerts: enableAlerts
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Token设置已保存', 'success');
            } else {
                throw new Error(data.error || '保存Token设置失败');
            }
        } catch (error) {
            console.error('保存Token设置失败:', error);
            this.showNotification('保存Token设置失败: ' + error.message, 'error');
        }
    }

    async updateTokenChart(period) {
        // 更新按钮状态
        document.querySelectorAll('#tokenChart').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        try {
            const response = await fetch(`/api/token-monitor/chart?period=${period}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTokenChart(data);
            }
        } catch (error) {
            console.error('更新Token图表失败:', error);
        }
    }

    async exportTokenData() {
        try {
            const response = await fetch('/api/token-monitor/export');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'token_usage_data.xlsx';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            this.showNotification('Token数据导出成功', 'success');
        } catch (error) {
            console.error('导出Token数据失败:', error);
            this.showNotification('导出Token数据失败: ' + error.message, 'error');
        }
    }

    async refreshTokenData() {
        await this.loadTokenMonitor();
        this.showNotification('Token数据已刷新', 'success');
    }

    // AI监控
    async loadAIMonitor() {
        try {
            const response = await fetch('/api/ai-monitor/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateAIStats(data);
                this.loadModelComparisonChart();
                this.loadErrorDistributionChart();
                this.loadErrorLog();
            } else {
                throw new Error(data.error || '加载AI监控数据失败');
            }
        } catch (error) {
            console.error('加载AI监控数据失败:', error);
            this.showNotification('加载AI监控数据失败: ' + error.message, 'error');
        }
    }

    updateAIStats(stats) {
        document.getElementById('ai-success-rate').textContent = `${stats.success_rate || 0}%`;
        document.getElementById('ai-response-time').textContent = `${stats.avg_response_time || 0}ms`;
        document.getElementById('ai-error-rate').textContent = `${stats.error_rate || 0}%`;
        document.getElementById('ai-total-calls').textContent = stats.total_calls || 0;
    }

    async loadModelComparisonChart() {
        try {
            const response = await fetch('/api/ai-monitor/model-comparison');
            const data = await response.json();
            
            if (data.success) {
                this.renderModelComparisonChart(data);
            }
        } catch (error) {
            console.error('加载模型对比图表失败:', error);
        }
    }

    renderModelComparisonChart(data) {
        const ctx = document.getElementById('modelComparisonChart').getContext('2d');
        
        if (this.charts.modelComparisonChart) {
            this.charts.modelComparisonChart.destroy();
        }
        
        this.charts.modelComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.models || [],
                datasets: [{
                    label: '成功率 (%)',
                    data: data.success_rates || [],
                    backgroundColor: 'rgba(40, 167, 69, 0.8)'
                }, {
                    label: '平均响应时间 (ms)',
                    data: data.response_times || [],
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '成功率 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '响应时间 (ms)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }

    async loadErrorDistributionChart() {
        try {
            const response = await fetch('/api/ai-monitor/error-distribution');
            const data = await response.json();
            
            if (data.success) {
                this.renderErrorDistributionChart(data);
            }
        } catch (error) {
            console.error('加载错误分布图表失败:', error);
        }
    }

    renderErrorDistributionChart(data) {
        const ctx = document.getElementById('errorDistributionChart').getContext('2d');
        
        if (this.charts.errorDistributionChart) {
            this.charts.errorDistributionChart.destroy();
        }
        
        this.charts.errorDistributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.error_types || [],
                datasets: [{
                    data: data.counts || [],
                    backgroundColor: [
                        '#dc3545',
                        '#fd7e14',
                        '#ffc107',
                        '#17a2b8',
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

    async loadErrorLog() {
        try {
            const response = await fetch('/api/ai-monitor/error-log');
            const data = await response.json();
            
            if (data.success) {
                this.renderErrorLog(data.errors || []);
            }
        } catch (error) {
            console.error('加载错误日志失败:', error);
        }
    }

    renderErrorLog(errors) {
        const tbody = document.getElementById('error-log');
        
        if (!errors || errors.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">暂无错误记录</td>
                </tr>
            `;
            return;
        }

        const html = errors.map(error => `
            <tr>
                <td>${new Date(error.timestamp).toLocaleString()}</td>
                <td><span class="badge bg-danger">${error.error_type || '未知'}</span></td>
                <td>${error.error_message || ''}</td>
                <td>${error.model || 'qwen-turbo'}</td>
                <td>${error.user_id || '匿名'}</td>
                <td>
                    <button class="btn btn-outline-primary btn-sm" onclick="dashboard.viewErrorDetail(${error.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = html;
    }

    async refreshErrorLog() {
        await this.loadErrorLog();
        this.showNotification('错误日志已刷新', 'success');
    }

    async clearErrorLog() {
        if (!confirm('确定要清空错误日志吗？')) {
            return;
        }

        try {
            const response = await fetch('/api/ai-monitor/error-log', { method: 'DELETE' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('错误日志已清空', 'success');
                await this.loadErrorLog();
            } else {
                throw new Error(data.error || '清空错误日志失败');
            }
        } catch (error) {
            console.error('清空错误日志失败:', error);
            this.showNotification('清空错误日志失败: ' + error.message, 'error');
        }
    }

    // 系统优化
    async loadSystemOptimizer() {
        try {
            const response = await fetch('/api/system-optimizer/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateSystemStats(data);
                this.loadSecuritySettings();
                this.loadTrafficSettings();
                this.loadCostSettings();
            } else {
                throw new Error(data.error || '加载系统优化数据失败');
            }
        } catch (error) {
            console.error('加载系统优化数据失败:', error);
            this.showNotification('加载系统优化数据失败: ' + error.message, 'error');
        }
    }

    updateSystemStats(stats) {
        document.getElementById('cpu-usage').textContent = `${stats.cpu_usage || 0}%`;
        document.getElementById('memory-usage-percent').textContent = `${stats.memory_usage || 0}%`;
        document.getElementById('disk-usage').textContent = `${stats.disk_usage || 0}%`;
        document.getElementById('network-latency').textContent = `${stats.network_latency || 0}ms`;
        
        // 更新健康指标
        this.updateHealthIndicator('system-health-indicator', stats.system_health || 95);
        this.updateHealthIndicator('database-health-indicator', stats.database_health || 98);
        this.updateHealthIndicator('api-health-indicator', stats.api_health || 92);
        this.updateHealthIndicator('cache-health-indicator', stats.cache_health || 99);
        
        document.getElementById('system-health-score').textContent = `${stats.system_health || 95}%`;
        document.getElementById('database-health-score').textContent = `${stats.database_health || 98}%`;
        document.getElementById('api-health-score').textContent = `${stats.api_health || 92}%`;
        document.getElementById('cache-health-score').textContent = `${stats.cache_health || 99}%`;
    }

    updateHealthIndicator(elementId, score) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.className = 'health-dot';
        if (score >= 95) element.classList.add('excellent');
        else if (score >= 85) element.classList.add('good');
        else if (score >= 70) element.classList.add('fair');
        else if (score >= 50) element.classList.add('poor');
        else element.classList.add('critical');
    }

    async optimizeCPU() {
        try {
            const response = await fetch('/api/system-optimizer/optimize-cpu', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message || 'CPU优化完成', 'success');
                this.updateOptimizationProgress('cpu-optimization', data.progress || 100);
                // 刷新状态并回落进度条
                await this.loadSystemOptimizer();
                setTimeout(() => this.updateOptimizationProgress('cpu-optimization', 0), 1500);
            } else {
                throw new Error(data.error || 'CPU优化失败');
            }
        } catch (error) {
            console.error('CPU优化失败:', error);
            this.showNotification('CPU优化失败: ' + error.message, 'error');
        }
    }

    async optimizeMemory() {
        try {
            const response = await fetch('/api/system-optimizer/optimize-memory', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message || '内存优化完成', 'success');
                this.updateOptimizationProgress('memory-optimization', data.progress || 100);
                await this.loadSystemOptimizer();
                setTimeout(() => this.updateOptimizationProgress('memory-optimization', 0), 1500);
            } else {
                throw new Error(data.error || '内存优化失败');
            }
        } catch (error) {
            console.error('内存优化失败:', error);
            this.showNotification('内存优化失败: ' + error.message, 'error');
        }
    }

    async optimizeDisk() {
        try {
            const response = await fetch('/api/system-optimizer/optimize-disk', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message || '磁盘优化完成', 'success');
                this.updateOptimizationProgress('disk-optimization', data.progress || 100);
                await this.loadSystemOptimizer();
                setTimeout(() => this.updateOptimizationProgress('disk-optimization', 0), 1500);
            } else {
                throw new Error(data.error || '磁盘优化失败');
            }
        } catch (error) {
            console.error('磁盘优化失败:', error);
            this.showNotification('磁盘优化失败: ' + error.message, 'error');
        }
    }

    updateOptimizationProgress(elementId, progress) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = `${progress}%`;
        }
    }

    async saveSecuritySettings() {
        const settings = {
            input_validation: document.getElementById('input-validation').checked,
            rate_limiting: document.getElementById('rate-limiting').checked,
            sql_injection_protection: document.getElementById('sql-injection-protection').checked,
            xss_protection: document.getElementById('xss-protection').checked
        };

        try {
            const response = await fetch('/api/system-optimizer/security-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('安全设置已保存', 'success');
            } else {
                throw new Error(data.error || '保存安全设置失败');
            }
        } catch (error) {
            console.error('保存安全设置失败:', error);
            this.showNotification('保存安全设置失败: ' + error.message, 'error');
        }
    }

    async saveTrafficSettings() {
        const settings = {
            request_limit: parseInt(document.getElementById('request-limit').value),
            concurrent_limit: parseInt(document.getElementById('concurrent-limit').value),
            ip_whitelist: document.getElementById('ip-whitelist').value.split('\n').filter(ip => ip.trim())
        };

        try {
            const response = await fetch('/api/system-optimizer/traffic-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('流量设置已保存', 'success');
            } else {
                throw new Error(data.error || '保存流量设置失败');
            }
        } catch (error) {
            console.error('保存流量设置失败:', error);
            this.showNotification('保存流量设置失败: ' + error.message, 'error');
        }
    }

    async saveCostSettings() {
        const settings = {
            monthly_budget_limit: parseFloat(document.getElementById('monthly-budget-limit').value),
            per_call_cost_limit: parseFloat(document.getElementById('per-call-cost-limit').value),
            auto_cost_control: document.getElementById('auto-cost-control').checked
        };

        try {
            const response = await fetch('/api/system-optimizer/cost-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('成本设置已保存', 'success');
            } else {
                throw new Error(data.error || '保存成本设置失败');
            }
        } catch (error) {
            console.error('保存成本设置失败:', error);
            this.showNotification('保存成本设置失败: ' + error.message, 'error');
        }
    }

    async runHealthCheck() {
        try {
            const response = await fetch('/api/system-optimizer/health-check', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('健康检查完成', 'success');
                this.updateSystemStats(data);
            } else {
                throw new Error(data.error || '健康检查失败');
            }
        } catch (error) {
            console.error('健康检查失败:', error);
            this.showNotification('健康检查失败: ' + error.message, 'error');
        }
    }

    async refreshSystemStatus() {
        await this.loadSystemOptimizer();
        this.showNotification('系统状态已刷新', 'success');
    }

    async clearCache() {
        try {
            const response = await fetch('/api/system-optimizer/clear-cache', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.showNotification(data.message || '缓存已清理', 'success');
                await this.loadSystemOptimizer();
            } else {
                throw new Error(data.error || '清理缓存失败');
            }
        } catch (error) {
            console.error('清理缓存失败:', error);
            this.showNotification('清理缓存失败: ' + error.message, 'error');
        }
    }

    async optimizeAll() {
        try {
            const response = await fetch('/api/system-optimizer/optimize-all', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.showNotification(data.message || '一键优化完成', 'success');
                await this.loadSystemOptimizer();
                ['cpu-optimization','memory-optimization','disk-optimization'].forEach(id => this.updateOptimizationProgress(id, 100));
                setTimeout(() => ['cpu-optimization','memory-optimization','disk-optimization'].forEach(id => this.updateOptimizationProgress(id, 0)), 1500);
            } else {
                throw new Error(data.error || '一键优化失败');
            }
        } catch (error) {
            console.error('一键优化失败:', error);
            this.showNotification('一键优化失败: ' + error.message, 'error');
        }
    }

    async loadSecuritySettings() {
        try {
            const response = await fetch('/api/system-optimizer/security-settings');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('input-validation').checked = data.input_validation || false;
                document.getElementById('rate-limiting').checked = data.rate_limiting || false;
                document.getElementById('sql-injection-protection').checked = data.sql_injection_protection || false;
                document.getElementById('xss-protection').checked = data.xss_protection || false;
            }
        } catch (error) {
            console.error('加载安全设置失败:', error);
        }
    }

    async loadTrafficSettings() {
        try {
            const response = await fetch('/api/system-optimizer/traffic-settings');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('request-limit').value = data.request_limit || 100;
                document.getElementById('concurrent-limit').value = data.concurrent_limit || 50;
                document.getElementById('ip-whitelist').value = (data.ip_whitelist || []).join('\n');
            }
        } catch (error) {
            console.error('加载流量设置失败:', error);
        }
    }

    async loadCostSettings() {
        try {
            const response = await fetch('/api/system-optimizer/cost-settings');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('monthly-budget-limit').value = data.monthly_budget_limit || 1000;
                document.getElementById('per-call-cost-limit').value = data.per_call_cost_limit || 0.1;
                document.getElementById('auto-cost-control').checked = data.auto_cost_control || false;
            }
        } catch (error) {
            console.error('加载成本设置失败:', error);
        }
    }

    // 数据分析
    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            const analytics = await response.json();
            this.updateAnalyticsDisplay(analytics);
            this.updateStatisticsCards(analytics); // 添加统计卡片更新
            this.initializeCharts();
        } catch (error) {
            console.error('加载分析数据失败:', error);
        }
    }

    // 初始化图表
    initializeCharts() {
        if (!this.charts) {
            this.charts = {};
        }
        this.updateCharts();
    }
    
    // 清理连接
    cleanupConnections() {
        // 关闭WebSocket连接
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        // 清理所有定时器
        Object.values(this.refreshIntervals).forEach(interval => {
            clearInterval(interval);
        });
        this.refreshIntervals = {};
    }

    // 销毁所有图表
    destroyAllCharts() {
        if (!this.charts) return;
        
        Object.keys(this.charts).forEach(chartId => {
            if (this.charts[chartId]) {
                try {
                    this.charts[chartId].destroy();
                } catch (e) {
                    console.warn(`Error destroying chart ${chartId}:`, e);
                }
                this.charts[chartId] = null;
            }
        });
        
        // 清理charts对象
        this.charts = {};
    }
    
    // 安全的图表创建方法
    createChart(canvasId, chartConfig) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element '${canvasId}' not found`);
            return null;
        }
        
        // 确保charts对象存在
        if (!this.charts) {
            this.charts = {};
        }
        
        // 销毁现有图表
        if (this.charts[canvasId]) {
            try {
                this.charts[canvasId].destroy();
            } catch (e) {
                console.warn(`Error destroying chart ${canvasId}:`, e);
            }
            this.charts[canvasId] = null;
        }
        
        try {
            const ctx = canvas.getContext('2d');
            this.charts[canvasId] = new Chart(ctx, chartConfig);
            return this.charts[canvasId];
        } catch (e) {
            console.error(`Error creating chart ${canvasId}:`, e);
            return null;
        }
    }

    // 更新所有图表
    async updateCharts() {
        try {
            const timeRange = document.getElementById('timeRange').value;
            const chartType = document.getElementById('chartType').value;
            const dataDimension = document.getElementById('dataDimension').value;

            // 获取数据
            const response = await fetch(`/api/analytics?timeRange=${timeRange}&dimension=${dataDimension}`);
            const data = await response.json();

            // 更新统计卡片
            this.updateStatisticsCards(data);

            // 更新图表
            this.updateMainChart(data, chartType);
            this.updateDistributionChart(data);
            this.updateTrendChart(data);
            this.updatePriorityChart(data);

            // 更新分析报告
            this.updateAnalyticsReport(data);

        } catch (error) {
            console.error('更新图表失败:', error);
            this.showNotification('更新图表失败: ' + error.message, 'error');
        }
    }

    // 更新统计卡片
    updateStatisticsCards(data) {
        // 更新工单统计
        const total = data.workorders?.total || 0;
        const open = data.workorders?.open || 0;
        const inProgress = data.workorders?.in_progress || 0;
        const resolved = data.workorders?.resolved || 0;
        const avgSatisfaction = data.satisfaction?.average || 0;

        // 更新工单统计数字（使用正确的元素ID）
        if (document.getElementById('workorders-total')) {
            document.getElementById('workorders-total').textContent = total;
        }
        if (document.getElementById('workorders-open')) {
            document.getElementById('workorders-open').textContent = open;
        }
        if (document.getElementById('workorders-progress')) {
            document.getElementById('workorders-progress').textContent = inProgress;
        }
        if (document.getElementById('workorders-resolved')) {
            document.getElementById('workorders-resolved').textContent = resolved;
        }
        
        // 同时更新其他可能的元素ID
        if (document.getElementById('totalWorkorders')) {
            document.getElementById('totalWorkorders').textContent = total;
        }
        if (document.getElementById('openWorkorders')) {
            document.getElementById('openWorkorders').textContent = open;
        }
        if (document.getElementById('resolvedWorkorders')) {
            document.getElementById('resolvedWorkorders').textContent = resolved;
        }
        document.getElementById('avgSatisfaction').textContent = avgSatisfaction.toFixed(1);

        // 更新预警统计
        const alertTotal = data.alerts?.total || 0;
        const alertActive = data.alerts?.active || 0;
        const alertCritical = data.alerts?.by_level?.critical || 0;
        const alertWarning = data.alerts?.by_level?.warning || 0;
        const alertError = data.alerts?.by_level?.error || 0;

        // 更新预警统计显示
        if (document.getElementById('critical-alerts')) {
            document.getElementById('critical-alerts').textContent = alertCritical;
        }
        if (document.getElementById('warning-alerts')) {
            document.getElementById('warning-alerts').textContent = alertWarning;
        }
        if (document.getElementById('error-alerts')) {
            document.getElementById('error-alerts').textContent = alertError;
        }
        if (document.getElementById('total-alerts-count')) {
            document.getElementById('total-alerts-count').textContent = alertTotal;
        }

        // 更新性能统计
        const performanceScore = data.performance?.score || 0;
        const performanceTrend = data.performance?.trend || 'stable';
        
        if (document.getElementById('performance-score')) {
            document.getElementById('performance-score').textContent = performanceScore.toFixed(1);
        }
        if (document.getElementById('performance-trend')) {
            document.getElementById('performance-trend').textContent = this.getPerformanceTrendText(performanceTrend);
        }

        // 更新满意度统计
        const satisfactionAvg = data.satisfaction?.average || 0;
        const satisfactionCount = data.satisfaction?.count || 0;
        
        if (document.getElementById('satisfaction-avg')) {
            document.getElementById('satisfaction-avg').textContent = satisfactionAvg.toFixed(1);
        }
        if (document.getElementById('satisfaction-count')) {
            document.getElementById('satisfaction-count').textContent = satisfactionCount;
        }

        // 更新进度条
        if (total > 0) {
            document.getElementById('openProgress').style.width = `${(open / total) * 100}%`;
            document.getElementById('resolvedProgress').style.width = `${(resolved / total) * 100}%`;
            document.getElementById('satisfactionProgress').style.width = `${(avgSatisfaction / 5) * 100}%`;
        }
    }

    // 更新主图表
    updateMainChart(data, chartType) {
        const chartData = this.prepareChartData(data, chartType);
        
        const chartConfig = {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '数据分析趋势'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: chartType === 'pie' || chartType === 'doughnut' ? {} : {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '时间'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '数量'
                        }
                    }
                }
            }
        };
        
        this.createChart('mainChart', chartConfig);
    }

    // 更新分布图表
    updateDistributionChart(data) {
        const currentDimension = document.getElementById('dataDimension')?.value || 'workorders';
        
        let labels, values, title, backgroundColor;
        
        if (currentDimension === 'alerts') {
            // 预警级别分布
            const alertLevels = data.alerts?.by_level || {};
            labels = Object.keys(alertLevels);
            values = Object.values(alertLevels);
            title = '预警级别分布';
            backgroundColor = [
                '#FF6384', // critical - 红色
                '#FFCE56', // warning - 黄色
                '#36A2EB', // error - 蓝色
                '#4BC0C0', // info - 青色
                '#9966FF'  // 其他
            ];
        } else if (currentDimension === 'performance') {
            // 性能指标分布
            const performanceMetrics = data.performance?.by_level || {};
            labels = Object.keys(performanceMetrics);
            values = Object.values(performanceMetrics);
            title = '性能指标分布';
            backgroundColor = [
                '#28a745', // 优秀 - 绿色
                '#ffc107', // 良好 - 黄色
                '#fd7e14', // 一般 - 橙色
                '#dc3545'  // 差 - 红色
            ];
        } else if (currentDimension === 'satisfaction') {
            // 满意度分布
            const satisfactionLevels = data.satisfaction?.by_level || {};
            labels = Object.keys(satisfactionLevels);
            values = Object.values(satisfactionLevels);
            title = '满意度分布';
            backgroundColor = [
                '#28a745', // 非常满意 - 绿色
                '#ffc107', // 满意 - 黄色
                '#fd7e14', // 一般 - 橙色
                '#dc3545'  // 不满意 - 红色
            ];
        } else {
            // 工单分类分布
            const categories = data.workorders?.by_category || {};
            labels = Object.keys(categories);
            values = Object.values(categories);
            title = '工单分类分布';
            backgroundColor = [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40'
            ];
        }

        const chartConfig = {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColor
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: title
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                }
            }
        };
        
        this.createChart('distributionChart', chartConfig);
    }

    // 更新趋势图表
    updateTrendChart(data) {
        const ctx = document.getElementById('trendChart').getContext('2d');
        
        if (this.charts.trendChart) {
            this.charts.trendChart.destroy();
        }

        const trendData = data.trend || [];
        const labels = trendData.map(item => item.date);
        const workorders = trendData.map(item => item.workorders);
        const alerts = trendData.map(item => item.alerts);

        this.charts.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '工单数量',
                    data: workorders,
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4
                }, {
                    label: '预警数量',
                    data: alerts,
                    borderColor: '#FF6384',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '时间趋势分析'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '数量'
                        }
                    }
                }
            }
        });
    }

    // 更新优先级图表
    updatePriorityChart(data) {
        const ctx = document.getElementById('priorityChart').getContext('2d');
        
        if (this.charts.priorityChart) {
            this.charts.priorityChart.destroy();
        }

        const currentDimension = document.getElementById('dataDimension')?.value || 'workorders';
        
        let labels, values, title, backgroundColor, label;
        
        if (currentDimension === 'alerts') {
            // 预警严重程度分布
            const alertSeverities = data.alerts?.by_severity || {};
            labels = Object.keys(alertSeverities).map(s => this.getSeverityText(s));
            values = Object.values(alertSeverities);
            title = '预警严重程度分布';
            label = '预警数量';
            backgroundColor = [
                '#28a745', // low - 绿色
                '#ffc107', // medium - 黄色
                '#fd7e14', // high - 橙色
                '#dc3545'  // critical - 红色
            ];
        } else if (currentDimension === 'performance') {
            // 性能指标分布
            const performanceMetrics = data.performance?.by_metric || {};
            labels = Object.keys(performanceMetrics);
            values = Object.values(performanceMetrics);
            title = '性能指标分布';
            label = '性能值';
            backgroundColor = [
                '#28a745', // 优秀 - 绿色
                '#ffc107', // 良好 - 黄色
                '#fd7e14', // 一般 - 橙色
                '#dc3545'  // 差 - 红色
            ];
        } else if (currentDimension === 'satisfaction') {
            // 满意度分布
            const satisfactionLevels = data.satisfaction?.by_level || {};
            labels = Object.keys(satisfactionLevels).map(s => this.getSatisfactionText(s));
            values = Object.values(satisfactionLevels);
            title = '满意度分布';
            label = '满意度数量';
            backgroundColor = [
                '#28a745', // 非常满意 - 绿色
                '#ffc107', // 满意 - 黄色
                '#fd7e14', // 一般 - 橙色
                '#dc3545'  // 不满意 - 红色
            ];
        } else {
            // 工单优先级分布
            const priorities = data.workorders?.by_priority || {};
            labels = Object.keys(priorities).map(p => this.getPriorityText(p));
            values = Object.values(priorities);
            title = '工单优先级分布';
            label = '工单数量';
            backgroundColor = [
                '#28a745', // 低 - 绿色
                '#ffc107', // 中 - 黄色
                '#fd7e14', // 高 - 橙色
                '#dc3545'  // 紧急 - 红色
            ];
        }

        this.charts.priorityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
                    backgroundColor: backgroundColor
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: title
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

    // 准备图表数据
    prepareChartData(data, chartType) {
        const trendData = data.trend || [];
        const labels = trendData.map(item => item.date);
        const workorders = trendData.map(item => item.workorders);
        const alerts = trendData.map(item => item.alerts);
        const performance = trendData.map(item => item.performance || 0);
        const satisfaction = trendData.map(item => item.satisfaction || 0);

        if (chartType === 'pie' || chartType === 'doughnut') {
            // 根据数据维度选择显示内容
            const currentDimension = document.getElementById('dataDimension')?.value || 'workorders';
            
            if (currentDimension === 'alerts') {
                const alertLevels = data.alerts?.by_level || {};
                return {
                    labels: Object.keys(alertLevels),
                    datasets: [{
                        data: Object.values(alertLevels),
                        backgroundColor: [
                            '#FF6384', // critical - 红色
                            '#FFCE56', // warning - 黄色
                            '#36A2EB', // error - 蓝色
                            '#4BC0C0', // info - 青色
                            '#9966FF'  // 其他
                        ]
                    }]
                };
            } else if (currentDimension === 'performance') {
                // 性能指标分布
                const performanceMetrics = data.performance || {};
                return {
                    labels: Object.keys(performanceMetrics),
                    datasets: [{
                        data: Object.values(performanceMetrics),
                        backgroundColor: [
                            '#28a745', // 优秀 - 绿色
                            '#ffc107', // 良好 - 黄色
                            '#fd7e14', // 一般 - 橙色
                            '#dc3545'  // 差 - 红色
                        ]
                    }]
                };
            } else if (currentDimension === 'satisfaction') {
                // 满意度分布
                const satisfactionLevels = data.satisfaction?.by_level || {};
                return {
                    labels: Object.keys(satisfactionLevels),
                    datasets: [{
                        data: Object.values(satisfactionLevels),
                        backgroundColor: [
                            '#28a745', // 非常满意 - 绿色
                            '#ffc107', // 满意 - 黄色
                            '#fd7e14', // 一般 - 橙色
                            '#dc3545'  // 不满意 - 红色
                        ]
                    }]
                };
            } else {
                const categories = data.workorders?.by_category || {};
                return {
                    labels: Object.keys(categories),
                    datasets: [{
                        data: Object.values(categories),
                        backgroundColor: [
                            '#FF6384',
                            '#36A2EB',
                            '#FFCE56',
                            '#4BC0C0',
                            '#9966FF',
                            '#FF9F40'
                        ]
                    }]
                };
            }
        } else {
            // 线图和柱状图根据数据维度显示不同内容
            const currentDimension = document.getElementById('dataDimension')?.value || 'workorders';
            const datasets = [];

            if (currentDimension === 'performance') {
                // 性能指标图表
                datasets.push({
                    label: '性能指标',
                    data: performance,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: chartType === 'line' ? 0.4 : 0
                });
            } else if (currentDimension === 'satisfaction') {
                // 满意度图表
                datasets.push({
                    label: '满意度评分',
                    data: satisfaction,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: chartType === 'line' ? 0.4 : 0
                });
            } else {
                // 默认显示工单和预警数据
                datasets.push({
                    label: '工单数量',
                    data: workorders,
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: chartType === 'line' ? 0.4 : 0
                });

                // 如果有预警数据，添加预警数据集
                if (alerts.some(alert => alert > 0)) {
                    datasets.push({
                        label: '预警数量',
                        data: alerts,
                        borderColor: '#FF6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: chartType === 'line' ? 0.4 : 0
                    });
                }
            }

            return {
                labels: labels,
                datasets: datasets
            };
        }
    }

    // 导出图表
    exportChart(chartId) {
        if (this.charts[chartId]) {
            const link = document.createElement('a');
            link.download = `${chartId}_chart.png`;
            link.href = this.charts[chartId].toBase64Image();
            link.click();
        }
    }

    // 全屏图表
    fullscreenChart(chartId) {
        // 这里可以实现全屏显示功能
        this.showNotification('全屏功能开发中', 'info');
    }

    // 导出报告
    async exportReport() {
        try {
            const response = await fetch('/api/analytics/export');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'analytics_report.xlsx';
            link.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('导出报告失败:', error);
            this.showNotification('导出报告失败: ' + error.message, 'error');
        }
    }

    // 打印报告
    printReport() {
        window.print();
    }

    // Agent执行历史相关功能
    async refreshAgentHistory() {
        try {
            const response = await fetch('/api/agent/action-history?limit=20');
            const data = await response.json();
            
            if (data.success) {
                this.updateAgentExecutionHistory(data.history);
                this.showNotification(`已加载 ${data.count} 条执行历史`, 'success');
            } else {
                throw new Error(data.error || '获取执行历史失败');
            }
        } catch (error) {
            console.error('刷新Agent历史失败:', error);
            this.showNotification('刷新Agent历史失败: ' + error.message, 'error');
        }
    }

    async triggerSampleAction() {
        try {
            const response = await fetch('/api/agent/trigger-sample', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                // 刷新执行历史
                await this.refreshAgentHistory();
            } else {
                throw new Error(data.error || '触发示例动作失败');
            }
        } catch (error) {
            console.error('触发示例动作失败:', error);
            this.showNotification('触发示例动作失败: ' + error.message, 'error');
        }
    }

    async clearAgentHistory() {
        if (!confirm('确定要清空Agent执行历史吗？此操作不可恢复。')) {
            return;
        }
        
        try {
            const response = await fetch('/api/agent/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                // 清空显示
                this.updateAgentExecutionHistory([]);
            } else {
                throw new Error(data.error || '清空历史失败');
            }
        } catch (error) {
            console.error('清空Agent历史失败:', error);
            this.showNotification('清空Agent历史失败: ' + error.message, 'error');
        }
    }

    updateAgentExecutionHistory(history) {
        const container = document.getElementById('agent-execution-history');
        
        if (!history || history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <p>暂无执行历史</p>
                </div>
            `;
            return;
        }

        const historyHtml = history.map(record => {
            const startTime = new Date(record.start_time * 1000).toLocaleString();
            const endTime = new Date(record.end_time * 1000).toLocaleString();
            const duration = Math.round((record.end_time - record.start_time) * 100) / 100;
            
            const priorityColor = {
                5: 'danger',
                4: 'warning', 
                3: 'info',
                2: 'secondary',
                1: 'light'
            }[record.priority] || 'secondary';
            
            const confidenceColor = record.confidence >= 0.8 ? 'success' : 
                                  record.confidence >= 0.5 ? 'warning' : 'danger';
            
            return `
                <div class="card mb-2">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${record.description}</h6>
                                <div class="d-flex gap-3 mb-2">
                                    <span class="badge bg-${priorityColor}">优先级 ${record.priority}</span>
                                    <span class="badge bg-${confidenceColor}">置信度 ${(record.confidence * 100).toFixed(0)}%</span>
                                    <span class="badge bg-${record.success ? 'success' : 'danger'}">${record.success ? '成功' : '失败'}</span>
                                </div>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>开始: ${startTime} | 
                                    <i class="fas fa-stopwatch me-1"></i>耗时: ${duration}秒
                                </small>
                            </div>
                            <div class="ms-3">
                                <span class="badge bg-primary">${record.action_type}</span>
                            </div>
                        </div>
                        ${record.result && record.result.message ? `
                            <div class="mt-2">
                                <small class="text-muted">结果: ${record.result.message}</small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = historyHtml;
    }

    // 更新分析报告
    updateAnalyticsReport(data) {
        const reportContainer = document.getElementById('analytics-report');
        
        if (!reportContainer) return;
        
        const summary = data.summary || {};
        const workorders = data.workorders || {};
        const satisfaction = data.satisfaction || {};
        const alerts = data.alerts || {};
        const performance = data.performance || {};
        
        const reportHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-chart-bar me-2"></i>工单统计概览</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td>总工单数</td>
                                <td><span class="badge bg-primary">${workorders.total || 0}</span></td>
                            </tr>
                            <tr>
                                <td>待处理</td>
                                <td><span class="badge bg-warning">${workorders.open || 0}</span></td>
                            </tr>
                            <tr>
                                <td>处理中</td>
                                <td><span class="badge bg-info">${workorders.in_progress || 0}</span></td>
                            </tr>
                            <tr>
                                <td>已解决</td>
                                <td><span class="badge bg-success">${workorders.resolved || 0}</span></td>
                            </tr>
                            <tr>
                                <td>已关闭</td>
                                <td><span class="badge bg-secondary">${workorders.closed || 0}</span></td>
                            </tr>
                        </table>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-star me-2"></i>满意度分析</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td>平均满意度</td>
                                <td><span class="badge bg-success">${satisfaction.average || 0}/5.0</span></td>
                            </tr>
                            <tr>
                                <td>5星评价</td>
                                <td>${satisfaction.distribution?.['5'] || 0} 个</td>
                            </tr>
                            <tr>
                                <td>4星评价</td>
                                <td>${satisfaction.distribution?.['4'] || 0} 个</td>
                            </tr>
                            <tr>
                                <td>3星评价</td>
                                <td>${satisfaction.distribution?.['3'] || 0} 个</td>
                            </tr>
                            <tr>
                                <td>2星及以下</td>
                                <td>${(satisfaction.distribution?.['2'] || 0) + (satisfaction.distribution?.['1'] || 0)} 个</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>预警统计</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td>总预警数</td>
                                <td><span class="badge bg-danger">${alerts.total || 0}</span></td>
                            </tr>
                            <tr>
                                <td>活跃预警</td>
                                <td><span class="badge bg-warning">${alerts.active || 0}</span></td>
                            </tr>
                            <tr>
                                <td>已解决</td>
                                <td><span class="badge bg-success">${alerts.resolved || 0}</span></td>
                            </tr>
                        </table>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-tachometer-alt me-2"></i>性能指标</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td>响应时间</td>
                                <td>${performance.response_time || 0} 秒</td>
                            </tr>
                            <tr>
                                <td>系统可用性</td>
                                <td>${performance.uptime || 0}%</td>
                            </tr>
                            <tr>
                                <td>错误率</td>
                                <td>${performance.error_rate || 0}%</td>
                            </tr>
                            <tr>
                                <td>吞吐量</td>
                                <td>${performance.throughput || 0} 请求/小时</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <h6><i class="fas fa-chart-line me-2"></i>关键指标总结</h6>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title text-primary">${summary.resolution_rate || 0}%</h5>
                                    <p class="card-text">解决率</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title text-success">${summary.avg_satisfaction || 0}</h5>
                                    <p class="card-text">平均满意度</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title text-warning">${summary.active_alerts || 0}</h5>
                                    <p class="card-text">活跃预警</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title text-info">${summary.total_workorders || 0}</h5>
                                    <p class="card-text">总工单数</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        reportContainer.innerHTML = reportHtml;
    }

    updateAnalyticsDisplay(analytics) {
        // 更新分析报告
        const reportContainer = document.getElementById('analytics-report');
        if (analytics.summary) {
            reportContainer.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>性能指标</h6>
                        <ul class="list-unstyled">
                            <li>总工单数: ${analytics.summary.total_orders || 0}</li>
                            <li>解决率: ${Math.round((analytics.summary.resolution_rate || 0) * 100)}%</li>
                            <li>平均解决时间: ${analytics.summary.avg_resolution_time_hours || 0}小时</li>
                            <li>平均满意度: ${analytics.summary.avg_satisfaction || 0}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>趋势分析</h6>
                        <ul class="list-unstyled">
                            <li>工单趋势: ${analytics.summary.trends?.orders_trend ? '上升' : '下降'}</li>
                            <li>满意度趋势: ${analytics.summary.trends?.satisfaction_trend ? '上升' : '下降'}</li>
                            <li>解决时间趋势: ${analytics.summary.trends?.resolution_time_trend ? '上升' : '下降'}</li>
                        </ul>
                    </div>
                </div>
            `;
        }

        // 更新类别分布图
        if (analytics.category_distribution && this.charts.category) {
            const labels = Object.keys(analytics.category_distribution);
            const data = Object.values(analytics.category_distribution);
            
            this.charts.category.data.labels = labels;
            this.charts.category.data.datasets[0].data = data;
            this.charts.category.update();
        }
    }

    // 系统设置
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            this.updateSettingsDisplay(settings);
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }

    updateSettingsDisplay(settings) {
        if (settings.api_timeout !== undefined) document.getElementById('api-timeout').value = settings.api_timeout;
        if (settings.max_history !== undefined) document.getElementById('max-history').value = settings.max_history;
        if (settings.refresh_interval !== undefined) document.getElementById('refresh-interval').value = settings.refresh_interval;
        if (settings.auto_monitoring !== undefined) document.getElementById('auto-monitoring').checked = settings.auto_monitoring;
        if (settings.agent_mode !== undefined) document.getElementById('agent-mode').checked = settings.agent_mode;
        // 新增：API与模型、端口、日志级别（如页面存在对应输入框则填充）
        const map = [
            ['api-provider','api_provider'],
            ['api-base-url','api_base_url'],
            ['api-key','api_key'],
            ['model-name','model_name'],
            ['model-temperature','model_temperature'],
            ['model-max-tokens','model_max_tokens'],
            ['server-port','server_port'],
            ['websocket-port','websocket_port'],
            ['log-level','log_level']
        ];
        map.forEach(([id, key]) => {
            const el = document.getElementById(id);
            if (el && settings[key] !== undefined) el.value = settings[key];
        });
        
        // 更新温度滑块显示值
        const tempSlider = document.getElementById('model-temperature');
        const tempValue = document.getElementById('temperature-value');
        if (tempSlider && tempValue) {
            tempSlider.addEventListener('input', function() {
                tempValue.textContent = this.value;
            });
            tempValue.textContent = tempSlider.value;
        }
        
        // 更新服务状态显示
        this.updateServiceStatus(settings);
    }

    async saveSystemSettings() {
        const settings = {
            api_timeout: parseInt(document.getElementById('api-timeout').value),
            max_history: parseInt(document.getElementById('max-history').value),
            refresh_interval: parseInt(document.getElementById('refresh-interval').value),
            auto_monitoring: document.getElementById('auto-monitoring').checked,
            agent_mode: document.getElementById('agent-mode').checked,
            api_provider: document.getElementById('api-provider')?.value || '',
            api_base_url: document.getElementById('api-base-url')?.value || '',
            api_key: document.getElementById('api-key')?.value || '',
            model_name: document.getElementById('model-name')?.value || '',
            model_temperature: parseFloat(document.getElementById('model-temperature')?.value || 0.7),
            model_max_tokens: parseInt(document.getElementById('model-max-tokens')?.value || 1000),
            server_port: parseInt(document.getElementById('server-port')?.value || 5000),
            websocket_port: parseInt(document.getElementById('websocket-port')?.value || 8765),
            log_level: document.getElementById('log-level')?.value || 'INFO'
        };

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('设置保存成功', 'success');
            } else {
                this.showNotification('保存设置失败', 'error');
            }
        } catch (error) {
            console.error('保存设置失败:', error);
            this.showNotification('保存设置失败', 'error');
        }
    }

    // 更新服务状态显示
    updateServiceStatus(settings) {
        // 更新仪表板服务状态卡片
        if (settings.current_server_port !== undefined) {
            const webPortEl = document.getElementById('web-port-status');
            if (webPortEl) webPortEl.textContent = settings.current_server_port;
        }
        if (settings.current_websocket_port !== undefined) {
            const wsPortEl = document.getElementById('ws-port-status');
            if (wsPortEl) wsPortEl.textContent = settings.current_websocket_port;
        }
        if (settings.log_level !== undefined) {
            const logLevelEl = document.getElementById('log-level-status');
            if (logLevelEl) logLevelEl.textContent = settings.log_level;
        }
        if (settings.uptime_seconds !== undefined) {
            const uptimeEl = document.getElementById('uptime-status');
            if (uptimeEl) {
                const hours = Math.floor(settings.uptime_seconds / 3600);
                const minutes = Math.floor((settings.uptime_seconds % 3600) / 60);
                uptimeEl.textContent = `${hours}小时${minutes}分钟`;
            }
        }
        
        // 更新系统设置页面的当前端口显示
        const currentPortEl = document.getElementById('current-server-port');
        if (currentPortEl && settings.current_server_port !== undefined) {
            currentPortEl.textContent = settings.current_server_port;
        }
    }

    // 刷新服务状态
    async refreshServiceStatus() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            this.updateServiceStatus(settings);
            this.showNotification('服务状态已刷新', 'success');
        } catch (error) {
            console.error('刷新服务状态失败:', error);
            this.showNotification('刷新服务状态失败', 'error');
        }
    }

    // 测试API连接
    async testApiConnection() {
        try {
            const apiProvider = document.getElementById('api-provider').value;
            const apiBaseUrl = document.getElementById('api-base-url').value;
            const apiKey = document.getElementById('api-key').value;
            const modelName = document.getElementById('model-name').value;
            
            const response = await fetch('/api/test/connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_provider: apiProvider,
                    api_base_url: apiBaseUrl,
                    api_key: apiKey,
                    model_name: modelName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification(`API连接测试成功: ${result.message}`, 'success');
            } else {
                this.showNotification(`API连接测试失败: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('API连接测试失败:', error);
            this.showNotification('API连接测试失败', 'error');
        }
    }

    // 测试模型回答
    async testModelResponse() {
        try {
            const testMessage = prompt('请输入测试消息:', '你好，请简单介绍一下你自己');
            if (!testMessage) return;
            
            const response = await fetch('/api/test/model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    test_message: testMessage
                })
            });
            
            const result = await response.json();
            if (result.success) {
                const message = `模型回答测试成功:\n\n问题: ${result.test_message}\n\n回答: ${result.response}\n\n响应时间: ${result.response_time}`;
                alert(message);
                this.showNotification('模型回答测试成功', 'success');
            } else {
                this.showNotification(`模型回答测试失败: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('模型回答测试失败:', error);
            this.showNotification('模型回答测试失败', 'error');
        }
    }

    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system/info');
            const info = await response.json();
            this.updateSystemInfoDisplay(info);
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    }

    updateSystemInfoDisplay(info) {
        const container = document.getElementById('system-info');
        container.innerHTML = `
            <div class="mb-3">
                <strong>系统版本:</strong> ${info.version || '1.0.0'}
            </div>
            <div class="mb-3">
                <strong>Python版本:</strong> ${info.python_version || '未知'}
            </div>
            <div class="mb-3">
                <strong>数据库:</strong> ${info.database || 'SQLite'}
            </div>
            <div class="mb-3">
                <strong>运行时间:</strong> ${info.uptime || '未知'}
            </div>
            <div class="mb-3">
                <strong>内存使用:</strong> ${info.memory_usage || '0'} MB
            </div>
        `;
    }

    // 工具函数
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

    getAlertColor(level) {
        const colorMap = {
            'critical': 'danger',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return colorMap[level] || 'secondary';
    }

    getPriorityText(priority) {
        const priorityMap = {
            'low': '低',
            'medium': '中',
            'high': '高',
            'urgent': '紧急'
        };
        return priorityMap[priority] || priority;
    }

    getSeverityText(severity) {
        const severityMap = {
            'low': '低',
            'medium': '中',
            'high': '高',
            'critical': '严重'
        };
        return severityMap[severity] || severity;
    }

    getSatisfactionText(level) {
        const satisfactionMap = {
            'very_satisfied': '非常满意',
            'satisfied': '满意',
            'neutral': '一般',
            'dissatisfied': '不满意'
        };
        return satisfactionMap[level] || level;
    }

    getPerformanceTrendText(trend) {
        const trendMap = {
            'up': '上升',
            'down': '下降',
            'stable': '稳定'
        };
        return trendMap[trend] || trend;
    }

    getPriorityColor(priority) {
        const colorMap = {
            'low': 'secondary',
            'medium': 'primary',
            'high': 'warning',
            'urgent': 'danger'
        };
        return colorMap[priority] || 'secondary';
    }

    getStatusText(status) {
        const statusMap = {
            'open': '待处理',
            'in_progress': '处理中',
            'resolved': '已解决',
            'closed': '已关闭'
        };
        return statusMap[status] || status;
    }

    // 统计数字预览功能
    async showStatPreview(type, status) {
        try {
            let title = '';
            let data = [];
            let apiUrl = '';

            switch (type) {
                case 'workorder':
                    title = this.getWorkorderPreviewTitle(status);
                    apiUrl = status === 'all' ? '/api/workorders' : `/api/workorders/by-status/${status}`;
                    break;
                case 'alert':
                    title = this.getAlertPreviewTitle(status);
                    apiUrl = `/api/alerts/by-level/${status}`;
                    break;
                case 'knowledge':
                    title = this.getKnowledgePreviewTitle(status);
                    apiUrl = `/api/knowledge/by-status/${status}`;
                    break;
                default:
                    return;
            }

            // 显示加载状态
            this.showLoadingModal(title);

            const response = await fetch(apiUrl);
            const result = await response.json();

            // 处理不同的API响应结构
            if (result.success !== false) {
                if (result.success === true) {
                    // 新API结构: {success: true, data: {workorders: [...]}}
                    data = result.data[type + 's'] || result.data.knowledge || [];
                } else if (result.workorders) {
                    // 旧API结构: {workorders: [...], page: 1, ...}
                    data = result.workorders || [];
                } else if (result.alerts) {
                    // 预警API结构
                    data = result.alerts || [];
                } else if (result.knowledge) {
                    // 知识库API结构
                    data = result.knowledge || [];
                } else {
                    data = [];
                }
                this.showPreviewModal(title, type, data);
            } else {
                const errorMsg = result.error || result.message || '未知错误';
                this.showNotification('获取数据失败: ' + errorMsg, 'error');
            }
        } catch (error) {
            console.error('预览失败:', error);
            this.showNotification('预览失败: ' + error.message, 'error');
        }
    }

    getWorkorderPreviewTitle(status) {
        const titles = {
            'all': '所有工单',
            'open': '待处理工单',
            'in_progress': '处理中工单',
            'resolved': '已解决工单',
            'closed': '已关闭工单'
        };
        return titles[status] || '工单列表';
    }

    getAlertPreviewTitle(level) {
        const titles = {
            'critical': '严重预警',
            'warning': '警告预警',
            'info': '信息预警'
        };
        return titles[level] || '预警列表';
    }

    getKnowledgePreviewTitle(status) {
        const titles = {
            'verified': '已验证知识',
            'unverified': '未验证知识'
        };
        return titles[status] || '知识库条目';
    }

    showLoadingModal(title) {
        const modalHtml = `
            <div class="modal fade" id="statPreviewModal" tabindex="-1" data-bs-backdrop="true" data-bs-keyboard="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <p class="mt-2">正在加载数据...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框和遮罩
        this.removeExistingModal();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById('statPreviewModal');
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true
        });
        
        // 添加事件监听器确保正确清理
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.cleanupModal();
        });
        
        modal.show();
    }

    showPreviewModal(title, type, data) {
        let contentHtml = '';
        
        if (data.length === 0) {
            contentHtml = `
                <div class="text-center py-4">
                    <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">暂无数据</h5>
                    <p class="text-muted">当前条件下没有找到相关记录</p>
                </div>
            `;
        } else {
            switch (type) {
                case 'workorder':
                    contentHtml = this.generateWorkorderPreviewHtml(data);
                    break;
                case 'alert':
                    contentHtml = this.generateAlertPreviewHtml(data);
                    break;
                case 'knowledge':
                    contentHtml = this.generateKnowledgePreviewHtml(data);
                    break;
            }
        }

        const modalHtml = `
            <div class="modal fade" id="statPreviewModal" tabindex="-1" data-bs-backdrop="true" data-bs-keyboard="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-eye me-2"></i>${title}
                                <span class="badge bg-primary ms-2">${data.length} 条记录</span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                        </div>
                        <div class="modal-body">
                            ${contentHtml}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            <button type="button" class="btn btn-primary" onclick="dashboard.goToFullView('${type}', '${status}')">查看完整列表</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框和遮罩
        this.removeExistingModal();
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById('statPreviewModal');
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true
        });
        
        // 添加事件监听器确保正确清理
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.cleanupModal();
        });
        
        modal.show();
    }

    generateWorkorderPreviewHtml(workorders) {
        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>工单ID</th>
                            <th>标题</th>
                            <th>状态</th>
                            <th>优先级</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${workorders.map(wo => `
                            <tr>
                                <td>${wo.order_id || wo.id}</td>
                                <td>
                                    <div class="text-truncate" style="max-width: 200px;" title="${wo.title}">
                                        ${wo.title}
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getStatusColor(wo.status)}">
                                        ${this.getStatusText(wo.status)}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getPriorityColor(wo.priority)}">
                                        ${this.getPriorityText(wo.priority)}
                                    </span>
                                </td>
                                <td>${new Date(wo.created_at).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="dashboard.viewWorkOrderDetails(${wo.id})">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    generateAlertPreviewHtml(alerts) {
        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>预警ID</th>
                            <th>消息</th>
                            <th>级别</th>
                            <th>类型</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map(alert => `
                            <tr>
                                <td>${alert.id}</td>
                                <td>
                                    <div class="text-truncate" style="max-width: 300px;" title="${alert.message}">
                                        ${alert.message}
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getAlertLevelColor(alert.level)}">
                                        ${this.getLevelText(alert.level)}
                                    </span>
                                </td>
                                <td>${this.getTypeText(alert.alert_type)}</td>
                                <td>${new Date(alert.created_at).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-success" onclick="dashboard.resolveAlert(${alert.id})">
                                        <i class="fas fa-check"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    generateKnowledgePreviewHtml(knowledge) {
        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>标题</th>
                            <th>分类</th>
                            <th>验证状态</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${knowledge.map(item => `
                            <tr>
                                <td>${item.id}</td>
                                <td>
                                    <div class="text-truncate" style="max-width: 250px;" title="${item.title}">
                                        ${item.title}
                                    </div>
                                </td>
                                <td>${item.category || '未分类'}</td>
                                <td>
                                    <span class="badge bg-${item.is_verified ? 'success' : 'warning'}">
                                        ${item.is_verified ? '已验证' : '未验证'}
                                    </span>
                                </td>
                                <td>${new Date(item.created_at).toLocaleString()}</td>
                                <td>
                                    <div class="btn-group">
                                        ${item.is_verified ? 
                                            `<button class="btn btn-sm btn-outline-warning" onclick="dashboard.unverifyKnowledge(${item.id})" title="取消验证">
                                                <i class="fas fa-times-circle"></i>
                                            </button>` :
                                            `<button class="btn btn-sm btn-outline-success" onclick="dashboard.verifyKnowledge(${item.id})" title="验证">
                                                <i class="fas fa-check-circle"></i>
                                            </button>`
                                        }
                                        <button class="btn btn-sm btn-outline-danger" onclick="dashboard.deleteKnowledge(${item.id})" title="删除">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    getAlertLevelColor(level) {
        const colorMap = {
            'critical': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return colorMap[level] || 'secondary';
    }

    goToFullView(type, status) {
        // 关闭预览模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('statPreviewModal'));
        if (modal) {
            modal.hide();
        }

        // 切换到对应的标签页
        switch (type) {
            case 'workorder':
                this.switchTab('workorders');
                // 设置筛选器
                if (status !== 'all') {
                    setTimeout(() => {
                        const filter = document.getElementById('workorder-status-filter');
                        if (filter) {
                            filter.value = status;
                            this.loadWorkOrders();
                        }
                    }, 100);
                }
                break;
            case 'alert':
                this.switchTab('alerts');
                // 设置筛选器
                setTimeout(() => {
                    const filter = document.getElementById('alert-filter');
                    if (filter) {
                        filter.value = status;
                        this.updateAlertsDisplay();
                    }
                }, 100);
                break;
            case 'knowledge':
                this.switchTab('knowledge');
                break;
        }
    }

    // 模态框清理方法
    removeExistingModal() {
        const existingModal = document.getElementById('statPreviewModal');
        if (existingModal) {
            // 获取模态框实例并销毁
            const modalInstance = bootstrap.Modal.getInstance(existingModal);
            if (modalInstance) {
                modalInstance.dispose();
            }
            existingModal.remove();
        }
        
        // 清理可能残留的遮罩
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // 恢复body的滚动
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    cleanupModal() {
        // 延迟清理，确保动画完成
        setTimeout(() => {
            this.removeExistingModal();
        }, 300);
    }

    getStatusColor(status) {
        const colorMap = {
            'open': 'warning',
            'in_progress': 'info',
            'resolved': 'success',
            'closed': 'secondary'
        };
        return colorMap[status] || 'secondary';
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

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    getSimilarityExplanation(percent) {
        if (percent >= 95) {
            return "语义高度相似，AI建议与人工描述基本一致，建议自动审批";
        } else if (percent >= 90) {
            return "语义较为相似，AI建议与人工描述大体一致，建议人工审核";
        } else if (percent >= 80) {
            return "语义部分相似，AI建议与人工描述有一定差异，需要人工判断";
        } else if (percent >= 60) {
            return "语义相似度较低，AI建议与人工描述差异较大，建议使用人工描述";
        } else {
            return "语义差异很大，AI建议与人工描述差异很大，优先使用人工描述";
        }
    }

    getSimilarityMessage(percent, approved, useHumanResolution = false) {
        if (useHumanResolution) {
            return `人工描述已保存！语义相似度: ${percent}%，AI准确率低于90%，将使用人工描述入库`;
        } else if (approved) {
            return `人工描述已保存！语义相似度: ${percent}%，已自动审批入库`;
        } else if (percent >= 90) {
            return `人工描述已保存！语义相似度: ${percent}%，建议人工审核后审批`;
        } else if (percent >= 80) {
            return `人工描述已保存！语义相似度: ${percent}%，需要人工判断是否审批`;
        } else {
            return `人工描述已保存！语义相似度: ${percent}%，建议使用人工描述入库`;
        }
    }

    showCreateWorkOrderModal() {
        const modal = new bootstrap.Modal(document.getElementById('createWorkOrderModal'));
        modal.show();
    }

    // 新增Agent对话功能
    async sendAgentMessage() {
        const messageInput = document.getElementById('agent-message-input');
        const message = messageInput.value.trim();
        
        if (!message) {
            this.showNotification('请输入消息', 'warning');
            return;
        }

        try {
            // 显示发送状态
            const sendBtn = document.getElementById('send-agent-message');
            const originalText = sendBtn.innerHTML;
            sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>发送中...';
            sendBtn.disabled = true;

            const response = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: {
                        user_id: 'admin',
                        session_id: `agent_session_${Date.now()}`
                    }
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Agent响应成功', 'success');
                // 清空输入框
                messageInput.value = '';
                // 刷新执行历史
                await this.loadAgentExecutionHistory();
            } else {
                this.showNotification('Agent响应失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('发送Agent消息失败:', error);
            this.showNotification('发送Agent消息失败: ' + error.message, 'error');
        } finally {
            // 恢复按钮状态
            const sendBtn = document.getElementById('send-agent-message');
            sendBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i>发送';
            sendBtn.disabled = false;
        }
    }

    // 清空Agent对话
    clearAgentChat() {
        document.getElementById('agent-message-input').value = '';
        this.showNotification('对话已清空', 'info');
    }

    // 加载Agent执行历史
    async loadAgentExecutionHistory() {
        try {
            const response = await fetch('/api/agent/action-history?limit=10');
            const data = await response.json();
            
            if (data.success) {
                this.updateExecutionHistory(data.history);
            }
        } catch (error) {
            console.error('加载Agent执行历史失败:', error);
        }
    }

    // 触发示例动作
    async triggerSampleAction() {
        try {
            const response = await fetch('/api/agent/trigger-sample', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('示例动作执行成功', 'success');
                await this.loadAgentExecutionHistory();
            } else {
                this.showNotification('示例动作执行失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('触发示例动作失败:', error);
            this.showNotification('触发示例动作失败: ' + error.message, 'error');
        }
    }

    // 清空Agent历史
    async clearAgentHistory() {
        if (!confirm('确定要清空Agent执行历史吗？')) {
            return;
        }

        try {
            const response = await fetch('/api/agent/clear-history', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Agent历史已清空', 'success');
                await this.loadAgentExecutionHistory();
            } else {
                this.showNotification('清空Agent历史失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('清空Agent历史失败:', error);
            this.showNotification('清空Agent历史失败: ' + error.message, 'error');
        }
    }
}

// 飞书同步管理器
class FeishuSyncManager {
    constructor() {
        this.loadConfig();
        this.refreshStatus();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/feishu-sync/config');
            const data = await response.json();
            
            if (data.success) {
                const config = data.config;
                document.getElementById('appId').value = config.feishu.app_id || '';
                document.getElementById('appSecret').value = '';
                document.getElementById('appToken').value = config.feishu.app_token || '';
                document.getElementById('tableId').value = config.feishu.table_id || '';
                
                // 显示配置状态
                const statusBadge = config.feishu.status === 'active' ? 
                    '<span class="badge bg-success">已配置</span>' : 
                    '<span class="badge bg-warning">未配置</span>';
                
                // 可以在这里添加状态显示
            }
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    async saveConfig() {
        const config = {
            app_id: document.getElementById('appId').value,
            app_secret: document.getElementById('appSecret').value,
            app_token: document.getElementById('appToken').value,
            table_id: document.getElementById('tableId').value
        };

        if (!config.app_id || !config.app_secret || !config.app_token || !config.table_id) {
            this.showNotification('请填写完整的配置信息', 'error');
            return;
        }

        try {
            const response = await fetch('/api/feishu-sync/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('配置保存成功', 'success');
            } else {
                this.showNotification('配置保存失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('配置保存失败: ' + error.message, 'error');
        }
    }

    async testConnection() {
        try {
            this.showNotification('正在测试连接...', 'info');
            
            const response = await fetch('/api/feishu-sync/test-connection');
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('飞书连接正常', 'success');
            } else {
                this.showNotification('连接失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('连接测试失败: ' + error.message, 'error');
        }
    }

    async syncFromFeishu() {
        try {
            const limit = document.getElementById('syncLimit').value;
            this.showNotification('开始从飞书同步数据...', 'info');
            this.showProgress(true);
            
            const response = await fetch('/api/feishu-sync/sync-from-feishu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    generate_ai_suggestions: false,
                    limit: parseInt(limit)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.addSyncLog(data.message);
                this.refreshStatus();
            } else {
                this.showNotification('同步失败: ' + data.error, 'error');
                this.addSyncLog('同步失败: ' + data.error);
            }
        } catch (error) {
            this.showNotification('同步失败: ' + error.message, 'error');
            this.addSyncLog('同步失败: ' + error.message);
        } finally {
            this.showProgress(false);
        }
    }

    async syncWithAI() {
        try {
            const limit = document.getElementById('syncLimit').value;
            this.showNotification('开始同步数据并生成AI建议...', 'info');
            this.showProgress(true);
            
            const response = await fetch('/api/feishu-sync/sync-from-feishu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    generate_ai_suggestions: true,
                    limit: parseInt(limit)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.addSyncLog(data.message);
                this.refreshStatus();
            } else {
                this.showNotification('同步失败: ' + data.error, 'error');
                this.addSyncLog('同步失败: ' + data.error);
            }
        } catch (error) {
            this.showNotification('同步失败: ' + error.message, 'error');
            this.addSyncLog('同步失败: ' + error.message);
        } finally {
            this.showProgress(false);
        }
    }

    // 打开字段映射管理页面
    openFieldMapping() {
        const section = document.getElementById('fieldMappingSection');
        if (section.style.display === 'none') {
            section.style.display = 'block';
            // 自动加载映射状态
            this.loadMappingStatus();
        } else {
            section.style.display = 'none';
        }
    }

    async previewFeishuData() {
        try {
            this.showNotification('正在获取飞书数据预览...', 'info');
            
            const response = await fetch('/api/feishu-sync/preview-feishu-data');
            const data = await response.json();
            
            if (data.success) {
                this.displayPreviewData(data.preview_data);
                this.showNotification(`获取到 ${data.total_count} 条预览数据`, 'success');
            } else {
                this.showNotification('获取预览数据失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('获取预览数据失败: ' + error.message, 'error');
        }
    }

    displayPreviewData(data) {
        const tbody = document.querySelector('#previewTable tbody');
        tbody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.record_id}</td>
                <td>${item.fields['TR Number'] || '-'}</td>
                <td>${item.fields['TR Description'] || '-'}</td>
                <td>${item.fields['Type of problem'] || '-'}</td>
                <td>${item.fields['Source'] || '-'}</td>
                <td>${item.fields['TR (Priority/Status)'] || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="feishuSync.createWorkorder('${item.record_id}')">
                        <i class="fas fa-plus"></i> 创建工单
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        document.getElementById('previewSection').style.display = 'block';
    }

    async refreshStatus() {
        try {
            const response = await fetch('/api/feishu-sync/status');
            const data = await response.json();
            
            if (data.success) {
                const status = data.status;
                document.getElementById('totalLocalWorkorders').textContent = status.total_local_workorders || 0;
                document.getElementById('syncedWorkorders').textContent = status.synced_workorders || 0;
                document.getElementById('unsyncedWorkorders').textContent = status.unsynced_workorders || 0;
            }
        } catch (error) {
            console.error('刷新状态失败:', error);
        }
    }

    showProgress(show) {
        const progress = document.getElementById('syncProgress');
        if (show) {
            progress.style.display = 'block';
            const bar = progress.querySelector('.progress-bar');
            bar.style.width = '100%';
        } else {
            setTimeout(() => {
                progress.style.display = 'none';
                const bar = progress.querySelector('.progress-bar');
                bar.style.width = '0%';
            }, 1000);
        }
    }

    addSyncLog(message) {
        const log = document.getElementById('syncLog');
        const timestamp = new Date().toLocaleString();
        const logEntry = document.createElement('div');
        logEntry.innerHTML = `<small class="text-muted">[${timestamp}]</small> ${message}`;
        
        if (log.querySelector('.text-muted')) {
            log.innerHTML = '';
        }
        
        log.appendChild(logEntry);
        log.scrollTop = log.scrollHeight;
    }

    async exportConfig() {
        try {
            const response = await fetch('/api/feishu-sync/config/export');
            const data = await response.json();
            
            if (data.success) {
                // 创建下载链接
                const blob = new Blob([data.config], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `feishu_config_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showNotification('配置导出成功', 'success');
            } else {
                this.showNotification('配置导出失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('配置导出失败: ' + error.message, 'error');
        }
    }

    showImportModal() {
        const modal = new bootstrap.Modal(document.getElementById('importConfigModal'));
        modal.show();
    }

    async importConfig() {
        try {
            const configJson = document.getElementById('configJson').value.trim();
            
            if (!configJson) {
                this.showNotification('请输入配置JSON数据', 'warning');
                return;
            }
            
            const response = await fetch('/api/feishu-sync/config/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ config: configJson })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('配置导入成功', 'success');
                this.loadConfig();
                this.refreshStatus();
                
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('importConfigModal'));
                modal.hide();
                document.getElementById('configJson').value = '';
            } else {
                this.showNotification('配置导入失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('配置导入失败: ' + error.message, 'error');
        }
    }

    async resetConfig() {
        if (confirm('确定要重置所有配置吗？此操作不可撤销！')) {
            try {
                const response = await fetch('/api/feishu-sync/config/reset', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('配置重置成功', 'success');
                    this.loadConfig();
                    this.refreshStatus();
                } else {
                    this.showNotification('配置重置失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('配置重置失败: ' + error.message, 'error');
            }
        }
    }

    async createWorkorder(recordId) {
        if (confirm(`确定要从飞书记录 ${recordId} 创建工单吗？`)) {
            try {
                this.showNotification('正在创建工单...', 'info');
                
                const response = await fetch('/api/feishu-sync/create-workorder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        record_id: recordId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification(data.message, 'success');
                    // 刷新工单列表（如果用户在工单页面）
                    if (typeof window.refreshWorkOrders === 'function') {
                        window.refreshWorkOrders();
                    }
                } else {
                    this.showNotification('创建工单失败: ' + data.message, 'error');
                }
            } catch (error) {
                this.showNotification('创建工单失败: ' + error.message, 'error');
            }
        }
    }

    // 字段映射管理方法
    async discoverFields() {
        try {
            this.showNotification('正在发现字段...', 'info');
            
            const response = await fetch('/api/feishu-sync/field-mapping/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ limit: 5 })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayDiscoveryResults(data.discovery_report);
                this.showNotification('字段发现完成', 'success');
            } else {
                this.showNotification('字段发现失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('字段发现失败: ' + error.message, 'error');
        }
    }

    displayDiscoveryResults(report) {
        const container = document.getElementById('fieldMappingContent');
        let html = '';

        // 已映射字段
        if (report.mapped_fields && Object.keys(report.mapped_fields).length > 0) {
            html += '<div class="mb-3"><h6 class="text-success"><i class="fas fa-check-circle"></i> 已映射字段</h6>';
            for (const [feishuField, localField] of Object.entries(report.mapped_fields)) {
                html += `<div class="alert alert-success py-2">
                    <strong>${feishuField}</strong> → <span class="badge bg-success">${localField}</span>
                </div>`;
            }
            html += '</div>';
        }

        // 未映射字段和建议
        if (report.unmapped_fields && report.unmapped_fields.length > 0) {
            html += '<div class="mb-3"><h6 class="text-warning"><i class="fas fa-exclamation-triangle"></i> 未映射字段</h6>';
            for (const field of report.unmapped_fields) {
                html += `<div class="alert alert-warning py-2">
                    <strong>${field}</strong>`;
                
                const suggestions = report.suggested_mappings[field] || [];
                if (suggestions.length > 0) {
                    html += '<div class="mt-2"><small class="text-muted">建议映射:</small>';
                    suggestions.slice(0, 2).forEach(suggestion => {
                        html += `<div class="mt-1">
                            <span class="badge bg-${suggestion.confidence === 'high' ? 'success' : 'warning'}">${suggestion.local_field}</span>
                            <small class="text-muted">(${suggestion.reason})</small>
                            <button class="btn btn-sm btn-outline-primary ms-2" onclick="feishuSync.applySuggestion('${field}', '${suggestion.local_field}')">应用</button>
                        </div>`;
                    });
                    html += '</div>';
                }
                
                html += '</div>';
            }
            html += '</div>';
        }

        container.innerHTML = html;
    }

    async applySuggestion(feishuField, localField) {
        if (confirm(`确定要将 "${feishuField}" 映射到 "${localField}" 吗？`)) {
            try {
                const response = await fetch('/api/feishu-sync/field-mapping/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        feishu_field: feishuField,
                        local_field: localField,
                        priority: 3
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('映射添加成功！', 'success');
                    this.discoverFields(); // 重新发现字段
                } else {
                    this.showNotification('添加映射失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('请求失败: ' + error.message, 'error');
            }
        }
    }

    async loadMappingStatus() {
        try {
            const response = await fetch('/api/feishu-sync/field-mapping/status');
            const data = await response.json();
            
            if (data.success) {
                this.displayMappingStatus(data.status);
            } else {
                this.showNotification('获取映射状态失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('请求失败: ' + error.message, 'error');
        }
    }

    displayMappingStatus(status) {
        const container = document.getElementById('fieldMappingContent');
        let html = '';

        html += `<div class="row mb-3">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${status.total_mappings}</h5>
                        <p class="card-text">直接映射</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-info">${status.total_aliases}</h5>
                        <p class="card-text">别名映射</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-warning">${status.total_patterns}</h5>
                        <p class="card-text">模式匹配</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title ${status.auto_mapping_enabled ? 'text-success' : 'text-danger'}">
                            ${status.auto_mapping_enabled ? '启用' : '禁用'}
                        </h5>
                        <p class="card-text">自动映射</p>
                    </div>
                </div>
            </div>
        </div>`;

        // 显示当前映射
        if (status.field_mapping && Object.keys(status.field_mapping).length > 0) {
            html += '<h6>当前字段映射:</h6><div class="row">';
            for (const [feishuField, localField] of Object.entries(status.field_mapping)) {
                html += `<div class="col-md-6 mb-2">
                    <div class="alert alert-info py-2">
                        <strong>${feishuField}</strong> → <span class="badge bg-primary">${localField}</span>
                        <button class="btn btn-sm btn-outline-danger float-end" onclick="feishuSync.removeMapping('${feishuField}')">删除</button>
                    </div>
                </div>`;
            }
            html += '</div>';
        }

        container.innerHTML = html;
    }

    async removeMapping(feishuField) {
        if (confirm(`确定要删除映射 "${feishuField}" 吗？`)) {
            try {
                const response = await fetch('/api/feishu-sync/field-mapping/remove', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        feishu_field: feishuField
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('映射删除成功！', 'success');
                    this.loadMappingStatus(); // 刷新状态
                } else {
                    this.showNotification('删除映射失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('请求失败: ' + error.message, 'error');
            }
        }
    }

    showAddMappingModal() {
        // 简单的添加映射功能
        const feishuField = prompt('请输入飞书字段名:');
        if (!feishuField) return;
        
        const localField = prompt('请输入本地字段名 (如: order_id, description, category):');
        if (!localField) return;
        
        this.addFieldMapping(feishuField, localField);
    }

    async addFieldMapping(feishuField, localField) {
        try {
            const response = await fetch('/api/feishu-sync/field-mapping/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    feishu_field: feishuField,
                    local_field: localField,
                    priority: 3
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('映射添加成功！', 'success');
                this.loadMappingStatus(); // 刷新状态
            } else {
                this.showNotification('添加映射失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('请求失败: ' + error.message, 'error');
        }
    }

    async checkPermissions() {
        try {
            this.showNotification('正在检查飞书权限...', 'info');
            
            const response = await fetch('/api/feishu-sync/check-permissions');
            const data = await response.json();
            
            if (data.success) {
                this.displayPermissionCheck(data.permission_check, data.summary);
                this.showNotification('权限检查完成', 'success');
            } else {
                this.showNotification('权限检查失败: ' + data.error, 'error');
            }
        } catch (error) {
            this.showNotification('权限检查失败: ' + error.message, 'error');
        }
    }

    displayPermissionCheck(permissionCheck, summary) {
        const container = document.getElementById('fieldMappingContent');
        
        let html = '<div class="card"><div class="card-header"><h6 class="card-title mb-0"><i class="fas fa-shield-alt me-2"></i>飞书权限检查结果</h6></div><div class="card-body">';
        
        // 整体状态
        const statusClass = permissionCheck.success ? 'success' : 'danger';
        const statusIcon = permissionCheck.success ? 'check-circle' : 'exclamation-triangle';
        html += `<div class="alert alert-${statusClass}">
            <i class="fas fa-${statusIcon}"></i> 
            整体状态: ${permissionCheck.success ? '正常' : '异常'}
        </div>`;
        
        // 检查项目
        html += '<h6>检查项目:</h6>';
        for (const [checkName, checkResult] of Object.entries(permissionCheck.checks)) {
            const statusClass = checkResult.status === 'success' ? 'success' : 
                               checkResult.status === 'warning' ? 'warning' : 'danger';
            const statusIcon = checkResult.status === 'success' ? 'check-circle' : 
                              checkResult.status === 'warning' ? 'exclamation-triangle' : 'times-circle';
            
            html += `<div class="alert alert-${statusClass} py-2">
                <i class="fas fa-${statusIcon}"></i> 
                <strong>${checkName}</strong>: ${checkResult.message}
            </div>`;
        }
        
        // 修复建议
        if (permissionCheck.recommendations && permissionCheck.recommendations.length > 0) {
            html += '<h6>修复建议:</h6><ul class="list-group mb-3">';
            permissionCheck.recommendations.forEach(rec => {
                html += `<li class="list-group-item">${rec}</li>`;
            });
            html += '</ul>';
        }
        
        // 错误信息
        if (permissionCheck.errors && permissionCheck.errors.length > 0) {
            html += '<h6>错误信息:</h6><ul class="list-group">';
            permissionCheck.errors.forEach(error => {
                html += `<li class="list-group-item list-group-item-danger">${error}</li>`;
            });
            html += '</ul>';
        }
        
        html += '</div></div>';
        
        container.innerHTML = html;
        
        // 显示字段映射管理区域
        const section = document.getElementById('fieldMappingSection');
        section.style.display = 'block';
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        container.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// 初始化应用
let dashboard;
let feishuSync;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new HelpdeskDashboard();
    feishuSync = new FeishuSyncManager();
});
