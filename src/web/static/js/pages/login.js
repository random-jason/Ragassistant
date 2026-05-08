/**
 * 登录页面组件
 */

export default class Login {
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
            console.error('Login init error:', error);
            this.showError(error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="page-container">
                <div class="page-header">
                    <div>
                        <h1 class="page-title">用户登录</h1>
                        <p class="page-subtitle">请输入您的账号信息</p>
                    </div>
                </div>

                <div class="page-content">
                    <div class="row justify-content-center">
                        <div class="col-md-6 col-lg-4">
                            <div class="card">
                                <div class="card-body">
                            <form id="login-form">
                                <!-- 用户名 -->
                                <div class="mb-3">
                                    <label for="username" class="form-label">用户名</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-user"></i>
                                        </span>
                                        <input type="text" class="form-control" id="username"
                                               name="username" required autofocus>
                                    </div>
                                </div>

                                <!-- 密码 -->
                                <div class="mb-3">
                                    <label for="password" class="form-label">密码</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-lock"></i>
                                        </span>
                                        <input type="password" class="form-control" id="password"
                                               name="password" required>
                                    </div>
                                </div>

                                <!-- 记住我 -->
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="remember"
                                           name="remember">
                                    <label class="form-check-label" for="remember">
                                        记住我
                                    </label>
                                </div>

                                <!-- 错误提示 -->
                                <div id="login-error" class="alert alert-danger d-none"></div>

                                <!-- 提交按钮 -->
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary" id="login-btn">
                                        <i class="fas fa-sign-in-alt me-2"></i>登录
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- 其他登录方式 -->
                    <div class="text-center mt-3">
                        <p class="text-muted">
                            还没有账号？<a href="#" class="text-decoration-none">立即注册</a>
                        </p>
                        <p class="text-muted">
                            <a href="#" class="text-decoration-none">忘记密码？</a>
                        </p>
                    </div>
                </div>
            </div>
            </div>
        `;
    }

    bindEvents() {
        const form = document.getElementById('login-form');
        const loginBtn = document.getElementById('login-btn');
        const errorDiv = document.getElementById('login-error');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 获取表单数据
            const formData = new FormData(form);
            const username = formData.get('username');
            const password = formData.get('password');
            const remember = formData.get('remember');

            // 显示加载状态
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>登录中...';
            errorDiv.classList.add('d-none');

            try {
                // 调用登录API
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username,
                        password,
                        remember
                    }),
                    credentials: 'same-origin'
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    // 登录成功
                    // 保存token到sessionStorage（会话级别）
                    sessionStorage.setItem('token', data.token);

                    // 如果选择记住我，也保存到localStorage
                    if (remember) {
                        localStorage.setItem('user', JSON.stringify(data.user));
                        localStorage.setItem('token', data.token);
                        localStorage.setItem('remember', 'true');
                    }

                    // 更新应用状态
                    if (window.store) {
                        window.store.commit('SET_USER', data.user);
                        window.store.commit('SET_LOGIN', true);
                        window.store.commit('SET_TOKEN', data.token);
                    }

                    // 显示成功提示
                    if (window.showToast) {
                        window.showToast('登录成功', 'success');
                    }

                    // 跳转到仪表板
                    if (window.router) {
                        window.router.push('/');
                    } else {
                        // 如果路由器还没初始化，直接跳转
                        window.location.href = '/';
                    }
                } else {
                    // 登录失败
                    errorDiv.textContent = data.message || '用户名或密码错误';
                    errorDiv.classList.remove('d-none');
                }
            } catch (error) {
                console.error('Login error:', error);
                errorDiv.textContent = '网络错误，请稍后重试';
                errorDiv.classList.remove('d-none');
            } finally {
                // 恢复按钮状态
                loginBtn.disabled = false;
                loginBtn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>登录';
            }
        });

        // 检查本地存储中的登录状态
        const rememberedUser = localStorage.getItem('remember');
        if (rememberedUser === 'true') {
            const user = localStorage.getItem('user');
            if (user) {
                try {
                    const userData = JSON.parse(user);
                    document.getElementById('username').value = userData.username || '';
                    document.getElementById('remember').checked = true;
                } catch (e) {
                    console.error('Error parsing remembered user:', e);
                }
            }
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