/**
 * Modal - 模態框組件
 */

import { generateId } from '../utils/helpers.js';
import { t } from '../i18n/i18n.js';

// Modal 容器
let container = null;

// 活動中的 Modal 堆疊
const modalStack = [];

/**
 * 初始化 Modal 容器
 */
function ensureContainer() {
    if (!container) {
        container = document.getElementById('modal-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'modal-container';
            container.className = 'modal-container';
            document.body.appendChild(container);
        }
    }
    return container;
}

/**
 * 建立 Modal 元素
 * @param {Object} options - Modal 選項
 * @returns {HTMLElement}
 */
function createModalElement(options) {
    const {
        id,
        title,
        content,
        footer,
        size = 'md',
        closable = true,
        closeOnBackdrop = true,
        className = ''
    } = options;

    const backdrop = document.createElement('div');
    backdrop.id = `modal-backdrop-${id}`;
    backdrop.className = 'modal-backdrop';

    const modal = document.createElement('div');
    modal.id = `modal-${id}`;
    modal.className = `modal modal--${size} ${className}`.trim();
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    if (title) {
        modal.setAttribute('aria-labelledby', `modal-title-${id}`);
    }

    // 建立內容
    let headerHtml = '';
    if (title || closable) {
        headerHtml = `
            <div class="modal__header">
                ${title ? `<h3 class="modal__title" id="modal-title-${id}">${title}</h3>` : ''}
                ${closable ? `
                    <button class="modal__close" aria-label="${t('common.close')}">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                ` : ''}
            </div>
        `;
    }

    const bodyHtml = `<div class="modal__body">${typeof content === 'string' ? content : ''}</div>`;

    let footerHtml = '';
    if (footer) {
        footerHtml = `<div class="modal__footer">${typeof footer === 'string' ? footer : ''}</div>`;
    }

    modal.innerHTML = headerHtml + bodyHtml + footerHtml;

    // 如果 content 是 DOM 元素
    if (content instanceof HTMLElement) {
        modal.querySelector('.modal__body').appendChild(content);
    }

    // 如果 footer 是 DOM 元素
    if (footer instanceof HTMLElement) {
        const footerEl = modal.querySelector('.modal__footer');
        if (footerEl) {
            footerEl.innerHTML = '';
            footerEl.appendChild(footer);
        }
    }

    // 事件綁定
    if (closable) {
        const closeBtn = modal.querySelector('.modal__close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => closeModal(id));
        }
    }

    if (closeOnBackdrop) {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                closeModal(id);
            }
        });
    }

    backdrop.appendChild(modal);
    return backdrop;
}

/**
 * 顯示 Modal
 * @param {Object} options - Modal 選項
 * @returns {Object} Modal 控制物件
 */
export function showModal(options) {
    const id = options.id || generateId('modal-');
    const mergedOptions = { ...options, id };

    ensureContainer();

    // 建立元素
    const backdrop = createModalElement(mergedOptions);
    container.appendChild(backdrop);

    // 禁用背景捲動
    if (modalStack.length === 0) {
        document.body.style.overflow = 'hidden';
    }

    // 加入堆疊
    modalStack.push({
        id,
        element: backdrop,
        options: mergedOptions
    });

    // 觸發動畫
    requestAnimationFrame(() => {
        backdrop.classList.add('modal-backdrop--visible');
        backdrop.querySelector('.modal').classList.add('modal--visible');
    });

    // 綁定 ESC 鍵
    const handleEscape = (e) => {
        if (e.key === 'Escape' && mergedOptions.closable !== false) {
            closeModal(id);
        }
    };
    document.addEventListener('keydown', handleEscape);

    // 返回控制物件
    return {
        id,
        close: () => closeModal(id),
        getElement: () => backdrop.querySelector('.modal'),
        updateContent: (content) => {
            const body = backdrop.querySelector('.modal__body');
            if (body) {
                if (typeof content === 'string') {
                    body.innerHTML = content;
                } else if (content instanceof HTMLElement) {
                    body.innerHTML = '';
                    body.appendChild(content);
                }
            }
        }
    };
}

/**
 * 關閉 Modal
 * @param {string} id - Modal ID
 */
export function closeModal(id) {
    const index = modalStack.findIndex(m => m.id === id);
    if (index === -1) return;

    const { element } = modalStack[index];
    const modal = element.querySelector('.modal');

    // 移除動畫
    modal.classList.remove('modal--visible');
    element.classList.remove('modal-backdrop--visible');

    // 移除元素
    setTimeout(() => {
        element.remove();
        modalStack.splice(index, 1);

        // 恢復背景捲動
        if (modalStack.length === 0) {
            document.body.style.overflow = '';
        }
    }, 300);
}

/**
 * 關閉所有 Modal
 */
export function closeAllModals() {
    [...modalStack].reverse().forEach(({ id }) => closeModal(id));
}

/**
 * 確認對話框
 * @param {Object|string} options - 選項或訊息
 * @returns {Promise<boolean>}
 */
export function confirm(options) {
    return new Promise((resolve) => {
        const config = typeof options === 'string'
            ? { message: options }
            : options;

        const {
            title = t('common.confirm'),
            message,
            confirmText = t('common.confirm'),
            cancelText = t('common.cancel'),
            confirmType = 'primary',
            danger = false
        } = config;

        // 建立 footer
        const footer = document.createElement('div');
        footer.className = 'modal__actions';
        footer.innerHTML = `
            <button class="btn btn--outline modal-cancel">${cancelText}</button>
            <button class="btn btn--${danger ? 'danger' : confirmType} modal-confirm">${confirmText}</button>
        `;

        const modal = showModal({
            title,
            content: `<p>${message}</p>`,
            footer,
            size: 'sm',
            closeOnBackdrop: false
        });

        const modalElement = modal.getElement();
        modalElement.querySelector('.modal-cancel').addEventListener('click', () => {
            modal.close();
            resolve(false);
        });
        modalElement.querySelector('.modal-confirm').addEventListener('click', () => {
            modal.close();
            resolve(true);
        });
    });
}

/**
 * 警告對話框
 * @param {Object|string} options - 選項或訊息
 * @returns {Promise<void>}
 */
export function alert(options) {
    return new Promise((resolve) => {
        const config = typeof options === 'string'
            ? { message: options }
            : options;

        const {
            title = '',
            message,
            okText = t('common.confirm')
        } = config;

        const footer = document.createElement('div');
        footer.className = 'modal__actions';
        footer.innerHTML = `<button class="btn btn--primary modal-ok">${okText}</button>`;

        const modal = showModal({
            title,
            content: `<p>${message}</p>`,
            footer,
            size: 'sm'
        });

        modal.getElement().querySelector('.modal-ok').addEventListener('click', () => {
            modal.close();
            resolve();
        });
    });
}

/**
 * 輸入對話框
 * @param {Object} options - 選項
 * @returns {Promise<string|null>}
 */
export function prompt(options) {
    return new Promise((resolve) => {
        const {
            title = '',
            message = '',
            defaultValue = '',
            placeholder = '',
            confirmText = t('common.confirm'),
            cancelText = t('common.cancel')
        } = options;

        const content = document.createElement('div');
        content.innerHTML = `
            ${message ? `<p>${message}</p>` : ''}
            <input type="text" class="input prompt-input" value="${defaultValue}" placeholder="${placeholder}">
        `;

        const footer = document.createElement('div');
        footer.className = 'modal__actions';
        footer.innerHTML = `
            <button class="btn btn--outline modal-cancel">${cancelText}</button>
            <button class="btn btn--primary modal-confirm">${confirmText}</button>
        `;

        const modal = showModal({
            title,
            content,
            footer,
            size: 'sm',
            closeOnBackdrop: false
        });

        const modalElement = modal.getElement();
        const input = modalElement.querySelector('.prompt-input');

        // 自動聚焦
        setTimeout(() => input.focus(), 100);

        // Enter 鍵確認
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                modal.close();
                resolve(input.value);
            }
        });

        modalElement.querySelector('.modal-cancel').addEventListener('click', () => {
            modal.close();
            resolve(null);
        });

        modalElement.querySelector('.modal-confirm').addEventListener('click', () => {
            modal.close();
            resolve(input.value);
        });
    });
}

export default {
    show: showModal,
    close: closeModal,
    closeAll: closeAllModals,
    confirm,
    alert,
    prompt
};
