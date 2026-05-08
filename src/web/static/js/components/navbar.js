/**
 * 导航栏组件
 */

import { addClass, removeClass, hasClass, toggleClass } from '../core/utils.js';
import store from '../core/store.js';
import router from '../core/router.js';

export class Navbar {
    constructor(container) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.userMenuOpen = false;
        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <nav class="navbar">
                <!-- 移动端菜单按钮 -->
                <button class="navbar-toggler" id="sidebar-toggle" type="button">
                    <i class="fas fa-bars"></i>
                </button>

                <div class="navbar-brand">
                    <i class="fas fa-shield-alt"></i>
                    <span>AI Helpdesk</span>
                </div>

                <ul class="navbar-nav">
                    <!-- 监控状态 -->
                    <li class="nav-item">
                        <span class="nav-link" id="monitor-status">
                            <i class="fas fa-circle" id="status-indicator"></i>
                            <span id="status-text">检查中...</span>
                        </span>
                    </li>

                    <!-- 通知 -->
                    <li class="nav-item dropdown" id="notifications-dropdown">
                        <a href="#" class="nav-link" data-toggle="dropdown">
                            <i class="fas fa-bell"></i>
                            <span class="badge bg-danger" id="notification-count">0</span>
                        </a>
                        <div class="dropdown-menu dropdown-menu-end">
                            <div class="dropdown-header">
                                <h6>通知</h6>
                                <a href="#" class="btn btn-sm btn-link" id="clear-notifications">清空</a>
                            </div>
                            <div class="dropdown-divider"></div>
                            <div id="notification-list" class="notification-list">
                                <div class="dropdown-item text-muted">暂无通知</div>
                            </div>
                        </div>
                    </li>

                    <!-- 用户菜单 -->
                    <li class="nav-item dropdown user-menu">
                        <a href="#" class="nav-link" id="user-menu-toggle">
                            <div class="user-avatar" id="user-avatar">
                                ${this.getUserInitial()}
                            </div>
                        </a>
                        <div class="user-dropdown" id="user-dropdown">
                            <div class="dropdown-header">
                                <div class="d-flex align-items-center">
                                    <div class="user-avatar me-2">
                                        ${this.getUserInitial()}
                                    </div>
                                    <div>
                                        <div class="fw-bold" id="user-name">${this.getUserName()}</div>
                                        <div class="small text-muted" id="user-role">${this.getUserRole()}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="dropdown-divider"></div>
                            <a href="#" class="user-dropdown-item" data-route="/profile">
                                <i class="fas fa-user me-2"></i>个人资料
                            </a>
                            <a href="#" class="user-dropdown-item" data-route="/settings">
                                <i class="fas fa-cog me-2"></i>系统设置
                            </a>
                            <div class="user-dropdown-divider"></div>
                            <a href="#" class="user-dropdown-item text-danger" id="logout-btn">
                                <i class="fas fa-sign-out-alt me-2"></i>退出登录
                            </a>
                        </div>
                    </li>

                    <!-- 主题切换 -->
                    <li class="nav-item">
                        <button class="nav-link btn btn-link" id="theme-toggle">
                            <i class="fas fa-moon" id="theme-icon"></i>
                        </button>
                    </li>
                </ul>
            </nav>
        `;
    }

    bindEvents() {
        // 侧边栏切换（移动端）
        const sidebarToggle = this.container.querySelector('#sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // 用户菜单切换
        const userMenuToggle = this.container.querySelector('#user-menu-toggle');
        if (userMenuToggle) {
            userMenuToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleUserMenu();
            });
        }

        // 通知下拉菜单
        const notificationsDropdown = this.container.querySelector('#notifications-dropdown');
        if (notificationsDropdown) {
            const toggle = notificationsDropdown.querySelector('[data-toggle="dropdown"]');
            if (toggle) {
                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleNotifications();
                });
            }
        }

        // 主题切换
        const themeToggle = this.container.querySelector('#theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // 退出登录
        const logoutBtn = this.container.querySelector('#logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        }

        // 清空通知
        const clearNotifications = this.container.querySelector('#clear-notifications');
        if (clearNotifications) {
            clearNotifications.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearNotifications();
            });
        }

        // 路由链接
        this.container.querySelectorAll('[data-route]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const route = e.currentTarget.getAttribute('data-route');
                if (route) {
                    router.push(route);
                }
            });
        });

        // 点击外部关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeUserMenu();
                this.closeNotifications();
            }
        });

        // 监听store变化
        store.subscribe((state) => {
            this.updateUser(state.user);
            this.updateNotifications(state.ui.notifications);
            this.updateMonitorStatus(state.monitor);
        });
    }

    toggleUserMenu() {
        const dropdown = this.container.querySelector('#user-dropdown');
        if (dropdown) {
            this.userMenuOpen = !this.userMenuOpen;
            toggleClass(dropdown, 'show');
        }
    }

    closeUserMenu() {
        const dropdown = this.container.querySelector('#user-dropdown');
        if (dropdown && hasClass(dropdown, 'show')) {
            this.userMenuOpen = false;
            removeClass(dropdown, 'show');
        }
    }

    toggleNotifications() {
        const dropdown = this.container.querySelector('#notifications-dropdown .dropdown-menu');
        if (dropdown) {
            toggleClass(dropdown, 'show');
        }
    }

    closeNotifications() {
        const dropdown = this.container.querySelector('#notifications-dropdown .dropdown-menu');
        if (dropdown && hasClass(dropdown, 'show')) {
            removeClass(dropdown, 'show');
        }
    }

    toggleTheme() {
        const currentTheme = store.getState('app.theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        store.commit('SET_THEME', newTheme);

        const icon = this.container.querySelector('#theme-icon');
        if (icon) {
            icon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    handleLogout() {
        if (confirm('确定要退出登录吗？')) {
            // 调用注销API
            fetch('/api/logout', { method: 'POST' })
                .then(() => {
                    // 清除应用状态
                    store.commit('SET_USER', null);
                    store.commit('SET_LOGIN', false);
                    store.commit('SET_TOKEN', null);

                    // 清除本地存储和会话存储
                    localStorage.removeItem('user');
                    localStorage.removeItem('token');
                    localStorage.removeItem('remember');
                    sessionStorage.removeItem('token');

                    // 显示提示
                    if (window.showToast) {
                        window.showToast('已退出登录', 'info');
                    }

                    // 跳转到登录页
                    router.push('/login');
                })
                .catch(error => {
                    console.error('注销失败:', error);
                    // 即使API调用失败，也要清除本地状态
                    store.commit('SET_USER', null);
                    store.commit('SET_LOGIN', false);
                    store.commit('SET_TOKEN', null);
                    localStorage.clear();
                    sessionStorage.clear();
                    router.push('/login');
                });
        }
    }

    clearNotifications() {
        store.setState({
            ui: {
                ...store.getState('ui'),
                notifications: []
            }
        });
    }

    updateNotifications(notifications) {
        const countEl = this.container.querySelector('#notification-count');
        const listEl = this.container.querySelector('#notification-list');

        if (!countEl || !listEl) return;

        const count = notifications.length;
        countEl.textContent = count;
        countEl.style.display = count > 0 ? 'inline-block' : 'none';

        if (count === 0) {
            listEl.innerHTML = '<div class="dropdown-item text-muted">暂无通知</div>';
        } else {
            listEl.innerHTML = notifications.slice(0, 5).map(notification => `
                <a href="#" class="dropdown-item ${notification.read ? '' : 'unread'}">
                    <div class="d-flex">
                        <div class="flex-shrink-0">
                            <i class="fas ${this.getNotificationIcon(notification.type)} text-${notification.type}"></i>
                        </div>
                        <div class="flex-grow-1 ms-2">
                            <div class="small">${notification.message}</div>
                            <div class="text-muted small">${this.formatTime(notification.time)}</div>
                        </div>
                    </div>
                </a>
            `).join('');
        }
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || 'fa-bell';
    }

    updateMonitorStatus(monitor) {
        const indicator = this.container.querySelector('#status-indicator');
        const text = this.container.querySelector('#status-text');

        if (!indicator || !text) return;

        if (monitor.status === 'running') {
            indicator.className = 'fas fa-circle text-success';
            text.textContent = '监控运行中';
        } else {
            indicator.className = 'fas fa-circle text-warning';
            text.textContent = '监控已停止';
        }
    }

    updateUser(user) {
        const avatar = this.container.querySelector('#user-avatar');
        const name = this.container.querySelector('#user-name');
        const role = this.container.querySelector('#user-role');

        if (user && user.info) {
            const initial = this.getInitial(user.info.name);
            if (avatar) avatar.textContent = initial;
            if (name) name.textContent = user.info.name;
            if (role) role.textContent = user.info.role || '用户';
        } else {
            if (avatar) avatar.textContent = 'U';
            if (name) name.textContent = '未登录';
            if (role) role.textContent = '访客';
        }
    }

    getUserInitial() {
        const user = store.getState('user.info');
        return user ? this.getInitial(user.name) : 'U';
    }

    getUserName() {
        const user = store.getState('user.info');
        return user ? user.name : '未登录';
    }

    getUserRole() {
        const user = store.getState('user.info');
        return user ? (user.role || '用户') : '访客';
    }

    getInitial(name) {
        if (!name) return 'U';
        const chars = name.trim().split(/\s+/);
        if (chars.length >= 2) {
            return chars[0][0] + chars[chars.length - 1][0];
        }
        return name[0].toUpperCase();
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay') || this.createOverlay();
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            // 移动端：切换显示
            toggleClass(sidebar, 'open');
            toggleClass(overlay, 'show');
        } else {
            // 桌面端：切换折叠
            toggleClass(sidebar, 'collapsed');
        }
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', () => {
            this.toggleSidebar();
        });
        document.body.appendChild(overlay);
        return overlay;
    }

    formatTime(time) {
        const date = new Date(time);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) {
            return '刚刚';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleDateString();
        }
    }
}

// 导出组件
export default Navbar;