/**
 * Characters Page - 角色列表頁面
 */

import { t } from '../i18n/i18n.js';
import {
    getCharacters,
    deleteCharacter,
    deleteCharacters,
    exportCharacters,
    getAnimeList
} from '../api/characters.js';
import characterStore, {
    setPage,
    setPageSize,
    setViewMode,
    updateFilters,
    toggleSort,
    toggleSelect,
    toggleSelectAll,
    clearSelection
} from '../stores/characterStore.js';
import { formatDate, formatQualityScore, truncate } from '../utils/formatters.js';
import { debounce } from '../utils/helpers.js';
import { renderPagination } from '../components/pagination.js';
import modal from '../components/modal.js';
import toast from '../components/toast.js';
import router from '../router.js';

/**
 * 渲染角色列表頁面
 * @param {HTMLElement} container - 容器元素
 * @param {Object} route - 路由資訊
 */
export async function renderCharactersPage(container, route) {
    // 從 URL 參數更新篩選條件
    if (route.query.search) {
        updateFilters({ search: route.query.search });
    }

    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('characters.title')}</h1>
                </div>
                <div class="page__actions">
                    <button class="btn btn--outline" id="export-btn" disabled>
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        ${t('common.export')}
                    </button>
                    <button class="btn btn--danger" id="batch-delete-btn" disabled>
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
                        ${t('characters.batchDelete')}
                    </button>
                </div>
            </div>

            <!-- 工具列 -->
            <div class="toolbar card mb-lg">
                <div class="toolbar__left">
                    <div class="input-group" style="width: 300px;">
                        <span class="input-group__prefix">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                            </svg>
                        </span>
                        <input type="text"
                               class="input"
                               id="search-input"
                               placeholder="${t('characters.search')}"
                               value="${characterStore.getState().filters.search || ''}">
                    </div>

                    <select class="select" id="anime-filter" style="width: 200px;">
                        <option value="">${t('characters.filterByAnime')}</option>
                    </select>
                </div>

                <div class="toolbar__right">
                    <div class="btn-group" id="view-mode-group">
                        <button class="btn btn--icon" data-view="table" title="${t('characters.tableView')}">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm-1 9v-1h5v2H5a1 1 0 01-1-1zm7 1h4a1 1 0 001-1v-1h-5v2zm0-4h5V8h-5v2zM9 8H4v2h5V8z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                        <button class="btn btn--icon" data-view="card" title="${t('characters.cardView')}">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- 選取資訊 -->
            <div class="selection-bar card mb-md hidden" id="selection-bar">
                <span id="selection-count"></span>
                <button class="btn btn--sm btn--ghost" id="clear-selection">${t('common.cancel')}</button>
            </div>

            <!-- 內容區域 -->
            <div class="card">
                <div class="card__body p-0" id="characters-content">
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <p>${t('common.loading')}</p>
                    </div>
                </div>
            </div>

            <!-- 分頁 -->
            <div class="mt-lg" id="pagination-container"></div>
        </div>
    `;

    // 綁定事件
    bindCharactersEvents(container);

    // 載入動畫列表
    loadAnimeFilter(container);

    // 載入角色資料
    await loadCharacters(container);

    // 訂閱狀態變化
    characterStore.subscribe(() => {
        updateSelectionUI(container);
    }, ['selectedIds', 'selectAll']);
}

/**
 * 綁定事件
 * @param {HTMLElement} container - 容器元素
 */
function bindCharactersEvents(container) {
    // 搜尋
    const searchInput = container.querySelector('#search-input');
    const handleSearch = debounce((value) => {
        updateFilters({ search: value });
        loadCharacters(container);
    }, 300);
    searchInput?.addEventListener('input', (e) => handleSearch(e.target.value));

    // 動畫篩選
    const animeFilter = container.querySelector('#anime-filter');
    animeFilter?.addEventListener('change', (e) => {
        updateFilters({ anime: e.target.value });
        loadCharacters(container);
    });

    // 視圖模式
    const viewModeGroup = container.querySelector('#view-mode-group');
    viewModeGroup?.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.view;
            setViewMode(mode);
            updateViewModeUI(container);
            renderCharactersList(container);
        });
    });

    // 批次刪除
    container.querySelector('#batch-delete-btn')?.addEventListener('click', async () => {
        const { selectedIds } = characterStore.getState();
        if (selectedIds.size === 0) return;

        const confirmed = await modal.confirm({
            title: t('characters.batchDelete'),
            message: t('characters.deleteConfirm'),
            danger: true
        });

        if (confirmed) {
            try {
                await deleteCharacters([...selectedIds]);
                toast.success(t('characters.deleteSuccess'));
                clearSelection();
                loadCharacters(container);
            } catch (error) {
                toast.error(error.message);
            }
        }
    });

    // 匯出
    container.querySelector('#export-btn')?.addEventListener('click', async () => {
        const { selectedIds } = characterStore.getState();
        try {
            await exportCharacters({ ids: [...selectedIds] });
            toast.success(t('common.success'));
        } catch (error) {
            toast.error(error.message);
        }
    });

    // 清除選取
    container.querySelector('#clear-selection')?.addEventListener('click', () => {
        clearSelection();
    });

    // 初始化視圖模式 UI
    updateViewModeUI(container);
}

/**
 * 載入動畫篩選器
 * @param {HTMLElement} container - 容器元素
 */
async function loadAnimeFilter(container) {
    try {
        const animeList = await getAnimeList();
        const select = container.querySelector('#anime-filter');
        if (select && animeList) {
            animeList.forEach(anime => {
                const option = document.createElement('option');
                option.value = anime;
                option.textContent = anime;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load anime list:', error);
    }
}

/**
 * 載入角色資料
 * @param {HTMLElement} container - 容器元素
 */
async function loadCharacters(container) {
    try {
        await getCharacters();
        renderCharactersList(container);
        renderPaginationUI(container);
    } catch (error) {
        console.error('Failed to load characters:', error);
        const content = container.querySelector('#characters-content');
        if (content) {
            content.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                    <p class="empty-state__title">${t('common.error')}</p>
                    <p class="empty-state__description">${error.message}</p>
                </div>
            `;
        }
    }
}

/**
 * 渲染角色列表
 * @param {HTMLElement} container - 容器元素
 */
function renderCharactersList(container) {
    const { characters, viewMode, selectedIds } = characterStore.getState();
    const content = container.querySelector('#characters-content');

    if (!content) return;

    if (!characters || characters.length === 0) {
        content.innerHTML = `
            <div class="empty-state">
                <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                </svg>
                <p class="empty-state__title">${t('characters.noCharacters')}</p>
            </div>
        `;
        return;
    }

    if (viewMode === 'card') {
        renderCardView(content, characters, selectedIds);
    } else {
        renderTableView(content, characters, selectedIds);
    }

    // 綁定項目事件
    bindItemEvents(container);
}

/**
 * 渲染表格視圖
 * @param {HTMLElement} content - 內容元素
 * @param {Array} characters - 角色列表
 * @param {Set} selectedIds - 選取的 ID
 */
function renderTableView(content, characters, selectedIds) {
    const { sortBy, sortOrder, selectAll } = characterStore.getState();

    const sortIcon = (field) => {
        if (sortBy !== field) return '';
        return sortOrder === 'asc'
            ? '<svg viewBox="0 0 20 20" fill="currentColor" class="sort-icon"><path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd"/></svg>'
            : '<svg viewBox="0 0 20 20" fill="currentColor" class="sort-icon"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>';
    };

    content.innerHTML = `
        <table class="table table--hover">
            <thead>
                <tr>
                    <th class="table__check">
                        <label class="checkbox">
                            <input type="checkbox" id="select-all" ${selectAll ? 'checked' : ''}>
                            <span class="checkbox__mark"></span>
                        </label>
                    </th>
                    <th class="table__sortable" data-sort="name">
                        ${t('characters.name')} ${sortIcon('name')}
                    </th>
                    <th class="table__sortable" data-sort="anime">
                        ${t('characters.anime')} ${sortIcon('anime')}
                    </th>
                    <th>${t('characters.description')}</th>
                    <th class="table__sortable" data-sort="quality_score">
                        ${t('characters.quality')} ${sortIcon('quality_score')}
                    </th>
                    <th class="table__sortable" data-sort="updated_at">
                        ${t('characters.updatedAt')} ${sortIcon('updated_at')}
                    </th>
                    <th>${t('common.actions')}</th>
                </tr>
            </thead>
            <tbody>
                ${characters.map(char => {
                    const id = char.id || char._id;
                    const quality = formatQualityScore(char.quality_score);
                    return `
                        <tr data-id="${id}" class="${selectedIds.has(id) ? 'table__row--selected' : ''}">
                            <td class="table__check">
                                <label class="checkbox">
                                    <input type="checkbox" class="row-checkbox" ${selectedIds.has(id) ? 'checked' : ''}>
                                    <span class="checkbox__mark"></span>
                                </label>
                            </td>
                            <td>
                                <div class="flex items-center gap-sm">
                                    <div class="avatar avatar--sm">
                                        ${char.image
                                            ? `<img src="${char.image}" alt="${char.name}">`
                                            : `<span>${char.name.charAt(0)}</span>`
                                        }
                                    </div>
                                    <a href="#/characters/${id}" class="link">${char.name}</a>
                                </div>
                            </td>
                            <td>${char.anime || '-'}</td>
                            <td class="text-muted">${truncate(char.description || '-', 50)}</td>
                            <td><span class="badge ${quality.className}">${quality.text}</span></td>
                            <td class="text-muted">${formatDate(char.updated_at, { format: 'relative' })}</td>
                            <td>
                                <div class="flex gap-xs">
                                    <button class="btn btn--icon btn--sm btn--ghost" data-action="view" title="${t('common.edit')}">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                                        </svg>
                                    </button>
                                    <button class="btn btn--icon btn--sm btn--ghost btn--danger" data-action="delete" title="${t('common.delete')}">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
}

/**
 * 渲染卡片視圖
 * @param {HTMLElement} content - 內容元素
 * @param {Array} characters - 角色列表
 * @param {Set} selectedIds - 選取的 ID
 */
function renderCardView(content, characters, selectedIds) {
    content.innerHTML = `
        <div class="character-grid">
            ${characters.map(char => {
                const id = char.id || char._id;
                const quality = formatQualityScore(char.quality_score);
                return `
                    <div class="character-card ${selectedIds.has(id) ? 'character-card--selected' : ''}" data-id="${id}">
                        <div class="character-card__checkbox">
                            <label class="checkbox">
                                <input type="checkbox" class="row-checkbox" ${selectedIds.has(id) ? 'checked' : ''}>
                                <span class="checkbox__mark"></span>
                            </label>
                        </div>
                        <div class="character-card__image">
                            ${char.image
                                ? `<img src="${char.image}" alt="${char.name}">`
                                : `<div class="character-card__placeholder">${char.name.charAt(0)}</div>`
                            }
                        </div>
                        <div class="character-card__content">
                            <h3 class="character-card__name">
                                <a href="#/characters/${id}">${char.name}</a>
                            </h3>
                            <p class="character-card__anime">${char.anime || '-'}</p>
                            <div class="character-card__footer">
                                <span class="badge ${quality.className}">${quality.text}</span>
                                <div class="character-card__actions">
                                    <button class="btn btn--icon btn--sm btn--ghost" data-action="view">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                                        </svg>
                                    </button>
                                    <button class="btn btn--icon btn--sm btn--ghost btn--danger" data-action="delete">
                                        <svg viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * 綁定項目事件
 * @param {HTMLElement} container - 容器元素
 */
function bindItemEvents(container) {
    // 全選
    container.querySelector('#select-all')?.addEventListener('change', () => {
        toggleSelectAll();
        renderCharactersList(container);
    });

    // 排序
    container.querySelectorAll('[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            toggleSort(th.dataset.sort);
            loadCharacters(container);
        });
    });

    // 行選取
    container.querySelectorAll('.row-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            const row = checkbox.closest('[data-id]');
            if (row) {
                toggleSelect(row.dataset.id);
                renderCharactersList(container);
            }
        });
    });

    // 行操作
    container.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const row = btn.closest('[data-id]');
            const id = row?.dataset.id;
            const action = btn.dataset.action;

            if (!id) return;

            if (action === 'view') {
                router.navigate(`/characters/${id}`);
            } else if (action === 'delete') {
                const confirmed = await modal.confirm({
                    title: t('common.delete'),
                    message: t('characters.deleteConfirm'),
                    danger: true
                });

                if (confirmed) {
                    try {
                        await deleteCharacter(id);
                        toast.success(t('characters.deleteSuccess'));
                        loadCharacters(container);
                    } catch (error) {
                        toast.error(error.message);
                    }
                }
            }
        });
    });
}

/**
 * 渲染分頁 UI
 * @param {HTMLElement} container - 容器元素
 */
function renderPaginationUI(container) {
    const { currentPage, totalPages, totalCount, pageSize } = characterStore.getState();
    const paginationContainer = container.querySelector('#pagination-container');

    if (!paginationContainer) return;

    paginationContainer.innerHTML = '';
    paginationContainer.appendChild(renderPagination({
        currentPage,
        totalPages,
        totalItems: totalCount,
        pageSize,
        onPageChange: (page) => {
            setPage(page);
            loadCharacters(container);
        },
        onPageSizeChange: (size) => {
            setPageSize(size);
            loadCharacters(container);
        }
    }));
}

/**
 * 更新視圖模式 UI
 * @param {HTMLElement} container - 容器元素
 */
function updateViewModeUI(container) {
    const { viewMode } = characterStore.getState();
    container.querySelectorAll('[data-view]').forEach(btn => {
        btn.classList.toggle('btn--primary', btn.dataset.view === viewMode);
    });
}

/**
 * 更新選取 UI
 * @param {HTMLElement} container - 容器元素
 */
function updateSelectionUI(container) {
    const { selectedIds } = characterStore.getState();
    const count = selectedIds.size;

    const selectionBar = container.querySelector('#selection-bar');
    const selectionCount = container.querySelector('#selection-count');
    const exportBtn = container.querySelector('#export-btn');
    const deleteBtn = container.querySelector('#batch-delete-btn');

    if (selectionBar) {
        selectionBar.classList.toggle('hidden', count === 0);
    }
    if (selectionCount) {
        selectionCount.textContent = t('characters.selected', { count });
    }
    if (exportBtn) {
        exportBtn.disabled = count === 0;
    }
    if (deleteBtn) {
        deleteBtn.disabled = count === 0;
    }
}

export default { render: renderCharactersPage };
