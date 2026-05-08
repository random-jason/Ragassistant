/**
 * 工单管理页面组件
 */

export default class WorkOrders {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.currentPage = 1;
        this.perPage = 20;
        this.currentStatus = 'all';
        this.searchQuery = '';
        this.init();
    }

    async init() {
        try {
            this.render();
            this.bindEvents();
            await this.loadWorkOrders();
        } catch (error) {
            console.error('WorkOrders init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-container">
                <div class="page-header">
                    <div>
                        <h1 class="page-title">工单管理</h1>
                        <p class="page-subtitle">工单列表与管理</p>
                    </div>
                    <div class="page-actions">
                        <button class="btn btn-primary" id="create-workorder-btn">
                            <i class="fas fa-plus me-2"></i>新建工单
                        </button>
                    </div>
                </div>

                <div class="page-content">

            <!-- 筛选和搜索 -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">状态筛选</label>
                            <select class="form-select" id="status-filter">
                                <option value="all">全部状态</option>
                                <option value="open">待处理</option>
                                <option value="in_progress">处理中</option>
                                <option value="resolved">已解决</option>
                                <option value="closed">已关闭</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">搜索</label>
                            <input type="text" class="form-control" id="search-input"
                                   placeholder="搜索工单标题、描述或ID...">
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button class="btn btn-outline-secondary w-100" id="search-btn">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 工单列表 -->
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="card-title mb-0">工单列表</h5>
                    <div id="workorder-count" class="text-muted small">共 0 个工单</div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover" id="workorders-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>标题</th>
                                    <th>类别</th>
                                    <th>优先级</th>
                                    <th>状态</th>
                                    <th>创建时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="workorders-tbody">
                                <tr>
                                    <td colspan="7" class="text-center text-muted">
                                        <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

                    <!-- 分页 -->
                    <nav id="pagination-nav" class="mt-4" style="display: none;">
                        <ul class="pagination justify-content-center" id="pagination-list">
                        </ul>
                    </nav>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 状态筛选
        document.getElementById('status-filter').addEventListener('change', () => {
            this.currentStatus = document.getElementById('status-filter').value;
            this.currentPage = 1;
            this.loadWorkOrders();
        });

        // 搜索
        document.getElementById('search-btn').addEventListener('click', () => {
            this.searchQuery = document.getElementById('search-input').value.trim();
            this.currentPage = 1;
            this.loadWorkOrders();
        });

        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('search-btn').click();
            }
        });

        // 新建工单
        document.getElementById('create-workorder-btn').addEventListener('click', () => {
            this.showCreateWorkOrderModal();
        });
    }

    async loadWorkOrders() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                status: this.currentStatus,
                search: this.searchQuery
            });

            const response = await fetch(`/api/workorders?${params}`);
            const data = await response.json();

            if (response.ok && data.success) {
                this.renderWorkOrders(data.workorders || []);
                this.renderPagination(data.pagination || {});
                document.getElementById('workorder-count').textContent = `共 ${data.total || 0} 个工单`;
            } else {
                this.showErrorInTable(data.message || '加载工单失败');
            }
        } catch (error) {
            console.error('加载工单失败:', error);
            this.showErrorInTable('网络错误');
        }
    }

    renderWorkOrders(workorders) {
        const tbody = document.getElementById('workorders-tbody');

        if (workorders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="fas fa-inbox me-2"></i>暂无工单
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = workorders.map(workorder => {
            const statusBadge = this.getStatusBadge(workorder.status);
            const priorityBadge = this.getPriorityBadge(workorder.priority);
            const createTime = new Date(workorder.created_at).toLocaleString();

            return `
                <tr>
                    <td>${workorder.order_id || workorder.id}</td>
                    <td>
                        <div class="fw-bold">${workorder.title}</div>
                        <small class="text-muted">${workorder.description?.substring(0, 50) || ''}...</small>
                    </td>
                    <td><span class="badge bg-secondary">${workorder.category || '未分类'}</span></td>
                    <td>${priorityBadge}</td>
                    <td>${statusBadge}</td>
                    <td>${createTime}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewWorkOrder(${workorder.id})">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-secondary" onclick="editWorkOrder(${workorder.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteWorkOrder(${workorder.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    renderPagination(pagination) {
        const nav = document.getElementById('pagination-nav');
        const list = document.getElementById('pagination-list');

        if (!pagination || pagination.total_pages <= 1) {
            nav.style.display = 'none';
            return;
        }

        nav.style.display = 'block';

        let html = '';

        // 上一页
        if (pagination.has_prev) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${pagination.page - 1})">上一页</a></li>`;
        }

        // 页码
        for (let i = Math.max(1, pagination.page - 2); i <= Math.min(pagination.total_pages, pagination.page + 2); i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            html += `<li class="page-item ${activeClass}"><a class="page-link" href="#" onclick="changePage(${i})">${i}</a></li>`;
        }

        // 下一页
        if (pagination.has_next) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${pagination.page + 1})">下一页</a></li>`;
        }

        list.innerHTML = html;
    }

    getStatusBadge(status) {
        const statusMap = {
            'open': '<span class="badge bg-danger">待处理</span>',
            'in_progress': '<span class="badge bg-warning">处理中</span>',
            'resolved': '<span class="badge bg-success">已解决</span>',
            'closed': '<span class="badge bg-secondary">已关闭</span>'
        };
        return statusMap[status] || `<span class="badge bg-light">${status}</span>`;
    }

    getPriorityBadge(priority) {
        const priorityMap = {
            'low': '<span class="badge bg-info">低</span>',
            'medium': '<span class="badge bg-warning">中</span>',
            'high': '<span class="badge bg-danger">高</span>',
            'urgent': '<span class="badge bg-dark">紧急</span>'
        };
        return priorityMap[priority] || `<span class="badge bg-light">${priority}</span>`;
    }

    showErrorInTable(message) {
        const tbody = document.getElementById('workorders-tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>${message}
                </td>
            </tr>
        `;
    }

    showCreateWorkOrderModal() {
        // 这里应该显示创建工单的模态框
        if (window.showToast) {
            window.showToast('创建工单功能开发中', 'info');
        }
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

// 全局函数供表格操作使用
window.viewWorkOrder = function(id) {
    if (window.showToast) {
        window.showToast(`查看工单 ${id} 功能开发中`, 'info');
    }
};

window.editWorkOrder = function(id) {
    if (window.showToast) {
        window.showToast(`编辑工单 ${id} 功能开发中`, 'info');
    }
};

window.deleteWorkOrder = function(id) {
    if (confirm(`确定要删除工单 ${id} 吗？`)) {
        if (window.showToast) {
            window.showToast('删除功能开发中', 'info');
        }
    }
};

window.changePage = function(page) {
    // 重新加载当前页面实例
    const event = new CustomEvent('changePage', { detail: { page } });
    document.dispatchEvent(event);
};