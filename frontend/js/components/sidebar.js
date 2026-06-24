/**
 * Sidebar - 側邊欄組件
 */

import { t } from '../i18n/i18n.js';
import { globalStore } from '../stores/store.js';
import router from '../router.js';

// 導航選單配置
const NAV_ITEMS = [
    {
        section: 'main',
        items: [
            {
                path: '/',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
                </svg>`,
                labelKey: 'nav.home'
            },
            {
                path: '/characters',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                </svg>`,
                labelKey: 'nav.characters'
            },
            {
                path: '/scraper',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 2V5h1v1H5zM3 13a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm2 2v-1h1v1H5zM13 3a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1V4a1 1 0 00-1-1h-3zm1 2v1h1V5h-1z" clip-rule="evenodd"/>
                    <path d="M11 4a1 1 0 10-2 0v1a1 1 0 002 0V4zM10 7a1 1 0 011 1v1h2a1 1 0 110 2h-3a1 1 0 01-1-1V8a1 1 0 011-1zM16 9a1 1 0 100 2 1 1 0 000-2zM9 13a1 1 0 011-1h1a1 1 0 110 2v2a1 1 0 11-2 0v-3zM7 11a1 1 0 100-2H4a1 1 0 100 2h3zM17 13a1 1 0 01-1 1h-2a1 1 0 110-2h2a1 1 0 011 1zM16 17a1 1 0 100-2h-3a1 1 0 100 2h3z"/>
                </svg>`,
                labelKey: 'nav.scraper'
            },
            {
                path: '/process',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 4a2 2 0 012-2h2.5a2 2 0 011.6.8L10 4h5a2 2 0 012 2v2H3V4zm0 6h14v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5zm3 2a1 1 0 100 2h2a1 1 0 100-2H6zm5 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.process'
            },
            {
                path: '/jobs',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 3a2 2 0 00-2 2v2a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4z"/>
                    <path fill-rule="evenodd" d="M18 11H2v4a2 2 0 002 2h12a2 2 0 002-2v-4z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.jobs'
            },
            {
                path: '/campaigns',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h3a2 2 0 012 2v1h5a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm2 0v10h10V8H8V5H5zm5 5a1 1 0 011-1h2a1 1 0 110 2h-2a1 1 0 01-1-1zm-4 3a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.campaigns'
            },
            {
                path: '/browse',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V7.414A2 2 0 0017.414 6L14 2.586A2 2 0 0012.586 2H4zm8 1.5V7a1 1 0 001 1h2.5L12 4.5z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.browse'
            },
            {
                path: '/export',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.export'
            }
        ]
    },
    {
        section: 'analytics',
        titleKey: 'nav.analytics',
        items: [
            {
                path: '/analysis',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 6a1 1 0 011-1h2a1 1 0 011 1v10a1 1 0 01-1 1H9a1 1 0 01-1-1V6zM14 3a1 1 0 011-1h2a1 1 0 011 1v13a1 1 0 01-1 1h-2a1 1 0 01-1-1V3z"/>
                </svg>`,
                labelKey: 'nav.analysis'
            },
            {
                path: '/charts',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
                </svg>`,
                labelKey: 'nav.charts'
            },
            {
                path: '/media',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.media'
            }
        ]
    },
    {
        section: 'system',
        titleKey: 'settings.title',
        items: [
            {
                path: '/compliance',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 1.944l6 2.25V8c0 3.72-2.288 7.05-6 8.056C6.288 15.05 4 11.72 4 8V4.194l6-2.25zM8.707 10.707l4-4a1 1 0 10-1.414-1.414L8 8.586 6.707 7.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.compliance'
            },
            {
                path: '/settings',
                icon: `<svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
                </svg>`,
                labelKey: 'nav.settings'
            }
        ]
    }
];

/**
 * 渲染 Sidebar
 * @param {HTMLElement} container - 容器元素
 */
export function renderSidebar(container) {
    const { sidebarCollapsed } = globalStore.getState();
    const currentPath = router.getCurrentPath();

    if (sidebarCollapsed) {
        container.classList.add('sidebar--collapsed');
    } else {
        container.classList.remove('sidebar--collapsed');
    }

    let html = `
        <nav class="sidebar__nav">
    `;

    NAV_ITEMS.forEach(section => {
        html += `<div class="sidebar__section">`;

        if (section.titleKey) {
            html += `<div class="sidebar__section-title">${t(section.titleKey)}</div>`;
        }

        html += `<div class="sidebar__menu">`;

        section.items.forEach(item => {
            const isActive = currentPath === item.path ||
                (item.path !== '/' && currentPath.startsWith(item.path));

            html += `
                <a href="#${item.path}"
                   class="sidebar__link ${isActive ? 'sidebar__link--active' : ''}"
                   data-tour="nav-${item.path === '/' ? 'home' : item.path.slice(1)}">
                    <span class="sidebar__icon">${item.icon}</span>
                    <span class="sidebar__label">${t(item.labelKey)}</span>
                </a>
            `;
        });

        html += `</div></div>`;
    });

    // 側邊欄摺疊按鈕
    html += `
        </nav>
        <div class="sidebar__footer">
            <button class="btn btn--icon sidebar__toggle" id="sidebar-toggle" title="${sidebarCollapsed ? 'Expand' : 'Collapse'}">
                <svg viewBox="0 0 20 20" fill="currentColor" class="${sidebarCollapsed ? 'rotate-180' : ''}">
                    <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    `;

    container.innerHTML = html;

    // 綁定事件
    bindSidebarEvents(container);
}

/**
 * 綁定 Sidebar 事件
 * @param {HTMLElement} container - 容器元素
 */
function bindSidebarEvents(container) {
    // 側邊欄摺疊
    const toggleBtn = container.querySelector('#sidebar-toggle');
    toggleBtn?.addEventListener('click', () => {
        const { sidebarCollapsed } = globalStore.getState();
        globalStore.setState({ sidebarCollapsed: !sidebarCollapsed });
        renderSidebar(container);
    });

    // 連結點擊（關閉移動端選單）
    container.querySelectorAll('.sidebar__link').forEach(link => {
        link.addEventListener('click', () => {
            // 在移動端關閉側邊欄
            if (window.innerWidth <= 1024) {
                container.classList.remove('sidebar--open');
            }
        });
    });
}

/**
 * 更新活動連結
 */
export function updateActiveLink() {
    const currentPath = router.getCurrentPath();

    document.querySelectorAll('.sidebar__link').forEach(link => {
        const href = link.getAttribute('href').replace('#', '');
        const isActive = currentPath === href ||
            (href !== '/' && currentPath.startsWith(href));

        link.classList.toggle('sidebar__link--active', isActive);
    });
}

export default { render: renderSidebar, updateActiveLink };
