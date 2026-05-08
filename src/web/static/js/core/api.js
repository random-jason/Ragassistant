/**
 * API统一管理模块
 */

import { defaultConfig, debounce, storage, handleError } from './utils.js';

// API配置
const config = {
    ...defaultConfig,
    timeout: 10000, // 请求超时时间
    retryTimes: 3, // 重试次数
    retryDelay: 1000 // 重试延迟
};

// 请求拦截器
const requestInterceptors = [];
const responseInterceptors = [];

// 添加请求拦截器
export function addRequestInterceptor(interceptor) {
    requestInterceptors.push(interceptor);
}

// 添加响应拦截器
export function addResponseInterceptor(interceptor) {
    responseInterceptors.push(interceptor);
}

// 默认请求拦截器
addRequestInterceptor(async (options) => {
    // 添加认证头
    const token = storage.get('authToken');
    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
    }

    // 添加用户信息头
    const userInfo = storage.get('userInfo');
    if (userInfo) {
        options.headers = {
            ...options.headers,
            'X-User-Name': userInfo.name || '',
            'X-User-Role': userInfo.role || ''
        };
    }

    // 添加请求ID
    options.headers = {
        ...options.headers,
        'X-Request-ID': generateRequestId()
    };

    return options;
});

// 默认响应拦截器
addResponseInterceptor(async (response) => {
    // 处理通用错误
    if (response.status === 401) {
        // 未授权，清除本地存储并跳转到登录页
        storage.remove('authToken');
        storage.remove('userInfo');
        window.location.href = '/login';
        throw new Error('未授权，请重新登录');
    }

    if (response.status >= 500) {
        throw new Error('服务器错误，请稍后重试');
    }

    return response;
});

// 生成请求ID
function generateRequestId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// 基础请求函数
async function request(url, options = {}) {
    // 合并配置
    const finalOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    // 执行请求拦截器
    for (const interceptor of requestInterceptors) {
        Object.assign(finalOptions, await interceptor(finalOptions));
    }

    // 构建完整URL
    const fullUrl = url.startsWith('http') ? url : `${config.apiBaseUrl}${url}`;

    // 创建AbortController用于超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);
    finalOptions.signal = controller.signal;

    try {
        let lastError;

        // 重试机制
        for (let i = 0; i <= config.retryTimes; i++) {
            try {
                const response = await fetch(fullUrl, finalOptions);

                // 执行响应拦截器
                let processedResponse = response;
                for (const interceptor of responseInterceptors) {
                    processedResponse = await interceptor(processedResponse);
                }

                // 解析响应
                const data = await parseResponse(processedResponse);

                // 如果响应表示失败，抛出错误
                if (data.code && data.code !== 200) {
                    throw new Error(data.message || '请求失败');
                }

                return data;
            } catch (error) {
                lastError = error;

                // 如果是网络错误或超时，且还有重试次数，则延迟后重试
                if (i < config.retryTimes && (error.name === 'TypeError' || error.name === 'AbortError')) {
                    await new Promise(resolve => setTimeout(resolve, config.retryDelay * Math.pow(2, i)));
                    continue;
                }

                // 其他错误直接抛出
                throw error;
            }
        }

        throw lastError;
    } catch (error) {
        handleError(error, `API Request: ${finalOptions.method} ${url}`);
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

// 解析响应
async function parseResponse(response) {
    const contentType = response.headers.get('content-type');

    if (contentType && contentType.includes('application/json')) {
        return await response.json();
    } else if (contentType && contentType.includes('text/')) {
        return {
            code: response.ok ? 200 : response.status,
            data: await response.text(),
            message: response.statusText
        };
    } else {
        return {
            code: response.ok ? 200 : response.status,
            data: await response.blob(),
            message: response.statusText
        };
    }
}

// HTTP方法封装
export const http = {
    get(url, params = {}, options = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return request(fullUrl, { ...options, method: 'GET' });
    },

    post(url, data = {}, options = {}) {
        return request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    put(url, data = {}, options = {}) {
        return request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    patch(url, data = {}, options = {}) {
        return request(url, {
            ...options,
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    delete(url, options = {}) {
        return request(url, { ...options, method: 'DELETE' });
    },

    upload(url, formData, options = {}) {
        return request(url, {
            ...options,
            method: 'POST',
            headers: {
                // 不要设置Content-Type，让浏览器自动设置multipart/form-data
            },
            body: formData
        });
    },

    download(url, params = {}, options = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;

        return request(fullUrl, {
            ...options,
            method: 'GET'
        }).then(response => {
            // 创建下载链接
            const blob = response.data;
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;

            // 从响应头获取文件名
            const contentDisposition = response.headers?.get('content-disposition');
            if (contentDisposition) {
                const filename = contentDisposition.match(/filename="?([^"]+)"?/);
                link.download = filename ? filename[1] : 'download';
            }

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

            return response;
        });
    }
};

// API接口定义
export const api = {
    // 系统相关
    system: {
        health: () => http.get('/health'),
        info: () => http.get('/system/info'),
        settings: () => http.get('/settings'),
        saveSettings: (data) => http.post('/settings', data)
    },

    // 工单管理
    workorders: {
        list: (params) => http.get('/workorders', params),
        create: (data) => http.post('/workorders', data),
        get: (id) => http.get(`/workorders/${id}`),
        update: (id, data) => http.put(`/workorders/${id}`, data),
        delete: (id) => http.delete(`/workorders/${id}`),
        dispatch: (id, module) => http.post(`/workorders/${id}/dispatch`, { target_module: module }),
        suggestModule: (id) => http.post(`/workorders/${id}/suggest-module`),
        aiSuggestion: (id) => http.post(`/workorders/${id}/ai-suggestion`),
        humanResolution: (id, data) => http.post(`/workorders/${id}/human-resolution`, data),
        approveToKnowledge: (id, data) => http.post(`/workorders/${id}/approve-to-knowledge`, data),
        processHistory: (id) => http.get(`/workorders/${id}/process-history`),
        addProcessHistory: (id, data) => http.post(`/workorders/${id}/process-history`, data),
        import: (file) => {
            const formData = new FormData();
            formData.append('file', file);
            return http.upload('/workorders/import', formData);
        },
        export: (params) => http.download('/workorders/export', params),
        getTemplate: () => http.get('/workorders/import/template'),
        downloadTemplate: () => http.download('/workorders/import/template/file'),
        modules: () => http.get('/workorders/modules'),
        byStatus: (status) => http.get(`/workorders/by-status/${status}`),
        batchDelete: (ids) => http.post('/batch-delete/workorders', { ids })
    },

    // 对话管理
    conversations: {
        list: (params) => http.get('/conversations', params),
        get: (id) => http.get(`/conversations/${id}`),
        delete: (id) => http.delete(`/conversations/${id}`),
        clear: () => http.delete('/conversations/clear'),
        search: (params) => http.get('/conversations/search', params),
        analytics: () => http.get('/conversations/analytics'),
        migrateMerge: (data) => http.post('/conversations/migrate-merge', data),
        timeline: (workOrderId, params) => http.get(`/conversations/workorder/${workOrderId}/timeline`, params),
        context: (workOrderId) => http.get(`/conversations/workorder/${workOrderId}/context`),
        summary: (workOrderId) => http.get(`/conversations/workorder/${workOrderId}/summary`)
    },

    // 聊天接口
    chat: {
        createSession: (data) => http.post('/chat/session', data),
        sendMessage: (data) => http.post('/chat/message', data),
        getHistory: (sessionId) => http.get(`/chat/history/${sessionId}`),
        createWorkOrder: (data) => http.post('/chat/work-order', data),
        getWorkOrderStatus: (workOrderId) => http.get(`/chat/work-order/${workOrderId}`),
        endSession: (sessionId) => http.delete(`/chat/session/${sessionId}`),
        sessions: () => http.get('/chat/sessions')
    },

    // 知识库
    knowledge: {
        list: (params) => http.get('/knowledge', params),
        search: (params) => http.get('/knowledge/search', params),
        create: (data) => http.post('/knowledge', data),
        get: (id) => http.get(`/knowledge/${id}`),
        update: (id, data) => http.put(`/knowledge/${id}`, data),
        delete: (id) => http.delete(`/knowledge/delete/${id}`),
        verify: (id) => http.post(`/knowledge/verify/${id}`),
        unverify: (id) => http.post(`/knowledge/unverify/${id}`),
        stats: () => http.get('/knowledge/stats'),
        upload: (file, data) => {
            const formData = new FormData();
            formData.append('file', file);
            Object.keys(data).forEach(key => {
                formData.append(key, data[key]);
            });
            return http.upload('/knowledge/upload', formData);
        },
        byStatus: (status) => http.get(`/knowledge/by-status/${status}`),
        batchDelete: (ids) => http.post('/batch-delete/knowledge', { ids })
    },

    // 预警管理
    alerts: {
        list: (params) => http.get('/alerts', params),
        create: (data) => http.post('/alerts', data),
        get: (id) => http.get(`/alerts/${id}`),
        update: (id, data) => http.put(`/alerts/${id}`, data),
        delete: (id) => http.delete(`/alerts/${id}`),
        resolve: (id, data) => http.post(`/alerts/${id}/resolve`, data),
        statistics: () => http.get('/alerts/statistics'),
        byLevel: (level) => http.get(`/alerts/by-level/${level}`),
        batchDelete: (ids) => http.post('/batch-delete/alerts', { ids })
    },

    // 预警规则
    rules: {
        list: () => http.get('/rules'),
        create: (data) => http.post('/rules', data),
        update: (name, data) => http.put(`/rules/${name}`, data),
        delete: (name) => http.delete(`/rules/${name}`)
    },

    // 监控管理
    monitor: {
        start: () => http.post('/monitor/start'),
        stop: () => http.post('/monitor/stop'),
        status: () => http.get('/monitor/status'),
        checkAlerts: () => http.post('/check-alerts'),
        analytics: (params) => http.get('/analytics', params)
    },

    // Token监控
    tokenMonitor: {
        stats: () => http.get('/token-monitor/stats'),
        chart: (params) => http.get('/token-monitor/chart', params),
        records: (params) => http.get('/token-monitor/records', params),
        settings: (data) => http.post('/token-monitor/settings', data),
        export: (params) => http.download('/token-monitor/export', params)
    },

    // AI监控
    aiMonitor: {
        stats: () => http.get('/ai-monitor/stats'),
        modelComparison: () => http.get('/ai-monitor/model-comparison'),
        errorDistribution: () => http.get('/ai-monitor/error-distribution'),
        errorLog: (params) => http.get('/ai-monitor/error-log', params),
        clearErrorLog: () => http.delete('/ai-monitor/error-log')
    },

    // Agent相关
    agent: {
        status: () => http.get('/agent/status'),
        toggle: () => http.post('/agent/toggle'),
        chat: (data) => http.post('/agent/chat', data),
        actionHistory: () => http.get('/agent/action-history'),
        clearHistory: () => http.post('/agent/clear-history'),
        tools: {
            stats: () => http.get('/agent/tools/stats'),
            execute: (data) => http.post('/agent/tools/execute', data),
            register: (data) => http.post('/agent/tools/register', data),
            unregister: (name) => http.delete(`/agent/tools/unregister/${name}`)
        },
        monitoring: {
            start: () => http.post('/agent/monitoring/start'),
            stop: () => http.post('/agent/monitoring/stop'),
            proactiveCheck: () => http.post('/agent/proactive-monitoring'),
            intelligentAnalysis: () => http.post('/agent/intelligent-analysis')
        },
        llmStats: () => http.get('/agent/llm-stats'),
        triggerSample: () => http.post('/agent/trigger-sample')
    },

    // 飞书同步
    feishu: {
        config: {
            get: () => http.get('/feishu-sync/config'),
            save: (data) => http.post('/feishu-sync/config', data)
        },
        testConnection: () => http.get('/feishu-sync/test-connection'),
        checkPermissions: () => http.get('/feishu-sync/check-permissions'),
        syncFromFeishu: (data) => http.post('/feishu-sync/sync-from-feishu', data),
        syncToFeishu: (workOrderId) => http.post(`/feishu-sync/sync-to-feishu/${workOrderId}`),
        status: () => http.get('/feishu-sync/status'),
        createWorkorder: (data) => http.post('/feishu-sync/create-workorder', data),
        fieldMapping: {
            status: () => http.get('/feishu-sync/field-mapping/status'),
            discover: () => http.post('/feishu-sync/field-mapping/discover'),
            add: (data) => http.post('/feishu-sync/field-mapping/add', data),
            remove: (data) => http.post('/feishu-sync/field-mapping/remove', data)
        },
        previewData: (params) => http.get('/feishu-sync/preview-feishu-data', params),
        config: {
            export: () => http.download('/feishu-sync/config/export'),
            import: (file) => {
                const formData = new FormData();
                formData.append('file', file);
                return http.upload('/feishu-sync/config/import', formData);
            },
            reset: () => http.post('/feishu-sync/config/reset')
        }
    },

    // 系统优化
    systemOptimizer: {
        status: () => http.get('/system-optimizer/status'),
        optimizeCpu: () => http.post('/system-optimizer/optimize-cpu'),
        optimizeMemory: () => http.post('/system-optimizer/optimize-memory'),
        optimizeDisk: () => http.post('/system-optimizer/optimize-disk'),
        clearCache: () => http.post('/system-optimizer/clear-cache'),
        optimizeAll: () => http.post('/system-optimizer/optimize-all'),
        securitySettings: (data) => http.post('/system-optimizer/security-settings', data),
        trafficSettings: (data) => http.post('/system-optimizer/traffic-settings', data),
        costSettings: (data) => http.post('/system-optimizer/cost-settings', data),
        healthCheck: () => http.post('/system-optimizer/health-check')
    },

    // 数据库备份
    backup: {
        info: () => http.get('/backup/info'),
        create: (data) => http.post('/backup/create', data),
        restore: (data) => http.post('/backup/restore', data)
    }
};

// 导出默认配置和请求方法
export { config };
export default { http, api, config };