/**
 * Scraper Page - 爬蟲控制頁面
 */

import { t } from '../i18n/i18n.js';
import {
    getPresets,
    startScraper,
    stopScraper,
    pauseScraper,
    resumeScraper,
    getScraperStatus,
    getScraperLogs,
    getScraperHistory,
    saveConfig,
    getConfig,
    getConfigs,
    deleteConfig
} from '../api/scraper.js';
import { showModal, closeModal } from '../components/modal.js';
import { wsManager } from '../utils/websocket.js';
import { formatDuration, formatNumber } from '../utils/formatters.js';
import toast from '../components/toast.js';

// 爬蟲狀態
let scraperState = {
    status: 'idle',
    progress: null,
    logs: []
};

/**
 * 渲染爬蟲控制頁面
 * @param {HTMLElement} container - 容器元素
 */
export async function renderScraperPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('scraper.title')}</h1>
                </div>
            </div>

            <div class="scraper-layout">
                <!-- 左側：設定面板 -->
                <div class="scraper-config">
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.config.title')}</h3>
                        </div>
                        <div class="card__body">
                            <form id="scraper-form">
                                <!-- 預設選擇 -->
                                <div class="form-group">
                                    <label class="form-label">${t('scraper.config.preset')}</label>
                                    <select class="select" id="preset-select">
                                        <option value="">${t('scraper.config.selectPreset')}</option>
                                    </select>
                                </div>

                                <!-- 自訂 URL -->
                                <div class="form-group">
                                    <label class="form-label">${t('scraper.config.baseUrl')}</label>
                                    <input type="url" class="input" id="base-url" placeholder="https://example.fandom.com">
                                </div>

                                <div class="form-group">
                                    <label class="form-label">${t('scraper.config.characterListUrl')}</label>
                                    <input type="url" class="input" id="character-list-url" placeholder="/wiki/Category:Characters">
                                </div>

                                <!-- 進階設定 -->
                                <details class="form-details">
                                    <summary class="form-details__summary">${t('scraper.config.advancedOptions')}</summary>
                                    <div class="form-details__content">
                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.config.delay')}</label>
                                            <input type="number" class="input" id="delay" value="1" min="0" step="0.5">
                                            <p class="form-help">${t('scraper.config.delayHelp')}</p>
                                        </div>

                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.config.retries')}</label>
                                            <input type="number" class="input" id="retries" value="3" min="0" max="10">
                                            <p class="form-help">${t('scraper.config.retriesHelp')}</p>
                                        </div>

                                        <div class="form-group">
                                            <label class="form-label">${t('scraper.config.concurrent')}</label>
                                            <input type="number" class="input" id="concurrent" value="1" min="1" max="5">
                                            <p class="form-help">${t('scraper.config.concurrentHelp')}</p>
                                        </div>
                                    </div>
                                </details>

                                <!-- 控制按鈕 -->
                                <div class="form-actions mt-lg">
                                    <button type="submit" class="btn btn--primary btn--lg btn--block" id="start-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                                        </svg>
                                        ${t('scraper.controls.start')}
                                    </button>
                                    <div class="btn-group btn--block mt-sm hidden" id="control-buttons">
                                        <button type="button" class="btn btn--warning flex-1" id="pause-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                            </svg>
                                            ${t('scraper.controls.pause')}
                                        </button>
                                        <button type="button" class="btn btn--danger flex-1" id="stop-btn">
                                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
                                            </svg>
                                            ${t('scraper.controls.stop')}
                                        </button>
                                    </div>
                                </div>

                                <!-- 配置保存按鈕 -->
                                <div class="config-actions mt-md">
                                    <button type="button" class="btn btn--outline btn--sm" id="save-config-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                            <path d="M9.707 7.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L13 8.586V5h3a2 2 0 012 2v9a2 2 0 01-2 2H4a2 2 0 01-2-2V7a2 2 0 012-2h3v3.586L5.707 7.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L9 8.586V5h1v3.586z"/>
                                        </svg>
                                        儲存設定
                                    </button>
                                    <button type="button" class="btn btn--ghost btn--sm" id="load-config-btn">
                                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                                        </svg>
                                        載入設定
                                    </button>
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
                            <h3 class="card__title">${t('scraper.progress.title')}</h3>
                            <span class="badge" id="status-badge">${t('scraper.idle')}</span>
                        </div>
                        <div class="card__body">
                            <div class="progress-stats">
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.total')}</span>
                                    <span class="progress-stat__value" id="stat-total">0</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.completed')}</span>
                                    <span class="progress-stat__value text-success" id="stat-completed">0</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.failed')}</span>
                                    <span class="progress-stat__value text-error" id="stat-failed">0</span>
                                </div>
                                <div class="progress-stat">
                                    <span class="progress-stat__label">${t('scraper.progress.speed')}</span>
                                    <span class="progress-stat__value" id="stat-speed">-</span>
                                </div>
                            </div>

                            <div class="progress mt-lg">
                                <div class="progress__bar" id="progress-bar" style="width: 0%"></div>
                            </div>
                            <div class="progress__text mt-sm">
                                <span id="progress-text">0%</span>
                                <span id="progress-eta"></span>
                            </div>
                        </div>
                    </div>

                    <!-- 日誌面板 -->
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">${t('scraper.logs.title')}</h3>
                            <div class="flex gap-sm">
                                <label class="checkbox checkbox--sm">
                                    <input type="checkbox" id="auto-scroll" checked>
                                    <span class="checkbox__mark"></span>
                                    <span class="checkbox__label">${t('scraper.logs.autoScroll')}</span>
                                </label>
                                <button class="btn btn--sm btn--ghost" id="clear-logs">
                                    ${t('scraper.logs.clear')}
                                </button>
                            </div>
                        </div>
                        <div class="card__body p-0">
                            <div class="log-viewer" id="log-viewer">
                                <div class="log-empty">${t('common.noData')}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindScraperEvents(container);

    // 載入預設
    loadPresets(container);

    // 取得當前狀態
    loadCurrentStatus(container);

    // 載入歷史記錄
    loadHistory(container);

    // 連接 WebSocket
    connectWebSocket(container);
}

/**
 * 綁定事件
 * @param {HTMLElement} container - 容器元素
 */
function bindScraperEvents(container) {
    const form = container.querySelector('#scraper-form');
    const startBtn = container.querySelector('#start-btn');
    const pauseBtn = container.querySelector('#pause-btn');
    const stopBtn = container.querySelector('#stop-btn');
    const clearLogsBtn = container.querySelector('#clear-logs');
    const presetSelect = container.querySelector('#preset-select');

    // 預設選擇
    presetSelect?.addEventListener('change', (e) => {
        const preset = e.target.options[e.target.selectedIndex].dataset;
        if (preset.baseUrl) {
            container.querySelector('#base-url').value = preset.baseUrl;
        }
        if (preset.listUrl) {
            container.querySelector('#character-list-url').value = preset.listUrl;
        }
    });

    // 啟動爬蟲
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const config = {
            base_url: container.querySelector('#base-url').value,
            character_list_url: container.querySelector('#character-list-url').value,
            delay: parseFloat(container.querySelector('#delay').value) || 1,
            retries: parseInt(container.querySelector('#retries').value) || 3,
            concurrent: parseInt(container.querySelector('#concurrent').value) || 1
        };

        if (!config.base_url) {
            toast.warning('Please enter a base URL');
            return;
        }

        try {
            await startScraper(config);
            updateStatus(container, 'running');
            toast.success('Scraper started');
        } catch (error) {
            toast.error(error.message);
        }
    });

    // 暫停
    pauseBtn?.addEventListener('click', async () => {
        try {
            if (scraperState.status === 'paused') {
                await resumeScraper();
                updateStatus(container, 'running');
            } else {
                await pauseScraper();
                updateStatus(container, 'paused');
            }
        } catch (error) {
            toast.error(error.message);
        }
    });

    // 停止
    stopBtn?.addEventListener('click', async () => {
        try {
            await stopScraper();
            updateStatus(container, 'idle');
            toast.info('Scraper stopped');
        } catch (error) {
            toast.error(error.message);
        }
    });

    // 清除日誌
    clearLogsBtn?.addEventListener('click', () => {
        scraperState.logs = [];
        updateLogs(container);
    });

    // 儲存設定
    const saveConfigBtn = container.querySelector('#save-config-btn');
    saveConfigBtn?.addEventListener('click', () => {
        showSaveConfigModal(container);
    });

    // 載入設定
    const loadConfigBtn = container.querySelector('#load-config-btn');
    loadConfigBtn?.addEventListener('click', () => {
        showLoadConfigModal(container);
    });

    // 重新整理歷史
    const refreshHistoryBtn = container.querySelector('#refresh-history-btn');
    refreshHistoryBtn?.addEventListener('click', () => {
        loadHistory(container);
    });
}

/**
 * 載入預設
 * @param {HTMLElement} container - 容器元素
 */
async function loadPresets(container) {
    try {
        const presets = await getPresets();
        const select = container.querySelector('#preset-select');

        if (select && presets) {
            presets.forEach(preset => {
                const option = document.createElement('option');
                option.value = preset.name;
                option.textContent = preset.name;
                option.dataset.baseUrl = preset.base_url;
                option.dataset.listUrl = preset.character_list_url;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load presets:', error);
    }
}

/**
 * 載入當前狀態
 * @param {HTMLElement} container - 容器元素
 */
async function loadCurrentStatus(container) {
    try {
        const status = await getScraperStatus();
        if (status) {
            scraperState.status = status.status || 'idle';
            scraperState.progress = status.progress || null;
            updateStatus(container, scraperState.status);
            if (scraperState.progress) {
                updateProgress(container, scraperState.progress);
            }
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

/**
 * 連接 WebSocket
 * @param {HTMLElement} container - 容器元素
 */
function connectWebSocket(container) {
    // 訂閱爬蟲事件
    wsManager.on('scraperProgress', (data) => {
        scraperState.progress = data;
        updateProgress(container, data);
    });

    wsManager.on('scraperComplete', (data) => {
        scraperState.status = 'idle';
        updateStatus(container, 'idle');
        toast.success(`Scraping completed! ${data.total} characters scraped.`);
    });

    wsManager.on('scraperError', (data) => {
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
 * @param {HTMLElement} container - 容器元素
 * @param {string} status - 狀態
 */
function updateStatus(container, status) {
    scraperState.status = status;

    const badge = container.querySelector('#status-badge');
    const startBtn = container.querySelector('#start-btn');
    const controlButtons = container.querySelector('#control-buttons');
    const pauseBtn = container.querySelector('#pause-btn');

    const statusConfig = {
        idle: { text: t('scraper.idle'), class: 'badge--default' },
        running: { text: t('scraper.running'), class: 'badge--success' },
        paused: { text: t('scraper.paused'), class: 'badge--warning' },
        stopped: { text: t('scraper.stopped'), class: 'badge--error' }
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
            ? `<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/></svg>${t('scraper.controls.resume')}`
            : `<svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>${t('scraper.controls.pause')}`;
    }
}

/**
 * 更新進度
 * @param {HTMLElement} container - 容器元素
 * @param {Object} progress - 進度資料
 */
function updateProgress(container, progress) {
    const { total, completed, failed, speed, eta } = progress;

    container.querySelector('#stat-total').textContent = formatNumber(total);
    container.querySelector('#stat-completed').textContent = formatNumber(completed);
    container.querySelector('#stat-failed').textContent = formatNumber(failed);
    container.querySelector('#stat-speed').textContent = speed ? `${speed}/s` : '-';

    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    container.querySelector('#progress-bar').style.width = `${percent}%`;
    container.querySelector('#progress-text').textContent = `${percent}%`;
    container.querySelector('#progress-eta').textContent = eta ? `ETA: ${formatDuration(eta)}` : '';
}

/**
 * 新增日誌
 * @param {HTMLElement} container - 容器元素
 * @param {Object} log - 日誌物件
 */
function addLog(container, log) {
    scraperState.logs.push(log);

    // 限制日誌數量
    if (scraperState.logs.length > 500) {
        scraperState.logs = scraperState.logs.slice(-500);
    }

    updateLogs(container);
}

/**
 * 更新日誌顯示
 * @param {HTMLElement} container - 容器元素
 */
function updateLogs(container) {
    const viewer = container.querySelector('#log-viewer');
    const autoScroll = container.querySelector('#auto-scroll')?.checked;

    if (!viewer) return;

    if (scraperState.logs.length === 0) {
        viewer.innerHTML = `<div class="log-empty">${t('common.noData')}</div>`;
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
 * 載入歷史記錄
 * @param {HTMLElement} container - 容器元素
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

/**
 * 顯示儲存設定對話框
 * @param {HTMLElement} container - 容器元素
 */
function showSaveConfigModal(container) {
    const config = getCurrentConfig(container);

    if (!config.base_url) {
        toast.warning('請先輸入基本 URL');
        return;
    }

    const modalContent = `
        <form id="save-config-form" class="form">
            <div class="form-group">
                <label class="form-label">設定名稱</label>
                <input type="text" class="input" name="name" required placeholder="例如：Dragon Ball 爬蟲設定">
            </div>
            <div class="form-group">
                <label class="form-label">摘要</label>
                <div class="config-preview">
                    <p><strong>Base URL:</strong> ${config.base_url}</p>
                    <p><strong>延遲:</strong> ${config.delay} 秒</p>
                    <p><strong>重試次數:</strong> ${config.retries}</p>
                    <p><strong>並發數:</strong> ${config.concurrent}</p>
                </div>
            </div>
        </form>
    `;

    showModal({
        title: '儲存爬蟲設定',
        content: modalContent,
        confirmText: '儲存',
        onConfirm: async () => {
            const form = document.getElementById('save-config-form');
            const name = form.querySelector('[name="name"]').value;

            if (!name) {
                toast.warning('請輸入設定名稱');
                return;
            }

            try {
                await saveConfig(name, config);
                toast.success('設定已儲存');
                closeModal();
            } catch (error) {
                toast.error(`儲存失敗: ${error.message}`);
            }
        }
    });
}

/**
 * 顯示載入設定對話框
 * @param {HTMLElement} container - 容器元素
 */
async function showLoadConfigModal(container) {
    try {
        const configs = await getConfigs();

        if (!configs || configs.length === 0) {
            toast.info('暫無已儲存的設定');
            return;
        }

        const modalContent = `
            <div class="config-list">
                ${configs.map(cfg => `
                    <div class="config-list-item" data-name="${cfg.name}">
                        <div class="config-list-item__info">
                            <div class="config-list-item__name">${cfg.name}</div>
                            <div class="config-list-item__url text-muted">${cfg.base_url || ''}</div>
                            <div class="config-list-item__date text-muted">${cfg.created_at ? new Date(cfg.created_at).toLocaleString('zh-TW') : ''}</div>
                        </div>
                        <div class="config-list-item__actions">
                            <button class="btn btn--sm btn--primary load-config-action" data-name="${cfg.name}">載入</button>
                            <button class="btn btn--sm btn--danger delete-config-action" data-name="${cfg.name}">刪除</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        showModal({
            title: '載入爬蟲設定',
            content: modalContent,
            showConfirm: false,
            cancelText: '關閉'
        });

        // 綁定載入和刪除事件
        setTimeout(() => {
            document.querySelectorAll('.load-config-action').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const name = e.target.dataset.name;
                    try {
                        const configData = await getConfig(name);
                        if (configData && configData.config) {
                            applyConfig(container, configData.config);
                            toast.success(`已載入設定: ${name}`);
                            closeModal();
                        }
                    } catch (error) {
                        toast.error(`載入失敗: ${error.message}`);
                    }
                });
            });

            document.querySelectorAll('.delete-config-action').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const name = e.target.dataset.name;
                    if (confirm(`確定要刪除設定「${name}」嗎？`)) {
                        try {
                            await deleteConfig(name);
                            toast.success('設定已刪除');
                            e.target.closest('.config-list-item').remove();
                        } catch (error) {
                            toast.error(`刪除失敗: ${error.message}`);
                        }
                    }
                });
            });
        }, 100);

    } catch (error) {
        toast.error(`載入設定列表失敗: ${error.message}`);
    }
}

/**
 * 取得當前表單設定
 * @param {HTMLElement} container - 容器元素
 * @returns {Object} 設定物件
 */
function getCurrentConfig(container) {
    return {
        base_url: container.querySelector('#base-url')?.value || '',
        character_list_url: container.querySelector('#character-list-url')?.value || '/wiki/Category:Characters',
        delay: parseFloat(container.querySelector('#delay')?.value) || 1,
        retries: parseInt(container.querySelector('#retries')?.value) || 3,
        concurrent: parseInt(container.querySelector('#concurrent')?.value) || 1
    };
}

/**
 * 套用設定到表單
 * @param {HTMLElement} container - 容器元素
 * @param {Object} config - 設定物件
 */
function applyConfig(container, config) {
    if (config.base_url) {
        container.querySelector('#base-url').value = config.base_url;
    }
    if (config.character_list_url) {
        container.querySelector('#character-list-url').value = config.character_list_url;
    }
    if (config.delay !== undefined) {
        container.querySelector('#delay').value = config.delay;
    }
    if (config.retries !== undefined) {
        container.querySelector('#retries').value = config.retries;
    }
    if (config.concurrent !== undefined) {
        container.querySelector('#concurrent').value = config.concurrent;
    }
}

export default { render: renderScraperPage };
