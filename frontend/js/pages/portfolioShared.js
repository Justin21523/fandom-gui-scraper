import { t } from '../i18n/i18n.js';

export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function statusBadge(status) {
  const normalized = String(status || 'info').toLowerCase();
  const tone = {
    passed: 'success',
    ready: 'success',
    completed: 'success',
    finished: 'success',
    skipped: 'success',
    partial: 'warning',
    stopped: 'warning',
    running: 'primary',
    warning: 'warning',
    planned: 'warning',
    failed: 'error',
    error: 'error',
  }[normalized] || 'primary';

  return `<span class="badge badge--${tone}">${escapeHtml(t(`status.${normalized}`) === `status.${normalized}` ? status : t(`status.${normalized}`))}</span>`;
}

export function renderDemoNotice(snapshot) {
  const label = snapshot.mode === 'live' ? t('portfolio.notice.live') : t('portfolio.notice.demo');
  return `
        <div class="demo-notice">
            <strong>${label}</strong>
            <span>${escapeHtml(snapshot.demoNotice)}</span>
        </div>
    `;
}

export function renderLoadingBlock(message = t('common.loading')) {
  return `
    <div class="loading-panel">
      <div class="loading-spinner"></div>
      <strong>${escapeHtml(message)}</strong>
      <span>${escapeHtml(t('portfolio.loadingPreparing'))}</span>
    </div>
  `;
}

export function renderErrorBlock(message, retryLabel = t('common.refresh')) {
  return `
    <div class="state-panel state-panel--error">
      <strong>${escapeHtml(t('common.error'))}</strong>
      <span>${escapeHtml(message)}</span>
      <button class="btn btn--sm btn--ghost" data-retry>${escapeHtml(retryLabel)}</button>
    </div>
  `;
}

export function renderEmptyBlock(message = t('common.noData')) {
  return `
    <div class="state-panel">
      <strong>${escapeHtml(t('common.noData'))}</strong>
      <span>${escapeHtml(message)}</span>
    </div>
  `;
}

export function renderMetricCards(metrics) {
  return `
        <div class="stats-grid">
            ${metrics.map(metric => `
                <div class="stat-card">
                    <div class="stat-card__content">
                        <div class="stat-card__label">${escapeHtml(metric.label)}</div>
                        <div class="stat-card__value">${escapeHtml(metric.value)}</div>
                        ${metric.help ? `<div class="text-xs text-muted">${escapeHtml(metric.help)}</div>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

export function renderKeyValueList(items) {
  return `
        <dl class="kv-list">
            ${items.map(([key, value]) => `
                <div>
                    <dt>${escapeHtml(key)}</dt>
                    <dd>${escapeHtml(value)}</dd>
                </div>
            `).join('')}
        </dl>
    `;
}
