import { loadDemoSnapshot } from '../services/demoData.js';
import { t } from '../i18n/i18n.js';
import { escapeHtml, renderDemoNotice, renderKeyValueList, renderLoadingBlock, statusBadge } from './portfolioShared.js';
import { buildUniversalJobWikiExportUrl, getUniversalJobWikiSummary, listUniversalJobs } from '../api/scraper.js';

export async function renderExportPage(container) {
  container.innerHTML = `<div class="page animate-fadeIn portfolio-page">${renderLoadingBlock()}</div>`;
  const snapshot = await loadDemoSnapshot();
  const run = snapshot.run;
  let liveJob = null;
  let liveSummary = null;
  let notice = renderDemoNotice(snapshot);
  try {
    const jobs = await listUniversalJobs(20);
    liveJob = jobs?.find(item => item.status === 'finished') || jobs?.[0] || null;
    if (liveJob) {
      liveSummary = await getUniversalJobWikiSummary(liveJob.job_id);
      notice = `<div class="demo-notice mb-md"><strong>${escapeHtml(t('portfolio.export.title'))}</strong><span>${escapeHtml(t('portfolio.export.liveNotice', { id: liveJob.job_id }))}</span></div>`;
    }
  } catch {
    liveJob = null;
  }
  const datasets = ['pages', 'categories', 'links', 'templates', 'images', 'revisions', 'infoboxes'];
  const parquetAvailable = Boolean(liveSummary?.summary?.capabilities?.parquet_available);

  container.innerHTML = `
        <div class="page animate-fadeIn portfolio-page">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.export.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.export.subtitle'))}</p>
                </div>
                <a class="btn btn--outline" href="#/browse">${escapeHtml(t('portfolio.actions.browse'))}</a>
            </div>

            ${notice}

            <section class="card">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.export.manifest'))}</h3>
                </div>
                <div class="card__body">
                    ${renderKeyValueList([
    ['Run ID', run.id],
    ['Wiki', run.wikiName],
    ['Rows represented', run.counts.pages + run.counts.categories + run.counts.links + run.counts.templates],
    ['Checkpoint resumable', run.checkpoint.resumable ? 'yes' : 'no'],
  ])}
                </div>
            </section>

            <section class="card mt-lg" data-tour="export-center">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(liveJob ? t('portfolio.export.datasets') : t('portfolio.export.artifacts'))}</h3>
                </div>
                <div class="card__body p-0 table-scroll">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>${escapeHtml(t('portfolio.export.dataset'))}</th>
                                <th>${escapeHtml(t('portfolio.export.rows'))}</th>
                                <th>CSV</th>
                                <th>JSON</th>
                                <th>Parquet</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${liveJob ? datasets.map(dataset => `
                                <tr>
                                    <td>${escapeHtml(dataset)}</td>
                                    <td>${escapeHtml(liveSummary?.summary?.counts?.[dataset] || 0)}</td>
                                    <td><a class="btn btn--sm btn--ghost" href="${buildUniversalJobWikiExportUrl(liveJob.job_id, dataset, 'csv')}">${escapeHtml(t('common.download'))}</a></td>
                                    <td><a class="btn btn--sm btn--ghost" href="${buildUniversalJobWikiExportUrl(liveJob.job_id, dataset, 'json')}">${escapeHtml(t('common.download'))}</a></td>
                                    <td>${parquetAvailable
    ? `<a class="btn btn--sm btn--ghost" href="${buildUniversalJobWikiExportUrl(liveJob.job_id, dataset, 'parquet')}">${escapeHtml(t('common.download'))}</a>`
    : `<span class="badge badge--warning">${escapeHtml(t('portfolio.export.parquetRequired'))}</span>`}</td>
                                </tr>
                            `).join('') : snapshot.exports.map(item => `
                                <tr>
                                    <td>${escapeHtml(item.format)}</td>
                                    <td>${escapeHtml(item.rows)}</td>
                                    <td><code>${escapeHtml(item.file)}</code></td>
                                    <td>${statusBadge(item.status)}</td>
                                    <td>${item.format === 'Parquet' ? statusBadge(item.status) : '<span class="text-muted">n/a</span>'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="card mt-lg">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.export.useCases'))}</h3>
                </div>
                <div class="card__body">
                    <div class="feature-list">
                        <div><strong>SQLite</strong><span>${escapeHtml(t('portfolio.export.sqliteUse'))}</span></div>
                        <div><strong>JSON/JSONL</strong><span>${escapeHtml(t('portfolio.export.jsonUse'))}</span></div>
                        <div><strong>CSV</strong><span>${escapeHtml(t('portfolio.export.csvUse'))}</span></div>
                        <div><strong>Parquet</strong><span>${escapeHtml(t('portfolio.export.parquetUse'))}</span></div>
                    </div>
                </div>
            </section>
        </div>
    `;
}

export default { render: renderExportPage };
