/**
 * 404页面组件
 */

export default class NotFound {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.init();
    }

    async init() {
        try {
            this.render();
            this.bindEvents();
        } catch (error) {
            console.error('NotFound init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">404 - 页面未找到</h1>
                    <p class="page-subtitle">抱歉，您访问的页面不存在</p>
                </div>
            </div>

            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card">
                        <div class="card-body py-5">
                            <div class="error-illustration mb-4">
                                <i class="fas fa-search fa-5x text-muted"></i>
                            </div>
                            <h4 class="mb-3">页面不存在</h4>
                            <p class="text-muted mb-4">
                                看起来您访问的页面已经被移除、名称已更改或暂时不可用。
                            </p>
                            <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                                <button class="btn btn-primary" onclick="window.router && window.router.push('/') || (window.location.href = '/')">
                                    <i class="fas fa-home me-2"></i>返回首页
                                </button>
                                <button class="btn btn-outline-secondary" onclick="window.history.back()">
                                    <i class="fas fa-arrow-left me-2"></i>返回上一页
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 快速导航 -->
            <div class="row mt-5">
                <div class="col-12">
                    <h5 class="mb-3">快速导航</h5>
                    <div class="row">
                        <div class="col-md-3 col-sm-6 mb-3">
                            <a href="#" class="text-decoration-none">
                                <div class="card h-100 border-0 shadow-sm hover-shadow">
                                    <div class="card-body text-center">
                                        <i class="fas fa-tachometer-alt fa-2x text-primary mb-2"></i>
                                        <h6 class="card-title">仪表板</h6>
                                        <p class="card-text text-muted small">系统概览</p>
                                    </div>
                                </div>
                            </a>
                        </div>
                        <div class="col-md-3 col-sm-6 mb-3">
                            <a href="#" class="text-decoration-none">
                                <div class="card h-100 border-0 shadow-sm hover-shadow">
                                    <div class="card-body text-center">
                                        <i class="fas fa-tasks fa-2x text-success mb-2"></i>
                                        <h6 class="card-title">工单管理</h6>
                                        <p class="card-text text-muted small">工单处理</p>
                                    </div>
                                </div>
                            </a>
                        </div>
                        <div class="col-md-3 col-sm-6 mb-3">
                            <a href="#" class="text-decoration-none">
                                <div class="card h-100 border-0 shadow-sm hover-shadow">
                                    <div class="card-body text-center">
                                        <i class="fas fa-bell fa-2x text-warning mb-2"></i>
                                        <h6 class="card-title">预警管理</h6>
                                        <p class="card-text text-muted small">系统预警</p>
                                    </div>
                                </div>
                            </a>
                        </div>
                        <div class="col-md-3 col-sm-6 mb-3">
                            <a href="#" class="text-decoration-none">
                                <div class="card h-100 border-0 shadow-sm hover-shadow">
                                    <div class="card-body text-center">
                                        <i class="fas fa-book fa-2x text-info mb-2"></i>
                                        <h6 class="card-title">知识库</h6>
                                        <p class="card-text text-muted small">知识文档</p>
                                    </div>
                                </div>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 绑定导航链接事件
        const links = this.container.querySelectorAll('a[href^="#"]');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const href = link.getAttribute('href');
                if (href === '#home' && window.router) {
                    window.router.push('/');
                }
            });
        });
    }

    showError(error) {
        this.container.innerHTML = `
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
        `;
    }
}