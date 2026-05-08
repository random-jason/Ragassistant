/**
 * 路由管理模块
 */

import { parseQueryString, serializeQueryString } from './utils.js';
import store from './store.js';

// 路由配置
class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.beforeEachHooks = [];
        this.afterEachHooks = [];
        this.mode = 'history'; // 'history' 或 'hash'
        this.base = '/';
        this.fallback = true;

        // 绑定事件处理器
        this.handlePopState = this.handlePopState.bind(this);
        this.handleHashChange = this.handleHashChange.bind(this);
    }

    // 配置路由
    config(options = {}) {
        if (options.mode) this.mode = options.mode;
        if (options.base) this.base = options.base;
        if (options.fallback !== undefined) this.fallback = options.fallback;
        return this;
    }

    // 添加路由
    addRoute(path, component, options = {}) {
        const route = {
            path,
            component,
            name: options.name || path,
            meta: options.meta || {},
            props: options.props || false,
            children: options.children || [],
            beforeEnter: options.beforeEnter
        };

        // 转换路径为正则表达式
        route.regex = this.pathToRegex(path);
        route.keys = [];

        // 提取动态参数
        const paramNames = path.match(/:\w+/g);
        if (paramNames) {
            route.keys = paramNames.map(name => name.slice(1));
        }

        this.routes.set(path, route);
        return this;
    }

    // 批量添加路由
    addRoutes(routes) {
        routes.forEach(route => {
            this.addRoute(route.path, route.component, route);
        });
        return this;
    }

    // 路径转正则
    pathToRegex(path) {
        const regexPath = path
            .replace(/\//g, '\\/')
            .replace(/:\w+/g, '([^\\/]+)')
            .replace(/\*/g, '(.*)');
        return new RegExp(`^${regexPath}$`);
    }

    // 匹配路由
    match(path) {
        for (const [routePath, route] of this.routes) {
            const match = path.match(route.regex);
            if (match) {
                const params = {};
                route.keys.forEach((key, index) => {
                    params[key] = match[index + 1];
                });

                return {
                    route,
                    params,
                    path,
                    query: this.parseQuery(path)
                };
            }
        }

        // 404处理
        return {
            route: { path: '/404', component: 'notfound' },
            params: {},
            path,
            query: {}
        };
    }

    // 解析查询字符串
    parseQuery(path) {
        const queryIndex = path.indexOf('?');
        if (queryIndex === -1) return {};

        const queryString = path.slice(queryIndex + 1);
        return parseQueryString(queryString);
    }

    // 构建路径
    buildPath(route, params = {}, query = {}) {
        let path = route.path;

        // 替换动态参数
        Object.keys(params).forEach(key => {
            path = path.replace(`:${key}`, params[key]);
        });

        // 添加查询字符串
        const queryString = serializeQueryString(query);
        if (queryString) {
            path += `?${queryString}`;
        }

        return path;
    }

    // 导航到指定路径
    push(path, data = {}) {
        return this.navigateTo(path, 'push', data);
    }

    // 替换当前路径
    replace(path, data = {}) {
        return this.navigateTo(path, 'replace', data);
    }

    // 返回上一页
    go(n) {
        window.history.go(n);
    }

    // 返回
    back() {
        this.go(-1);
    }

    // 前进
    forward() {
        this.go(1);
    }

    // 执行导航
    async navigateTo(path, type = 'push', data = {}) {
        // 匹配路由
        const matched = this.match(path);

        // 创建路由对象
        const route = {
            path: matched.path,
            name: matched.route.name,
            params: matched.params,
            query: matched.query,
            meta: matched.route.meta,
            hash: this.parseHash(path),
            ...data
        };

        // 执行前置守卫
        const guards = [...this.beforeEachHooks, matched.route.beforeEnter].filter(Boolean);
        for (const guard of guards) {
            const result = await guard(route, this.currentRoute);
            if (result === false) {
                return Promise.reject(new Error('Navigation cancelled'));
            }
            if (typeof result === 'string') {
                return this.navigateTo(result, type, data);
            }
            if (result && typeof result === 'object') {
                return this.navigateTo(result.path || result, type, result);
            }
        }

        // 保存当前路由
        const prevRoute = this.currentRoute;
        this.currentRoute = route;

        // 更新URL
        this.updateURL(path, type);

        // 执行后置守卫
        this.afterEachHooks.forEach(hook => {
            try {
                hook(route, prevRoute);
            } catch (error) {
                console.error('After each hook error:', error);
            }
        });

        // 更新store
        store.commit('SET_CURRENT_ROUTE', route);

        return route;
    }

    // 更新URL
    updateURL(path, type) {
        if (this.mode === 'history') {
            const url = this.base === '/' ? path : `${this.base}${path}`.replace('//', '/');
            if (type === 'replace') {
                window.history.replaceState({ path }, '', url);
            } else {
                window.history.pushState({ path }, '', url);
            }
        } else {
            const hash = this.mode === 'hash' ? `#${path}` : `#${this.base}${path}`.replace('//', '/');
            if (type === 'replace') {
                window.location.replace(hash);
            } else {
                window.location.hash = hash;
            }
        }
    }

    // 解析hash
    parseHash(path) {
        const hashIndex = path.indexOf('#');
        return hashIndex === -1 ? '' : path.slice(hashIndex + 1);
    }

    // 处理popstate事件
    handlePopState(event) {
        if (event.state && event.state.path) {
            this.navigateTo(event.state.path, 'push', { replace: true });
        } else {
            const path = this.getCurrentPath();
            this.navigateTo(path, 'push', { replace: true });
        }
    }

    // 处理hashchange事件
    handleHashChange() {
        const path = this.getCurrentPath();
        this.navigateTo(path, 'push', { replace: true });
    }

    // 获取当前路径
    getCurrentPath() {
        if (this.mode === 'history') {
            const path = window.location.pathname;
            return path.startsWith(this.base) ? path.slice(this.base.length) : path;
        } else {
            const hash = window.location.hash.slice(1);
            return hash.startsWith(this.base) ? hash.slice(this.base.length) : hash;
        }
    }

    // 全局前置守卫
    beforeEach(hook) {
        this.beforeEachHooks.push(hook);
    }

    // 全局后置守卫
    afterEach(hook) {
        this.afterEachHooks.push(hook);
    }

    // 启动路由
    start() {
        // 监听事件
        if (this.mode === 'history') {
            window.addEventListener('popstate', this.handlePopState);
        } else {
            window.addEventListener('hashchange', this.handleHashChange);
        }

        // 处理初始路由
        const path = this.getCurrentPath();
        this.navigateTo(path, 'push', { replace: true });

        // 拦截链接点击
        this.interceptLinks();

        return this;
    }

    // 拦截链接
    interceptLinks() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('tel:')) {
                return;
            }

            e.preventDefault();
            this.push(href);
        });
    }

    // 停止路由
    stop() {
        window.removeEventListener('popstate', this.handlePopState);
        window.removeEventListener('hashchange', this.handleHashChange);
        return this;
    }
}

// 创建路由实例
export const router = new Router();

// 路由配置
router.config({
    mode: 'history',
    base: '/',
    fallback: true
});

// 添加路由
router.addRoutes([
    {
        path: '/',
        name: 'dashboard',
        component: 'Dashboard',
        meta: { title: '仪表板', icon: 'fas fa-tachometer-alt' }
    },
    {
        path: '/workorders',
        name: 'workorders',
        component: 'WorkOrders',
        meta: { title: '工单管理', icon: 'fas fa-tasks' }
    },
    {
        path: '/workorders/:id',
        name: 'workorder-detail',
        component: 'WorkOrderDetail',
        meta: { title: '工单详情' }
    },
    {
        path: '/alerts',
        name: 'alerts',
        component: 'Alerts',
        meta: { title: '预警管理', icon: 'fas fa-bell' }
    },
    {
        path: '/knowledge',
        name: 'knowledge',
        component: 'Knowledge',
        meta: { title: '知识库', icon: 'fas fa-book' }
    },
    {
        path: '/knowledge/:id',
        name: 'knowledge-detail',
        component: 'KnowledgeDetail',
        meta: { title: '知识详情' }
    },
    {
        path: '/chat',
        name: 'chat',
        component: 'Chat',
        meta: { title: '智能对话', icon: 'fas fa-comments' }
    },
    {
        path: '/chat-http',
        name: 'chat-http',
        component: 'ChatHttp',
        meta: { title: '对话(HTTP)', icon: 'fas fa-comment-dots' }
    },
    {
        path: '/monitoring',
        name: 'monitoring',
        component: 'Monitoring',
        meta: { title: '系统监控', icon: 'fas fa-chart-line' }
    },
    {
        path: '/settings',
        name: 'settings',
        component: 'Settings',
        meta: { title: '系统设置', icon: 'fas fa-cog' }
    },
    {
        path: '/feishu',
        name: 'feishu',
        component: 'Feishu',
        meta: { title: '飞书同步', icon: 'fab fa-lark' }
    },
    {
        path: '/agent',
        name: 'agent',
        component: 'Agent',
        meta: { title: '智能Agent', icon: 'fas fa-robot' }
    },
    {
        path: '/profile',
        name: 'profile',
        component: 'Profile',
        meta: { title: '个人资料' }
    },
    {
        path: '/login',
        name: 'login',
        component: 'Login',
        meta: { title: '登录', requiresAuth: false }
    },
    {
        path: '/404',
        name: '404',
        component: 'notfound',
        meta: { title: '页面未找到' }
    },
    {
        path: '*',
        redirect: '/404'
    }
]);

// 全局前置守卫
router.beforeEach((to, from) => {
    // 设置页面标题
    if (to.meta.title) {
        document.title = `${to.meta.title} - AI Helpdesk`;
    }

    // 权限检查
    if (to.meta.requiresAuth !== false && !store.getState('user.isLogin')) {
        return '/login';
    }

    // 管理员权限检查
    if (to.meta.requiresAdmin && !store.getState('user.info.isAdmin')) {
        return '/403';
    }
});

// 导出路由实例和辅助函数
export function push(path, data) {
    return router.push(path, data);
}

export function replace(path, data) {
    return router.replace(path, data);
}

export function go(n) {
    return router.go(n);
}

export function back() {
    return router.back();
}

export function forward() {
    return router.forward();
}

export default router;