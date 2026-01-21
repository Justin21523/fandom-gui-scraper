/**
 * Browse Page - 讀取 job 輸出 (manifest + jsonl.gz 預覽)
 */

import {
    listUniversalJobs,
    getUniversalJobManifest,
    listUniversalJobFiles,
    previewUniversalJobFile,
} from '../api/scraper.js';
import toast from '../components/toast.js';


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


export async function renderBrowsePage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">Browse</h1>
                    <p class="page__subtitle">瀏覽 job 輸出（manifest + data 預覽）</p>
                </div>
                <div class="flex gap-sm">
                    <button class="btn btn--ghost" id="browse-refresh">重新整理</button>
                </div>
            </div>

            <div class="grid" style="grid-template-columns: 1fr 2fr; gap: 16px;">
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">任務</h3>
                    </div>
                    <div class="card__body" id="browse-jobs">載入中...</div>
                </div>

                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">內容</h3>
                    </div>
                    <div class="card__body">
                        <div id="browse-detail" class="text-sm text-muted">選擇一個 job</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    let selectedJobId = null;
    let selectedPath = null;

    async function renderJobs() {
        const el = container.querySelector('#browse-jobs');
        try {
            const jobs = await listUniversalJobs(50);
            if (!jobs || jobs.length === 0) {
                el.innerHTML = '<div class="empty-state">暫無任務</div>';
                return;
            }
            el.innerHTML = jobs.map(j => {
                const created = new Date(j.created_at).toLocaleString('zh-TW');
                const source = j.config?.input_source || '';
                return `
                    <div class="flex items-center justify-between gap-sm mb-sm">
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
                    await renderDetail();
                });
            });
        } catch (e) {
            el.innerHTML = `<div class="text-muted">載入失敗：${escapeHtml(e.message)}</div>`;
        }
    }

    async function renderDetail() {
        const el = container.querySelector('#browse-detail');
        if (!selectedJobId) {
            el.innerHTML = '<div class="text-sm text-muted">選擇一個 job</div>';
            return;
        }

        el.innerHTML = '載入中...';
        try {
            const [manifestResp, filesResp] = await Promise.all([
                getUniversalJobManifest(selectedJobId).catch(() => null),
                listUniversalJobFiles(selectedJobId, 2000),
            ]);

            const items = filesResp.items || [];
            const files = items.filter(x => x.type === 'file');
            const manifest = manifestResp?.manifest || null;

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
                    <div class="text-xs text-muted">檔案（點選可預覽前 200 筆）</div>
                    <div class="mt-xs flex gap-sm" style="flex-wrap: wrap;">${fileButtons || '<span class="text-muted">（無資料檔）</span>'}</div>
                </div>
                <div class="mt-md">
                    <div class="text-xs text-muted">manifest.json</div>
                    <pre class="json-viewer"><code>${escapeHtml(pretty(manifest || { error: 'manifest.json not found' }))}</code></pre>
                </div>
                <div class="mt-md">
                    <div class="text-xs text-muted">預覽</div>
                    <div id="browse-preview" class="text-sm text-muted">選擇一個檔案</div>
                </div>
            `;

            el.querySelectorAll('[data-path]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    selectedPath = btn.getAttribute('data-path');
                    await renderPreview();
                    await renderDetail();
                });
            });

            await renderPreview();
        } catch (e) {
            el.innerHTML = `<div class="text-muted">載入失敗：${escapeHtml(e.message)}</div>`;
        }
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
