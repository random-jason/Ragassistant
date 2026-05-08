/**
 * 主入口文件
 */

import { ready, storage } from './core/utils.js';
import store from './core/store.js';
import router from './core/router.js';
import { initWebSocket } from './core/websocket.js';
import Navbar from './components/navbar.js';
import Sidebar from './components/sidebar.js';
import { showToast } from './components/modal.js';

// 应用主类
class App {
    constructor() {
        this.components = {};
        this.currentRoute = null;
    }

    // 初始化应用
    async init() {
        try {
            // 显示加载状态
            this.showLoading();

            // 初始化路由
            router.start();

            // 初始化UI组件
            this.initComponents();

            // 恢复应用状态
            this.restoreAppState();

            // 初始化WebSocket
            initWebSocket();

            // 绑定全局事件
            this.bindGlobalEvents();

            // 注册服务工作者（PWA支持）
            this.registerServiceWorker();

            // 隐藏加载状态
            this.hideLoading();

            console.log('App initialized successfully');
        } catch (error) {
            console.error('App initialization failed:', error);
            this.handleInitError(error);
        }
    }

    // 初始化组件
    initComponents() {
        // 初始化导航栏
        const navbarContainer = document.querySelector('#navbar');
        if (navbarContainer) {
            this.components.navbar = new Navbar(navbarContainer);
        }

        // 初始化侧边栏
        const sidebarContainer = document.querySelector('#sidebar-container');
        if (sidebarContainer) {
            this.components.sidebar = new Sidebar(sidebarContainer);
        }

        // 初始化其他组件...
    }

    // 恢复应用状态
    restoreAppState() {
        // 恢复主题
        const savedTheme = storage.get('app.theme', 'light');
        store.commit('SET_THEME', savedTheme);

        // 恢复用户信息（如果有）
        const userInfo = storage.get('userInfo');
        if (userInfo) {
            store.commit('SET_USER', userInfo);
            store.commit('SET_LOGIN', true);
        }

        // 恢复其他设置...
    }

    // 绑定全局事件
    bindGlobalEvents() {
        // 监听路由变化
        router.afterEach((to) => {
            this.handleRouteChange(to);
        });

        // 监听网络状态
        window.addEventListener('online', () => {
            showToast('网络已连接', 'success');
        });

        window.addEventListener('offline', () => {
            showToast('网络已断开', 'warning');
        });

        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                store.commit('SET_APP_ACTIVE', false);
            } else {
                store.commit('SET_APP_ACTIVE', true);
            }
        });

        // 监听存储变化（多标签页同步）
        window.addEventListener('storage', (e) => {
            this.handleStorageChange(e);
        });

        // 监听未捕获的错误
        window.addEventListener('error', (e) => {
            this.handleError(e.error);
        });

        window.addEventListener('unhandledrejection', (e) => {
            this.handleError(e.reason);
        });
    }

    // 处理路由变化
    async handleRouteChange(to) {
        this.currentRoute = to;

        // 更新页面标题
        if (to.meta.title) {
            document.title = `${to.meta.title} - AI Helpdesk`;
        }

        // 加载页面组件
        await this.loadPage(to);

        // 更新导航状态
        this.updateNavigation(to);

        // 滚动到顶部
        window.scrollTo(0, 0);
    }

    // 加载页面组件
    async loadPage(route) {
        const pageContainer = document.querySelector('#page-content');
        if (!pageContainer) return;

        // 显示加载状态
        pageContainer.innerHTML = this.createLoadingHTML();

        try {
            // 映射路由到页面文件
            const pageFile = this.getPageFile(route.name);

            // 动态导入页面组件
            const pageModule = await import(`./pages/${pageFile}.js`);
            const PageComponent = pageModule.default;

            // 实例化页面组件
            const page = new PageComponent(pageContainer, route);

            // 保存页面实例
            this.components.currentPage = page;

            // 将页面实例暴露到全局（供内联事件使用）
            if (route.name === 'alerts') {
                window.alerage = page;
            }

        } catch (error) {
            console.error('Failed to load page:', error);
            pageContainer.innerHTML = this.createErrorHTML(error);
        }
    }

    // 获取页面文件名
    getPageFile(routeName) {
        const pageMap = {
            'dashboard': 'dashboard',
            'workorders': 'workorders',
            'workorder-detail': 'workorders',
            'alerts': 'alerts',
            'knowledge': 'knowledge',
            'knowledge-detail': 'knowledge',
            'chat': 'chat',
            'chat-http': 'chat',
            'monitoring': 'monitoring',
            'settings': 'settings',
            'profile': 'settings',
            'login': 'login',
            'feishu': 'feishu',
            'agent': 'agent',
            'vehicle': 'vehicle'
        };

        return pageMap[routeName] || 'dashboard';
    }

    // 更新导航状态
    updateNavigation(route) {
        // 更新侧边栏激活状态
        if (this.components.sidebar) {
            this.components.sidebar.updateActiveMenu(route.path);
        }

        // 更新导航栏面包屑
        this.updateBreadcrumb(route);
    }

    // 更新面包屑
    updateBreadcrumb(route) {
        const breadcrumbContainer = document.querySelector('#breadcrumb');
        if (!breadcrumbContainer) return;

        const items = [
            { text: '首页', link: '/' }
        ];

        // 根据路由构建面包屑
        if (route.path !== '/') {
            const pathSegments = route.path.split('/').filter(Boolean);
            let currentPath = '';

            pathSegments.forEach((segment, index) => {
                currentPath += `/${segment}`;
                const isLast = index === pathSegments.length - 1;

                // 这里可以根据路由配置获取更友好的名称
                const name = this.getPathName(segment);

                items.push({
                    text: name,
                    link: isLast ? null : currentPath
                });
            });
        }

        breadcrumbContainer.innerHTML = this.createBreadcrumbHTML(items);
    }

    // 获取路径名称
    getPathName(segment) {
        const names = {
            workorders: '工单管理',
            alerts: '预警管理',
            knowledge: '知识库',
            chat: '智能对话',
            'chat-http': 'HTTP对话',
            monitoring: '系统监控',
            settings: '系统设置'
        };
        return names[segment] || segment;
    }

    // 处理存储变化
    handleStorageChange(e) {
        // 处理多标签页之间的状态同步
        if (e.key === '_assistant_store') {
            const newState = JSON.parse(e.newValue);
            store.setState(newState, false);
        }
    }

    // 处理错误
    handleError(error) {
        console.error('Application error:', error);

        // 显示错误提示
        showToast('发生错误，请刷新页面重试', 'error');

        // 发送错误报告（如果配置了且有report方法）
        if (window.errorReporting && window.errorReporting.enabled && window.errorReporting.report) {
            try {
                window.errorReporting.report(error);
            } catch (reportError) {
                console.error('Error reporting failed:', reportError);
            }
        }
    }

    // 处理初始化错误
    handleInitError(error) {
        this.hideLoading();

        const pageContainer = document.querySelector('#page-content');
        if (pageContainer) {
            pageContainer.innerHTML = `
                <div class="container-fluid">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body text-center">
                                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                                    <h4>应用初始化失败</h4>
                                    <p class="text-muted">${error.message || '未知错误'}</p>
                                    <button class="btn btn-primary" onclick="location.reload()">
                                        <i class="fas fa-redo me-2"></i>重新加载
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // 注册服务工作者
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('ServiceWorker registered:', registration);
                })
                .catch(error => {
                    console.log('ServiceWorker registration failed:', error);
                });
        }
    }

    // 显示加载状态
    showLoading() {
        const loadingHTML = `
            <div id="loading-overlay" class="loading-overlay">
                <div class="loading-content">
                    <div class="spinner"></div>
                    <p class="mt-3">加载中...</p>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    }

    // 隐藏加载状态
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    // 创建加载HTML
    createLoadingHTML() {
        return `
            <div class="d-flex justify-content-center align-items-center" style="min-height: 400px;">
                <div class="text-center">
                    <div class="spinner"></div>
                    <p class="mt-3">加载中...</p>
                </div>
            </div>
        `;
    }

    // 创建错误HTML
    createErrorHTML(error) {
        return `
            <div class="container-fluid">
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
            </div>
        `;
    }

    // 创建面包屑HTML
    createBreadcrumbHTML(items) {
        return `
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    ${items.map((item, index) => `
                        <li class="breadcrumb-item ${index === items.length - 1 ? 'active' : ''}">
                            ${item.link ? `<a href="${item.link}">${item.text}</a>` : item.text}
                        </li>
                    `).join('')}
                </ol>
            </nav>
        `;
    }
}

// 创建应用实例
const app = new App();

// DOM加载完成后初始化应用
ready(() => {
    app.init();
});

// 暴露到全局（便于调试）
window.app = app;
window.store = store;
window.router = router;