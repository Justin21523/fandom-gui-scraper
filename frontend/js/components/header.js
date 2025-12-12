/**
 * Header - 頂部導航組件
 */

import { t } from '../i18n/i18n.js';
import { globalStore } from '../stores/store.js';
import { authStore, logout } from '../stores/authStore.js';
import router from '../router.js';
import { debounce } from '../utils/helpers.js';

/**
 * 渲染 Header
 * @param {HTMLElement} container - 容器元素
 */
export function renderHeader(container) {
    const { theme } = globalStore.getState();
    const { isAuthenticated, user } = authStore.getState();

    container.innerHTML = `
        <div class="header__logo">
            <svg class="header__logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
            <span>Fandom Scraper</span>
        </div>

        <div class="header__search">
            <svg class="header__search-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
            </svg>
            <input type="text"
                   class="header__search-input"
                   placeholder="${t('characters.search')}"
                   id="global-search">
        </div>

        <nav class="header__nav">
            <div class="header__actions">
                <!-- 主題切換 -->
                <button class="btn btn--icon" id="theme-toggle" title="${t('settings.general.theme')}">
                    ${theme === 'dark' ? `
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"/>
                        </svg>
                    ` : `
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
                        </svg>
                    `}
                </button>

                <!-- 語言切換 -->
                <div class="dropdown" id="locale-dropdown">
                    <button class="btn btn--icon dropdown__trigger" title="${t('settings.general.language')}">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                    <div class="dropdown__menu">
                        <button class="dropdown__item" data-locale="zh">繁體中文</button>
                        <button class="dropdown__item" data-locale="en">English</button>
                    </div>
                </div>

                <!-- 通知 -->
                <button class="btn btn--icon" id="notifications-btn" title="Notifications">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
                    </svg>
                </button>

                <!-- 使用者選單 -->
                ${isAuthenticated ? `
                    <div class="dropdown" id="user-dropdown">
                        <button class="btn btn--icon dropdown__trigger">
                            <div class="avatar avatar--sm">
                                ${user?.avatar
                                    ? `<img src="${user.avatar}" alt="${user.username}">`
                                    : `<span>${(user?.username || 'U').charAt(0).toUpperCase()}</span>`
                                }
                            </div>
                        </button>
                        <div class="dropdown__menu dropdown__menu--right">
                            <div class="dropdown__header">
                                <strong>${user?.username || 'User'}</strong>
                            </div>
                            <button class="dropdown__item" data-action="settings">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
                                </svg>
                                ${t('common.settings')}
                            </button>
                            <div class="dropdown__divider"></div>
                            <button class="dropdown__item dropdown__item--danger" data-action="logout">
                                <svg viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd"/>
                                </svg>
                                ${t('common.logout')}
                            </button>
                        </div>
                    </div>
                ` : `
                    <a href="#/login" class="btn btn--primary btn--sm">${t('common.login')}</a>
                `}
            </div>
        </nav>

        <!-- 移動端選單按鈕 -->
        <button class="btn btn--icon header__menu-toggle" id="menu-toggle">
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
            </svg>
        </button>
    `;

    // 綁定事件
    bindHeaderEvents(container);
}

/**
 * 綁定 Header 事件
 * @param {HTMLElement} container - 容器元素
 */
function bindHeaderEvents(container) {
    // 主題切換
    const themeToggle = container.querySelector('#theme-toggle');
    themeToggle?.addEventListener('click', () => {
        const { theme } = globalStore.getState();
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        globalStore.setState({ theme: newTheme });
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        renderHeader(container);
    });

    // 語言切換
    const localeDropdown = container.querySelector('#locale-dropdown');
    setupDropdown(localeDropdown);
    localeDropdown?.querySelectorAll('[data-locale]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const locale = btn.dataset.locale;
            const { setLocale } = await import('../i18n/i18n.js');
            await setLocale(locale);
            renderHeader(container);
        });
    });

    // 使用者選單
    const userDropdown = container.querySelector('#user-dropdown');
    setupDropdown(userDropdown);
    userDropdown?.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            if (action === 'logout') {
                logout();
                router.navigate('/login');
            } else if (action === 'settings') {
                router.navigate('/settings');
            }
        });
    });

    // 全域搜尋
    const searchInput = container.querySelector('#global-search');
    const handleSearch = debounce((value) => {
        if (value.trim()) {
            router.navigate('/characters', { query: { search: value } });
        }
    }, 500);

    searchInput?.addEventListener('input', (e) => handleSearch(e.target.value));
    searchInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.value.trim()) {
            router.navigate('/characters', { query: { search: e.target.value } });
        }
    });

    // 移動端選單
    const menuToggle = container.querySelector('#menu-toggle');
    menuToggle?.addEventListener('click', () => {
        const sidebar = document.querySelector('.sidebar');
        sidebar?.classList.toggle('sidebar--open');
    });
}

/**
 * 設定下拉選單
 * @param {HTMLElement} dropdown - 下拉選單元素
 */
function setupDropdown(dropdown) {
    if (!dropdown) return;

    const trigger = dropdown.querySelector('.dropdown__trigger');
    const menu = dropdown.querySelector('.dropdown__menu');

    trigger?.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.contains('dropdown--open');

        // 關閉其他下拉選單
        document.querySelectorAll('.dropdown--open').forEach(d => {
            d.classList.remove('dropdown--open');
        });

        if (!isOpen) {
            dropdown.classList.add('dropdown--open');
        }
    });

    // 點擊外部關閉
    document.addEventListener('click', () => {
        dropdown.classList.remove('dropdown--open');
    });

    menu?.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

export default { render: renderHeader };
