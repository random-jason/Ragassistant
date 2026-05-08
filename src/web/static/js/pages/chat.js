/**
 * 聊天页面组件
 */

export default class Chat {
    constructor(container, route) {
        this.container = container;
        this.route = route;
        this.init();
    }

    async init() {
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">智能对话</h1>
                <p class="page-subtitle">WebSocket实时聊天</p>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="text-center py-5">
                        <i class="fas fa-comments fa-3x text-muted mb-3"></i>
                        <h4 class="text-muted">聊天页面</h4>
                        <p class="text-muted">该功能正在开发中...</p>
                    </div>
                </div>
            </div>
        `;
    }
}