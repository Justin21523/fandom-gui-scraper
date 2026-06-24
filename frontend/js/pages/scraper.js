/**
 * Scraper Page - Universal Fandom Scraper 控制頁面
 *
 * 支援功能:
 * - 動畫名稱搜尋 (Brave Search API)
 * - 直接 URL 輸入
 * - 多類別爬取 (characters, episodes, galleries, chapters)
 * - 分類別進度追蹤
 * - 即時日誌顯示
 */

import { t } from '../i18n/i18n.js';
import {
    searchAnime,
    startUniversalScraper,
    getUniversalStatus,
    stopUniversalScraper,
    pauseUniversalScraper,
    resumeUniversalScraper,
    getUniversalLogs,
    listUniversalJobs,
    selectUniversalJob,
    // Legacy API (保留用於歷史記錄)
    getScraperHistory
} from '../api/scraper.js';
import { showModal, closeModal } from '../components/modal.js';
import { wsManager } from '../utils/websocket.js';
import { formatDuration, formatNumber } from '../utils/formatters.js';
import toast from '../components/toast.js';

// 爬蟲狀態
let scraperState = {
    status: 'idle',
    inputType: 'name',  // 'name' or 'url'
    animeSearchResults: [],
    selectedWiki: null,
    progress: null,
    logs: []
};

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * 渲染爬蟲控制頁面
 */
export async function renderScraperPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('scraper.universal.title')}</h1>
                    <p class="page__subtitle">${t('scraper.universal.subtitle')}</p>
                </div>
            </div>

            <div class="scraper-layout">
                <!-- 左側：設定面板 -->
                <div class="scraper-config">
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.universal.newJob')}</h3>
                        </div>
                        <div class="card__body">
                            <form id="universal-scraper-form">
                                <!-- 輸入類型選擇 -->
                                <div class="form-group" data-tour="scraper-source">
                                    <label class="form-label">${t('scraper.universal.inputSource')}</label>
                                    <div class="btn-group btn--block">
                                        <button type="button" class="btn flex-1 input-type-btn active" data-type="name">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"/>
                                            </svg>
                                            ${t('scraper.universal.wikiNameSearch')}
                                        </button>
                                        <button type="button" class="btn flex-1 input-type-btn" data-type="url">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd"/>
                                            </svg>
                                            ${t('scraper.universal.urlEndpoint')}
                                        </button>
                                    </div>
                                </div>

                                <!-- 動畫名稱搜尋 (預設顯示) -->
                                <div id="input-mode-name">
                                    <div class="form-group">
                                        <label class="form-label">${t('scraper.universal.wikiTopicName')}</label>
                                        <div class="input-group--horizontal">
                                            <input type="text" class="input" id="anime-name-input"
                                                placeholder="${escapeHtml(t('scraper.universal.topicPlaceholder'))}" autocomplete="off">
                                            <button type="button" class="btn btn--primary" id="search-anime-btn">
                                                <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                    <path d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"/>
                                                </svg>
                                                ${t('common.search')}
                                            </button>
                                        </div>
                                    </div>

                                    <!-- 搜尋結果 -->
                                    <div id="search-results-container" class="hidden">
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.searchResults')}</label>
                                            <div id="search-results-list" class="search-results-list">
                                                <!-- 動態填充 -->
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- URL 輸入 (隱藏) -->
                                <div id="input-mode-url" class="hidden">
                                    <div class="form-group">
                                        <label class="form-label">${t('scraper.universal.urlLabel')}</label>
                                        <input type="url" class="input" id="wiki-url-input"
                                            placeholder="https://onepiece.fandom.com or https://onepiece.fandom.com/api.php">
                                        <p class="form-help">${t('scraper.universal.urlHelp')}</p>
                                    </div>
                                </div>

                                <!-- 爬取範圍 -->
                                <div class="form-group" data-tour="scraper-scope">
                                    <label class="form-label">${t('scraper.universal.contentScope')}</label>
                                    <div class="checkbox-group--vertical">
                                        <label class="checkbox-wrapper">
                                            <input type="checkbox" class="checkbox" id="crawl-characters" checked>
                                            <span class="checkbox__label">${t('scraper.universal.pagesCharacters')}</span>
                                        </label>
                                        <label class="checkbox-wrapper">
                                            <input type="checkbox" class="checkbox" id="crawl-episodes" checked>
                                            <span class="checkbox__label">${t('scraper.universal.categoriesEpisodes')}</span>
                                        </label>
                                        <label class="checkbox-wrapper">
                                            <input type="checkbox" class="checkbox" id="crawl-galleries" checked>
                                            <span class="checkbox__label">${t('scraper.universal.imagesGalleries')}</span>
                                        </label>
                                        <label class="checkbox-wrapper">
                                            <input type="checkbox" class="checkbox" id="crawl-chapters">
                                            <span class="checkbox__label">${t('scraper.universal.linksChapters')}</span>
                                        </label>
                                    </div>
                                </div>

                                <!-- 分類別限制 -->
                                <details class="form-details" data-tour="scraper-compliance">
                                    <summary class="form-details__summary">${t('scraper.universal.limits')}</summary>
                                    <div class="form-details__content">
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.maxPages')}</label>
                                            <input type="number" class="input" id="max-chars"
                                                value="100" min="0" step="10">
                                            <p class="form-help">${t('scraper.universal.noLimitHelp')}</p>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.maxCategories')}</label>
                                            <input type="number" class="input" id="max-episodes"
                                                value="50" min="0" step="10">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.maxImages')}</label>
                                            <input type="number" class="input" id="max-gallery"
                                                value="200" min="0" step="50">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.maxLinks')}</label>
                                            <input type="number" class="input" id="max-chapters"
                                                value="50" min="0" step="10">
                                        </div>
                                    </div>
                                </details>

                                <!-- 進階設定 -->
                                <details class="form-details">
                                    <summary class="form-details__summary">${t('scraper.universal.complianceExport')}</summary>
                                    <div class="form-details__content">
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.requestDelay')}</label>
                                            <input type="number" class="input" id="delay"
                                                value="1" min="0" max="10" step="0.5">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.retries')}</label>
                                            <input type="number" class="input" id="retries"
                                                value="3" min="0" max="10">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.runtimeControls')}</label>
                                            <div class="checkbox-group--vertical">
                                                <label class="checkbox-label">
                                                    <input type="checkbox" id="use-playwright">
                                                    <span>${t('scraper.universal.usePlaywright')}</span>
                                                </label>
                                                <label class="checkbox-label">
                                                    <input type="checkbox" id="use-playwright-detail">
                                                    <span>${t('scraper.universal.usePlaywrightDetail')}</span>
                                                </label>
                                                <label class="checkbox-label">
                                                    <input type="checkbox" id="download-images">
                                                    <span>${t('scraper.universal.downloadImages')}</span>
                                                </label>
                                                <label class="checkbox-label">
                                                    <input type="checkbox" id="export-gzip" checked>
                                                    <span>${t('scraper.universal.compressJson')}</span>
                                                </label>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.universal.jsonExportMode')}</label>
                                            <select class="input" id="export-mode">
                                                <option value="jsonl" selected>${t('scraper.universal.exportJsonl')}</option>
                                                <option value="per_item">${t('scraper.universal.exportPerItem')}</option>
                                            </select>
                                            <p class="form-help">${t('scraper.universal.exportModeHelp')}</p>
                                        </div>
                                    </div>
                                </details>

                                <!-- 控制按鈕 -->
                                <div class="form-actions mt-lg">
                                    <button type="submit" class="btn btn--primary btn--lg btn--block" id="start-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                                        </svg>
                                        ${t('scraper.universal.startCrawl')}
                                    </button>
                                    <div class="btn-group btn--block mt-sm hidden" id="control-buttons">
                                        <button type="button" class="btn btn--warning flex-1" id="pause-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                            </svg>
                                            ${t('scraper.universal.pause')}
                                        </button>
                                        <button type="button" class="btn btn--danger flex-1" id="stop-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
                                            </svg>
                                            ${t('scraper.universal.stop')}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- 歷史記錄 -->
                    <div class="card mt-lg">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.universal.recentRuns')}</h3>
                            <button class="btn btn--sm btn--ghost" id="refresh-history-btn">
                                <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                                </svg>
                            </button>
                        </div>
                        <div class="card__body p-0">
                            <div class="history-list" id="history-list">
                                <div class="empty-state p-lg">
                                    <p class="text-muted">${t('common.loading')}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 最近任務 -->
                    <div class="card mt-lg">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.universal.recentJobs')}</h3>
                            <button class="btn btn--sm btn--ghost" id="refresh-jobs-btn">
                                <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                                </svg>
                            </button>
                        </div>
                        <div class="card__body">
                            <div id="jobs-list" class="text-sm text-muted">${t('common.loading')}</div>
                        </div>
                    </div>
                </div>

                <!-- 右側：狀態和日誌 -->
                <div class="scraper-status">
                    <!-- 狀態卡片 -->
                    <div class="card mb-lg" data-tour="scraper-progress">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.universal.crawlProgress')}</h3>
                            <span class="badge" id="status-badge">${t('status.idle')}</span>
                        </div>
                        <div class="card__body">
                            <!-- 整體進度 -->
                            <div class="progress-stats mb-lg">
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.universal.topic')}</span>
                                    <span class="progress-stat__value" id="stat-anime">-</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.completed')}</span>
                                    <span class="progress-stat__value text-success" id="stat-overall">0</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.speed')}</span>
                                    <span class="progress-stat__value" id="stat-speed">-</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.eta')}</span>
                                    <span class="progress-stat__value" id="stat-eta">-</span>
                                </div>
                            </div>

                            <!-- 分類別進度 -->
                            <div class="category-progress">
                                <!-- Characters -->
                                <div class="category-progress-item" data-category="characters">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">${t('scraper.universal.pagesCharacters')}</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Episodes -->
                                <div class="category-progress-item" data-category="episodes">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">${t('scraper.universal.categoriesEpisodes')}</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Galleries -->
                                <div class="category-progress-item" data-category="galleries">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">${t('scraper.universal.imagesGalleries')}</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Chapters -->
                                <div class="category-progress-item" data-category="chapters">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">${t('scraper.universal.linksChapters')}</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 日誌面板 -->
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.universal.liveLogs')}</h3>
                            <div class="flex gap-sm">
                                <label class="checkbox checkbox--sm">
                                    <input type="checkbox" id="auto-scroll" checked>
                                    <span class="checkbox__mark"></span>
                                    <span class="checkbox__label">${t('scraper.logs.autoScroll')}</span>
                                </label>
                                <button class="btn btn--sm btn--ghost" id="clear-logs">
                                    ${t('common.clear')}
                                </button>
                            </div>
                        </div>
                        <div class="card__body p-0">
                            <div class="log-viewer" id="log-viewer">
                                <div class="log-empty">${t('scraper.universal.waiting')}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindScraperEvents(container);

    // 載入當前狀態
    loadCurrentStatus(container);

    // 載入歷史記錄
    loadHistory(container);

    // 載入最近任務
    loadJobs(container);

    // 連接 WebSocket
    connectWebSocket(container);
}

/**
 * 綁定事件
 */
function bindScraperEvents(container) {
    // 輸入類型切換
    const inputTypeBtns = container.querySelectorAll('.input-type-btn');
    inputTypeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            inputTypeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const type = btn.dataset.type;
            scraperState.inputType = type;

            container.querySelector('#input-mode-name').classList.toggle('hidden', type !== 'name');
            container.querySelector('#input-mode-url').classList.toggle('hidden', type !== 'url');
        });
    });

    // 動畫搜尋
    const searchBtn = container.querySelector('#search-anime-btn');
    const animeInput = container.querySelector('#anime-name-input');

    searchBtn?.addEventListener('click', () => performAnimeSearch(container));
    animeInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performAnimeSearch(container);
        }
    });

    // 最近任務
    container.querySelector('#refresh-jobs-btn')?.addEventListener('click', () => loadJobs(container));

    // 表單提交
    const form = container.querySelector('#universal-scraper-form');
    form?.addEventListener('submit', (e) => {
        e.preventDefault();
        startUniversalScraping(container);
    });

    // 控制按鈕
    container.querySelector('#pause-btn')?.addEventListener('click', () => togglePause(container));
    container.querySelector('#stop-btn')?.addEventListener('click', () => stopScraping(container));
    container.querySelector('#clear-logs')?.addEventListener('click', () => clearLogs(container));
    container.querySelector('#refresh-history-btn')?.addEventListener('click', () => loadHistory(container));
}

/**
 * 執行動畫搜尋
 */
async function performAnimeSearch(container) {
    const input = container.querySelector('#anime-name-input');
    const animeName = input.value.trim();

    if (!animeName) {
        toast.warning(t('scraper.universal.enterTopic'));
        return;
    }

    const searchBtn = container.querySelector('#search-anime-btn');
    const originalText = searchBtn.innerHTML;
    searchBtn.disabled = true;
    searchBtn.innerHTML = `<span class="loading-spinner loading-spinner--sm"></span> ${t('scraper.universal.searching')}`;

    try {
        const results = await searchAnime(animeName, 5);
        scraperState.animeSearchResults = results;
        renderSearchResults(container, results);
        toast.success(t('scraper.universal.resultsFound', { count: results.length }));
    } catch (error) {
        toast.error(t('scraper.universal.searchFailed', { message: error.message }));
        console.error('Search error:', error);
    } finally {
        searchBtn.disabled = false;
        searchBtn.innerHTML = originalText;
    }
}

/**
 * 渲染搜尋結果
 */
function renderSearchResults(container, results) {
    const resultsContainer = container.querySelector('#search-results-container');
    const resultsList = container.querySelector('#search-results-list');

    if (!results || results.length === 0) {
        resultsContainer.classList.add('hidden');
        return;
    }

    resultsContainer.classList.remove('hidden');

    resultsList.innerHTML = results.map((result, index) => `
        <div class="search-result-item ${index === 0 ? 'active' : ''}" data-index="${index}">
            <div class="search-result-info">
                <div class="search-result-title">${escapeHtml(result.title)}</div>
                <div class="search-result-url text-muted">${escapeHtml(result.url)}</div>
                ${result.description ? `<div class="search-result-desc text-sm">${escapeHtml(result.description)}</div>` : ''}
            </div>
            <div class="search-result-score">
                <span class="badge badge--${result.relevance_score >= 80 ? 'success' : 'default'}">
                    ${Math.round(result.relevance_score)}%
                </span>
            </div>
        </div>
    `).join('');

    // 預設選擇第一個結果
    scraperState.selectedWiki = results[0];

    // 綁定選擇事件
    resultsList.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
            resultsList.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            const index = parseInt(item.dataset.index);
            scraperState.selectedWiki = results[index];
        });
    });
}

/**
 * 開始 Universal Scraping
 */
async function startUniversalScraping(container) {
    // 獲取輸入源
    let inputSource;
    if (scraperState.inputType === 'name') {
        if (!scraperState.selectedWiki) {
            toast.warning(t('scraper.universal.selectWikiFirst'));
            return;
        }
        inputSource = scraperState.selectedWiki.url;
    } else {
        inputSource = container.querySelector('#wiki-url-input').value.trim();
        if (!inputSource) {
            toast.warning(t('scraper.universal.enterWikiUrl'));
            return;
        }
    }

    // 構建配置
    const config = {
        input_source: inputSource,
        input_type: 'url',  // 轉換為 URL 模式
        crawl_characters: container.querySelector('#crawl-characters').checked,
        crawl_episodes: container.querySelector('#crawl-episodes').checked,
        crawl_galleries: container.querySelector('#crawl-galleries').checked,
        crawl_chapters: container.querySelector('#crawl-chapters').checked,
        max_chars: parseInt(container.querySelector('#max-chars').value) || 0,
        max_episodes: parseInt(container.querySelector('#max-episodes').value) || 0,
        max_gallery_images: parseInt(container.querySelector('#max-gallery').value) || 0,
        max_chapters: parseInt(container.querySelector('#max-chapters').value) || 0,
        delay: parseFloat(container.querySelector('#delay').value) || 1.0,
        retries: parseInt(container.querySelector('#retries').value) || 3,
        use_playwright: container.querySelector('#use-playwright')?.checked || false,
        use_playwright_detail_pages: container.querySelector('#use-playwright-detail')?.checked || false,
        download_images: container.querySelector('#download-images')?.checked || false,
        export_mode: container.querySelector('#export-mode')?.value || 'jsonl',
        export_json_gzip: container.querySelector('#export-gzip')?.checked ?? true
    };

    // 驗證至少選擇一個類別
    if (!config.crawl_characters && !config.crawl_episodes &&
        !config.crawl_galleries && !config.crawl_chapters) {
        toast.warning(t('scraper.universal.selectScope'));
        return;
    }

    try {
        const result = await startUniversalScraper(config);
        updateStatus(container, 'running');
        scraperState.logs = [];
        await loadJobs(container);
        toast.success(t('scraper.universal.started'));
        addLog(container, { level: 'info', message: t('scraper.universal.startedJob', { id: result.job_id || '-' }), timestamp: new Date() });
    } catch (error) {
        toast.error(t('scraper.universal.startFailed', { message: error.message }));
        console.error('Start error:', error);
    }
}

async function loadJobs(container) {
    const listEl = container.querySelector('#jobs-list');
    if (!listEl) return;

    try {
        const jobs = await listUniversalJobs(10);
        if (!jobs || jobs.length === 0) {
            listEl.innerHTML = `<div class="empty-state">${t('scraper.universal.noJobs')}</div>`;
            return;
        }

        listEl.innerHTML = jobs.map(j => {
            const created = new Date(j.created_at).toLocaleString('zh-TW');
            const source = j.config?.input_source || '';
            return `
                <div class="flex items-center justify-between gap-sm mb-sm">
                    <div class="flex-1">
                        <div class="text-sm"><strong>${escapeHtml(j.job_id)}</strong> <span class="text-muted">(${escapeHtml(j.status)})</span></div>
                        <div class="text-xs text-muted">${escapeHtml(created)} • ${escapeHtml(source)}</div>
                    </div>
                    <button class="btn btn--sm btn--ghost" data-job-select="${escapeHtml(j.job_id)}">${t('scraper.universal.switchJob')}</button>
                </div>
            `;
        }).join('');

        listEl.querySelectorAll('[data-job-select]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const jobId = btn.getAttribute('data-job-select');
                try {
                    await selectUniversalJob(jobId);
                    await loadCurrentStatus(container);
                    toast.info(t('scraper.universal.jobSelected', { id: jobId }));
                } catch (e) {
                    toast.error(e.message);
                }
            });
        });

    } catch (e) {
        listEl.innerHTML = `<div class="text-muted">${t('scraper.universal.loadFailed')}</div>`;
    }
}

/**
 * 切換暫停/繼續
 */
async function togglePause(container) {
    try {
        if (scraperState.status === 'paused') {
            await resumeUniversalScraper();
            updateStatus(container, 'running');
            toast.info(t('scraper.universal.resumed'));
        } else {
            await pauseUniversalScraper();
            updateStatus(container, 'paused');
            toast.info(t('scraper.universal.paused'));
        }
    } catch (error) {
        toast.error(error.message);
    }
}

/**
 * 停止爬取
 */
async function stopScraping(container) {
    try {
        await stopUniversalScraper();
        updateStatus(container, 'idle');
        toast.info(t('scraper.universal.stopped'));
    } catch (error) {
        toast.error(error.message);
    }
}

/**
 * 載入當前狀態
 */
async function loadCurrentStatus(container) {
    try {
        const status = await getUniversalStatus();
        scraperState.status = status.status || 'idle';
        scraperState.progress = status.progress;

        updateStatus(container, scraperState.status);

        if (scraperState.progress) {
            updateProgress(container, scraperState.progress, status.anime_name);
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

/**
 * 連接 WebSocket
 */
function connectWebSocket(container) {
    // 訂閱 Universal Scraper 事件
    wsManager.on('universalScraperProgress', (data) => {
        scraperState.progress = data;
        updateProgress(container, data);
    });

    wsManager.on('universalScraperComplete', (data) => {
        scraperState.status = 'idle';
        updateStatus(container, 'idle');
        toast.success(t('scraper.universal.completed', { count: data.overall_completed }));
    });

    wsManager.on('universalScraperError', (data) => {
        addLog(container, { level: 'error', message: data.message, timestamp: new Date() });
    });

    wsManager.on('log', (data) => {
        addLog(container, data);
    });

    // 連接
    wsManager.connect().catch(error => {
        console.warn('WebSocket connection failed:', error);
    });
}

/**
 * 更新狀態
 */
function updateStatus(container, status) {
    scraperState.status = status;

    const badge = container.querySelector('#status-badge');
    const startBtn = container.querySelector('#start-btn');
    const controlButtons = container.querySelector('#control-buttons');
    const pauseBtn = container.querySelector('#pause-btn');

    const statusConfig = {
        idle: { text: t('status.idle'), class: 'badge--default' },
        running: { text: t('status.running'), class: 'badge--success' },
        paused: { text: t('scraper.status.paused'), class: 'badge--warning' },
        stopped: { text: t('status.stopped'), class: 'badge--error' }
    };

    const config = statusConfig[status] || statusConfig.idle;

    if (badge) {
        badge.textContent = config.text;
        badge.className = `badge ${config.class}`;
    }

    if (startBtn && controlButtons) {
        const isRunning = status === 'running' || status === 'paused';
        startBtn.classList.toggle('hidden', isRunning);
        controlButtons.classList.toggle('hidden', !isRunning);
    }

    if (pauseBtn) {
        pauseBtn.innerHTML = status === 'paused'
            ? `<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/></svg>${t('scraper.universal.resume')}`
            : `<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>${t('scraper.universal.pause')}`;
    }
}

/**
 * 更新進度
 */
function updateProgress(container, progress, animeName = null) {
    if (!progress) return;

    // 更新整體統計
    if (animeName) {
        container.querySelector('#stat-anime').textContent = animeName;
    }
    container.querySelector('#stat-overall').textContent = formatNumber(progress.overall_completed);
    container.querySelector('#stat-speed').textContent = progress.speed ? `${progress.speed.toFixed(1)}/s` : '-';
    container.querySelector('#stat-eta').textContent = progress.eta ? formatDuration(progress.eta) : '-';

    // 更新分類別進度
    const categories = ['characters', 'episodes', 'galleries', 'chapters'];
    categories.forEach(category => {
        const categoryData = progress[category];
        if (!categoryData) return;

        const item = container.querySelector(`.category-progress-item[data-category="${category}"]`);
        if (!item) return;

        // 如果類別未啟用，隱藏進度條
        if (!categoryData.enabled) {
            item.style.opacity = '0.4';
            item.querySelector('.category-progress-value').textContent = t('scraper.universal.disabled');
            return;
        }

        item.style.opacity = '1';

        const total = categoryData.max_limit || categoryData.total;
        const completed = categoryData.completed;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

        item.querySelector('.category-progress-value').textContent =
            `${formatNumber(completed)} / ${total === 0 ? '∞' : formatNumber(total)}`;
        item.querySelector('.progress__bar').style.width = `${percent}%`;
    });
}

/**
 * 新增日誌
 */
function addLog(container, log) {
    scraperState.logs.push(log);

    if (scraperState.logs.length > 500) {
        scraperState.logs = scraperState.logs.slice(-500);
    }

    updateLogs(container);
}

/**
 * 更新日誌顯示
 */
function updateLogs(container) {
    const viewer = container.querySelector('#log-viewer');
    const autoScroll = container.querySelector('#auto-scroll')?.checked;

    if (!viewer) return;

    if (scraperState.logs.length === 0) {
        viewer.innerHTML = `<div class="log-empty">${t('scraper.universal.waiting')}</div>`;
        return;
    }

    viewer.innerHTML = scraperState.logs.map(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        const levelClass = {
            info: 'log-line--info',
            warning: 'log-line--warning',
            error: 'log-line--error',
            debug: 'log-line--debug'
        }[log.level] || '';

        return `<div class="log-line ${levelClass}">
            <span class="log-time">${time}</span>
            <span class="log-level">${escapeHtml(log.level?.toUpperCase() || 'INFO')}</span>
            <span class="log-message">${escapeHtml(log.message)}</span>
        </div>`;
    }).join('');

    if (autoScroll) {
        viewer.scrollTop = viewer.scrollHeight;
    }
}

/**
 * 清除日誌
 */
function clearLogs(container) {
    scraperState.logs = [];
    updateLogs(container);
}

/**
 * 載入歷史記錄
 */
async function loadHistory(container) {
    const historyList = container.querySelector('#history-list');
    if (!historyList) return;

    try {
        const history = await getScraperHistory({ limit: 10 });

        if (!history || history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state p-lg">
                    <p class="text-muted">${t('scraper.universal.noHistory')}</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = history.map(entry => {
            const date = new Date(entry.timestamp).toLocaleString('zh-TW');
            const result = entry.result || {};

            return `
                <div class="history-item">
                    <div class="history-item__info">
                        <div class="history-item__url">${escapeHtml(entry.base_url || t('common.noData'))}</div>
                        <div class="history-item__date">${escapeHtml(date)}</div>
                    </div>
                    <div class="history-item__stats">
                        <span class="badge badge--success">${escapeHtml(t('scraper.universal.completedCount', { count: result.completed || 0 }))}</span>
                        ${result.failed > 0 ? `<span class="badge badge--error">${escapeHtml(t('scraper.universal.failedCount', { count: result.failed }))}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load history:', error);
        historyList.innerHTML = `
            <div class="empty-state p-lg">
                <p class="text-muted">${t('scraper.universal.historyFailed')}</p>
            </div>
        `;
    }
}

export default { render: renderScraperPage };
