/**
 * CharacterStore - 角色資料狀態管理
 */

import { Store } from './store.js';

const initialState = {
    // 角色列表
    characters: [],
    totalCount: 0,

    // 分頁
    currentPage: 1,
    pageSize: 20,
    totalPages: 0,

    // 篩選和排序
    filters: {
        anime: '',
        search: '',
        tags: [],
        minQuality: 0
    },
    sortBy: 'name',
    sortOrder: 'asc',

    // 視圖模式
    viewMode: 'table', // 'table' | 'card' | 'tree'

    // 選取的角色
    selectedIds: new Set(),
    selectAll: false,

    // 當前角色詳情
    currentCharacter: null,

    // 載入狀態
    isLoading: false,
    error: null
};

export const characterStore = new Store(initialState);

/**
 * 設定角色列表
 * @param {Object} data - API 回傳的分頁資料
 */
export function setCharacters(data) {
    const { items, total, page, page_size, total_pages } = data;
    characterStore.setState({
        characters: items,
        totalCount: total,
        currentPage: page,
        pageSize: page_size,
        totalPages: total_pages,
        isLoading: false,
        error: null
    });
}

/**
 * 設定當前角色
 * @param {Object} character - 角色資料
 */
export function setCurrentCharacter(character) {
    characterStore.setState({ currentCharacter: character });
}

/**
 * 更新篩選條件
 * @param {Object} newFilters - 新的篩選條件
 */
export function updateFilters(newFilters) {
    characterStore.setState(state => ({
        filters: { ...state.filters, ...newFilters },
        currentPage: 1 // 重置到第一頁
    }));
}

/**
 * 設定排序
 * @param {string} sortBy - 排序欄位
 * @param {string} sortOrder - 排序方向 'asc' | 'desc'
 */
export function setSort(sortBy, sortOrder = 'asc') {
    characterStore.setState({ sortBy, sortOrder });
}

/**
 * 切換排序
 * @param {string} field - 欄位名稱
 */
export function toggleSort(field) {
    const { sortBy, sortOrder } = characterStore.getState();
    if (sortBy === field) {
        characterStore.setState({
            sortOrder: sortOrder === 'asc' ? 'desc' : 'asc'
        });
    } else {
        characterStore.setState({
            sortBy: field,
            sortOrder: 'asc'
        });
    }
}

/**
 * 設定頁碼
 * @param {number} page - 頁碼
 */
export function setPage(page) {
    characterStore.setState({ currentPage: page });
}

/**
 * 設定每頁數量
 * @param {number} size - 每頁數量
 */
export function setPageSize(size) {
    characterStore.setState({
        pageSize: size,
        currentPage: 1
    });
}

/**
 * 設定視圖模式
 * @param {string} mode - 視圖模式
 */
export function setViewMode(mode) {
    characterStore.setState({ viewMode: mode });
}

/**
 * 切換選取角色
 * @param {string} id - 角色 ID
 */
export function toggleSelect(id) {
    characterStore.setState(state => {
        const selectedIds = new Set(state.selectedIds);
        if (selectedIds.has(id)) {
            selectedIds.delete(id);
        } else {
            selectedIds.add(id);
        }
        return {
            selectedIds,
            selectAll: selectedIds.size === state.characters.length
        };
    });
}

/**
 * 全選/取消全選
 */
export function toggleSelectAll() {
    characterStore.setState(state => {
        if (state.selectAll) {
            return { selectedIds: new Set(), selectAll: false };
        }
        return {
            selectedIds: new Set(state.characters.map(c => c.id || c._id)),
            selectAll: true
        };
    });
}

/**
 * 清除選取
 */
export function clearSelection() {
    characterStore.setState({
        selectedIds: new Set(),
        selectAll: false
    });
}

/**
 * 設定載入狀態
 * @param {boolean} isLoading - 是否載入中
 * @param {string} error - 錯誤訊息
 */
export function setLoading(isLoading, error = null) {
    characterStore.setState({ isLoading, error });
}

/**
 * 重置狀態
 */
export function resetCharacterStore() {
    characterStore.reset(initialState);
}

export default characterStore;
