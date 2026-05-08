/**
 * Service Worker
 */

const CACHE_NAME = 'ai-helpdesk-v1.0.0';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/core/utils.js',
    '/static/js/core/api.js',
    '/static/js/core/store.js',
    '/static/js/core/websocket.js',
    '/static/js/core/router.js',
    '/static/js/components/navbar.js',
    '/static/js/components/sidebar.js',
    '/static/js/components/modal.js',
    '/static/js/pages/dashboard.js',
    '/static/js/pages/alerts.js',
    '/static/js/pages/workorders.js',
    '/static/js/pages/knowledge.js',
    '/static/js/pages/chat.js',
    '/static/js/pages/monitoring.js',
    '/static/js/pages/settings.js'
];

// 安装事件
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(urlsToCache);
            })
    );
});

// 激活事件
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// 请求拦截
self.addEventListener('fetch', (event) => {
    // 只缓存GET请求
    if (event.request.method !== 'GET') {
        return;
    }

    // 不缓存API请求
    if (event.request.url.startsWith('/api/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // 缓存命中，返回缓存的资源
                if (response) {
                    return response;
                }

                // 缓存未命中，发起网络请求
                return fetch(event.request).then(
                    (response) => {
                        // 检查是否是有效响应
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // 克隆响应，因为响应是流，只能使用一次
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
    );
});