/**
 * App - 主應用程式入口
 * Fandom Scraper Web Frontend
 */

import { router } from './router.js';
import { initI18n, updatePageTranslations, t } from './i18n/i18n.js';
import { globalStore } from './stores/store.js';
import { authStore, isTokenExpired } from './stores/authStore.js';
import { renderHeader } from './components/header.js';
import { renderSidebar, updateActiveLink } from './components/sidebar.js';
import { initDemoGuide } from './components/demoGuide.js';

// 頁面模組
import { renderHomePage } from './pages/home.js';
import { renderLoginPage } from './pages/login.js';
import { renderCharactersPage } from './pages/characters.js';
import { renderScraperPage } from './pages/scraper.js';
import { renderSettingsPage } from './pages/settings.js';
import { renderChartsPage } from './pages/charts.js';
import { renderMediaPage } from './pages/media.js';
import { renderCharacterDetailPage } from './pages/characterDetail.js';
import { renderJobsPage } from './pages/jobs.js';
import { renderCampaignsPage } from './pages/campaigns.js';
import { renderBrowsePage } from './pages/browse.js';
import { renderProcessPage } from './pages/process.js';
import { renderAnalysisPage } from './pages/analysis.js';
import { renderExportPage } from './pages/export.js';
import { renderCompliancePage } from './pages/compliance.js';

// 容器元素
let headerEl, sidebarEl, mainContentEl;

/**
 * 初始化應用程式
 */
async function initApp() {
    console.log('Initializing Fandom Scraper...');

    // 取得容器元素
    headerEl = document.getElementById('header');
    sidebarEl = document.getElementById('sidebar');
    mainContentEl = document.getElementById('main-content');

    // 初始化主題
    initTheme();

    // 初始化多語言
    await initI18n();

    // 渲染佈局
    renderLayout();

    // 設定路由
    setupRouter();

    // 啟動路由
    router.start();

    // 啟動作品集導覽小幫手
    initDemoGuide({ router });

    // 隱藏載入畫面
    hideLoading();

    console.log('Fandom Scraper initialized!');
}

/**
 * 初始化主題
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const normalizedTheme = savedTheme === 'dark' ? 'indigo' : savedTheme;
    document.documentElement.setAttribute('data-theme', normalizedTheme);
    localStorage.setItem('theme', normalizedTheme);
    globalStore.setState({ theme: normalizedTheme });
}

/**
 * 渲染佈局
 */
function renderLayout() {
    renderHeader(headerEl);
    renderSidebar(sidebarEl);

    // 訂閱狀態變化
    globalStore.subscribe(() => {
        renderHeader(headerEl);
    }, ['theme', 'locale']);

    authStore.subscribe(() => {
        renderHeader(headerEl);
    }, ['isAuthenticated', 'user']);
}

/**
 * 設定路由
 */
function setupRouter() {
    // 路由前鉤子 - 認證檢查
    router.beforeEach((to, from, next) => {
        // 登入頁面不需要認證
        if (to.path === '/login') {
            next();
            return;
        }

        // 檢查認證狀態
        const { isAuthenticated } = authStore.getState();

        // 如果未認證或 Token 過期，重導向到登入頁面
        // 注意：在開發模式下可以跳過認證
        const requireAuth = false; // 設定為 true 以啟用認證

        if (requireAuth && (!isAuthenticated || isTokenExpired())) {
            next('/login');
            return;
        }

        next();
    });

    // 路由後鉤子 - 更新 UI
    router.afterEach((to) => {
        updateActiveLink();
        updatePageTranslations();

        // 更新頁面標題
        const titles = {
            '/': 'home.title',
            '/characters': 'characters.title',
            '/scraper': 'scraper.title',
            '/jobs': 'nav.jobs',
            '/campaigns': 'portfolio.campaigns.title',
            '/browse': 'portfolio.browse.title',
            '/process': 'portfolio.process.title',
            '/analysis': 'portfolio.analysis.title',
            '/export': 'portfolio.export.title',
            '/compliance': 'portfolio.compliance.title',
            '/charts': 'charts.title',
            '/media': 'media.title',
            '/settings': 'settings.title',
            '/login': 'auth.login'
        };
        document.title = `${titles[to.path] ? t(titles[to.path]) : 'Page'} - Fandom Scraper`;
    });

    // 註冊路由
    router.registerAll({
        '/': {
            handler: (route) => renderHomePage(mainContentEl, route),
            meta: { title: 'Dashboard' }
        },
        '/login': {
            handler: (route) => renderLoginPage(mainContentEl, route),
            meta: { title: 'Login', layout: 'blank' }
        },
        '/characters': {
            handler: (route) => renderCharactersPage(mainContentEl, route),
            meta: { title: 'Characters' }
        },
        '/characters/:id': {
            handler: (route) => renderCharacterDetailPage(mainContentEl, route),
            meta: { title: 'Character Detail' }
        },
        '/scraper': {
            handler: (route) => renderScraperPage(mainContentEl, route),
            meta: { title: 'Scraper' }
        },
        '/jobs': {
            handler: (route) => renderJobsPage(mainContentEl, route),
            meta: { title: 'Jobs' }
        },
        '/campaigns': {
            handler: (route) => renderCampaignsPage(mainContentEl, route),
            meta: { title: 'Campaigns' }
        },
        '/browse': {
            handler: (route) => renderBrowsePage(mainContentEl, route),
            meta: { title: 'Browse' }
        },
        '/process': {
            handler: (route) => renderProcessPage(mainContentEl, route),
            meta: { title: 'Crawler Process' }
        },
        '/analysis': {
            handler: (route) => renderAnalysisPage(mainContentEl, route),
            meta: { title: 'Analysis' }
        },
        '/export': {
            handler: (route) => renderExportPage(mainContentEl, route),
            meta: { title: 'Export' }
        },
        '/compliance': {
            handler: (route) => renderCompliancePage(mainContentEl, route),
            meta: { title: 'Compliance' }
        },
        '/charts': {
            handler: (route) => renderChartsPage(mainContentEl, route),
            meta: { title: 'Charts' }
        },
        '/media': {
            handler: (route) => renderMediaPage(mainContentEl, route),
            meta: { title: 'Media' }
        },
        '/settings': {
            handler: (route) => renderSettingsPage(mainContentEl, route),
            meta: { title: 'Settings' }
        }
    });

    // 404 處理
    router.notFoundHandler = (path) => {
        mainContentEl.innerHTML = `
            <div class="page">
                <div class="empty-state" style="padding: 100px 0;">
                    <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                    <h2 class="empty-state__title">404 - Page Not Found</h2>
                    <p class="empty-state__description">The page "${path}" does not exist.</p>
                    <a href="#/" class="btn btn--primary mt-lg">Go to Home</a>
                </div>
            </div>
        `;
    };
}

/**
 * 隱藏載入畫面
 */
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// 當 DOM 載入完成時初始化應用程式
document.addEventListener('DOMContentLoaded', initApp);

// 匯出供除錯使用
window.__app = {
    router,
    globalStore,
    authStore
};
