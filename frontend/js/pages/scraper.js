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

/**
 * 渲染爬蟲控制頁面
 */
export async function renderScraperPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">Universal Fandom Scraper</h1>
                    <p class="page__subtitle">支援任何 Fandom wiki 的通用爬蟲系統</p>
                </div>
            </div>

            <div class="scraper-layout">
                <!-- 左側：設定面板 -->
                <div class="scraper-config">
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">爬蟲設定</h3>
                        </div>
                        <div class="card__body">
                            <form id="universal-scraper-form">
                                <!-- 輸入類型選擇 -->
                                <div class="form-group">
                                    <label class="form-label">輸入方式</label>
                                    <div class="btn-group btn--block">
                                        <button type="button" class="btn flex-1 input-type-btn active" data-type="name">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"/>
                                            </svg>
                                            動畫名稱搜尋
                                        </button>
                                        <button type="button" class="btn flex-1 input-type-btn" data-type="url">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd"/>
                                            </svg>
                                            直接 URL
                                        </button>
                                    </div>
                                </div>

                                <!-- 動畫名稱搜尋 (預設顯示) -->
                                <div id="input-mode-name">
                                    <div class="form-group">
                                        <label class="form-label">動畫名稱</label>
                                        <div class="input-group">
                                            <input type="text" class="input" id="anime-name-input"
                                                placeholder="例如: Attack on Titan" autocomplete="off">
                                            <button type="button" class="btn btn--primary" id="search-anime-btn">
                                                <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                    <path d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"/>
                                                </svg>
                                                搜尋
                                            </button>
                                        </div>
                                    </div>

                                    <!-- 搜尋結果 -->
                                    <div id="search-results-container" class="hidden">
                                        <div class="form-group">
                                            <label class="form-label">搜尋結果</label>
                                            <div id="search-results-list" class="search-results-list">
                                                <!-- 動態填充 -->
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- URL 輸入 (隱藏) -->
                                <div id="input-mode-url" class="hidden">
                                    <div class="form-group">
                                        <label class="form-label">Fandom Wiki URL</label>
                                        <input type="url" class="input" id="wiki-url-input"
                                            placeholder="https://onepiece.fandom.com">
                                        <p class="form-help">輸入完整的 Fandom wiki URL</p>
                                    </div>
                                </div>

                                <!-- 爬取範圍 -->
                                <div class="form-group">
                                    <label class="form-label">爬取範圍</label>
                                    <div class="checkbox-group">
                                        <label class="checkbox">
                                            <input type="checkbox" id="crawl-characters" checked>
                                            <span class="checkbox__mark"></span>
                                            <span class="checkbox__label">角色資料 (Characters)</span>
                                        </label>
                                        <label class="checkbox">
                                            <input type="checkbox" id="crawl-episodes" checked>
                                            <span class="checkbox__mark"></span>
                                            <span class="checkbox__label">劇集資料 (Episodes)</span>
                                        </label>
                                        <label class="checkbox">
                                            <input type="checkbox" id="crawl-galleries" checked>
                                            <span class="checkbox__mark"></span>
                                            <span class="checkbox__label">圖庫資料 (Gallery)</span>
                                        </label>
                                        <label class="checkbox">
                                            <input type="checkbox" id="crawl-chapters">
                                            <span class="checkbox__mark"></span>
                                            <span class="checkbox__label">章節資料 (Chapters/Manga)</span>
                                        </label>
                                    </div>
                                </div>

                                <!-- 分類別限制 -->
                                <details class="form-details">
                                    <summary class="form-details__summary">分類別爬取限制</summary>
                                    <div class="form-details__content">
                                        <div class="form-group">
                                            <label class="form-label">最大角色數</label>
                                            <input type="number" class="input" id="max-chars"
                                                value="100" min="0" step="10">
                                            <p class="form-help">0 = 無限制</p>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">最大劇集數</label>
                                            <input type="number" class="input" id="max-episodes"
                                                value="50" min="0" step="10">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">最大圖片數</label>
                                            <input type="number" class="input" id="max-gallery"
                                                value="200" min="0" step="50">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">最大章節數</label>
                                            <input type="number" class="input" id="max-chapters"
                                                value="50" min="0" step="10">
                                        </div>
                                    </div>
                                </details>

                                <!-- 進階設定 -->
                                <details class="form-details">
                                    <summary class="form-details__summary">進階設定</summary>
                                    <div class="form-details__content">
                                        <div class="form-group">
                                            <label class="form-label">請求延遲 (秒)</label>
                                            <input type="number" class="input" id="delay"
                                                value="1" min="0" max="10" step="0.5">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">重試次數</label>
                                            <input type="number" class="input" id="retries"
                                                value="3" min="0" max="10">
                                        </div>
                                    </div>
                                </details>

                                <!-- 控制按鈕 -->
                                <div class="form-actions mt-lg">
                                    <button type="submit" class="btn btn--primary btn--lg btn--block" id="start-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                                        </svg>
                                        開始爬取
                                    </button>
                                    <div class="btn-group btn--block mt-sm hidden" id="control-buttons">
                                        <button type="button" class="btn btn--warning flex-1" id="pause-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                            </svg>
                                            暫停
                                        </button>
                                        <button type="button" class="btn btn--danger flex-1" id="stop-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
                                            </svg>
                                            停止
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>

                    <!-- 歷史記錄 -->
                    <div class="card mt-lg">
                        <div class="card__header">
                            <h3 class="card__title">爬取歷史</h3>
                            <button class="btn btn--sm btn--ghost" id="refresh-history-btn">
                                <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                                </svg>
                            </button>
                        </div>
                        <div class="card__body p-0">
                            <div class="history-list" id="history-list">
                                <div class="empty-state p-lg">
                                    <p class="text-muted">載入中...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 右側：狀態和日誌 -->
                <div class="scraper-status">
                    <!-- 狀態卡片 -->
                    <div class="card mb-lg">
                        <div class="card__header">
                            <h3 class="card__title">爬取進度</h3>
                            <span class="badge" id="status-badge">閒置中</span>
                        </div>
                        <div class="card__body">
                            <!-- 整體進度 -->
                            <div class="progress-stats mb-lg">
                                <div class="progress-stat">
                                    <span class="progress-stat__label">動畫</span>
                                    <span class="progress-stat__value" id="stat-anime">-</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">總計完成</span>
                                    <span class="progress-stat__value text-success" id="stat-overall">0</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">速度</span>
                                    <span class="progress-stat__value" id="stat-speed">-</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">預計時間</span>
                                    <span class="progress-stat__value" id="stat-eta">-</span>
                                </div>
                            </div>

                            <!-- 分類別進度 -->
                            <div class="category-progress">
                                <!-- Characters -->
                                <div class="category-progress-item" data-category="characters">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">角色</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Episodes -->
                                <div class="category-progress-item" data-category="episodes">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">劇集</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Galleries -->
                                <div class="category-progress-item" data-category="galleries">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">圖庫</span>
                                        <span class="category-progress-value">0 / 0</span>
                                    </div>
                                    <div class="progress progress--sm">
                                        <div class="progress__bar"></div>
                                    </div>
                                </div>

                                <!-- Chapters -->
                                <div class="category-progress-item" data-category="chapters">
                                    <div class="category-progress-header">
                                        <span class="category-progress-name">章節</span>
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
                            <h3 class="card__title">即時日誌</h3>
                            <div class="flex gap-sm">
                                <label class="checkbox checkbox--sm">
                                    <input type="checkbox" id="auto-scroll" checked>
                                    <span class="checkbox__mark"></span>
                                    <span class="checkbox__label">自動捲動</span>
                                </label>
                                <button class="btn btn--sm btn--ghost" id="clear-logs">
                                    清除
                                </button>
                            </div>
                        </div>
                        <div class="card__body p-0">
                            <div class="log-viewer" id="log-viewer">
                                <div class="log-empty">等待開始...</div>
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
        toast.warning('請輸入動畫名稱');
        return;
    }

    const searchBtn = container.querySelector('#search-anime-btn');
    const originalText = searchBtn.innerHTML;
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="loading-spinner loading-spinner--sm"></span> 搜尋中...';

    try {
        const results = await searchAnime(animeName, 5);
        scraperState.animeSearchResults = results;
        renderSearchResults(container, results);
        toast.success(`找到 ${results.length} 個結果`);
    } catch (error) {
        toast.error(`搜尋失敗: ${error.message}`);
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
                <div class="search-result-title">${result.title}</div>
                <div class="search-result-url text-muted">${result.url}</div>
                ${result.description ? `<div class="search-result-desc text-sm">${result.description}</div>` : ''}
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
            toast.warning('請先搜尋並選擇一個 wiki');
            return;
        }
        inputSource = scraperState.selectedWiki.url;
    } else {
        inputSource = container.querySelector('#wiki-url-input').value.trim();
        if (!inputSource) {
            toast.warning('請輸入 wiki URL');
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
        retries: parseInt(container.querySelector('#retries').value) || 3
    };

    // 驗證至少選擇一個類別
    if (!config.crawl_characters && !config.crawl_episodes &&
        !config.crawl_galleries && !config.crawl_chapters) {
        toast.warning('請至少選擇一個爬取範圍');
        return;
    }

    try {
        await startUniversalScraper(config);
        updateStatus(container, 'running');
        scraperState.logs = [];
        toast.success('Universal Scraper 已啟動');
        addLog(container, { level: 'info', message: 'Universal Scraper 已啟動', timestamp: new Date() });
    } catch (error) {
        toast.error(`啟動失敗: ${error.message}`);
        console.error('Start error:', error);
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
            toast.info('已繼續');
        } else {
            await pauseUniversalScraper();
            updateStatus(container, 'paused');
            toast.info('已暫停');
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
        toast.info('已停止');
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
        toast.success(`爬取完成！共完成 ${data.overall_completed} 項`);
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
        idle: { text: '閒置中', class: 'badge--default' },
        running: { text: '運行中', class: 'badge--success' },
        paused: { text: '已暫停', class: 'badge--warning' },
        stopped: { text: '已停止', class: 'badge--error' }
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
            ? '<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/></svg>繼續'
            : '<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>暫停';
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
            item.querySelector('.category-progress-value').textContent = '未啟用';
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
        viewer.innerHTML = '<div class="log-empty">等待開始...</div>';
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
            <span class="log-level">${log.level?.toUpperCase() || 'INFO'}</span>
            <span class="log-message">${log.message}</span>
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
                    <p class="text-muted">暫無爬取歷史記錄</p>
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
                        <div class="history-item__url">${entry.base_url || '未知'}</div>
                        <div class="history-item__date">${date}</div>
                    </div>
                    <div class="history-item__stats">
                        <span class="badge badge--success">${result.completed || 0} 完成</span>
                        ${result.failed > 0 ? `<span class="badge badge--error">${result.failed} 失敗</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load history:', error);
        historyList.innerHTML = `
            <div class="empty-state p-lg">
                <p class="text-muted">載入歷史記錄失敗</p>
            </div>
        `;
    }
}

export default { render: renderScraperPage };
