/**
 * Pagination - 分頁組件
 */

import { t } from '../i18n/i18n.js';

/**
 * 渲染分頁組件
 * @param {Object} options - 分頁選項
 * @returns {HTMLElement}
 */
export function renderPagination(options) {
    const {
        currentPage = 1,
        totalPages = 1,
        totalItems = 0,
        pageSize = 20,
        pageSizes = [10, 20, 50, 100],
        showTotal = true,
        showPageSize = true,
        showQuickJump = false,
        maxButtons = 7,
        onPageChange,
        onPageSizeChange
    } = options;

    const container = document.createElement('div');
    container.className = 'pagination';

    // 總數資訊
    if (showTotal) {
        const totalInfo = document.createElement('span');
        totalInfo.className = 'pagination__total';
        totalInfo.textContent = `${t('pagination.of')} ${totalItems} ${t('pagination.items')}`;
        container.appendChild(totalInfo);
    }

    // 每頁數量選擇
    if (showPageSize) {
        const pageSizeWrapper = document.createElement('div');
        pageSizeWrapper.className = 'pagination__page-size';

        const select = document.createElement('select');
        select.className = 'select select--sm';
        pageSizes.forEach(size => {
            const option = document.createElement('option');
            option.value = size;
            option.textContent = `${size} / ${t('pagination.page')}`;
            option.selected = size === pageSize;
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            if (onPageSizeChange) {
                onPageSizeChange(parseInt(e.target.value, 10));
            }
        });

        pageSizeWrapper.appendChild(select);
        container.appendChild(pageSizeWrapper);
    }

    // 分頁按鈕
    const buttons = document.createElement('div');
    buttons.className = 'pagination__buttons';

    // 計算顯示的頁碼範圍
    const pages = calculatePageRange(currentPage, totalPages, maxButtons);

    // 上一頁按鈕
    const prevBtn = createPageButton({
        text: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>`,
        title: t('pagination.prev'),
        disabled: currentPage <= 1,
        onClick: () => onPageChange && onPageChange(currentPage - 1)
    });
    buttons.appendChild(prevBtn);

    // 第一頁
    if (pages[0] > 1) {
        buttons.appendChild(createPageButton({
            text: '1',
            onClick: () => onPageChange && onPageChange(1)
        }));

        if (pages[0] > 2) {
            buttons.appendChild(createEllipsis());
        }
    }

    // 頁碼按鈕
    pages.forEach(page => {
        buttons.appendChild(createPageButton({
            text: String(page),
            active: page === currentPage,
            onClick: () => onPageChange && onPageChange(page)
        }));
    });

    // 最後一頁
    if (pages[pages.length - 1] < totalPages) {
        if (pages[pages.length - 1] < totalPages - 1) {
            buttons.appendChild(createEllipsis());
        }

        buttons.appendChild(createPageButton({
            text: String(totalPages),
            onClick: () => onPageChange && onPageChange(totalPages)
        }));
    }

    // 下一頁按鈕
    const nextBtn = createPageButton({
        text: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>`,
        title: t('pagination.next'),
        disabled: currentPage >= totalPages,
        onClick: () => onPageChange && onPageChange(currentPage + 1)
    });
    buttons.appendChild(nextBtn);

    container.appendChild(buttons);

    // 快速跳轉
    if (showQuickJump && totalPages > maxButtons) {
        const jumpWrapper = document.createElement('div');
        jumpWrapper.className = 'pagination__jump';

        const label = document.createElement('span');
        label.textContent = t('pagination.page');
        jumpWrapper.appendChild(label);

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'input input--sm';
        input.min = '1';
        input.max = String(totalPages);
        input.value = currentPage;
        input.style.width = '60px';

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const page = parseInt(input.value, 10);
                if (page >= 1 && page <= totalPages && onPageChange) {
                    onPageChange(page);
                }
            }
        });

        jumpWrapper.appendChild(input);
        container.appendChild(jumpWrapper);
    }

    return container;
}

/**
 * 計算頁碼範圍
 * @param {number} current - 當前頁
 * @param {number} total - 總頁數
 * @param {number} maxButtons - 最大按鈕數
 * @returns {number[]}
 */
function calculatePageRange(current, total, maxButtons) {
    if (total <= maxButtons) {
        return Array.from({ length: total }, (_, i) => i + 1);
    }

    const sideButtons = Math.floor((maxButtons - 3) / 2);
    let start = Math.max(2, current - sideButtons);
    let end = Math.min(total - 1, current + sideButtons);

    // 調整範圍
    if (current - sideButtons < 2) {
        end = Math.min(total - 1, maxButtons - 2);
    }
    if (current + sideButtons > total - 1) {
        start = Math.max(2, total - maxButtons + 3);
    }

    const pages = [];
    for (let i = start; i <= end; i++) {
        pages.push(i);
    }

    return pages;
}

/**
 * 建立分頁按鈕
 * @param {Object} options - 按鈕選項
 * @returns {HTMLElement}
 */
function createPageButton(options) {
    const { text, title, active = false, disabled = false, onClick } = options;

    const btn = document.createElement('button');
    btn.className = `pagination__btn ${active ? 'pagination__btn--active' : ''} ${disabled ? 'pagination__btn--disabled' : ''}`;
    btn.innerHTML = text;
    btn.disabled = disabled;
    if (title) btn.title = title;

    if (!disabled && onClick) {
        btn.addEventListener('click', onClick);
    }

    return btn;
}

/**
 * 建立省略號
 * @returns {HTMLElement}
 */
function createEllipsis() {
    const span = document.createElement('span');
    span.className = 'pagination__ellipsis';
    span.textContent = '...';
    return span;
}

export default { render: renderPagination };
