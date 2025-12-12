/**
 * i18n - 多語言系統
 */

import { globalStore } from '../stores/store.js';

// 語言檔案
const translations = {
    zh: null,
    en: null
};

// 當前語言
let currentLocale = 'zh';

// 監聽器
const listeners = new Set();

/**
 * 載入語言檔案
 * @param {string} locale - 語言代碼
 * @returns {Promise<Object>}
 */
async function loadLocale(locale) {
    if (translations[locale]) {
        return translations[locale];
    }

    try {
        const response = await fetch(`/frontend/js/i18n/${locale}.json`);
        if (!response.ok) {
            throw new Error(`Failed to load locale: ${locale}`);
        }
        translations[locale] = await response.json();
        return translations[locale];
    } catch (error) {
        console.error(`Failed to load locale ${locale}:`, error);
        return {};
    }
}

/**
 * 初始化 i18n
 * @param {string} locale - 初始語言
 */
export async function initI18n(locale = 'zh') {
    // 從 localStorage 讀取偏好語言
    const savedLocale = localStorage.getItem('locale') || locale;
    await setLocale(savedLocale);
}

/**
 * 設定語言
 * @param {string} locale - 語言代碼
 */
export async function setLocale(locale) {
    if (!['zh', 'en'].includes(locale)) {
        console.warn(`Unknown locale: ${locale}, falling back to zh`);
        locale = 'zh';
    }

    await loadLocale(locale);
    currentLocale = locale;
    localStorage.setItem('locale', locale);

    // 更新全域狀態
    globalStore.setState({ locale });

    // 更新頁面
    updatePageTranslations();

    // 通知監聽器
    listeners.forEach(callback => callback(locale));
}

/**
 * 取得當前語言
 * @returns {string}
 */
export function getLocale() {
    return currentLocale;
}

/**
 * 翻譯文字
 * @param {string} key - 翻譯鍵
 * @param {Object} params - 替換參數
 * @returns {string}
 */
export function t(key, params = {}) {
    const keys = key.split('.');
    let value = translations[currentLocale];

    for (const k of keys) {
        if (value && typeof value === 'object') {
            value = value[k];
        } else {
            value = undefined;
            break;
        }
    }

    if (value === undefined) {
        console.warn(`Translation missing: ${key}`);
        return key;
    }

    // 替換參數 {{param}}
    return String(value).replace(/\{\{(\w+)\}\}/g, (_, name) => {
        return params[name] !== undefined ? params[name] : `{{${name}}}`;
    });
}

/**
 * 翻譯並返回 HTML（支援簡單標籤）
 * @param {string} key - 翻譯鍵
 * @param {Object} params - 替換參數
 * @returns {string}
 */
export function tHtml(key, params = {}) {
    return t(key, params);
}

/**
 * 更新頁面上所有帶有 data-i18n 屬性的元素
 */
export function updatePageTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);

        // 檢查是否有屬性翻譯
        const attrPrefix = 'data-i18n-';
        Array.from(element.attributes).forEach(attr => {
            if (attr.name.startsWith(attrPrefix)) {
                const targetAttr = attr.name.substring(attrPrefix.length);
                element.setAttribute(targetAttr, t(attr.value));
            }
        });

        // 設定文字內容
        if (translation !== key) {
            element.textContent = translation;
        }
    });

    // 更新 placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = t(key);
    });

    // 更新 title
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        element.title = t(key);
    });
}

/**
 * 監聽語言變化
 * @param {Function} callback - 回調函數
 * @returns {Function} 取消監聽函數
 */
export function onLocaleChange(callback) {
    listeners.add(callback);
    return () => listeners.delete(callback);
}

/**
 * 取得所有可用語言
 * @returns {Array<{code: string, name: string}>}
 */
export function getAvailableLocales() {
    return [
        { code: 'zh', name: '繁體中文' },
        { code: 'en', name: 'English' }
    ];
}

/**
 * 格式化複數
 * @param {string} key - 翻譯鍵（需包含 _one, _other 等後綴）
 * @param {number} count - 數量
 * @param {Object} params - 其他參數
 * @returns {string}
 */
export function plural(key, count, params = {}) {
    const suffix = count === 1 ? '_one' : '_other';
    return t(`${key}${suffix}`, { ...params, count });
}

export default {
    initI18n,
    setLocale,
    getLocale,
    t,
    tHtml,
    updatePageTranslations,
    onLocaleChange,
    getAvailableLocales,
    plural
};
