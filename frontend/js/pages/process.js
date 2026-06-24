import { loadDemoSnapshot } from '../services/demoData.js';
import { t } from '../i18n/i18n.js';
import { escapeHtml, renderDemoNotice, renderKeyValueList, renderLoadingBlock, statusBadge } from './portfolioShared.js';

export async function renderProcessPage(container) {
  container.innerHTML = `<div class="page animate-fadeIn portfolio-page">${renderLoadingBlock()}</div>`;
  const snapshot = await loadDemoSnapshot();
  const run = snapshot.run;
  const liveEvents = snapshot.live?.campaignEvents || [];
  const timeline = liveEvents.length
    ? liveEvents.map(event => ({
      title: event.stage,
      status: event.status,
      method: event.wiki_url || event.campaign_id || 'campaign',
      durationMs: '',
      request: event.job_id || event.campaign_id || '',
      result: event.message || '',
    }))
    : snapshot.pipelineSteps;

  container.innerHTML = `
        <div class="page animate-fadeIn portfolio-page">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.process.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.process.subtitle'))}</p>
                </div>
                <a class="btn btn--primary" href="#/scraper">${escapeHtml(t('portfolio.process.configureJob'))}</a>
            </div>

            ${renderDemoNotice(snapshot)}

            <div class="grid grid-cols-2 gap-lg portfolio-grid">
                <section class="card">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.process.runContext'))}</h3>
                    </div>
                    <div class="card__body">
                        ${renderKeyValueList([
    ['Input', run.input],
    ['Normalized base URL', run.normalizedBaseUrl],
    ['Detected API endpoint', run.apiEndpoint],
    ['Status', run.status],
    ['Checkpoint cursor', run.checkpoint.lastCursor],
  ])}
                    </div>
                </section>

                <section class="card">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.process.apiPolicy'))}</h3>
                    </div>
                    <div class="card__body">
                        <p class="m-0">${escapeHtml(t('portfolio.process.apiPolicyText'))}</p>
                    </div>
                </section>
            </div>

            <section class="card mt-lg" data-tour="process-timeline">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.process.timeline'))}</h3>
                </div>
                <div class="card__body">
                    <div class="timeline">
                        ${timeline.map((step, index) => `
                            <article class="timeline-item">
                                <div class="timeline-index">${index + 1}</div>
                                <div class="timeline-content">
                                    <div class="flex items-center justify-between gap-md">
                                        <h4>${escapeHtml(step.title)}</h4>
                                        ${statusBadge(step.status)}
                                    </div>
                                    <div class="text-sm text-muted">${escapeHtml(step.method)}${step.durationMs !== '' ? ` · ${escapeHtml(step.durationMs)} ms` : ''}</div>
                                    <pre class="code-block"><code>${escapeHtml(step.request)}</code></pre>
                                    <p>${escapeHtml(step.result)}</p>
                                </div>
                            </article>
                        `).join('')}
                    </div>
                </div>
            </section>
        </div>
    `;
}

export default { render: renderProcessPage };
