/**
 * Settings Page - 設定頁面
 */

import { t, setLocale, getLocale, getAvailableLocales } from '../i18n/i18n.js';
import { globalStore } from '../stores/store.js';
import toast from '../components/toast.js';

/**
 * 渲染設定頁面
 * @param {HTMLElement} container - 容器元素
 */
export function renderSettingsPage(container) {
    const { theme } = globalStore.getState();
    const currentLocale = getLocale();
    const locales = getAvailableLocales();

    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <h1 class="page__title">${t('settings.title')}</h1>
            </div>

            <div class="settings-grid">
                <!-- 一般設定 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">${t('settings.general.title')}</h3>
                    </div>
                    <div class="card__body">
                        <!-- 語言 -->
                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.general.language')}</div>
                                <div class="settings-item__description">選擇界面顯示語言</div>
                            </div>
                            <div class="settings-item__control">
                                <select class="select" id="locale-select">
                                    ${locales.map(l => `
                                        <option value="${l.code}" ${l.code === currentLocale ? 'selected' : ''}>
                                            ${l.name}
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                        </div>

                        <!-- 主題 -->
                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.general.theme')}</div>
                                <div class="settings-item__description">選擇界面顏色主題</div>
                            </div>
                            <div class="settings-item__control">
                                <div class="theme-options">
                                    <button class="theme-option ${theme === 'light' ? 'theme-option--active' : ''}" data-theme="light">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"/>
                                        </svg>
                                        <span>${t('settings.general.lightTheme')}</span>
                                    </button>
                                    <button class="theme-option ${theme === 'dark' ? 'theme-option--active' : ''}" data-theme="dark">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
                                        </svg>
                                        <span>${t('settings.general.darkTheme')}</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- API 設定 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">${t('settings.api.title')}</h3>
                    </div>
                    <div class="card__body">
                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.api.baseUrl')}</div>
                                <div class="settings-item__description">API 伺服器地址</div>
                            </div>
                            <div class="settings-item__control">
                                <input type="text" class="input" id="api-base-url" value="/api/v1" disabled>
                            </div>
                        </div>

                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.api.timeout')}</div>
                                <div class="settings-item__description">請求超時時間</div>
                            </div>
                            <div class="settings-item__control">
                                <input type="number" class="input" id="api-timeout" value="30" min="5" max="120">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 通知設定 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">${t('settings.notifications.title')}</h3>
                    </div>
                    <div class="card__body">
                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.notifications.enableNotifications')}</div>
                                <div class="settings-item__description">啟用瀏覽器通知</div>
                            </div>
                            <div class="settings-item__control">
                                <label class="switch">
                                    <input type="checkbox" id="enable-notifications">
                                    <span class="switch__slider"></span>
                                </label>
                            </div>
                        </div>

                        <div class="settings-item">
                            <div class="settings-item__info">
                                <div class="settings-item__label">${t('settings.notifications.soundEnabled')}</div>
                                <div class="settings-item__description">啟用音效提示</div>
                            </div>
                            <div class="settings-item__control">
                                <label class="switch">
                                    <input type="checkbox" id="enable-sound">
                                    <span class="switch__slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 關於 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">關於</h3>
                    </div>
                    <div class="card__body">
                        <div class="about-info">
                            <div class="about-info__logo">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                                    <path d="M2 17l10 5 10-5"/>
                                    <path d="M2 12l10 5 10-5"/>
                                </svg>
                            </div>
                            <div class="about-info__content">
                                <h4>Fandom Scraper</h4>
                                <p class="text-muted">Version 1.0.0</p>
                                <p class="text-muted mt-sm">動畫角色資料爬蟲與管理系統</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindSettingsEvents(container);
}

/**
 * 綁定設定頁面事件
 * @param {HTMLElement} container - 容器元素
 */
function bindSettingsEvents(container) {
    // 語言切換
    const localeSelect = container.querySelector('#locale-select');
    localeSelect?.addEventListener('change', async (e) => {
        await setLocale(e.target.value);
        toast.success(t('common.success'));
        // 重新渲染頁面
        renderSettingsPage(container);
    });

    // 主題切換
    container.querySelectorAll('[data-theme]').forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            globalStore.setState({ theme });
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);

            // 更新 UI
            container.querySelectorAll('[data-theme]').forEach(b => {
                b.classList.toggle('theme-option--active', b.dataset.theme === theme);
            });

            toast.success(t('common.success'));
        });
    });

    // 通知設定
    const notificationsToggle = container.querySelector('#enable-notifications');
    notificationsToggle?.addEventListener('change', async (e) => {
        if (e.target.checked) {
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                e.target.checked = false;
                toast.warning('Notification permission denied');
            }
        }
    });
}

export default { render: renderSettingsPage };
