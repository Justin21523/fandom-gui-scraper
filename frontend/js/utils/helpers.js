/**
 * Helpers - 工具函數
 */

/**
 * 防抖函數
 * @param {Function} func - 要防抖的函數
 * @param {number} wait - 等待時間（毫秒）
 * @returns {Function}
 */
export function debounce(func, wait = 300) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 節流函數
 * @param {Function} func - 要節流的函數
 * @param {number} limit - 時間限制（毫秒）
 * @returns {Function}
 */
export function throttle(func, limit = 300) {
    let inThrottle;

    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 深層複製
 * @param {any} obj - 要複製的物件
 * @returns {any}
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }

    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }

    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }

    if (obj instanceof Set) {
        return new Set([...obj].map(item => deepClone(item)));
    }

    if (obj instanceof Map) {
        return new Map([...obj].map(([k, v]) => [deepClone(k), deepClone(v)]));
    }

    const cloned = {};
    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            cloned[key] = deepClone(obj[key]);
        }
    }

    return cloned;
}

/**
 * 深層合併物件
 * @param {Object} target - 目標物件
 * @param {...Object} sources - 來源物件
 * @returns {Object}
 */
export function deepMerge(target, ...sources) {
    if (!sources.length) return target;

    const source = sources.shift();

    if (isObject(target) && isObject(source)) {
        for (const key in source) {
            if (isObject(source[key])) {
                if (!target[key]) {
                    Object.assign(target, { [key]: {} });
                }
                deepMerge(target[key], source[key]);
            } else {
                Object.assign(target, { [key]: source[key] });
            }
        }
    }

    return deepMerge(target, ...sources);
}

/**
 * 檢查是否為物件
 * @param {any} item
 * @returns {boolean}
 */
export function isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
}

/**
 * 產生唯一 ID
 * @param {string} prefix - 前綴
 * @returns {string}
 */
export function generateId(prefix = '') {
    const timestamp = Date.now().toString(36);
    const randomPart = Math.random().toString(36).substring(2, 9);
    return `${prefix}${timestamp}${randomPart}`;
}

/**
 * 等待指定時間
 * @param {number} ms - 毫秒
 * @returns {Promise<void>}
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 將陣列分組
 * @param {Array} array - 陣列
 * @param {string|Function} key - 分組鍵
 * @returns {Object}
 */
export function groupBy(array, key) {
    return array.reduce((result, item) => {
        const groupKey = typeof key === 'function' ? key(item) : item[key];
        (result[groupKey] = result[groupKey] || []).push(item);
        return result;
    }, {});
}

/**
 * 將陣列去重
 * @param {Array} array - 陣列
 * @param {string|Function} key - 去重鍵（可選）
 * @returns {Array}
 */
export function unique(array, key = null) {
    if (!key) {
        return [...new Set(array)];
    }

    const seen = new Set();
    return array.filter(item => {
        const k = typeof key === 'function' ? key(item) : item[key];
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
    });
}

/**
 * 排序陣列
 * @param {Array} array - 陣列
 * @param {string} key - 排序鍵
 * @param {string} order - 排序方向 'asc' | 'desc'
 * @returns {Array}
 */
export function sortBy(array, key, order = 'asc') {
    return [...array].sort((a, b) => {
        const aVal = typeof key === 'function' ? key(a) : a[key];
        const bVal = typeof key === 'function' ? key(b) : b[key];

        let comparison = 0;
        if (aVal > bVal) comparison = 1;
        if (aVal < bVal) comparison = -1;

        return order === 'desc' ? -comparison : comparison;
    });
}

/**
 * 安全地取得巢狀屬性
 * @param {Object} obj - 物件
 * @param {string} path - 屬性路徑（用 . 分隔）
 * @param {any} defaultValue - 預設值
 * @returns {any}
 */
export function get(obj, path, defaultValue = undefined) {
    const keys = path.split('.');
    let result = obj;

    for (const key of keys) {
        if (result === null || result === undefined) {
            return defaultValue;
        }
        result = result[key];
    }

    return result === undefined ? defaultValue : result;
}

/**
 * 安全地設定巢狀屬性
 * @param {Object} obj - 物件
 * @param {string} path - 屬性路徑
 * @param {any} value - 值
 * @returns {Object}
 */
export function set(obj, path, value) {
    const keys = path.split('.');
    let current = obj;

    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current) || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }

    current[keys[keys.length - 1]] = value;
    return obj;
}

/**
 * 建立事件發射器
 * @returns {Object}
 */
export function createEventEmitter() {
    const listeners = new Map();

    return {
        on(event, callback) {
            if (!listeners.has(event)) {
                listeners.set(event, new Set());
            }
            listeners.get(event).add(callback);

            return () => this.off(event, callback);
        },

        off(event, callback) {
            if (listeners.has(event)) {
                listeners.get(event).delete(callback);
            }
        },

        emit(event, ...args) {
            if (listeners.has(event)) {
                listeners.get(event).forEach(callback => {
                    try {
                        callback(...args);
                    } catch (error) {
                        console.error(`Event listener error [${event}]:`, error);
                    }
                });
            }
        },

        once(event, callback) {
            const wrapper = (...args) => {
                this.off(event, wrapper);
                callback(...args);
            };
            this.on(event, wrapper);
        }
    };
}

/**
 * 將物件轉換為查詢字串
 * @param {Object} params - 參數物件
 * @returns {string}
 */
export function toQueryString(params) {
    return Object.entries(params)
        .filter(([_, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => {
            if (Array.isArray(v)) {
                return v.map(item => `${encodeURIComponent(k)}=${encodeURIComponent(item)}`).join('&');
            }
            return `${encodeURIComponent(k)}=${encodeURIComponent(v)}`;
        })
        .join('&');
}

/**
 * 解析查詢字串
 * @param {string} queryString - 查詢字串
 * @returns {Object}
 */
export function parseQueryString(queryString) {
    const params = {};
    const searchParams = new URLSearchParams(queryString);

    searchParams.forEach((value, key) => {
        if (params[key]) {
            if (Array.isArray(params[key])) {
                params[key].push(value);
            } else {
                params[key] = [params[key], value];
            }
        } else {
            params[key] = value;
        }
    });

    return params;
}

/**
 * 複製文字到剪貼簿
 * @param {string} text - 要複製的文字
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback 方法
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        const result = document.execCommand('copy');
        document.body.removeChild(textarea);
        return result;
    }
}

export default {
    debounce,
    throttle,
    deepClone,
    deepMerge,
    isObject,
    generateId,
    sleep,
    groupBy,
    unique,
    sortBy,
    get,
    set,
    createEventEmitter,
    toQueryString,
    parseQueryString,
    copyToClipboard
};
