/**
 * 工具函数集合
 */

// 防抖函数
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 格式化日期
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '';

    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

// 相对时间格式化
export function formatRelativeTime(date) {
    if (!date) return '';

    const now = new Date();
    const target = new Date(date);
    const diff = now - target;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 30) {
        return formatDate(date, 'YYYY-MM-DD');
    } else if (days > 0) {
        return `${days}天前`;
    } else if (hours > 0) {
        return `${hours}小时前`;
    } else if (minutes > 0) {
        return `${minutes}分钟前`;
    } else {
        return '刚刚';
    }
}

// 文件大小格式化
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 数字千分位格式化
export function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 深拷贝
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }

    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }

    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }

    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

// 生成唯一ID
export function generateId(prefix = '') {
    const timestamp = Date.now().toString(36);
    const randomStr = Math.random().toString(36).substr(2, 5);
    return `${prefix}${timestamp}${randomStr}`;
}

// 查询参数解析
export function parseQueryString(queryString) {
    const params = new URLSearchParams(queryString);
    const result = {};

    for (const [key, value] of params) {
        result[key] = value;
    }

    return result;
}

// 查询参数序列化
export function serializeQueryString(params) {
    return Object.entries(params)
        .filter(([_, value]) => value !== undefined && value !== null)
        .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
        .join('&');
}

// 获取查询参数
export function getQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// 设置查询参数
export function setQueryParam(name, value) {
    const params = new URLSearchParams(window.location.search);
    params.set(name, value);
    const newUrl = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
    window.history.replaceState(null, '', newUrl);
}

// 删除查询参数
export function removeQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    params.delete(name);
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}${window.location.hash}`;
    window.history.replaceState(null, '', newUrl);
}

// 本地存储封装
export const storage = {
    set(key, value, isSession = false) {
        try {
            const storage = isSession ? sessionStorage : localStorage;
            storage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Storage set error:', e);
        }
    },

    get(key, defaultValue = null, isSession = false) {
        try {
            const storage = isSession ? sessionStorage : localStorage;
            const item = storage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage get error:', e);
            return defaultValue;
        }
    },

    remove(key, isSession = false) {
        try {
            const storage = isSession ? sessionStorage : localStorage;
            storage.removeItem(key);
        } catch (e) {
            console.error('Storage remove error:', e);
        }
    },

    clear(isSession = false) {
        try {
            const storage = isSession ? sessionStorage : localStorage;
            storage.clear();
        } catch (e) {
            console.error('Storage clear error:', e);
        }
    }
};

// Cookie操作
export const cookie = {
    set(name, value, days = 7) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    },

    get(name) {
        const nameEQ = `${name}=`;
        const ca = document.cookie.split(';');
        for (let c of ca) {
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length, c.length);
            }
        }
        return null;
    },

    remove(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
};

// 类名操作
export function addClass(element, className) {
    if (element.classList) {
        element.classList.add(className);
    } else {
        element.className += ` ${className}`;
    }
}

export function removeClass(element, className) {
    if (element.classList) {
        element.classList.remove(className);
    } else {
        element.className = element.className.replace(
            new RegExp(`(^|\\b)${className.split(' ').join('|')}(\\b|$)`, 'gi'),
            ' '
        );
    }
}

export function hasClass(element, className) {
    if (element.classList) {
        return element.classList.contains(className);
    } else {
        return new RegExp(`(^| )${className}( |$)`, 'gi').test(element.className);
    }
}

export function toggleClass(element, className) {
    if (hasClass(element, className)) {
        removeClass(element, className);
    } else {
        addClass(element, className);
    }
}

// 事件委托
export function delegate(parent, selector, event, handler) {
    parent.addEventListener(event, function(e) {
        if (e.target.matches(selector)) {
            handler(e);
        }
    });
}

// DOM就绪
export function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// 动画帧
export const raf = window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    function(callback) { return setTimeout(callback, 1000 / 60); };

export const caf = window.cancelAnimationFrame ||
    window.webkitCancelAnimationFrame ||
    window.mozCancelAnimationFrame ||
    function(id) { clearTimeout(id); };

// 错误处理
export function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);

    // 发送错误到服务器（可选）
    if (window.errorReporting) {
        window.errorReporting.report(error, context);
    }

    // 显示用户友好的错误信息
    showToast('发生错误，请稍后重试', 'error');
}

// 安全的JSON解析
export function safeJsonParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch (e) {
        return defaultValue;
    }
}

// XSS防护 - HTML转义
export function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// 验证函数
export const validators = {
    email: (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    phone: (phone) => {
        const re = /^1[3-9]\d{9}$/;
        return re.test(phone);
    },

    url: (url) => {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    idCard: (idCard) => {
        const re = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
        return re.test(idCard);
    }
};

// URL构建器
export class URLBuilder {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.params = {};
    }

    path(path) {
        this.baseURL = this.baseURL.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
        return this;
    }

    query(key, value) {
        if (value !== undefined && value !== null) {
            this.params[key] = value;
        }
        return this;
    }

    build() {
        const queryString = serializeQueryString(this.params);
        return queryString ? `${this.baseURL}?${queryString}` : this.baseURL;
    }
}

// 图片压缩
export function compressImage(file, options = {}) {
    const {
        maxWidth = 800,
        maxHeight = 800,
        quality = 0.8,
        mimeType = 'image/jpeg'
    } = options;

    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
            // 计算新尺寸
            let { width, height } = img;

            if (width > maxWidth || height > maxHeight) {
                const ratio = Math.min(maxWidth / width, maxHeight / height);
                width *= ratio;
                height *= ratio;
            }

            canvas.width = width;
            canvas.height = height;

            // 绘制并压缩
            ctx.drawImage(img, 0, 0, width, height);
            canvas.toBlob(resolve, mimeType, quality);
        };

        img.src = URL.createObjectURL(file);
    });
}

// 导出默认配置
export const defaultConfig = {
    apiBaseUrl: '/api',
    wsUrl: `ws://${window.location.host}:8765`,
    toastDuration: 3000,
    paginationSize: 10,
    debounceDelay: 300,
    throttleDelay: 100
};