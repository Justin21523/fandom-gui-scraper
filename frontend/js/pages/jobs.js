/**
 * Jobs Page - 任務管理與輸出瀏覽
 */

import {
    listUniversalJobs,
    selectUniversalJob,
    cleanupUniversalJobs,
    deleteUniversalJob,
    getUniversalJobOutputStats,
    listUniversalJobFiles,
} from '../api/scraper.js';
import api from '../api/client.js';
import toast from '../components/toast.js';
import { formatNumber } from '../utils/formatters.js';


function formatBytes(bytes) {
    if (bytes == null) return '-';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let value = bytes;
    let i = 0;
    while (value >= 1024 && i < units.length - 1) {
        value /= 1024;
        i++;
    }
    return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}


async function fetchJob(jobId) {
    return api.get(`/scraper/jobs/${encodeURIComponent(jobId)}`);
}

async function fetchStats(jobId) {
    return getUniversalJobOutputStats(jobId);
}

async function fetchFiles(jobId, limit = 500) {
    return listUniversalJobFiles(jobId, limit);
}


export async function renderJobsPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">Jobs</h1>
                    <p class="page__subtitle">任務列表、輸出統計、打包下載</p>
                </div>
                <div class="flex gap-sm">
                    <button class="btn btn--ghost" id="jobs-refresh">重新整理</button>
                    <button class="btn btn--ghost" id="jobs-cleanup">清理過期</button>
                </div>
            </div>

            <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 16px;">
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">任務列表</h3>
                    </div>
                    <div class="card__body" id="jobs-list">載入中...</div>
                </div>

                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">任務詳情</h3>
                        <div class="flex gap-sm">
                            <button class="btn btn--sm btn--ghost" id="job-refresh" disabled>更新</button>
                            <button class="btn btn--sm btn--ghost" id="job-download" disabled>下載 ZIP</button>
                            <button class="btn btn--sm btn--danger" id="job-delete" disabled>刪除</button>
                        </div>
                    </div>
                    <div class="card__body" id="job-detail">
                        <div class="empty-state">選擇左側任務以查看詳情</div>
                    </div>
                </div>

                <div class="card" style="grid-column: 1 / span 2;">
                    <div class="card__header">
                        <h3 class="card__title">輸出檔案</h3>
                        <div class="flex gap-sm">
                            <label class="checkbox checkbox--sm">
                                <input type="checkbox" id="include-images" checked>
                                <span class="checkbox__mark"></span>
                                <span class="checkbox__label">包含 images/（體積大）</span>
                            </label>
                        </div>
                    </div>
                    <div class="card__body">
                        <div id="job-stats" class="text-sm text-muted">-</div>
                        <div id="job-files" class="mt-sm text-sm">-</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    let selectedJobId = null;

    async function renderJobsList() {
        const el = container.querySelector('#jobs-list');
        try {
            const jobs = await listUniversalJobs(30);
            if (!jobs || jobs.length === 0) {
                el.innerHTML = '<div class="empty-state">暫無任務</div>';
                return;
            }

            el.innerHTML = jobs.map(j => {
                const created = new Date(j.created_at).toLocaleString('zh-TW');
                const source = j.config?.input_source || '';
                const status = j.status;
                return `
                    <div class="flex items-center justify-between gap-sm mb-sm">
                        <div class="flex-1">
                            <div class="text-sm"><strong>${j.job_id}</strong> <span class="text-muted">(${status})</span></div>
                            <div class="text-xs text-muted">${created} • ${source}</div>
                        </div>
                        <button class="btn btn--sm btn--ghost" data-select="${j.job_id}">查看</button>
                    </div>
                `;
            }).join('');

            el.querySelectorAll('[data-select]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    selectedJobId = btn.getAttribute('data-select');
                    await selectUniversalJob(selectedJobId);
                    await renderJobDetail();
                });
            });
        } catch (e) {
            el.innerHTML = `<div class="text-muted">載入失敗：${e.message}</div>`;
        }
    }

    async function renderJobDetail() {
        const detail = container.querySelector('#job-detail');
        const statsEl = container.querySelector('#job-stats');
        const filesEl = container.querySelector('#job-files');
        const refreshBtn = container.querySelector('#job-refresh');
        const downloadBtn = container.querySelector('#job-download');
        const deleteBtn = container.querySelector('#job-delete');

        refreshBtn.disabled = !selectedJobId;
        downloadBtn.disabled = !selectedJobId;
        deleteBtn.disabled = !selectedJobId;

        if (!selectedJobId) return;

        try {
            const job = await fetchJob(selectedJobId);
            detail.innerHTML = `
                <div class="text-sm">
                    <div><strong>ID:</strong> ${job.job_id}</div>
                    <div><strong>Status:</strong> ${job.status}</div>
                    <div><strong>Source:</strong> ${job.config?.input_source || '-'}</div>
                    <div><strong>Created:</strong> ${new Date(job.created_at).toLocaleString('zh-TW')}</div>
                    <div><strong>Started:</strong> ${job.started_at ? new Date(job.started_at).toLocaleString('zh-TW') : '-'}</div>
                    <div><strong>Finished:</strong> ${job.finished_at ? new Date(job.finished_at).toLocaleString('zh-TW') : '-'}</div>
                    ${job.error ? `<div class="text-danger"><strong>Error:</strong> ${job.error}</div>` : ''}
                    <div class="mt-sm"><strong>Progress:</strong> ${formatNumber(job.progress?.overall_completed || 0)}</div>
                </div>
            `;

            const statResp = await fetchStats(selectedJobId);
            const s = statResp.stats;
            statsEl.innerHTML = `
                <div class="text-sm">
                    <strong>檔案數:</strong> ${formatNumber(s.total_files)} /
                    <strong>大小:</strong> ${formatBytes(s.total_bytes)}
                </div>
            `;

            const fileResp = await fetchFiles(selectedJobId, 500);
            const items = fileResp.items || [];
            const files = items.filter(x => x.type === 'file');
            filesEl.innerHTML = `
                <div class="text-xs text-muted">顯示前 ${formatNumber(items.length)} 筆（含資料夾）</div>
                <div class="mt-xs" style="max-height: 280px; overflow: auto; border-top: 1px solid var(--border-color); padding-top: 8px;">
                    ${items.map(it => {
                        const size = it.type === 'file' ? ` <span class="text-muted">(${formatBytes(it.bytes)})</span>` : '';
                        return `<div class="text-sm">${it.type === 'dir' ? '📁' : '📄'} ${it.path}${size}</div>`;
                    }).join('')}
                </div>
            `;

        } catch (e) {
            detail.innerHTML = `<div class="text-muted">載入失敗：${e.message}</div>`;
            statsEl.textContent = '-';
            filesEl.textContent = '-';
        }
    }

    container.querySelector('#jobs-refresh')?.addEventListener('click', renderJobsList);
    container.querySelector('#job-refresh')?.addEventListener('click', renderJobDetail);
    container.querySelector('#jobs-cleanup')?.addEventListener('click', async () => {
        try {
            const res = await cleanupUniversalJobs();
            toast.success(`清理完成：刪除 ${res.deleted?.length || 0} 個`);
            await renderJobsList();
            await renderJobDetail();
        } catch (e) {
            toast.error(e.message);
        }
    });

    container.querySelector('#job-download')?.addEventListener('click', async () => {
        if (!selectedJobId) return;
        const includeImages = container.querySelector('#include-images')?.checked ?? true;
        try {
            await api.download(`/scraper/jobs/${encodeURIComponent(selectedJobId)}/download`, { include_images: includeImages });
        } catch (e) {
            toast.error(e.message);
        }
    });

    container.querySelector('#job-delete')?.addEventListener('click', async () => {
        if (!selectedJobId) return;
        if (!confirm(`確定刪除 job ${selectedJobId}（含輸出檔案）？`)) return;
        try {
            await deleteUniversalJob(selectedJobId);
            toast.success('已刪除');
            selectedJobId = null;
            await renderJobsList();
            container.querySelector('#job-detail').innerHTML = '<div class="empty-state">選擇左側任務以查看詳情</div>';
            container.querySelector('#job-stats').textContent = '-';
            container.querySelector('#job-files').textContent = '-';
        } catch (e) {
            toast.error(e.message);
        }
    });

    await renderJobsList();
}

export default { render: renderJobsPage };
