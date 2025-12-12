/**
 * Store - 簡易響應式狀態管理
 * 提供類似 Redux 的狀態管理機制
 */

export class Store {
    constructor(initialState = {}) {
        this._state = initialState;
        this._subscribers = new Set();
        this._middleware = [];
    }

    /**
     * 取得當前狀態
     * @returns {Object} 當前狀態的複本
     */
    getState() {
        return { ...this._state };
    }

    /**
     * 更新狀態
     * @param {Object|Function} update - 新狀態或更新函數
     */
    setState(update) {
        const prevState = this._state;

        // 支援函數式更新
        const newState = typeof update === 'function'
            ? update(prevState)
            : update;

        // 執行中間件
        let finalState = { ...prevState, ...newState };
        for (const middleware of this._middleware) {
            finalState = middleware(prevState, finalState) || finalState;
        }

        this._state = finalState;

        // 通知所有訂閱者
        this._notifySubscribers(prevState, this._state);
    }

    /**
     * 訂閱狀態變化
     * @param {Function} callback - 狀態變化時的回調函數
     * @param {string[]} keys - 可選，只監聽特定鍵值的變化
     * @returns {Function} 取消訂閱的函數
     */
    subscribe(callback, keys = null) {
        const subscriber = { callback, keys };
        this._subscribers.add(subscriber);

        return () => {
            this._subscribers.delete(subscriber);
        };
    }

    /**
     * 新增中間件
     * @param {Function} middleware - 中間件函數 (prevState, nextState) => nextState
     */
    use(middleware) {
        this._middleware.push(middleware);
    }

    /**
     * 重置狀態
     * @param {Object} newState - 新的初始狀態
     */
    reset(newState = {}) {
        const prevState = this._state;
        this._state = newState;
        this._notifySubscribers(prevState, this._state);
    }

    /**
     * 通知訂閱者
     * @private
     */
    _notifySubscribers(prevState, nextState) {
        for (const { callback, keys } of this._subscribers) {
            // 如果指定了 keys，只在這些 key 變化時通知
            if (keys) {
                const hasChanged = keys.some(key => prevState[key] !== nextState[key]);
                if (!hasChanged) continue;
            }

            try {
                callback(nextState, prevState);
            } catch (error) {
                console.error('Store subscriber error:', error);
            }
        }
    }
}

/**
 * 建立帶有持久化的 Store
 * @param {string} key - localStorage 的鍵名
 * @param {Object} initialState - 初始狀態
 * @returns {Store}
 */
export function createPersistentStore(key, initialState) {
    // 嘗試從 localStorage 讀取
    let savedState = initialState;
    try {
        const saved = localStorage.getItem(key);
        if (saved) {
            savedState = { ...initialState, ...JSON.parse(saved) };
        }
    } catch (error) {
        console.warn(`Failed to load state from localStorage[${key}]:`, error);
    }

    const store = new Store(savedState);

    // 自動保存到 localStorage
    store.subscribe((state) => {
        try {
            localStorage.setItem(key, JSON.stringify(state));
        } catch (error) {
            console.warn(`Failed to save state to localStorage[${key}]:`, error);
        }
    });

    return store;
}

// 全域 Store 實例
export const globalStore = new Store({
    // UI 狀態
    sidebarCollapsed: false,
    theme: 'light',
    locale: 'zh',

    // 載入狀態
    isLoading: false,
    loadingMessage: '',

    // 錯誤狀態
    error: null,

    // 通知
    toasts: []
});

export default Store;
