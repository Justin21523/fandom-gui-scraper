import { getCampaignEvents, listCampaignPresets, listCampaigns, runCampaign } from '../api/scraper.js';
import toast from '../components/toast.js';
import { t } from '../i18n/i18n.js';
import { escapeHtml, renderEmptyBlock, renderErrorBlock, renderLoadingBlock, renderMetricCards, statusBadge } from './portfolioShared.js';

const DATASET_KEYS = ['pages', 'categories', 'links', 'templates', 'images', 'revisions', 'infoboxes', 'errors'];

const FALLBACK_PRESETS = [
    {
        id: 'offline-portfolio-smoke',
        label: '快速離線展示',
        mode: 'sample',
        campaign_id: 'portfolio-smoke',
        targets: [],
        defaults: { page_limit: 50, batch_size: 25, rate_delay: 1, parse_html_limit: 10, force: false },
        offline_available: true,
    },
];


function count(campaign, key) {
    return campaign?.summary?.[key] || campaign?.analysis?.overview?.[key] || 0;
}

function matchesFilters(job, search, status) {
    const haystack = `${job.job_id || ''} ${job.wiki_url || ''} ${job.api_endpoint || ''}`.toLowerCase();
    const statusMatch = status === 'all' || String(job.status || '').toLowerCase() === status;
    return haystack.includes(search.toLowerCase()) && statusMatch;
}

function errorEvents(events = []) {
    return events.filter(event => ['failed', 'error', 'warning', 'stopped'].includes(String(event.status || event.level || '').toLowerCase()));
}

function renderDatasetSummary(campaign) {
    return `
        <div class="dataset-strip mt-lg">
            ${DATASET_KEYS.map(key => `
                <div class="dataset-chip">
                    <span>${escapeHtml(t(`portfolio.datasets.${key}`))}</span>
                    <strong>${escapeHtml(count(campaign, key).toLocaleString())}</strong>
                </div>
            `).join('')}
        </div>
    `;
}

function renderWikiRows(jobs = []) {
    if (!jobs.length) {
        return `<tr><td colspan="8" class="text-muted">${escapeHtml(t('portfolio.campaigns.noCampaign'))}</td></tr>`;
    }
    return jobs.map(job => {
        const counts = job.counts || {};
        return `
            <tr>
                <td>${escapeHtml(job.wiki_url || job.job_id)}</td>
                <td>${statusBadge(job.status)}</td>
                <td>${escapeHtml((counts.pages || 0).toLocaleString())}</td>
                <td>${escapeHtml((counts.categories || 0).toLocaleString())}</td>
                <td>${escapeHtml((counts.links || 0).toLocaleString())}</td>
                <td>${escapeHtml((counts.infoboxes || 0).toLocaleString())}</td>
                <td>${escapeHtml((counts.errors || 0).toLocaleString())}</td>
                <td>
                    <div class="inline-actions">
                        <a class="btn btn--sm btn--ghost" href="#/browse?job=${encodeURIComponent(job.job_id)}">${escapeHtml(t('portfolio.actions.browse'))}</a>
                        <a class="btn btn--sm btn--ghost" href="#/browse?job=${encodeURIComponent(job.job_id)}&dataset=errors">${escapeHtml(t('portfolio.actions.openErrors'))}</a>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function renderErrorPanel(campaign, events = []) {
    const jobsWithErrors = (campaign.jobs || []).filter(job => Number(job.counts?.errors || 0) > 0 || job.error);
    const notableEvents = errorEvents(events).slice(-12).reverse();
    const empty = !jobsWithErrors.length && !notableEvents.length;
    return `
        <section class="card mt-lg">
            <div class="card__header">
                <h3 class="card__title">${escapeHtml(t('portfolio.campaigns.errorDrilldown'))}</h3>
                ${statusBadge(empty ? 'passed' : 'warning')}
            </div>
            <div class="card__body">
                ${empty ? `<div class="empty-state">${escapeHtml(t('portfolio.campaigns.noErrors'))}</div>` : `
                    <div class="error-grid">
                        ${jobsWithErrors.map(job => `
                            <article class="error-card">
                                <div>
                                    <strong>${escapeHtml(job.job_id)}</strong>
                                    <div class="text-xs text-muted">${escapeHtml(job.wiki_url || '')}</div>
                                </div>
                                <div>${statusBadge(job.status)}</div>
                                <p>${escapeHtml(job.error || t('portfolio.campaigns.errorRecords', { count: job.counts?.errors || 0 }))}</p>
                                <a class="btn btn--sm btn--ghost" href="#/browse?job=${encodeURIComponent(job.job_id)}&dataset=errors">${escapeHtml(t('portfolio.actions.openErrors'))}</a>
                            </article>
                        `).join('')}
                    </div>
                    ${notableEvents.length ? `
                        <div class="mt-md">
                            <div class="text-xs text-muted mb-sm">${escapeHtml(t('portfolio.campaigns.warningEvents'))}</div>
                            <div class="event-list">
                                ${notableEvents.map(event => `
                                    <div class="event-row">
                                        <span>${escapeHtml(event.time || '')}</span>
                                        <strong>${escapeHtml(event.stage || event.event || 'event')}</strong>
                                        ${statusBadge(event.status || event.level)}
                                        <em>${escapeHtml(event.message || '')}</em>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                `}
            </div>
        </section>
    `;
}

function renderEvents(events = []) {
    if (!events.length) return renderEmptyBlock(t('portfolio.campaigns.executionEvents'));
    return `
        <div class="timeline">
            ${events.slice(-30).map((event, index) => `
                <article class="timeline-item">
                    <div class="timeline-index">${index + 1}</div>
                    <div class="timeline-content">
                        <div class="flex items-center justify-between gap-md">
                            <h4>${escapeHtml(event.stage)}</h4>
                            ${statusBadge(event.status)}
                        </div>
                        <div class="text-xs text-muted">${escapeHtml(event.time || '')} ${event.wiki_url ? `· ${escapeHtml(event.wiki_url)}` : ''}</div>
                        <p>${escapeHtml(event.message || '')}</p>
                    </div>
                </article>
            `).join('')}
        </div>
    `;
}

export async function renderCampaignsPage(container) {
    let selectedCampaignId = null;
    let wikiSearch = '';
    let statusFilter = 'all';
    let pollTimer = null;
    let selectedPresetId = 'offline-portfolio-smoke';
    let presets = FALLBACK_PRESETS;

    container.innerHTML = `
        <div class="page animate-fadeIn portfolio-page" data-tour="campaigns-overview">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.campaigns.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.campaigns.subtitle'))}</p>
                </div>
                <div class="flex gap-sm">
                    <button class="btn btn--ghost" id="campaign-sample">${escapeHtml(t('portfolio.actions.loadSample'))}</button>
                    <button class="btn btn--ghost" id="campaign-refresh">${escapeHtml(t('portfolio.actions.refreshStatus'))}</button>
                    <button class="btn btn--primary" id="campaign-run">${escapeHtml(t('portfolio.actions.runPreset'))}</button>
                </div>
            </div>
            <div id="campaign-content" class="text-sm text-muted">${renderLoadingBlock()}</div>
        </div>
    `;

    async function render() {
        const content = container.querySelector('#campaign-content');
        try {
            const [response, presetResponse] = await Promise.all([
                listCampaigns(10),
                listCampaignPresets().catch(() => ({ items: FALLBACK_PRESETS })),
            ]);
            presets = presetResponse.items?.length ? presetResponse.items : FALLBACK_PRESETS;
            if (!presets.some(preset => preset.id === selectedPresetId)) {
                selectedPresetId = presets[0]?.id || 'offline-portfolio-smoke';
            }
            const selectedPreset = presets.find(preset => preset.id === selectedPresetId) || presets[0] || FALLBACK_PRESETS[0];
            const campaigns = response.items || [];
            if (!selectedCampaignId && campaigns[0]) selectedCampaignId = campaigns[0].campaign_id;
            const campaign = campaigns.find(item => item.campaign_id === selectedCampaignId) || campaigns[0];
            if (!campaign) {
                content.innerHTML = `
                    <section class="card">
                        <div class="card__body">
                            ${renderPresetPanel(selectedPreset, presets)}
                            ${renderEmptyBlock(t('portfolio.campaigns.noCampaign'))}
                        </div>
                    </section>
                `;
                bindPresetControls(content);
                return;
            }
            const eventResponse = await getCampaignEvents(campaign.campaign_id, 500).catch(() => ({ events: [] }));
            const events = eventResponse.events || [];
            const statuses = ['all', ...new Set((campaign.jobs || []).map(job => String(job.status || 'unknown').toLowerCase()))];
            const visibleJobs = (campaign.jobs || []).filter(job => matchesFilters(job, wikiSearch, statusFilter));
            if (pollTimer && !['running', 'queued'].includes(String(campaign.status || '').toLowerCase())) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
            content.innerHTML = `
                ${renderMetricCards([
                    { label: t('portfolio.metrics.wikis'), value: campaign.jobs?.length || 0, help: t('portfolio.metrics.wikisHelp') },
                    { label: t('portfolio.metrics.pages'), value: count(campaign, 'pages'), help: t('portfolio.metrics.pagesHelp') },
                    { label: t('portfolio.metrics.links'), value: count(campaign, 'links'), help: t('portfolio.metrics.linksHelp') },
                    { label: t('portfolio.metrics.errors'), value: count(campaign, 'errors'), help: t('portfolio.metrics.errorsHelp') },
                ])}
                ${renderDatasetSummary(campaign)}
                ${renderPresetPanel(selectedPreset, presets)}

                <section class="card mt-lg" data-tour="campaign-filters">
                    <div class="card__body">
                        <div class="data-toolbar">
                            <label class="input-group">
                                <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.selector'))}</span>
                                <select class="select input" id="campaign-select">
                                    ${campaigns.map(item => `<option value="${escapeHtml(item.campaign_id)}" ${item.campaign_id === campaign.campaign_id ? 'selected' : ''}>${escapeHtml(item.campaign_id)}</option>`).join('')}
                                </select>
                            </label>
                            <label class="input-group">
                                <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.searchWikis'))}</span>
                                <input class="input" id="campaign-wiki-search" value="${escapeHtml(wikiSearch)}" placeholder="wiki URL or job id">
                            </label>
                            <label class="input-group">
                                <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.status'))}</span>
                                <select class="select input" id="campaign-status-filter">
                                    ${statuses.map(status => `<option value="${escapeHtml(status)}" ${status === statusFilter ? 'selected' : ''}>${escapeHtml(status)}</option>`).join('')}
                                </select>
                            </label>
                        </div>
                    </div>
                </section>

                <section class="card mt-lg" data-tour="campaign-wikis">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.campaigns.wikiTable'))} · ${escapeHtml(campaign.campaign_id)}</h3>
                        ${statusBadge(campaign.status)}
                    </div>
                    <div class="card__body p-0">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Wiki</th>
                                    <th>${escapeHtml(t('portfolio.campaigns.status'))}</th>
                                    <th>${escapeHtml(t('portfolio.datasets.pages'))}</th>
                                    <th>${escapeHtml(t('portfolio.datasets.categories'))}</th>
                                    <th>${escapeHtml(t('portfolio.datasets.links'))}</th>
                                    <th>${escapeHtml(t('portfolio.datasets.infoboxes'))}</th>
                                    <th>${escapeHtml(t('portfolio.datasets.errors'))}</th>
                                    <th>${escapeHtml(t('common.actions'))}</th>
                                </tr>
                            </thead>
                            <tbody>${renderWikiRows(visibleJobs)}</tbody>
                        </table>
                    </div>
                </section>

                ${renderErrorPanel(campaign, events)}

                <section class="card mt-lg" data-tour="campaign-events">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.campaigns.executionEvents'))}</h3>
                        <span class="text-xs text-muted">${escapeHtml(t('portfolio.campaigns.eventsCount', { count: events.length }))}</span>
                    </div>
                    <div class="card__body">
                        ${renderEvents(events)}
                    </div>
                </section>
            `;
            content.querySelector('#campaign-select')?.addEventListener('change', event => {
                selectedCampaignId = event.currentTarget.value;
                wikiSearch = '';
                statusFilter = 'all';
                render();
            });
            content.querySelector('#campaign-wiki-search')?.addEventListener('input', event => {
                wikiSearch = event.currentTarget.value.trim();
                render();
            });
            content.querySelector('#campaign-status-filter')?.addEventListener('change', event => {
                statusFilter = event.currentTarget.value;
                render();
            });
            bindPresetControls(content);
        } catch (e) {
            content.innerHTML = renderErrorBlock(`${t('portfolio.campaigns.unavailable')} ${e.message}`);
            content.querySelector('[data-retry]')?.addEventListener('click', render);
        }
    }

    function renderPresetPanel(selectedPreset, items) {
        const defaults = selectedPreset.defaults || {};
        const targets = selectedPreset.targets || [];
        return `
            <section class="card mt-lg" data-tour="campaign-preset">
                <div class="card__header">
                    <h3 class="card__title">${escapeHtml(t('portfolio.campaigns.liveOptions'))}</h3>
                    ${statusBadge(selectedPreset.mode === 'sample' ? 'ready' : 'planned')}
                </div>
                <div class="card__body">
                    <div class="data-toolbar">
                        <label class="input-group">
                            <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.preset'))}</span>
                            <select class="select input" id="campaign-preset-select">
                                ${items.map(preset => `<option value="${escapeHtml(preset.id)}" ${preset.id === selectedPreset.id ? 'selected' : ''}>${escapeHtml(preset.label || preset.id)}</option>`).join('')}
                            </select>
                        </label>
                        <div class="input-group">
                            <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.mode'))}</span>
                            <div>${statusBadge(selectedPreset.mode || 'sample')}</div>
                        </div>
                        <div class="input-group">
                            <span class="input-group__label">${escapeHtml(t('portfolio.campaigns.defaults'))}</span>
                            <div class="text-xs text-muted">
                                ${escapeHtml(t('portfolio.campaigns.defaultSummary', {
                                    pages: defaults.page_limit ?? 0,
                                    delay: defaults.rate_delay ?? 1,
                                    html: defaults.parse_html_limit ?? 0,
                                }))}
                            </div>
                        </div>
                    </div>
                    <p class="text-sm text-muted mt-sm">${escapeHtml(selectedPreset.description || '')}</p>
                    <div class="target-chip-list mt-sm">
                        ${(targets.length ? targets : [t('portfolio.campaigns.offlineTarget')]).map(target => `
                            <span class="target-chip">${escapeHtml(target)}</span>
                        `).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    function bindPresetControls(root) {
        root.querySelector('#campaign-preset-select')?.addEventListener('change', event => {
            selectedPresetId = event.currentTarget.value;
            const preset = presets.find(item => item.id === selectedPresetId);
            if (preset?.campaign_id) {
                selectedCampaignId = preset.campaign_id;
            }
            render();
        });
    }

    async function runSelectedPreset(button) {
        const preset = presets.find(item => item.id === selectedPresetId) || presets[0] || FALLBACK_PRESETS[0];
        if (preset.mode === 'sample') {
            selectedCampaignId = preset.campaign_id || 'portfolio-smoke';
            await render();
            toast.success(t('portfolio.campaigns.sampleLoaded'));
            return;
        }
        const payload = {
            campaign_id: preset.campaign_id,
            targets: preset.targets || [],
            ...(preset.defaults || {}),
        };
        button.disabled = true;
        button.textContent = t('common.queued');
        await runCampaign(payload);
        selectedCampaignId = payload.campaign_id;
        toast.success(t('portfolio.campaigns.queued'));
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(render, 2000);
        setTimeout(() => {
            if (pollTimer) clearInterval(pollTimer);
        }, 600000);
    }

    container.querySelector('#campaign-refresh')?.addEventListener('click', render);
    container.querySelector('#campaign-sample')?.addEventListener('click', async () => {
        selectedCampaignId = 'portfolio-smoke';
        selectedPresetId = 'offline-portfolio-smoke';
        await render();
        toast.success(t('portfolio.campaigns.sampleLoaded'));
    });
    container.querySelector('#campaign-run')?.addEventListener('click', async () => {
        const button = container.querySelector('#campaign-run');
        try {
            await runSelectedPreset(button);
        } catch (e) {
            toast.error(e.message);
        } finally {
            button.disabled = false;
            button.textContent = t('portfolio.actions.runPreset');
        }
    });

    await render();
}

export default { render: renderCampaignsPage };
