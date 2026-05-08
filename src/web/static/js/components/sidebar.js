/**
 * 侧边栏组件
 */

import { addClass, removeClass, hasClass, toggleClass } from '../core/utils.js';
import router from '../core/router.js';

export class Sidebar {
    constructor(container) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.collapsed = false;
        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="sidebar" id="sidebar">
                <!-- Logo -->
                <div class="sidebar-header">
                    <a href="/" class="sidebar-logo">
                        <i class="fas fa-shield-alt"></i>
                        <span></span>
                    </a>
                    <button class="btn btn-link sidebar-toggle" id="sidebar-toggle">
                        <i class="fas fa-bars"></i>
                    </button>
                </div>

                <!-- Navigation -->
                <nav class="sidebar-nav">
                    ${this.renderMenuItems()}
                </nav>
            </div>
        `;

        // 初始化折叠状态
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsed) {
            this.collapsed = true;
            addClass(this.container.querySelector('#sidebar'), 'collapsed');
        }
    }

    renderMenuItems() {
        const menuItems = [
            {
                path: '/',
                icon: 'fas fa-tachometer-alt',
                title: '仪表板',
                badge: null
            },
            {
                path: '/workorders',
                icon: 'fas fa-tasks',
                title: '工单管理',
                badge: 'workorders'
            },
            {
                path: '/alerts',
                icon: 'fas fa-bell',
                title: '预警管理',
                badge: 'alerts'
            },
            {
                path: '/knowledge',
                icon: 'fas fa-book',
                title: '知识库',
                badge: null
            },
            {
                path: '/chat',
                icon: 'fas fa-comments',
                title: '智能对话',
                badge: null
            },
            {
                path: '/chat-http',
                icon: 'fas fa-comment-dots',
                title: 'HTTP对话',
                badge: null
            },
            {
                path: '/monitoring',
                icon: 'fas fa-chart-line',
                title: '系统监控',
                badge: null
            },
            {
                path: '/feishu',
                icon: 'fab fa-lark',
                title: '飞书同步',
                badge: null
            },
            {
                path: '/agent',
                icon: 'fas fa-robot',
                title: '智能Agent',
                badge: null
            },
            {
                path: '/settings',
                icon: 'fas fa-cog',
                title: '系统设置',
                badge: null
            }
        ];

        return menuItems.map(item => `
            <a href="${item.path}" class="sidebar-nav-item" data-route="${item.path}">
                <i class="${item.icon}"></i>
                <span>${item.title}</span>
                ${item.badge ? `<span class="badge bg-danger ms-auto" id="sidebar-badge-${item.badge}">0</span>` : ''}
            </a>
        `).join('');
    }

    bindEvents() {
        // 折叠切换
        const toggleBtn = this.container.querySelector('#sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });
        }

        // 菜单项点击
        this.container.querySelectorAll('.sidebar-nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const route = e.currentTarget.getAttribute('data-route');
                if (route) {
                    router.push(route);
                }

                // 移动端点击后自动收起侧边栏
                if (window.innerWidth < 992 && !this.collapsed) {
                    this.toggle();
                }
            });
        });

        // 监听路由变化
        router.afterEach((to) => {
            this.updateActiveMenu(to.path);
        });

        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // 初始化激活状态
        this.updateActiveMenu(window.location.pathname);
    }

    toggle() {
        const sidebar = this.container.querySelector('#sidebar');
        if (sidebar) {
            this.collapsed = !this.collapsed;
            toggleClass(sidebar, 'collapsed');
            localStorage.setItem('sidebar-collapsed', this.collapsed);
        }
    }

    expand() {
        const sidebar = this.container.querySelector('#sidebar');
        if (sidebar && hasClass(sidebar, 'collapsed')) {
            this.collapsed = false;
            removeClass(sidebar, 'collapsed');
            localStorage.setItem('sidebar-collapsed', 'false');
        }
    }

    collapse() {
        const sidebar = this.container.querySelector('#sidebar');
        if (sidebar && !hasClass(sidebar, 'collapsed')) {
            this.collapsed = true;
            addClass(sidebar, 'collapsed');
            localStorage.setItem('sidebar-collapsed', 'true');
        }
    }

    updateActiveMenu(path) {
        this.container.querySelectorAll('.sidebar-nav-item').forEach(item => {
            const route = item.getAttribute('data-route');
            if (route === path) {
                addClass(item, 'active');
            } else {
                removeClass(item, 'active');
            }
        });
    }

    updateBadge(type, count) {
        const badge = this.container.querySelector(`#sidebar-badge-${type}`);
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    handleResize() {
        if (window.innerWidth >= 992) {
            // 桌面端，恢复之前的折叠状态
            const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
            if (isCollapsed !== this.collapsed) {
                if (isCollapsed) {
                    this.collapse();
                } else {
                    this.expand();
                }
            }
        } else {
            // 移动端，默认收起
            if (!this.collapsed) {
                this.collapse();
            }
        }
    }
}

// 导出组件
export default Sidebar;