/**
 * Toast - 提示訊息組件
 */

import { generateId } from '../utils/helpers.js';
import { t } from '../i18n/i18n.js';

// Toast 容器
let container = null;

// 活動中的 Toast
const activeToasts = new Map();

// 預設設定
const DEFAULT_OPTIONS = {
    duration: 3000,
    position: 'top-right',
    closable: true,
    pauseOnHover: true
};

/**
 * 初始化 Toast 容器
 */
function ensureContainer() {
    if (!container) {
        container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }
    return container;
}

/**
 * 建立 Toast 元素
 * @param {Object} options - Toast 選項
 * @returns {HTMLElement}
 */
function createToastElement(options) {
    const { id, type, title, message, closable, icon } = options;

    const toast = document.createElement('div');
    toast.id = `toast-${id}`;
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');

    // 圖示
    const iconMap = {
        success: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
        error: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
        warning: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
        info: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
    };

    toast.innerHTML = `
        <div class="toast__icon">
            ${icon || iconMap[type] || iconMap.info}
        </div>
        <div class="toast__content">
            ${title ? `<div class="toast__title">${title}</div>` : ''}
            <div class="toast__message">${message}</div>
        </div>
        ${closable ? `
            <button class="toast__close" aria-label="${t('common.close')}">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        ` : ''}
    `;

    return toast;
}

/**
 * 顯示 Toast
 * @param {Object|string} options - Toast 選項或訊息
 * @returns {string} Toast ID
 */
export function showToast(options) {
    // 支援簡易呼叫
    if (typeof options === 'string') {
        options = { message: options };
    }

    const id = options.id || generateId('toast-');
    const mergedOptions = { ...DEFAULT_OPTIONS, ...options, id };
    const { duration, pauseOnHover, closable } = mergedOptions;

    ensureContainer();

    // 建立元素
    const toast = createToastElement(mergedOptions);

    // 綁定事件
    if (closable) {
        const closeBtn = toast.querySelector('.toast__close');
        closeBtn.addEventListener('click', () => hideToast(id));
    }

    // 暫停計時
    let timeoutId = null;
    let remainingTime = duration;
    let startTime = null;

    const startTimer = () => {
        if (duration > 0) {
            startTime = Date.now();
            timeoutId = setTimeout(() => hideToast(id), remainingTime);
        }
    };

    const pauseTimer = () => {
        if (timeoutId) {
            clearTimeout(timeoutId);
            remainingTime -= Date.now() - startTime;
        }
    };

    if (pauseOnHover) {
        toast.addEventListener('mouseenter', pauseTimer);
        toast.addEventListener('mouseleave', startTimer);
    }

    // 儲存 Toast 資訊
    activeToasts.set(id, { element: toast, timeoutId });

    // 加入容器
    container.appendChild(toast);

    // 觸發動畫
    requestAnimationFrame(() => {
        toast.classList.add('toast--visible');
    });

    // 啟動計時
    startTimer();

    return id;
}

/**
 * 隱藏 Toast
 * @param {string} id - Toast ID
 */
export function hideToast(id) {
    const toast = activeToasts.get(id);
    if (!toast) return;

    const { element, timeoutId } = toast;

    // 清除計時器
    if (timeoutId) {
        clearTimeout(timeoutId);
    }

    // 移除動畫
    element.classList.remove('toast--visible');
    element.classList.add('toast--hiding');

    // 移除元素
    setTimeout(() => {
        element.remove();
        activeToasts.delete(id);
    }, 300);
}

/**
 * 隱藏所有 Toast
 */
export function hideAllToasts() {
    activeToasts.forEach((_, id) => hideToast(id));
}

/**
 * 成功提示
 * @param {string} message - 訊息
 * @param {Object} options - 選項
 */
export function success(message, options = {}) {
    return showToast({ ...options, type: 'success', message });
}

/**
 * 錯誤提示
 * @param {string} message - 訊息
 * @param {Object} options - 選項
 */
export function error(message, options = {}) {
    return showToast({ ...options, type: 'error', message, duration: 5000 });
}

/**
 * 警告提示
 * @param {string} message - 訊息
 * @param {Object} options - 選項
 */
export function warning(message, options = {}) {
    return showToast({ ...options, type: 'warning', message });
}

/**
 * 資訊提示
 * @param {string} message - 訊息
 * @param {Object} options - 選項
 */
export function info(message, options = {}) {
    return showToast({ ...options, type: 'info', message });
}

export default {
    show: showToast,
    hide: hideToast,
    hideAll: hideAllToasts,
    success,
    error,
    warning,
    info
};
