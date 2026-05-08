/**
 * 模态框组件
 */

import { addClass, removeClass, hasClass } from '../core/utils.js';

export class Modal {
    constructor(options = {}) {
        this.id = options.id || `modal-${Date.now()}`;
        this.title = options.title || '';
        this.content = options.content || '';
        this.size = options.size || ''; // sm, lg, xl
        this.backdrop = options.backdrop !== false;
        this.keyboard = options.keyboard !== false;
        this.centered = options.centered || false;
        this.scrollable = options.scrollable || false;
        this.static = options.static || false;
        this.className = options.className || '';
        this.footer = options.footer || null;
        this.show = false;

        this.onShow = options.onShow || (() => {});
        this.onShown = options.onShown || (() => {});
        this.onHide = options.onHide || (() => {});
        this.onHidden = options.onHidden || (() => {});

        this.init();
    }

    init() {
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // 创建模态框容器
        this.modal = document.createElement('div');
        this.modal.className = 'modal fade';
        this.modal.id = this.id;
        this.modal.setAttribute('tabindex', '-1');
        this.modal.setAttribute('aria-labelledby', `${this.id}-label`);
        this.modal.setAttribute('aria-hidden', 'true');

        // 模态框对话框
        const dialog = document.createElement('div');
        dialog.className = `modal-dialog ${this.size ? `modal-${this.size}` : ''} ${this.centered ? 'modal-dialog-centered' : ''} ${this.scrollable ? 'modal-dialog-scrollable' : ''}`;

        // 模态框内容
        const content = document.createElement('div');
        content.className = 'modal-content';
        if (this.className) {
            addClass(content, this.className);
        }

        // 构建模态框HTML
        let modalHTML = `
            <div class="modal-header">
                <h5 class="modal-title" id="${this.id}-label">${this.title}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                ${this.content}
            </div>
        `;

        // 添加底部按钮
        if (this.footer) {
            modalHTML += `
                <div class="modal-footer">
                    ${typeof this.footer === 'string' ? this.footer : this.renderFooter()}
                </div>
            `;
        }

        content.innerHTML = modalHTML;
        dialog.appendChild(content);
        this.modal.appendChild(dialog);

        // 添加到页面
        document.body.appendChild(this.modal);
    }

    renderFooter() {
        if (!this.footer) return '';

        if (Array.isArray(this.footer)) {
            return this.footer.map(btn => {
                const attrs = Object.keys(btn)
                    .filter(key => key !== 'text')
                    .map(key => `${key}="${btn[key]}"`)
                    .join(' ');
                return `<button ${attrs}>${btn.text}</button>`;
            }).join('');
        }

        return '';
    }

    bindEvents() {
        // 关闭按钮
        const closeBtn = this.modal.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }

        // 背景点击
        if (!this.static) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });
        }

        // ESC键关闭
        if (this.keyboard) {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.show) {
                    this.hide();
                }
            });
        }
    }

    show() {
        if (this.show) return;

        // 触发显示前事件
        this.onShow();

        // 添加到页面
        if (!this.modal.parentNode) {
            document.body.appendChild(this.modal);
        }

        // 显示模态框
        this.modal.style.display = 'block';
        addClass(this.modal, 'show');
        this.modal.setAttribute('aria-hidden', 'false');

        // 防止背景滚动
        document.body.style.overflow = 'hidden';

        this.show = true;

        // 聚焦到第一个可聚焦元素
        setTimeout(() => {
            const focusable = this.modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable) {
                focusable.focus();
            }
        }, 100);

        // 触发显示后事件
        setTimeout(() => {
            this.onShown();
        }, 150);
    }

    hide() {
        if (!this.show) return;

        // 触发隐藏前事件
        this.onHide();

        // 隐藏模态框
        removeClass(this.modal, 'show');
        this.modal.setAttribute('aria-hidden', 'true');

        // 恢复背景滚动
        document.body.style.overflow = '';

        this.show = false;

        // 延迟移除DOM
        setTimeout(() => {
            if (this.modal) {
                this.modal.style.display = 'none';
                if (this.modal.parentNode) {
                    this.modal.parentNode.removeChild(this.modal);
                }
            }

            // 触发隐藏后事件
            this.onHidden();
        }, 150);
    }

    toggle() {
        if (this.show) {
            this.hide();
        } else {
            this.show();
        }
    }

    update(options) {
        if (options.title) {
            this.title = options.title;
            const titleEl = this.modal.querySelector('.modal-title');
            if (titleEl) {
                titleEl.textContent = this.title;
            }
        }

        if (options.content) {
            this.content = options.content;
            const bodyEl = this.modal.querySelector('.modal-body');
            if (bodyEl) {
                bodyEl.innerHTML = this.content;
            }
        }

        if (options.footer !== undefined) {
            this.footer = options.footer;
            const footerEl = this.modal.querySelector('.modal-footer');
            if (footerEl) {
                if (this.footer) {
                    footerEl.style.display = 'block';
                    footerEl.innerHTML = typeof this.footer === 'string' ? this.footer : this.renderFooter();

                    // 重新绑定底部按钮事件
                    this.bindFooterEvents();
                } else {
                    footerEl.style.display = 'none';
                }
            }
        }
    }

    bindFooterEvents() {
        const footer = this.modal.querySelector('.modal-footer');
        if (!footer) return;

        footer.querySelectorAll('button').forEach(btn => {
            const dataDismiss = btn.getAttribute('data-bs-dismiss');
            if (dataDismiss === 'modal') {
                btn.addEventListener('click', () => this.hide());
            }
        });
    }

    getModal() {
        return this.modal;
    }

    getElement(selector) {
        return this.modal.querySelector(selector);
    }

    destroy() {
        this.hide();
        setTimeout(() => {
            if (this.modal && this.modal.parentNode) {
                this.modal.parentNode.removeChild(this.modal);
            }
            this.modal = null;
        }, 200);
    }
}

// 确认对话框
export function confirm(options = {}) {
    return new Promise((resolve) => {
        const modal = new Modal({
            title: options.title || '确认',
            content: `
                <div class="text-center">
                    <i class="fas fa-question-circle fa-3x text-warning mb-3"></i>
                    <p>${options.message || '确定要执行此操作吗？'}</p>
                </div>
            `,
            size: 'sm',
            centered: true,
            footer: [
                { text: '取消', class: 'btn btn-secondary', 'data-bs-dismiss': 'modal' },
                { text: '确定', class: 'btn btn-primary', id: 'confirm-btn' }
            ]
        });

        modal.onHidden = () => {
            modal.destroy();
        };

        modal.getElement('#confirm-btn').addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });

        modal.onHidden = () => {
            resolve(false);
            modal.destroy();
        };

        modal.show();
    });
}

// 警告对话框
export function alert(options = {}) {
    return new Promise((resolve) => {
        const modal = new Modal({
            title: options.title || '提示',
            content: `
                <div class="text-center">
                    <i class="fas fa-${options.type === 'error' ? 'exclamation-circle text-danger' : 'info-circle text-info'} fa-3x mb-3"></i>
                    <p>${options.message || ''}</p>
                </div>
            `,
            size: 'sm',
            centered: true,
            footer: [
                { text: '确定', class: 'btn btn-primary', id: 'alert-btn' }
            ]
        });

        modal.onHidden = () => {
            modal.destroy();
            resolve();
        };

        modal.getElement('#alert-btn').addEventListener('click', () => {
            modal.hide();
        });

        modal.show();
    });
}

// Toast通知
export class Toast {
    constructor(options = {}) {
        this.id = `toast-${Date.now()}`;
        this.type = options.type || 'info';
        this.message = options.message || '';
        this.duration = options.duration || 3000;
        this.closable = options.closable !== false;
        this.autoHide = options.autoHide !== false;

        this.init();
    }

    init() {
        this.createToast();
        this.show();
    }

    createToast() {
        // 查找或创建toast容器
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // 创建toast元素
        this.toast = document.createElement('div');
        this.toast.className = `toast ${this.type}`;
        this.toast.id = this.id;

        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        this.toast.innerHTML = `
            <div class="toast-content">
                <i class="fas ${iconMap[this.type] || iconMap.info} me-2"></i>
                <span>${this.message}</span>
                ${this.closable ? '<button type="button" class="btn-close ms-2" aria-label="Close"></button>' : ''}
            </div>
        `;

        container.appendChild(this.toast);

        // 绑定关闭事件
        if (this.closable) {
            const closeBtn = this.toast.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hide());
            }
        }

        // 自动隐藏
        if (this.autoHide) {
            setTimeout(() => this.hide(), this.duration);
        }
    }

    show() {
        setTimeout(() => {
            addClass(this.toast, 'show');
        }, 10);
    }

    hide() {
        removeClass(this.toast, 'show');
        setTimeout(() => {
            if (this.toast && this.toast.parentNode) {
                this.toast.parentNode.removeChild(this.toast);
            }
        }, 300);
    }
}

// 创建全局toast函数
export function showToast(options) {
    if (typeof options === 'string') {
        options = { message: options };
    }
    return new Toast(options);
}

// 导出
export default Modal;