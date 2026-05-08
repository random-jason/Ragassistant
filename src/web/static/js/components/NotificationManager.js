/**
 * 通知管理组件
 * 统一处理应用内通知显示
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // 创建通知容器
        this.container = document.createElement('div');
        this.container.className = 'notification-container position-fixed';
        this.container.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);

        // 监听状态变化
        store.subscribe((prevState, newState) => {
            if (prevState.notifications !== newState.notifications) {
                this.renderNotifications(newState.notifications);
            }
        });
    }

    renderNotifications(notifications) {
        this.container.innerHTML = '';

        notifications.forEach(notification => {
            const notificationEl = this.createNotificationElement(notification);
            this.container.appendChild(notificationEl);
        });
    }

    createNotificationElement(notification) {
        const div = document.createElement('div');
        const typeClass = this.getTypeClass(notification.type);

        div.className = `alert alert-${typeClass} alert-dismissible fade show shadow`;
        div.style.cssText = `
            margin-bottom: 10px;
            border-radius: 8px;
            border: none;
        `;

        div.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${this.getIconClass(notification.type)} me-2"></i>
                <div class="flex-grow-1">
                    <strong>${notification.title || this.getDefaultTitle(notification.type)}</strong>
                    <div class="small mt-1">${notification.message}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // 添加关闭事件
        const closeBtn = div.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            store.removeNotification(notification.id);
        });

        return div;
    }

    getTypeClass(type) {
        const typeMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }

    getIconClass(type) {
        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle'
        };
        return iconMap[type] || 'fas fa-info-circle';
    }

    getDefaultTitle(type) {
        const titleMap = {
            'success': '成功',
            'error': '错误',
            'warning': '警告',
            'info': '提示'
        };
        return titleMap[type] || '通知';
    }

    // 便捷方法
    success(message, title = null) {
        store.addNotification({
            type: 'success',
            message,
            title
        });
    }

    error(message, title = null) {
        store.addNotification({
            type: 'error',
            message,
            title
        });
    }

    warning(message, title = null) {
        store.addNotification({
            type: 'warning',
            message,
            title
        });
    }

    info(message, title = null) {
        store.addNotification({
            type: 'info',
            message,
            title
        });
    }
}

// 创建全局通知管理器实例
const notificationManager = new NotificationManager();
