/**
 * Home Page - 首頁/儀表板
 */

import { t } from '../i18n/i18n.js';
import { getCharacterStats, getCharacters } from '../api/characters.js';
import { getScraperStatus } from '../api/scraper.js';
import { formatNumber, formatRelativeTime } from '../utils/formatters.js';
import router from '../router.js';
import toast from '../components/toast.js';

/**
 * 渲染首頁
 * @param {HTMLElement} container - 容器元素
 */
export async function renderHomePage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('home.title')}</h1>
                    <p class="page__subtitle">${t('home.welcome')}</p>
                </div>
                <div class="page__actions">
                    <button class="btn btn--primary" id="start-scraper-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                        </svg>
                        ${t('home.startScraper')}
                    </button>
                </div>
            </div>

            <!-- 統計卡片 -->
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card skeleton-loading">
                    <div class="stat-card__icon stat-card__icon--primary">
                        <div class="skeleton skeleton--icon"></div>
                    </div>
                    <div class="stat-card__content">
                        <div class="skeleton skeleton--text" style="width: 80px;"></div>
                        <div class="skeleton skeleton--text" style="width: 60px; height: 32px;"></div>
                    </div>
                </div>
                <div class="stat-card skeleton-loading">
                    <div class="stat-card__icon stat-card__icon--success">
                        <div class="skeleton skeleton--icon"></div>
                    </div>
                    <div class="stat-card__content">
                        <div class="skeleton skeleton--text" style="width: 80px;"></div>
                        <div class="skeleton skeleton--text" style="width: 60px; height: 32px;"></div>
                    </div>
                </div>
                <div class="stat-card skeleton-loading">
                    <div class="stat-card__icon stat-card__icon--warning">
                        <div class="skeleton skeleton--icon"></div>
                    </div>
                    <div class="stat-card__content">
                        <div class="skeleton skeleton--text" style="width: 80px;"></div>
                        <div class="skeleton skeleton--text" style="width: 60px; height: 32px;"></div>
                    </div>
                </div>
                <div class="stat-card skeleton-loading">
                    <div class="stat-card__icon stat-card__icon--error">
                        <div class="skeleton skeleton--icon"></div>
                    </div>
                    <div class="stat-card__content">
                        <div class="skeleton skeleton--text" style="width: 80px;"></div>
                        <div class="skeleton skeleton--text" style="width: 60px; height: 32px;"></div>
                    </div>
                </div>
            </div>

            <!-- 主要內容區域 -->
            <div class="grid grid-cols-2 gap-lg">
                <!-- 最近爬取的角色 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">${t('home.recentCharacters')}</h3>
                        <a href="#/characters" class="btn btn--sm btn--outline">${t('home.viewCharacters')}</a>
                    </div>
                    <div class="card__body" id="recent-characters">
                        <div class="loading-container">
                            <div class="loading-spinner"></div>
                        </div>
                    </div>
                </div>

                <!-- 快速操作 -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">${t('home.quickActions')}</h3>
                    </div>
                    <div class="card__body">
                        <div class="quick-actions">
                            <button class="quick-action-btn" data-action="scraper">
                                <div class="quick-action-btn__icon">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 2V5h1v1H5zM3 13a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm2 2v-1h1v1H5zM13 3a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1V4a1 1 0 00-1-1h-3zm1 2v1h1V5h-1z" clip-rule="evenodd"/>
                                        <path d="M11 4a1 1 0 10-2 0v1a1 1 0 002 0V4zM10 7a1 1 0 011 1v1h2a1 1 0 110 2h-3a1 1 0 01-1-1V8a1 1 0 011-1zM16 9a1 1 0 100 2 1 1 0 000-2zM9 13a1 1 0 011-1h1a1 1 0 110 2v2a1 1 0 11-2 0v-3zM7 11a1 1 0 100-2H4a1 1 0 100 2h3zM17 13a1 1 0 01-1 1h-2a1 1 0 110-2h2a1 1 0 011 1zM16 17a1 1 0 100-2h-3a1 1 0 100 2h3z"/>
                                    </svg>
                                </div>
                                <span>${t('nav.scraper')}</span>
                            </button>
                            <button class="quick-action-btn" data-action="characters">
                                <div class="quick-action-btn__icon">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                                    </svg>
                                </div>
                                <span>${t('nav.characters')}</span>
                            </button>
                            <button class="quick-action-btn" data-action="charts">
                                <div class="quick-action-btn__icon">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
                                    </svg>
                                </div>
                                <span>${t('nav.charts')}</span>
                            </button>
                            <button class="quick-action-btn" data-action="media">
                                <div class="quick-action-btn__icon">
                                    <svg viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                                    </svg>
                                </div>
                                <span>${t('nav.media')}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindHomeEvents(container);

    // 載入資料
    loadHomeData(container);
}

/**
 * 綁定首頁事件
 * @param {HTMLElement} container - 容器元素
 */
function bindHomeEvents(container) {
    // 啟動爬蟲按鈕
    container.querySelector('#start-scraper-btn')?.addEventListener('click', () => {
        router.navigate('/scraper');
    });

    // 快速操作按鈕
    container.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            router.navigate(`/${action}`);
        });
    });
}

/**
 * 載入首頁資料
 * @param {HTMLElement} container - 容器元素
 */
async function loadHomeData(container) {
    try {
        // 並行載入資料
        const [stats, recentChars, scraperStatus] = await Promise.all([
            getCharacterStats().catch(() => null),
            getCharacters({ pageSize: 5, sortBy: 'updated_at', sortOrder: 'desc' }).catch(() => null),
            getScraperStatus().catch(() => null)
        ]);

        // 更新統計卡片
        renderStatsGrid(container.querySelector('#stats-grid'), stats, scraperStatus);

        // 更新最近角色列表
        renderRecentCharacters(container.querySelector('#recent-characters'), recentChars);

    } catch (error) {
        console.error('Failed to load home data:', error);
        toast.error(t('errors.serverError'));
    }
}

/**
 * 渲染統計網格
 * @param {HTMLElement} container - 容器元素
 * @param {Object} stats - 統計資料
 * @param {Object} scraperStatus - 爬蟲狀態
 */
function renderStatsGrid(container, stats, scraperStatus) {
    if (!container) return;

    const statusText = {
        idle: t('scraper.idle'),
        running: t('scraper.running'),
        paused: t('scraper.paused'),
        stopped: t('scraper.stopped')
    };

    const statusClass = {
        idle: 'text-muted',
        running: 'text-success',
        paused: 'text-warning',
        stopped: 'text-error'
    };

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--primary">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                </svg>
            </div>
            <div class="stat-card__content">
                <div class="stat-card__label">${t('home.totalCharacters')}</div>
                <div class="stat-card__value">${formatNumber(stats?.total_characters || 0, { compact: true })}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--success">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                </svg>
            </div>
            <div class="stat-card__content">
                <div class="stat-card__label">${t('home.totalAnime')}</div>
                <div class="stat-card__value">${formatNumber(stats?.total_anime || 0)}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--warning">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                </svg>
            </div>
            <div class="stat-card__content">
                <div class="stat-card__label">${t('home.recentUpdates')}</div>
                <div class="stat-card__value">${formatNumber(stats?.recent_updates || 0)}</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-card__icon stat-card__icon--error">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/>
                </svg>
            </div>
            <div class="stat-card__content">
                <div class="stat-card__label">${t('home.systemStatus')}</div>
                <div class="stat-card__value ${statusClass[scraperStatus?.status] || 'text-muted'}">
                    ${statusText[scraperStatus?.status] || statusText.idle}
                </div>
            </div>
        </div>
    `;
}

/**
 * 渲染最近角色列表
 * @param {HTMLElement} container - 容器元素
 * @param {Object} data - 角色資料
 */
function renderRecentCharacters(container, data) {
    if (!container) return;

    if (!data || !data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                </svg>
                <p class="empty-state__title">${t('characters.noCharacters')}</p>
                <p class="empty-state__description">${t('home.startScraper')}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="recent-list">
            ${data.items.map(char => `
                <a href="#/characters/${char.id || char._id}" class="recent-list__item">
                    <div class="recent-list__avatar">
                        ${char.image
                            ? `<img src="${char.image}" alt="${char.name}">`
                            : `<span>${char.name.charAt(0)}</span>`
                        }
                    </div>
                    <div class="recent-list__info">
                        <div class="recent-list__name">${char.name}</div>
                        <div class="recent-list__meta">${char.anime || '-'}</div>
                    </div>
                    <div class="recent-list__time">
                        ${formatRelativeTime(char.updated_at || char.created_at)}
                    </div>
                </a>
            `).join('')}
        </div>
    `;
}

export default { render: renderHomePage };
