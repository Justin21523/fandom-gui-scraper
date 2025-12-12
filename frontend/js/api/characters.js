/**
 * Characters API - 角色相關 API
 */

import api from './client.js';
import {
    setCharacters,
    setCurrentCharacter,
    setLoading
} from '../stores/characterStore.js';
import characterStore from '../stores/characterStore.js';

/**
 * 取得角色列表
 * @param {Object} options - 查詢選項
 * @returns {Promise<Object>} 分頁角色列表
 */
export async function getCharacters(options = {}) {
    setLoading(true);

    try {
        const state = characterStore.getState();
        const params = {
            page: options.page ?? state.currentPage,
            page_size: options.pageSize ?? state.pageSize,
            sort_by: options.sortBy ?? state.sortBy,
            sort_order: options.sortOrder ?? state.sortOrder,
            ...state.filters,
            ...options.filters
        };

        // 移除空值
        Object.keys(params).forEach(key => {
            if (params[key] === '' || params[key] === null || params[key] === undefined) {
                delete params[key];
            }
        });

        const data = await api.get('/characters', params);
        setCharacters(data);

        return data;
    } catch (error) {
        setLoading(false, error.message);
        throw error;
    }
}

/**
 * 取得單一角色
 * @param {string} id - 角色 ID
 * @returns {Promise<Object>} 角色資料
 */
export async function getCharacter(id) {
    const data = await api.get(`/characters/${id}`);
    setCurrentCharacter(data);
    return data;
}

/**
 * 搜尋角色
 * @param {string} query - 搜尋關鍵字
 * @param {Object} options - 搜尋選項
 * @returns {Promise<Object>} 搜尋結果
 */
export async function searchCharacters(query, options = {}) {
    setLoading(true);

    try {
        const params = {
            q: query,
            page: options.page || 1,
            page_size: options.pageSize || 20,
            ...options
        };

        const data = await api.get('/characters/search', params);
        setCharacters(data);

        return data;
    } catch (error) {
        setLoading(false, error.message);
        throw error;
    }
}

/**
 * 建立角色
 * @param {Object} characterData - 角色資料
 * @returns {Promise<Object>} 建立的角色
 */
export async function createCharacter(characterData) {
    return api.post('/characters', characterData);
}

/**
 * 更新角色
 * @param {string} id - 角色 ID
 * @param {Object} characterData - 更新資料
 * @returns {Promise<Object>} 更新後的角色
 */
export async function updateCharacter(id, characterData) {
    const data = await api.patch(`/characters/${id}`, characterData);
    setCurrentCharacter(data);
    return data;
}

/**
 * 刪除角色
 * @param {string} id - 角色 ID
 * @returns {Promise<void>}
 */
export async function deleteCharacter(id) {
    await api.delete(`/characters/${id}`);
}

/**
 * 批次刪除角色
 * @param {string[]} ids - 角色 ID 陣列
 * @returns {Promise<Object>}
 */
export async function deleteCharacters(ids) {
    return api.post('/characters/batch-delete', { ids });
}

/**
 * 取得角色統計
 * @returns {Promise<Object>} 統計資料
 */
export async function getCharacterStats() {
    return api.get('/characters/stats');
}

/**
 * 取得動畫列表
 * @returns {Promise<string[]>} 動畫名稱列表
 */
export async function getAnimeList() {
    return api.get('/characters/anime');
}

/**
 * 取得標籤列表
 * @returns {Promise<string[]>} 標籤列表
 */
export async function getTags() {
    return api.get('/characters/tags');
}

/**
 * 為角色新增標籤
 * @param {string} id - 角色 ID
 * @param {string[]} tags - 標籤陣列
 * @returns {Promise<Object>}
 */
export async function addTags(id, tags) {
    return api.post(`/characters/${id}/tags`, { tags });
}

/**
 * 從角色移除標籤
 * @param {string} id - 角色 ID
 * @param {string[]} tags - 標籤陣列
 * @returns {Promise<Object>}
 */
export async function removeTags(id, tags) {
    return api.delete(`/characters/${id}/tags`, { data: { tags } });
}

/**
 * 匯出角色
 * @param {Object} options - 匯出選項
 * @param {string} options.format - 格式 (json, csv, excel)
 * @param {string[]} options.ids - 角色 ID（空陣列表示全部）
 * @returns {Promise<void>}
 */
export async function exportCharacters(options = {}) {
    const { format = 'json', ids = [], filters = {} } = options;
    const params = { format, ...filters };

    if (ids.length > 0) {
        params.ids = ids.join(',');
    }

    await api.download('/export/characters', params);
}

export default {
    getCharacters,
    getCharacter,
    searchCharacters,
    createCharacter,
    updateCharacter,
    deleteCharacter,
    deleteCharacters,
    getCharacterStats,
    getAnimeList,
    getTags,
    addTags,
    removeTags,
    exportCharacters
};
