/**
 * Browse Page - 讀取 job 輸出 (manifest + jsonl.gz 預覽)
 */

import {
    listUniversalJobs,
    getUniversalJobManifest,
    listUniversalJobFiles,
    previewUniversalJobFile,
    getUniversalJobWikiSummary,
    browseUniversalJobWikiTable,
    getUniversalJobWikiPage,
} from '../api/scraper.js';
import toast from '../components/toast.js';
import { getSampleRun } from '../services/demoData.js';
import { t } from '../i18n/i18n.js';
import { renderEmptyBlock, renderErrorBlock, renderLoadingBlock } from './portfolioShared.js';

const DATASETS = ['pages', 'categories', 'links', 'templates', 'images', 'revisions', 'infoboxes', 'errors', 'checkpoints'];


function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}


function pretty(obj) {
    try {
        return JSON.stringify(obj, null, 2);
    } catch {
        return String(obj);
    }
}

function readHashQuery() {
    return new URLSearchParams((window.location.hash.split('?')[1] || ''));
}

function updateHashQuery(state) {
    const params = new URLSearchParams();
    if (state.job) params.set('job', state.job);
    if (state.dataset && state.dataset !== 'pages') params.set('dataset', state.dataset);
    if (state.q) params.set('q', state.q);
    if (state.offset) params.set('offset', String(state.offset));
    if (state.limit && state.limit !== 50) params.set('limit', String(state.limit));
    const query = params.toString();
    const nextHash = `#/browse${query ? `?${query}` : ''}`;
    if (window.location.hash !== nextHash) {
        window.history.replaceState(null, '', nextHash);
    }
}

function cellValue(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return value;
}

function renderRelationList(title, rows, labelKeys) {
    if (!rows?.length) {
        return `
            <div class="relation-block">
                <strong>${escapeHtml(title)}</strong>
                <span class="text-xs text-muted">${escapeHtml(t('portfolio.browse.noRelationRows'))}</span>
            </div>
        `;
    }
    return `
        <div class="relation-block">
            <strong>${escapeHtml(title)} <span class="text-muted">(${rows.length})</span></strong>
            <div class="relation-list">
                ${rows.slice(0, 12).map(row => `
                    <span>${escapeHtml(labelKeys.map(key => row[key]).filter(Boolean).join(' · ') || JSON.stringify(row))}</span>
                `).join('')}
            </div>
        </div>
    `;
}


export async function renderBrowsePage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.browse.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.browse.subtitle'))}</p>
                </div>
                <div class="flex gap-sm">
                    <button class="btn btn--ghost" id="browse-refresh">${escapeHtml(t('common.refresh'))}</button>
                </div>
            </div>

            <div class="browse-workbench">
                <div class="card" data-tour="browse-runs">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.browse.runs'))}</h3>
                    </div>
                    <div class="card__body" id="browse-jobs">${renderLoadingBlock()}</div>
                </div>

                <div class="card" data-tour="browse-datasets">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.browse.datasetBrowser'))}</h3>
                    </div>
                    <div class="card__body">
                        <div id="browse-detail" class="text-sm text-muted">${escapeHtml(t('portfolio.browse.selectRun'))}</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    let selectedJobId = null;
    let selectedPath = null;
    let selectedDataset = 'pages';
    let useDemo = false;
    let wikiOffset = 0;
    let wikiLimit = 50;
    let wikiSearch = '';
    let selectedPageDetail = null;
    const query = readHashQuery();
    const queryJobId = query.get('job');
    selectedDataset = DATASETS.includes(query.get('dataset')) ? query.get('dataset') : 'pages';
    wikiSearch = query.get('q') || '';
    wikiOffset = Math.max(0, Number(query.get('offset')) || 0);
    wikiLimit = [25, 50, 100, 250].includes(Number(query.get('limit'))) ? Number(query.get('limit')) : 50;

    async function renderJobs() {
        const el = container.querySelector('#browse-jobs');
        try {
            const jobs = await listUniversalJobs(50);
            if (!jobs || jobs.length === 0) {
                useDemo = true;
                selectedJobId = 'demo-onepiece-action-api-001';
                el.innerHTML = renderDemoRunList();
                await renderDetail();
                return;
            }
            if (queryJobId && jobs.some(j => j.job_id === queryJobId)) {
                selectedJobId = queryJobId;
            }
            if (!selectedJobId && jobs[0]) {
                selectedJobId = jobs[0].job_id;
            }
            el.innerHTML = jobs.map(j => {
                const created = new Date(j.created_at).toLocaleString('zh-TW');
                const source = j.config?.input_source || '';
                const active = selectedJobId === j.job_id ? 'run-card--active' : '';
                return `
                    <div class="run-card ${active}">
                        <div class="flex-1">
                            <div class="text-sm"><strong>${j.job_id}</strong> <span class="text-muted">(${j.status})</span></div>
                            <div class="text-xs text-muted">${created} • ${escapeHtml(source)}</div>
                        </div>
                        <button class="btn btn--sm btn--ghost" data-select="${j.job_id}">查看</button>
                    </div>
                `;
            }).join('');

            el.querySelectorAll('[data-select]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    selectedJobId = btn.getAttribute('data-select');
                    selectedPath = null;
                    wikiOffset = 0;
                    selectedPageDetail = null;
                    updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
                    await renderDetail();
                    await renderJobs();
                });
            });
            if (selectedJobId) {
                updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
                await renderDetail();
            }
        } catch (e) {
            useDemo = true;
            selectedJobId = 'demo-onepiece-action-api-001';
            el.innerHTML = renderDemoRunList();
            await renderDetail();
        }
    }

    async function renderDetail() {
        const el = container.querySelector('#browse-detail');
        if (useDemo) {
            renderDemoDetail(el);
            return;
        }
        if (!selectedJobId) {
            el.innerHTML = '<div class="text-sm text-muted">Select a run</div>';
            return;
        }

            el.innerHTML = renderLoadingBlock();
        try {
            const [manifestResp, filesResp] = await Promise.all([
                getUniversalJobManifest(selectedJobId).catch(() => null),
                listUniversalJobFiles(selectedJobId, 2000),
            ]);

            const items = filesResp.items || [];
            const files = items.filter(x => x.type === 'file');
            const manifest = manifestResp?.manifest || null;
            const wikiDbAvailable = Boolean(manifest?.wiki_db?.path || files.some(f => f.path === 'wiki.db'));
            const wikiDbData = wikiDbAvailable ? await loadWikiDbSectionData() : null;
            const wikiDbSection = wikiDbData ? renderWikiDbSection(wikiDbData) : '';

            const dataFiles = files
                .map(f => f.path)
                .filter(p => p.endsWith('.json') || p.endsWith('.jsonl') || p.endsWith('.jsonl.gz'))
                .sort();

            const fileButtons = dataFiles.map(p => {
                const active = selectedPath === p ? 'btn--primary' : 'btn--ghost';
                return `<button class="btn btn--sm ${active}" data-path="${escapeHtml(p)}">${escapeHtml(p)}</button>`;
            }).join(' ');

            el.innerHTML = `
                <div class="text-sm">
                    <div><strong>job_id:</strong> ${selectedJobId}</div>
                    ${manifest?.wiki_url ? `<div><strong>wiki_url:</strong> ${escapeHtml(manifest.wiki_url)}</div>` : ''}
                    ${manifest?.anime_name ? `<div><strong>anime_name:</strong> ${escapeHtml(manifest.anime_name)}</div>` : ''}
                </div>
                <div class="mt-sm">
                    <div class="text-xs text-muted">${escapeHtml(t('portfolio.browse.files'))}</div>
                    <div class="mt-xs flex gap-sm" style="flex-wrap: wrap;">${fileButtons || '<span class="text-muted">（無資料檔）</span>'}</div>
                </div>
                ${wikiDbSection}
                <details class="mt-md">
                    <summary class="text-xs text-muted">manifest.json</summary>
                    <pre class="json-viewer"><code>${escapeHtml(pretty(manifest || { error: 'manifest.json not found' }))}</code></pre>
                </details>
                <div class="mt-md">
                    <div class="text-xs text-muted">${escapeHtml(t('portfolio.browse.preview'))}</div>
                    <div id="browse-preview" class="text-sm text-muted">${escapeHtml(t('portfolio.browse.fileHelp'))}</div>
                </div>
            `;

            el.querySelectorAll('[data-path]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    selectedPath = btn.getAttribute('data-path');
                    await renderPreview();
                    await renderDetail();
                });
            });
            bindWikiDbControls(el);

            await renderPreview();
        } catch (e) {
            el.innerHTML = renderErrorBlock(`${t('portfolio.browse.loadFailed')}: ${e.message}`);
            el.querySelector('[data-retry]')?.addEventListener('click', renderDetail);
        }
    }

    async function loadWikiDbSectionData() {
        try {
            const [summaryResp, tableResp] = await Promise.all([
                getUniversalJobWikiSummary(selectedJobId),
                browseUniversalJobWikiTable(selectedJobId, selectedDataset, { limit: wikiLimit, offset: wikiOffset, q: wikiSearch }),
            ]);
            return { summaryResp, tableResp };
        } catch (e) {
            return { error: e };
        }
    }

    function renderWikiDbSection({ summaryResp, tableResp, error }) {
        if (error) {
            return `<section class="mt-md">${renderErrorBlock(`${t('portfolio.browse.wikiDbUnavailable')}: ${error.message}`)}</section>`;
        }
        try {
            const counts = summaryResp.summary?.counts || {};
            const buttons = DATASETS.map(dataset => {
                const active = selectedDataset === dataset ? 'dataset-tab--active' : '';
                return `<button class="dataset-tab ${active}" data-dataset="${dataset}">
                    <span>${dataset}</span>
                    <strong>${escapeHtml(counts[dataset] || 0)}</strong>
                </button>`;
            }).join(' ');
            const rows = tableResp.items || [];
            const columns = tableResp.columns || [];
            const start = tableResp.total ? tableResp.offset + 1 : 0;
            const end = Math.min(tableResp.offset + tableResp.items.length, tableResp.total);
            const canPrev = wikiOffset > 0;
            const canNext = wikiOffset + wikiLimit < tableResp.total;
            const detail = renderPageDetail(selectedPageDetail);
            return `
                <section class="mt-md">
                    <div class="section-heading">
                        <div>
                            <div class="text-xs text-muted">${escapeHtml(t('portfolio.browse.wikiDb'))}</div>
                            <h4>${escapeHtml(t('portfolio.browse.dataset', { dataset: selectedDataset }))}</h4>
                        </div>
                        <span class="text-xs text-muted">${escapeHtml(t('portfolio.browse.matchingRows', { count: (tableResp.total || 0).toLocaleString() }))}</span>
                    </div>
                    <div class="dataset-tabs" data-tour="browse-dataset-tabs">${buttons}</div>
                    <div class="data-toolbar mt-sm" data-tour="browse-table-controls">
                        <input id="wiki-search" class="input" value="${escapeHtml(wikiSearch)}" placeholder="${escapeHtml(t('portfolio.browse.searchDataset', { dataset: selectedDataset }))}">
                        <select id="wiki-limit" class="select input" style="max-width: 100px;">
                            ${[25, 50, 100, 250].map(value => `<option value="${value}" ${wikiLimit === value ? 'selected' : ''}>${value}</option>`).join('')}
                        </select>
                        <button class="btn btn--sm btn--ghost" id="wiki-search-btn">${escapeHtml(t('common.search'))}</button>
                        <button class="btn btn--sm btn--ghost" id="wiki-clear-btn" ${wikiSearch ? '' : 'disabled'}>${escapeHtml(t('common.clear'))}</button>
                        <button class="btn btn--sm btn--ghost" id="wiki-prev" ${canPrev ? '' : 'disabled'}>${escapeHtml(t('common.previous'))}</button>
                        <button class="btn btn--sm btn--ghost" id="wiki-next" ${canNext ? '' : 'disabled'}>${escapeHtml(t('common.next'))}</button>
                        <span class="text-xs text-muted">${start}-${end} of ${tableResp.total}</span>
                    </div>
                    <div class="table-scroll mt-sm" data-tour="browse-table">
                        <table class="data-table">
                            <thead><tr>${columns.map(col => `<th>${escapeHtml(col)}</th>`).join('')}${selectedDataset === 'pages' ? '<th>Detail</th>' : ''}</tr></thead>
                            <tbody>
                                ${rows.length ? rows.map(row => `
                                    <tr>
                                        ${columns.map(col => `<td>${escapeHtml(cellValue(row[col]))}</td>`).join('')}
                                        ${selectedDataset === 'pages' ? `<td><button class="btn btn--sm btn--ghost" data-page-id="${escapeHtml(row.id)}">Open</button></td>` : ''}
                                    </tr>
                                `).join('') : `<tr><td colspan="${columns.length + (selectedDataset === 'pages' ? 1 : 0)}" class="text-muted">${escapeHtml(t('portfolio.browse.noRows'))}</td></tr>`}
                            </tbody>
                        </table>
                    </div>
                    ${detail}
                </section>
            `;
        } catch (e) {
            return `<section class="mt-md">${renderErrorBlock(`${t('portfolio.browse.wikiDbUnavailable')}: ${e.message}`)}</section>`;
        }
    }

    function renderPageDetail(detail) {
        if (!detail) return '';
        const page = detail.page || {};
        return `
            <aside class="detail-drawer mt-md">
                <div class="detail-drawer__header">
                    <div>
                        <div class="text-xs text-muted">${escapeHtml(t('portfolio.browse.selectedPageDetail'))}</div>
                        <h4>${escapeHtml(page.title || `Page ${page.id}`)}</h4>
                    </div>
                    <button class="btn btn--sm btn--ghost" id="page-detail-close">${escapeHtml(t('common.close'))}</button>
                </div>
                <div class="detail-grid">
                    <div><span>${escapeHtml(t('portfolio.browse.pageId'))}</span><strong>${escapeHtml(page.pageid || page.id || '')}</strong></div>
                    <div><span>${escapeHtml(t('portfolio.browse.namespace'))}</span><strong>${escapeHtml(page.ns ?? '')}</strong></div>
                    <div><span>${escapeHtml(t('portfolio.browse.length'))}</span><strong>${escapeHtml(page.length ?? '')}</strong></div>
                    <div><span>${escapeHtml(t('portfolio.browse.touched'))}</span><strong>${escapeHtml(page.touched || '')}</strong></div>
                </div>
                <div class="relation-grid mt-md">
                    ${renderRelationList('Categories', detail.categories, ['category_title'])}
                    ${renderRelationList('Links', detail.links, ['target_title'])}
                    ${renderRelationList('Templates', detail.templates, ['template_title'])}
                    ${renderRelationList('Images', detail.images, ['image_title'])}
                    ${renderRelationList('Infobox fields', detail.infoboxes, ['field_name', 'field_value'])}
                    ${renderRelationList('Revisions', detail.revisions, ['revid', 'user', 'timestamp'])}
                </div>
            </aside>
        `;
    }

    function bindWikiDbControls(el) {
        el.querySelectorAll('[data-dataset]').forEach(btn => {
            btn.addEventListener('click', async () => {
                selectedDataset = btn.getAttribute('data-dataset');
                wikiOffset = 0;
                selectedPageDetail = null;
                updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
                await renderDetail();
            });
        });
        el.querySelector('#wiki-search-btn')?.addEventListener('click', async () => {
            wikiSearch = el.querySelector('#wiki-search')?.value.trim() || '';
            wikiOffset = 0;
            selectedPageDetail = null;
            updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
            await renderDetail();
        });
        el.querySelector('#wiki-search')?.addEventListener('keydown', async event => {
            if (event.key === 'Enter') {
                wikiSearch = event.currentTarget.value.trim();
                wikiOffset = 0;
                selectedPageDetail = null;
                updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
                await renderDetail();
            }
        });
        el.querySelector('#wiki-limit')?.addEventListener('change', async event => {
            wikiLimit = Number(event.currentTarget.value) || 50;
            wikiOffset = 0;
            updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
            await renderDetail();
        });
        el.querySelector('#wiki-clear-btn')?.addEventListener('click', async () => {
            wikiSearch = '';
            wikiOffset = 0;
            selectedPageDetail = null;
            updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
            await renderDetail();
        });
        el.querySelector('#wiki-prev')?.addEventListener('click', async () => {
            wikiOffset = Math.max(0, wikiOffset - wikiLimit);
            updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
            await renderDetail();
        });
        el.querySelector('#wiki-next')?.addEventListener('click', async () => {
            wikiOffset += wikiLimit;
            updateHashQuery({ job: selectedJobId, dataset: selectedDataset, q: wikiSearch, offset: wikiOffset, limit: wikiLimit });
            await renderDetail();
        });
        el.querySelectorAll('[data-page-id]').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    selectedPageDetail = await getUniversalJobWikiPage(selectedJobId, Number(btn.getAttribute('data-page-id')));
                    await renderDetail();
                } catch (e) {
                    toast.error(e.message);
                }
            });
        });
        el.querySelector('#page-detail-close')?.addEventListener('click', async () => {
            selectedPageDetail = null;
            await renderDetail();
        });
    }

    function renderDemoRunList() {
        const sample = getSampleRun();
        return `
            <div class="demo-notice mb-sm"><strong>${escapeHtml(t('portfolio.browse.demoRun'))}</strong><span>${escapeHtml(t('portfolio.browse.demoNotice'))}</span></div>
            <div class="flex items-center justify-between gap-sm">
                <div class="flex-1">
                    <div class="text-sm"><strong>${escapeHtml(sample.run.id)}</strong> <span class="text-muted">(${sample.run.status})</span></div>
                    <div class="text-xs text-muted">${escapeHtml(sample.run.wikiName)} • ${escapeHtml(sample.run.normalizedBaseUrl)}</div>
                </div>
                <button class="btn btn--sm btn--primary" type="button">Viewing</button>
            </div>
        `;
    }

    function renderDemoTable(title, rows) {
        const columns = [...new Set(rows.flatMap(row => Object.keys(row)))].slice(0, 5);
        return `
            <section class="mt-md">
                <h4 class="mb-sm">${escapeHtml(title)}</h4>
                <div class="table-scroll">
                    <table class="data-table">
                        <thead><tr>${columns.map(col => `<th>${escapeHtml(col)}</th>`).join('')}</tr></thead>
                        <tbody>
                            ${rows.map(row => `
                                <tr>${columns.map(col => `<td>${escapeHtml(typeof row[col] === 'object' ? JSON.stringify(row[col]) : row[col])}</td>`).join('')}</tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </section>
        `;
    }

    function renderDemoDetail(el) {
        const sample = getSampleRun();
        el.innerHTML = `
            <div class="text-sm">
                <div><strong>run_id:</strong> ${escapeHtml(sample.run.id)}</div>
                <div><strong>wiki_url:</strong> ${escapeHtml(sample.run.normalizedBaseUrl)}</div>
                <div><strong>api_endpoint:</strong> ${escapeHtml(sample.run.apiEndpoint)}</div>
                <div><strong>mode:</strong> API-first with HTML fallback for infobox-like fields</div>
            </div>
            <div data-tour="browse-table">
            ${renderDemoTable('Pages', sample.collections.pages)}
            ${renderDemoTable('Categories', sample.collections.categories)}
            ${renderDemoTable('Links', sample.collections.links)}
            ${renderDemoTable('Templates', sample.collections.templates)}
            ${renderDemoTable('Images metadata', sample.collections.images)}
            ${renderDemoTable('Revisions metadata', sample.collections.revisions)}
            ${renderDemoTable('Infobox-like data', sample.collections.infoboxes)}
            ${renderDemoTable('Page text snippets', sample.collections.textSnippets)}
            </div>
        `;
    }

    async function renderPreview() {
        if (!selectedJobId || !selectedPath) return;
        const previewEl = container.querySelector('#browse-preview');
        if (!previewEl) return;

        previewEl.textContent = '讀取中...';
        try {
            const res = await previewUniversalJobFile(selectedJobId, selectedPath, 200);
            if (res.type === 'json') {
                previewEl.innerHTML = `<pre class="json-viewer"><code>${escapeHtml(pretty(res.data))}</code></pre>`;
                return;
            }
            previewEl.innerHTML = `<pre class="json-viewer"><code>${escapeHtml(pretty(res.items || []))}</code></pre>`;
        } catch (e) {
            previewEl.innerHTML = `<div class="text-danger">預覽失敗：${escapeHtml(e.message)}</div>`;
            toast.error(e.message);
        }
    }

    container.querySelector('#browse-refresh')?.addEventListener('click', async () => {
        await renderJobs();
        await renderDetail();
    });

    await renderJobs();
}

export default { render: renderBrowsePage };
