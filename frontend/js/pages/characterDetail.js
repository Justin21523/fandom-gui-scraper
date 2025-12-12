/**
 * Character Detail Page - 角色詳情頁面
 */

import { t } from '../i18n/i18n.js';
import { getCharacter, updateCharacter, deleteCharacter } from '../api/characters.js';
import { authStore } from '../stores/authStore.js';
import { showModal, closeModal } from '../components/modal.js';
import toast from '../components/toast.js';

/**
 * 渲染角色詳情頁面
 * @param {HTMLElement} container - 容器元素
 * @param {Object} route - 路由資訊
 */
export async function renderCharacterDetailPage(container, route) {
    const { id } = route.params;

    // 載入中
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p>載入角色資料...</p>
            </div>
        </div>
    `;

    try {
        const character = await getCharacter(id);
        renderCharacterContent(container, character);
    } catch (error) {
        console.error('Failed to load character:', error);
        container.innerHTML = `
            <div class="page animate-fadeIn">
                <div class="page__header">
                    <a href="#/characters" class="btn btn--ghost">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
                        </svg>
                        返回列表
                    </a>
                </div>
                <div class="card">
                    <div class="card__body">
                        <div class="empty-state">
                            <svg class="empty-state__icon" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                            </svg>
                            <h2 class="empty-state__title">無法載入角色</h2>
                            <p class="empty-state__description">${error.message || '角色不存在或已被刪除'}</p>
                            <a href="#/characters" class="btn btn--primary mt-lg">返回角色列表</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * 渲染角色內容
 */
function renderCharacterContent(container, character) {
    const { isAuthenticated } = authStore.getState();

    // 處理屬性
    const attributes = character.attributes || {};
    const relationships = character.relationships || [];
    const images = character.images || [];
    const tags = character.tags || [];

    container.innerHTML = `
        <div class="page animate-fadeIn character-detail-page">
            <!-- 頁面標題列 -->
            <div class="page__header">
                <a href="#/characters" class="btn btn--ghost">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                        <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
                    </svg>
                    返回列表
                </a>
                <div class="page__actions">
                    ${isAuthenticated ? `
                        <button class="btn btn--outline" id="edit-character-btn">
                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                            </svg>
                            編輯
                        </button>
                        <button class="btn btn--danger" id="delete-character-btn">
                            <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                            </svg>
                            刪除
                        </button>
                    ` : ''}
                </div>
            </div>

            <!-- 主要內容 -->
            <div class="character-detail">
                <!-- 左側：圖片區 -->
                <div class="character-detail__sidebar">
                    <div class="character-detail__image-card card">
                        <div class="character-detail__main-image">
                            <img src="${character.image || 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23e5e7eb%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%239ca3af%22 font-size=%2212%22>無圖片</text></svg>'}"
                                 alt="${character.name}"
                                 id="main-character-image">
                        </div>
                        ${images.length > 0 ? `
                            <div class="character-detail__gallery">
                                <div class="character-gallery">
                                    ${[character.image, ...images.map(img => typeof img === 'string' ? img : img.url)].filter(Boolean).map((img, idx) => `
                                        <div class="character-gallery__item ${idx === 0 ? 'character-gallery__item--active' : ''}"
                                             data-src="${img}">
                                            <img src="${img}" alt="${character.name} - ${idx + 1}">
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- 品質分數 -->
                    <div class="card mt-lg">
                        <div class="card__header">
                            <h3 class="card__title">品質評分</h3>
                        </div>
                        <div class="card__body">
                            <div class="quality-score">
                                <div class="quality-score__ring" style="--score: ${character.quality_score || 0}">
                                    <span class="quality-score__value">${character.quality_score || 0}</span>
                                </div>
                                <div class="quality-score__label">${getQualityLabel(character.quality_score)}</div>
                            </div>
                        </div>
                    </div>

                    <!-- 標籤 -->
                    ${tags.length > 0 ? `
                        <div class="card mt-lg">
                            <div class="card__header">
                                <h3 class="card__title">標籤</h3>
                            </div>
                            <div class="card__body">
                                <div class="tag-list">
                                    ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <!-- 右側：資訊區 -->
                <div class="character-detail__main">
                    <!-- 基本資訊 -->
                    <div class="card">
                        <div class="card__header">
                            <h2 class="card__title character-name">${character.name}</h2>
                            ${character.name_ja ? `<span class="character-name-ja">${character.name_ja}</span>` : ''}
                        </div>
                        <div class="card__body">
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-item__label">動畫</span>
                                    <span class="info-item__value">${character.anime || '-'}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-item__label">來源</span>
                                    <span class="info-item__value">
                                        ${character.source_url
                                            ? `<a href="${character.source_url}" target="_blank" rel="noopener">${new URL(character.source_url).hostname}</a>`
                                            : '-'
                                        }
                                    </span>
                                </div>
                                <div class="info-item">
                                    <span class="info-item__label">建立時間</span>
                                    <span class="info-item__value">${formatDate(character.created_at)}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-item__label">更新時間</span>
                                    <span class="info-item__value">${formatDate(character.updated_at)}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 描述 -->
                    ${character.description ? `
                        <div class="card mt-lg">
                            <div class="card__header">
                                <h3 class="card__title">角色介紹</h3>
                            </div>
                            <div class="card__body">
                                <div class="character-description">
                                    ${formatDescription(character.description)}
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 屬性 -->
                    ${Object.keys(attributes).length > 0 ? `
                        <div class="card mt-lg">
                            <div class="card__header">
                                <h3 class="card__title">角色屬性</h3>
                            </div>
                            <div class="card__body">
                                <div class="attributes-grid">
                                    ${Object.entries(attributes).map(([key, value]) => `
                                        <div class="attribute-item">
                                            <span class="attribute-item__label">${formatAttributeKey(key)}</span>
                                            <span class="attribute-item__value">${formatAttributeValue(value)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 關係 -->
                    ${relationships.length > 0 ? `
                        <div class="card mt-lg">
                            <div class="card__header">
                                <h3 class="card__title">人物關係</h3>
                            </div>
                            <div class="card__body">
                                <div class="relationships-list">
                                    ${relationships.map(rel => `
                                        <div class="relationship-item">
                                            <div class="relationship-item__icon">
                                                ${getRelationshipIcon(rel.type)}
                                            </div>
                                            <div class="relationship-item__content">
                                                <span class="relationship-item__name">${rel.name}</span>
                                                <span class="relationship-item__type">${rel.type || '關係'}</span>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 原始資料（可展開） -->
                    <details class="card mt-lg">
                        <summary class="card__header" style="cursor: pointer;">
                            <h3 class="card__title">原始資料 (JSON)</h3>
                        </summary>
                        <div class="card__body">
                            <pre class="json-viewer"><code>${JSON.stringify(character, null, 2)}</code></pre>
                        </div>
                    </details>
                </div>
            </div>
        </div>
    `;

    // 綁定事件
    bindCharacterDetailEvents(container, character);
}

/**
 * 綁定角色詳情頁面事件
 */
function bindCharacterDetailEvents(container, character) {
    // 圖片切換
    container.querySelectorAll('.character-gallery__item').forEach(item => {
        item.addEventListener('click', () => {
            const src = item.dataset.src;
            const mainImage = document.getElementById('main-character-image');
            if (mainImage && src) {
                mainImage.src = src;
                container.querySelectorAll('.character-gallery__item').forEach(i =>
                    i.classList.remove('character-gallery__item--active')
                );
                item.classList.add('character-gallery__item--active');
            }
        });
    });

    // 主圖點擊放大
    container.querySelector('.character-detail__main-image img')?.addEventListener('click', (e) => {
        showImageModal(e.target.src, character.name);
    });

    // 編輯按鈕
    container.querySelector('#edit-character-btn')?.addEventListener('click', () => {
        showEditModal(container, character);
    });

    // 刪除按鈕
    container.querySelector('#delete-character-btn')?.addEventListener('click', () => {
        showDeleteConfirm(character);
    });
}

/**
 * 顯示圖片模態框
 */
function showImageModal(src, alt) {
    const modalContent = `
        <div class="image-modal">
            <img src="${src}" alt="${alt}" style="max-width: 100%; max-height: 80vh; object-fit: contain;">
        </div>
    `;

    showModal({
        title: alt,
        content: modalContent,
        size: 'large',
        showCancel: false,
        confirmText: '關閉'
    });
}

/**
 * 顯示編輯模態框
 */
function showEditModal(container, character) {
    const modalContent = `
        <form id="edit-character-form" class="form">
            <div class="form-group">
                <label class="form-label">名稱</label>
                <input type="text" class="input" name="name" value="${character.name || ''}" required>
            </div>
            <div class="form-group">
                <label class="form-label">日文名</label>
                <input type="text" class="input" name="name_ja" value="${character.name_ja || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">動畫</label>
                <input type="text" class="input" name="anime" value="${character.anime || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">描述</label>
                <textarea class="input" name="description" rows="5">${character.description || ''}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">圖片 URL</label>
                <input type="url" class="input" name="image" value="${character.image || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">標籤（以逗號分隔）</label>
                <input type="text" class="input" name="tags" value="${(character.tags || []).join(', ')}">
            </div>
        </form>
    `;

    showModal({
        title: '編輯角色',
        content: modalContent,
        confirmText: '儲存',
        onConfirm: async () => {
            const form = document.getElementById('edit-character-form');
            const formData = new FormData(form);

            const updatedData = {
                name: formData.get('name'),
                name_ja: formData.get('name_ja') || null,
                anime: formData.get('anime') || null,
                description: formData.get('description') || null,
                image: formData.get('image') || null,
                tags: formData.get('tags')
                    ? formData.get('tags').split(',').map(t => t.trim()).filter(Boolean)
                    : []
            };

            try {
                const updated = await updateCharacter(character.id, updatedData);
                toast.success('角色已更新');
                closeModal();
                renderCharacterContent(container, updated);
            } catch (error) {
                toast.error(`更新失敗: ${error.message}`);
            }
        }
    });
}

/**
 * 顯示刪除確認
 */
function showDeleteConfirm(character) {
    showModal({
        title: '確認刪除',
        content: `
            <p>確定要刪除角色「<strong>${character.name}</strong>」嗎？</p>
            <p class="text-muted mt-md">此操作無法復原。</p>
        `,
        confirmText: '刪除',
        confirmClass: 'btn--danger',
        onConfirm: async () => {
            try {
                await deleteCharacter(character.id);
                toast.success('角色已刪除');
                closeModal();
                window.location.hash = '#/characters';
            } catch (error) {
                toast.error(`刪除失敗: ${error.message}`);
            }
        }
    });
}

/**
 * 取得品質標籤
 */
function getQualityLabel(score) {
    if (score >= 81) return '優秀';
    if (score >= 61) return '良好';
    if (score >= 41) return '普通';
    if (score >= 21) return '較差';
    return '很差';
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString('zh-TW', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

/**
 * 格式化描述
 */
function formatDescription(desc) {
    if (!desc) return '';
    return desc
        .split('\n')
        .map(p => p.trim())
        .filter(Boolean)
        .map(p => `<p>${p}</p>`)
        .join('');
}

/**
 * 格式化屬性鍵
 */
function formatAttributeKey(key) {
    const keyMap = {
        'age': '年齡',
        'gender': '性別',
        'height': '身高',
        'weight': '體重',
        'birthday': '生日',
        'blood_type': '血型',
        'occupation': '職業',
        'affiliation': '所屬',
        'voice_actor': '聲優',
        'first_appearance': '初次登場',
        'status': '狀態'
    };
    return keyMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * 格式化屬性值
 */
function formatAttributeValue(value) {
    if (value === null || value === undefined) return '-';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}

/**
 * 取得關係圖示
 */
function getRelationshipIcon(type) {
    const iconMap = {
        '家人': '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>',
        '朋友': '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/></svg>',
        '敵人': '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clip-rule="evenodd"/></svg>',
        '戀人': '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/></svg>'
    };

    return iconMap[type] || '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>';
}

export default { render: renderCharacterDetailPage };
