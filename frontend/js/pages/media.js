/**
 * Media Page - 媒體庫頁面
 */

import { t } from '../i18n/i18n.js';
import { getCharacters } from '../api/characters.js';
import toast from '../components/toast.js';

// 狀態
let mediaState = {
    images: [],
    filteredImages: [],
    selectedImages: new Set(),
    currentIndex: 0,
    viewMode: 'medium', // small, medium, large
    filter: 'all', // all, character, other
    sortBy: 'date', // date, name, character
    lightboxOpen: false,
    slideshowRunning: false,
    slideshowInterval: null
};

/**
 * 渲染媒體庫頁面
 * @param {HTMLElement} container - 容器元素
 */
export async function renderMediaPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('media.title')}</h1>
                    <p class="page__subtitle">管理和瀏覽角色圖片</p>
                </div>
                <div class="page__actions">
                    <button class="btn btn--outline" id="select-all-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                        </svg>
                        ${t('media.selectAll')}
                    </button>
                    <button class="btn btn--outline" id="download-selected-btn" disabled>
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        ${t('media.downloadSelected')} (<span id="selected-count">0</span>)
                    </button>
                    <button class="btn btn--primary" id="slideshow-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                        </svg>
                        ${t('media.slideshow')}
                    </button>
                </div>
            </div>

            <!-- 篩選和視圖控制 -->
            <div class="media-toolbar card mb-lg">
                <div class="media-toolbar__left">
                    <div class="form-group form-group--inline">
                        <label class="form-label">篩選：</label>
                        <select class="select" id="media-filter">
                            <option value="all">全部圖片</option>
                            <option value="portrait">人物肖像</option>
                            <option value="scene">場景</option>
                        </select>
                    </div>
                    <div class="form-group form-group--inline">
                        <label class="form-label">排序：</label>
                        <select class="select" id="media-sort">
                            <option value="date">日期</option>
                            <option value="name">名稱</option>
                            <option value="character">角色</option>
                            <option value="anime">動畫</option>
                        </select>
                    </div>
                    <div class="form-group form-group--inline">
                        <input type="text" class="input" id="media-search" placeholder="搜尋圖片...">
                    </div>
                </div>
                <div class="media-toolbar__right">
                    <div class="view-toggle">
                        <button class="view-toggle__btn" data-view="small" title="小圖示">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 2V5h1v1H5zM3 12a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm2 2v-1h1v1H5zM11 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zm2 2V5h1v1h-1zM11 12a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3zm2 2v-1h1v1h-1z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                        <button class="view-toggle__btn view-toggle__btn--active" data-view="medium" title="中圖示">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                        <button class="view-toggle__btn" data-view="large" title="大圖示">
                            <svg viewBox="0 0 20 20" fill="currentColor">
                                <path d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm9 4a1 1 0 10-2 0v2.586l-.707-.707a1 1 0 00-1.414 1.414l2.5 2.5a1 1 0 001.414 0l2.5-2.5a1 1 0 00-1.414-1.414l-.879.879V7z"/>
                            </svg>
                        </button>
                    </div>
                    <span class="media-count" id="media-count">載入中...</span>
                </div>
            </div>

            <!-- 圖片網格 -->
            <div class="media-grid media-grid--medium" id="media-grid">
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <p>載入圖片中...</p>
                </div>
            </div>

            <!-- 空狀態 -->
            <div class="empty-state" id="media-empty" style="display: none;">
                <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                </svg>
                <h2 class="empty-state__title">沒有找到圖片</h2>
                <p class="empty-state__description">目前沒有符合條件的圖片</p>
            </div>
        </div>

        <!-- Lightbox -->
        <div class="lightbox" id="lightbox" style="display: none;">
            <div class="lightbox__overlay"></div>
            <button class="lightbox__close" id="lightbox-close">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
            <button class="lightbox__nav lightbox__nav--prev" id="lightbox-prev">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
            </button>
            <button class="lightbox__nav lightbox__nav--next" id="lightbox-next">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
            </button>
            <div class="lightbox__content">
                <img class="lightbox__image" id="lightbox-image" src="" alt="">
            </div>
            <div class="lightbox__info" id="lightbox-info">
                <h3 class="lightbox__title" id="lightbox-title"></h3>
                <p class="lightbox__meta" id="lightbox-meta"></p>
            </div>
            <div class="lightbox__controls">
                <button class="lightbox__btn" id="lightbox-zoom-out" title="縮小">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                        <path fill-rule="evenodd" d="M5 8a1 1 0 011-1h4a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <button class="lightbox__btn" id="lightbox-zoom-in" title="放大">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
                        <path fill-rule="evenodd" d="M8 5a1 1 0 011 1v1h1a1 1 0 110 2H9v1a1 1 0 11-2 0V9H6a1 1 0 110-2h1V6a1 1 0 011-1z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <button class="lightbox__btn" id="lightbox-fullscreen" title="全螢幕">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M3 4a1 1 0 011-1h4a1 1 0 010 2H5v3a1 1 0 01-2 0V4zM16 4a1 1 0 00-1-1h-4a1 1 0 100 2h3v3a1 1 0 102 0V4zM3 16a1 1 0 001 1h4a1 1 0 100-2H5v-3a1 1 0 10-2 0v4zM17 16a1 1 0 01-1 1h-4a1 1 0 110-2h3v-3a1 1 0 112 0v4z"/>
                    </svg>
                </button>
                <button class="lightbox__btn" id="lightbox-download" title="下載">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <button class="lightbox__btn" id="lightbox-slideshow" title="幻燈片">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
            <div class="lightbox__counter" id="lightbox-counter">1 / 1</div>
        </div>
    `;

    // 重置狀態
    mediaState.selectedImages.clear();
    mediaState.lightboxOpen = false;
    stopSlideshow();

    // 綁定事件
    bindMediaEvents(container);

    // 載入資料
    await loadMediaData(container);
}

/**
 * 綁定媒體頁面事件
 */
function bindMediaEvents(container) {
    // 視圖切換
    container.querySelectorAll('.view-toggle__btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            setViewMode(container, view);
        });
    });

    // 篩選
    container.querySelector('#media-filter')?.addEventListener('change', (e) => {
        mediaState.filter = e.target.value;
        filterAndRenderImages(container);
    });

    // 排序
    container.querySelector('#media-sort')?.addEventListener('change', (e) => {
        mediaState.sortBy = e.target.value;
        filterAndRenderImages(container);
    });

    // 搜尋
    let searchTimeout;
    container.querySelector('#media-search')?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            filterAndRenderImages(container, e.target.value);
        }, 300);
    });

    // 全選
    container.querySelector('#select-all-btn')?.addEventListener('click', () => {
        toggleSelectAll(container);
    });

    // 下載選中
    container.querySelector('#download-selected-btn')?.addEventListener('click', () => {
        downloadSelectedImages();
    });

    // 幻燈片
    container.querySelector('#slideshow-btn')?.addEventListener('click', () => {
        if (mediaState.filteredImages.length > 0) {
            openLightbox(0);
            startSlideshow();
        }
    });

    // Lightbox 事件
    bindLightboxEvents();
}

/**
 * 綁定 Lightbox 事件
 */
function bindLightboxEvents() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox) return;

    // 關閉
    lightbox.querySelector('#lightbox-close')?.addEventListener('click', closeLightbox);
    lightbox.querySelector('.lightbox__overlay')?.addEventListener('click', closeLightbox);

    // 導航
    lightbox.querySelector('#lightbox-prev')?.addEventListener('click', () => navigateLightbox(-1));
    lightbox.querySelector('#lightbox-next')?.addEventListener('click', () => navigateLightbox(1));

    // 縮放
    let zoomLevel = 1;
    lightbox.querySelector('#lightbox-zoom-in')?.addEventListener('click', () => {
        zoomLevel = Math.min(zoomLevel + 0.25, 3);
        setImageZoom(zoomLevel);
    });
    lightbox.querySelector('#lightbox-zoom-out')?.addEventListener('click', () => {
        zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
        setImageZoom(zoomLevel);
    });

    // 全螢幕
    lightbox.querySelector('#lightbox-fullscreen')?.addEventListener('click', toggleFullscreen);

    // 下載
    lightbox.querySelector('#lightbox-download')?.addEventListener('click', () => {
        const currentImage = mediaState.filteredImages[mediaState.currentIndex];
        if (currentImage) {
            downloadImage(currentImage.url, currentImage.name);
        }
    });

    // 幻燈片
    lightbox.querySelector('#lightbox-slideshow')?.addEventListener('click', () => {
        if (mediaState.slideshowRunning) {
            stopSlideshow();
        } else {
            startSlideshow();
        }
    });

    // 鍵盤事件
    document.addEventListener('keydown', handleLightboxKeydown);
}

/**
 * 處理 Lightbox 鍵盤事件
 */
function handleLightboxKeydown(e) {
    if (!mediaState.lightboxOpen) return;

    switch (e.key) {
        case 'Escape':
            closeLightbox();
            break;
        case 'ArrowLeft':
            navigateLightbox(-1);
            break;
        case 'ArrowRight':
            navigateLightbox(1);
            break;
        case ' ':
            e.preventDefault();
            if (mediaState.slideshowRunning) {
                stopSlideshow();
            } else {
                startSlideshow();
            }
            break;
    }
}

/**
 * 載入媒體資料
 */
async function loadMediaData(container) {
    try {
        const result = await getCharacters({ pageSize: 1000 });
        const characters = result.items || [];

        // 提取所有圖片
        const images = [];
        characters.forEach(char => {
            // 主圖
            if (char.image) {
                images.push({
                    id: `${char.id}-main`,
                    url: char.image,
                    name: char.name,
                    characterId: char.id,
                    characterName: char.name,
                    anime: char.anime || '未知動畫',
                    type: 'portrait',
                    date: char.updated_at || char.created_at || new Date().toISOString()
                });
            }

            // 額外圖片
            if (char.images && Array.isArray(char.images)) {
                char.images.forEach((img, idx) => {
                    const url = typeof img === 'string' ? img : img.url;
                    if (url) {
                        images.push({
                            id: `${char.id}-${idx}`,
                            url: url,
                            name: `${char.name} - ${idx + 1}`,
                            characterId: char.id,
                            characterName: char.name,
                            anime: char.anime || '未知動畫',
                            type: typeof img === 'object' && img.type ? img.type : 'other',
                            date: char.updated_at || char.created_at || new Date().toISOString()
                        });
                    }
                });
            }
        });

        mediaState.images = images;
        filterAndRenderImages(container);

    } catch (error) {
        console.error('Failed to load media:', error);
        const grid = container.querySelector('#media-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                    <h2 class="empty-state__title">載入失敗</h2>
                    <p class="empty-state__description">${error.message}</p>
                </div>
            `;
        }
    }
}

/**
 * 篩選並渲染圖片
 */
function filterAndRenderImages(container, searchQuery = '') {
    let filtered = [...mediaState.images];

    // 篩選類型
    if (mediaState.filter !== 'all') {
        filtered = filtered.filter(img => img.type === mediaState.filter);
    }

    // 搜尋
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(img =>
            img.name.toLowerCase().includes(query) ||
            img.characterName.toLowerCase().includes(query) ||
            img.anime.toLowerCase().includes(query)
        );
    }

    // 排序
    switch (mediaState.sortBy) {
        case 'date':
            filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
            break;
        case 'name':
            filtered.sort((a, b) => a.name.localeCompare(b.name, 'zh-TW'));
            break;
        case 'character':
            filtered.sort((a, b) => a.characterName.localeCompare(b.characterName, 'zh-TW'));
            break;
        case 'anime':
            filtered.sort((a, b) => a.anime.localeCompare(b.anime, 'zh-TW'));
            break;
    }

    mediaState.filteredImages = filtered;
    renderMediaGrid(container);
}

/**
 * 渲染圖片網格
 */
function renderMediaGrid(container) {
    const grid = container.querySelector('#media-grid');
    const empty = container.querySelector('#media-empty');
    const countEl = container.querySelector('#media-count');

    if (!grid) return;

    countEl.textContent = `${mediaState.filteredImages.length} 張圖片`;

    if (mediaState.filteredImages.length === 0) {
        grid.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    grid.style.display = '';
    empty.style.display = 'none';

    grid.innerHTML = mediaState.filteredImages.map((img, index) => `
        <div class="media-item ${mediaState.selectedImages.has(img.id) ? 'media-item--selected' : ''}"
             data-id="${img.id}" data-index="${index}">
            <div class="media-item__checkbox">
                <input type="checkbox" ${mediaState.selectedImages.has(img.id) ? 'checked' : ''}>
            </div>
            <div class="media-item__image-wrapper">
                <img class="media-item__image"
                     src="${img.url}"
                     alt="${img.name}"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23e5e7eb%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%239ca3af%22 font-size=%2212%22>載入失敗</text></svg>'">
            </div>
            <div class="media-item__overlay">
                <button class="media-item__action" data-action="view" title="檢視">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                        <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <button class="media-item__action" data-action="download" title="下載">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
                <a href="#/characters/${img.characterId}" class="media-item__action" title="查看角色">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                    </svg>
                </a>
            </div>
            <div class="media-item__info">
                <div class="media-item__name" title="${img.name}">${img.name}</div>
                <div class="media-item__meta">${img.anime}</div>
            </div>
        </div>
    `).join('');

    // 綁定圖片事件
    grid.querySelectorAll('.media-item').forEach(item => {
        // 選擇
        item.querySelector('.media-item__checkbox input')?.addEventListener('change', (e) => {
            e.stopPropagation();
            const id = item.dataset.id;
            if (e.target.checked) {
                mediaState.selectedImages.add(id);
                item.classList.add('media-item--selected');
            } else {
                mediaState.selectedImages.delete(id);
                item.classList.remove('media-item--selected');
            }
            updateSelectedCount();
        });

        // 點擊圖片開啟 Lightbox
        item.querySelector('.media-item__image-wrapper')?.addEventListener('click', () => {
            openLightbox(parseInt(item.dataset.index));
        });

        // 操作按鈕
        item.querySelectorAll('.media-item__action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const index = parseInt(item.dataset.index);
                const img = mediaState.filteredImages[index];

                if (action === 'view') {
                    openLightbox(index);
                } else if (action === 'download' && img) {
                    downloadImage(img.url, img.name);
                }
            });
        });
    });
}

/**
 * 設定視圖模式
 */
function setViewMode(container, mode) {
    mediaState.viewMode = mode;

    const grid = container.querySelector('#media-grid');
    if (grid) {
        grid.className = `media-grid media-grid--${mode}`;
    }

    container.querySelectorAll('.view-toggle__btn').forEach(btn => {
        btn.classList.toggle('view-toggle__btn--active', btn.dataset.view === mode);
    });
}

/**
 * 切換全選
 */
function toggleSelectAll(container) {
    const allSelected = mediaState.selectedImages.size === mediaState.filteredImages.length;

    if (allSelected) {
        mediaState.selectedImages.clear();
    } else {
        mediaState.filteredImages.forEach(img => {
            mediaState.selectedImages.add(img.id);
        });
    }

    renderMediaGrid(container);
    updateSelectedCount();
}

/**
 * 更新選中數量
 */
function updateSelectedCount() {
    const countEl = document.getElementById('selected-count');
    const downloadBtn = document.getElementById('download-selected-btn');

    if (countEl) {
        countEl.textContent = mediaState.selectedImages.size;
    }

    if (downloadBtn) {
        downloadBtn.disabled = mediaState.selectedImages.size === 0;
    }
}

/**
 * 下載選中的圖片
 */
async function downloadSelectedImages() {
    const selected = mediaState.filteredImages.filter(img =>
        mediaState.selectedImages.has(img.id)
    );

    if (selected.length === 0) {
        toast.warning('請先選擇要下載的圖片');
        return;
    }

    toast.info(`開始下載 ${selected.length} 張圖片...`);

    for (const img of selected) {
        await downloadImage(img.url, img.name);
        // 延遲以避免過快下載
        await new Promise(resolve => setTimeout(resolve, 200));
    }

    toast.success('下載完成');
}

/**
 * 下載單張圖片
 */
async function downloadImage(url, filename) {
    try {
        const response = await fetch(url);
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = `${filename}.${getImageExtension(url)}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(blobUrl);
    } catch (error) {
        console.error('Download failed:', error);
        // 退回直接連結
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.target = '_blank';
        link.click();
    }
}

/**
 * 取得圖片副檔名
 */
function getImageExtension(url) {
    const match = url.match(/\.(jpg|jpeg|png|gif|webp|svg)/i);
    return match ? match[1].toLowerCase() : 'jpg';
}

/**
 * 開啟 Lightbox
 */
function openLightbox(index) {
    mediaState.currentIndex = index;
    mediaState.lightboxOpen = true;

    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.style.display = 'flex';
        updateLightboxImage();
    }

    document.body.style.overflow = 'hidden';
}

/**
 * 關閉 Lightbox
 */
function closeLightbox() {
    mediaState.lightboxOpen = false;
    stopSlideshow();

    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.style.display = 'none';
    }

    document.body.style.overflow = '';
}

/**
 * 更新 Lightbox 圖片
 */
function updateLightboxImage() {
    const img = mediaState.filteredImages[mediaState.currentIndex];
    if (!img) return;

    const imageEl = document.getElementById('lightbox-image');
    const titleEl = document.getElementById('lightbox-title');
    const metaEl = document.getElementById('lightbox-meta');
    const counterEl = document.getElementById('lightbox-counter');

    if (imageEl) {
        imageEl.src = img.url;
        imageEl.alt = img.name;
        imageEl.style.transform = 'scale(1)';
    }

    if (titleEl) {
        titleEl.textContent = img.name;
    }

    if (metaEl) {
        metaEl.textContent = `${img.anime} • ${new Date(img.date).toLocaleDateString('zh-TW')}`;
    }

    if (counterEl) {
        counterEl.textContent = `${mediaState.currentIndex + 1} / ${mediaState.filteredImages.length}`;
    }
}

/**
 * 導航 Lightbox
 */
function navigateLightbox(direction) {
    const total = mediaState.filteredImages.length;
    mediaState.currentIndex = (mediaState.currentIndex + direction + total) % total;
    updateLightboxImage();
}

/**
 * 設定圖片縮放
 */
function setImageZoom(level) {
    const imageEl = document.getElementById('lightbox-image');
    if (imageEl) {
        imageEl.style.transform = `scale(${level})`;
    }
}

/**
 * 切換全螢幕
 */
function toggleFullscreen() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox) return;

    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        lightbox.requestFullscreen();
    }
}

/**
 * 開始幻燈片
 */
function startSlideshow() {
    if (mediaState.slideshowRunning) return;

    mediaState.slideshowRunning = true;
    const btn = document.getElementById('lightbox-slideshow');
    if (btn) {
        btn.classList.add('lightbox__btn--active');
        btn.innerHTML = `
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
        `;
    }

    mediaState.slideshowInterval = setInterval(() => {
        navigateLightbox(1);
    }, 3000);
}

/**
 * 停止幻燈片
 */
function stopSlideshow() {
    mediaState.slideshowRunning = false;

    if (mediaState.slideshowInterval) {
        clearInterval(mediaState.slideshowInterval);
        mediaState.slideshowInterval = null;
    }

    const btn = document.getElementById('lightbox-slideshow');
    if (btn) {
        btn.classList.remove('lightbox__btn--active');
        btn.innerHTML = `
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
            </svg>
        `;
    }
}

export default { render: renderMediaPage };
