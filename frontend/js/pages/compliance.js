import { loadDemoSnapshot } from '../services/demoData.js';
import { t } from '../i18n/i18n.js';
import { escapeHtml, renderDemoNotice, renderLoadingBlock, renderMetricCards } from './portfolioShared.js';

function levelClass(level) {
  return {
    info: 'badge--primary',
    warning: 'badge--warning',
    error: 'badge--error',
  }[String(level).toLowerCase()] || 'badge--primary';
}

export async function renderCompliancePage(container) {
  container.innerHTML = `<div class="page animate-fadeIn portfolio-page">${renderLoadingBlock()}</div>`;
  const snapshot = await loadDemoSnapshot();
  const run = snapshot.run;
  const events = snapshot.live?.campaignEvents?.length
    ? snapshot.live.campaignEvents.map(event => ({
      time: event.time,
      level: event.status === 'failed' ? 'error' : event.status === 'warning' || event.status === 'stopped' ? 'warning' : 'info',
      event: `${event.stage}${event.wiki_url ? ` · ${event.wiki_url}` : ''}`,
      action: event.message,
    }))
    : snapshot.complianceEvents;

  container.innerHTML = `
        <div class="page animate-fadeIn portfolio-page">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.compliance.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.compliance.subtitle'))}</p>
                </div>
            </div>

            ${renderDemoNotice(snapshot)}

            ${renderMetricCards([
    { label: t('portfolio.compliance.robots'), value: 'obeyed', help: 'Checked before crawling selected paths' },
    { label: t('portfolio.compliance.rateLimit'), value: '30/min', help: 'Polite crawling default' },
    { label: t('portfolio.compliance.retryStyle'), value: 'backoff', help: 'No forced access on restrictions' },
    { label: t('portfolio.compliance.userAgent'), value: 'descriptive', help: 'Identifies portfolio scraper' },
  ])}

            <section class="card mt-lg" data-tour="compliance-log">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.compliance.events'))}</h3>
                </div>
                <div class="card__body p-0">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Level</th>
                                <th>Event</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${events.map(event => `
                                <tr>
                                    <td>${escapeHtml(event.time)}</td>
                                    <td><span class="badge ${levelClass(event.level)}">${escapeHtml(event.level)}</span></td>
                                    <td>${escapeHtml(event.event)}</td>
                                    <td>${escapeHtml(event.action)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="card mt-lg">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.compliance.nonGoals'))}</h3>
                </div>
                <div class="card__body">
                    <div class="feature-list">
                        <div><strong>No CAPTCHA solving</strong><span>Restricted pages are recorded and skipped or the run is stopped.</span></div>
                        <div><strong>No proxy pools</strong><span>The crawler slows down instead of rotating identity.</span></div>
                        <div><strong>No browser fingerprint spoofing</strong><span>Playwright is only a JavaScript rendering fallback when allowed.</span></div>
                        <div><strong>No login or paywall handling</strong><span>The platform targets public MediaWiki/Fandom content.</span></div>
                    </div>
                    <pre class="code-block mt-md"><code>${escapeHtml(run.userAgent)}</code></pre>
                </div>
            </section>
        </div>
    `;
}

export default { render: renderCompliancePage };
