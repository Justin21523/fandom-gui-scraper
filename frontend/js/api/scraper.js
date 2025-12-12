/**
 * Scraper API - 爬蟲控制 API
 */

import api from './client.js';

/**
 * 取得爬蟲預設配置
 * @returns {Promise<Object[]>} 動畫預設列表
 */
export async function getPresets() {
    return api.get('/scraper/presets');
}

/**
 * 啟動爬蟲
 * @param {Object} config - 爬蟲配置
 * @returns {Promise<Object>} 啟動結果
 */
export async function startScraper(config) {
    return api.post('/scraper/start', config);
}

/**
 * 停止爬蟲
 * @returns {Promise<Object>}
 */
export async function stopScraper() {
    return api.post('/scraper/stop');
}

/**
 * 暫停爬蟲
 * @returns {Promise<Object>}
 */
export async function pauseScraper() {
    return api.post('/scraper/pause');
}

/**
 * 繼續爬蟲
 * @returns {Promise<Object>}
 */
export async function resumeScraper() {
    return api.post('/scraper/resume');
}

/**
 * 取得爬蟲狀態
 * @returns {Promise<Object>} 爬蟲狀態
 */
export async function getScraperStatus() {
    return api.get('/scraper/status');
}

/**
 * 取得爬蟲歷史記錄
 * @param {Object} options - 查詢選項
 * @returns {Promise<Object[]>} 歷史記錄
 */
export async function getScraperHistory(options = {}) {
    return api.get('/scraper/history', options);
}

/**
 * 取得爬蟲日誌
 * @param {Object} options - 查詢選項
 * @returns {Promise<Object[]>} 日誌列表
 */
export async function getScraperLogs(options = {}) {
    const { limit = 100, level = 'all', since = null } = options;
    return api.get('/scraper/logs', { limit, level, since });
}

/**
 * 驗證 URL
 * @param {string} url - 要驗證的 URL
 * @returns {Promise<Object>} 驗證結果
 */
export async function validateUrl(url) {
    return api.post('/scraper/validate-url', { url });
}

/**
 * 測試選擇器
 * @param {string} url - 測試頁面 URL
 * @param {Object} selectors - 選擇器配置
 * @returns {Promise<Object>} 測試結果
 */
export async function testSelectors(url, selectors) {
    return api.post('/scraper/test-selectors', { url, selectors });
}

/**
 * 取得爬蟲統計
 * @returns {Promise<Object>} 統計資料
 */
export async function getScraperStats() {
    return api.get('/scraper/stats');
}

/**
 * 儲存爬蟲配置
 * @param {string} name - 配置名稱
 * @param {Object} config - 配置內容
 * @returns {Promise<Object>}
 */
export async function saveConfig(name, config) {
    return api.post(`/scraper/configs?name=${encodeURIComponent(name)}`, config);
}

/**
 * 取得特定配置
 * @param {string} name - 配置名稱
 * @returns {Promise<Object>}
 */
export async function getConfig(name) {
    return api.get(`/scraper/configs/${encodeURIComponent(name)}`);
}

/**
 * 取得已儲存的配置列表
 * @returns {Promise<Object[]>}
 */
export async function getConfigs() {
    return api.get('/scraper/configs');
}

/**
 * 刪除配置
 * @param {string} name - 配置名稱
 * @returns {Promise<void>}
 */
export async function deleteConfig(name) {
    return api.delete(`/scraper/configs/${encodeURIComponent(name)}`);
}

// ========================================
// UNIVERSAL FANDOM SCRAPER API
// ========================================

/**
 * 搜尋動畫的 Fandom wiki
 * @param {string} animeName - 動畫名稱
 * @param {number} topN - 返回結果數量
 * @returns {Promise<Object[]>} 搜尋結果列表
 */
export async function searchAnime(animeName, topN = 5) {
    return api.post('/scraper/search-anime', {
        anime_name: animeName,
        top_n: topN
    });
}

/**
 * 啟動 Universal Fandom Scraper
 * @param {Object} config - Universal scraper 配置
 * @returns {Promise<Object>} 啟動結果
 */
export async function startUniversalScraper(config) {
    return api.post('/scraper/start-universal', config);
}

/**
 * 取得 Universal Scraper 狀態
 * @returns {Promise<Object>} 狀態資訊 (包含分類別進度)
 */
export async function getUniversalStatus() {
    return api.get('/scraper/universal-status');
}

/**
 * 停止 Universal Scraper
 * @returns {Promise<Object>}
 */
export async function stopUniversalScraper() {
    return api.post('/scraper/stop-universal');
}

/**
 * 暫停 Universal Scraper
 * @returns {Promise<Object>}
 */
export async function pauseUniversalScraper() {
    return api.post('/scraper/pause-universal');
}

/**
 * 繼續 Universal Scraper
 * @returns {Promise<Object>}
 */
export async function resumeUniversalScraper() {
    return api.post('/scraper/resume-universal');
}

/**
 * 取得 Universal Scraper 日誌
 * @param {Object} options - 查詢選項
 * @returns {Promise<Object[]>} 日誌列表
 */
export async function getUniversalLogs(options = {}) {
    const { limit = 100, level = 'all' } = options;
    return api.get('/scraper/universal-logs', { limit, level });
}

export default {
    // Legacy scraper
    getPresets,
    startScraper,
    stopScraper,
    pauseScraper,
    resumeScraper,
    getScraperStatus,
    getScraperHistory,
    getScraperLogs,
    validateUrl,
    testSelectors,
    getScraperStats,
    saveConfig,
    getConfig,
    getConfigs,
    deleteConfig,

    // Universal scraper
    searchAnime,
    startUniversalScraper,
    getUniversalStatus,
    stopUniversalScraper,
    pauseUniversalScraper,
    resumeUniversalScraper,
    getUniversalLogs
};
