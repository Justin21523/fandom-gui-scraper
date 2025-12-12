/**
 * Login Page - 登入頁面
 */

import { t } from '../i18n/i18n.js';
import { login } from '../api/auth.js';
import { authStore } from '../stores/authStore.js';
import router from '../router.js';
import toast from '../components/toast.js';

/**
 * 渲染登入頁面
 * @param {HTMLElement} container - 容器元素
 */
export function renderLoginPage(container) {
    // 如果已經登入，重導向到首頁
    const { isAuthenticated } = authStore.getState();
    if (isAuthenticated) {
        router.navigate('/', { replace: true });
        return;
    }

    container.innerHTML = `
        <div class="login-page">
            <div class="login-card animate-slideUp">
                <div class="login-card__header">
                    <div class="login-card__logo">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                            <path d="M2 17l10 5 10-5"/>
                            <path d="M2 12l10 5 10-5"/>
                        </svg>
                    </div>
                    <h1 class="login-card__title">Fandom Scraper</h1>
                    <p class="login-card__subtitle">${t('auth.login')}</p>
                </div>

                <form class="login-form" id="login-form">
                    <div class="form-group">
                        <label class="form-label" for="username">${t('auth.username')}</label>
                        <div class="input-group">
                            <span class="input-group__prefix">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                                </svg>
                            </span>
                            <input type="text"
                                   class="input"
                                   id="username"
                                   name="username"
                                   placeholder="${t('auth.username')}"
                                   required
                                   autocomplete="username">
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="password">${t('auth.password')}</label>
                        <div class="input-group">
                            <span class="input-group__prefix">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                                </svg>
                            </span>
                            <input type="password"
                                   class="input"
                                   id="password"
                                   name="password"
                                   placeholder="${t('auth.password')}"
                                   required
                                   autocomplete="current-password">
                            <button type="button" class="input-group__suffix btn btn--icon" id="toggle-password">
                                <svg viewBox="0 0 20 20" fill="currentColor" class="icon-show">
                                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                                </svg>
                                <svg viewBox="0 0 20 20" fill="currentColor" class="icon-hide hidden">
                                    <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/>
                                    <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div class="form-group form-group--inline">
                        <label class="checkbox">
                            <input type="checkbox" name="remember" id="remember">
                            <span class="checkbox__mark"></span>
                            <span class="checkbox__label">${t('auth.rememberMe')}</span>
                        </label>
                    </div>

                    <div class="form-group">
                        <button type="submit" class="btn btn--primary btn--lg btn--block" id="login-btn">
                            <span class="btn__text">${t('auth.login')}</span>
                            <span class="btn__loading hidden">
                                <svg class="animate-spin" viewBox="0 0 24 24" fill="none">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </span>
                        </button>
                    </div>

                    <div class="form-error hidden" id="login-error"></div>
                </form>

                <div class="login-card__footer">
                    <p class="text-muted text-sm text-center">
                        Demo: admin / admin
                    </p>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindLoginEvents(container);
}

/**
 * 綁定登入頁面事件
 * @param {HTMLElement} container - 容器元素
 */
function bindLoginEvents(container) {
    const form = container.querySelector('#login-form');
    const loginBtn = container.querySelector('#login-btn');
    const errorDiv = container.querySelector('#login-error');
    const togglePasswordBtn = container.querySelector('#toggle-password');
    const passwordInput = container.querySelector('#password');

    // 密碼顯示切換
    togglePasswordBtn?.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        togglePasswordBtn.querySelector('.icon-show').classList.toggle('hidden');
        togglePasswordBtn.querySelector('.icon-hide').classList.toggle('hidden');
    });

    // 表單提交
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const username = formData.get('username');
        const password = formData.get('password');

        // 驗證
        if (!username || !password) {
            showError(errorDiv, t('errors.validationError'));
            return;
        }

        // 開始載入
        setLoading(loginBtn, true);
        hideError(errorDiv);

        try {
            await login(username, password);
            toast.success(t('auth.loginSuccess'));
            router.navigate('/', { replace: true });
        } catch (error) {
            console.error('Login failed:', error);
            showError(errorDiv, error.message || t('auth.invalidCredentials'));
        } finally {
            setLoading(loginBtn, false);
        }
    });
}

/**
 * 設定載入狀態
 * @param {HTMLElement} button - 按鈕元素
 * @param {boolean} loading - 是否載入中
 */
function setLoading(button, loading) {
    if (!button) return;

    button.disabled = loading;
    button.querySelector('.btn__text')?.classList.toggle('hidden', loading);
    button.querySelector('.btn__loading')?.classList.toggle('hidden', !loading);
}

/**
 * 顯示錯誤
 * @param {HTMLElement} element - 錯誤元素
 * @param {string} message - 錯誤訊息
 */
function showError(element, message) {
    if (!element) return;
    element.textContent = message;
    element.classList.remove('hidden');
}

/**
 * 隱藏錯誤
 * @param {HTMLElement} element - 錯誤元素
 */
function hideError(element) {
    if (!element) return;
    element.classList.add('hidden');
}

export default { render: renderLoginPage };
