import { loadDemoSnapshot } from '../services/demoData.js';
import { t } from '../i18n/i18n.js';
import { escapeHtml, renderDemoNotice, renderLoadingBlock, renderMetricCards, statusBadge } from './portfolioShared.js';
import { getUniversalJobWikiAnalysis, listUniversalJobs } from '../api/scraper.js';

const NETWORK_LIMIT = 18;

function barList(items, labelKey = 'label', valueKey = 'value') {
  if (!items?.length) {
    return `<div class="text-muted">${escapeHtml(t('portfolio.analysis.noData'))}</div>`;
  }
  const max = Math.max(...items.map(item => item[valueKey]), 1);
  return `
        <div class="bar-list">
            ${items.map(item => {
    const value = item[valueKey];
    const width = Math.max(8, Math.round((value / max) * 100));
    return `
                    <div class="bar-row">
                        <span>${escapeHtml(item[labelKey])}</span>
                        <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
                        <strong>${escapeHtml(value)}</strong>
                    </div>
                `;
  }).join('')}
        </div>
    `;
}

function wikiComparison(perWiki = []) {
  if (!perWiki.length) return `<div class="text-muted">${escapeHtml(t('portfolio.analysis.noPerWiki'))}</div>`;
  const maxPages = Math.max(...perWiki.map(item => item.counts?.pages || 0), 1);
  return `
    <div class="wiki-comparison">
      ${perWiki.map(item => {
        const counts = item.counts || {};
        const warningCount = (item.quality || []).filter(check => check.status !== 'passed').length;
        return `
          <article class="wiki-comparison-row">
            <div>
              <strong>${escapeHtml(item.wiki || item.job_id)}</strong>
              <span>${escapeHtml(item.job_id || '')}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" style="width:${Math.max(4, Math.round(((counts.pages || 0) / maxPages) * 100))}%"></div></div>
            <div class="wiki-comparison-stats">
              <span>${escapeHtml(counts.pages || 0)} pages</span>
              <span>${escapeHtml(counts.links || 0)} links</span>
              <span>${escapeHtml(warningCount)} warnings</span>
            </div>
          </article>
        `;
      }).join('')}
    </div>
  `;
}

function connectedEdges(network, selectedNode) {
  const edges = network.edges || [];
  if (!selectedNode) return edges.slice(0, 12);
  return edges.filter(edge => edge.source === selectedNode || edge.target === selectedNode).slice(0, 16);
}

function networkGraph(network, selectedNode = null) {
  const nodes = (network.nodes || []).slice(0, NETWORK_LIMIT);
  const edges = (network.edges || []).slice(0, 80);
  if (!nodes.length) {
    return `<div class="text-muted">${escapeHtml(t('portfolio.analysis.noNetwork'))}</div>`;
  }
  const width = 680;
  const height = 360;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 135;
  const positions = new Map();
  nodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
    const degreeOffset = Math.min(36, Number(node.degree || 0) * 1.5);
    positions.set(node.id, {
      x: Math.round(centerX + Math.cos(angle) * (radius + degreeOffset)),
      y: Math.round(centerY + Math.sin(angle) * (radius + degreeOffset)),
    });
  });
  const lines = edges
    .filter(edge => positions.has(edge.source) && positions.has(edge.target))
    .map(edge => {
      const a = positions.get(edge.source);
      const b = positions.get(edge.target);
      const active = selectedNode && (edge.source === selectedNode || edge.target === selectedNode) ? 'network-edge--active' : '';
      return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" class="network-edge ${active}"></line>`;
    })
    .join('');
  const circles = nodes.map(node => {
    const point = positions.get(node.id);
    const size = Math.max(8, Math.min(24, 7 + Number(node.degree || 1)));
    const active = selectedNode === node.id ? 'network-circle--active' : '';
    return `
      <g class="network-node-svg" data-node="${escapeHtml(node.id)}">
        <circle cx="${point.x}" cy="${point.y}" r="${size}" class="network-circle ${active}"></circle>
        <text x="${point.x}" y="${point.y + size + 14}" text-anchor="middle">${escapeHtml(node.id).slice(0, 18)}</text>
      </g>
    `;
  }).join('');
  return `
    <div class="network-graph">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Relationship network">
        ${lines}
        ${circles}
      </svg>
    </div>
  `;
}

function edgeList(network, selectedNode) {
  const edges = connectedEdges(network, selectedNode);
  if (!edges.length) return `<div class="text-muted">${escapeHtml(t('portfolio.analysis.noEdges'))}</div>`;
  return `
    <div class="edge-list">
      ${edges.map(edge => `
        <div class="edge-row">
          <strong>${escapeHtml(edge.source)}</strong>
          <span>→</span>
          <strong>${escapeHtml(edge.target)}</strong>
        </div>
      `).join('')}
    </div>
  `;
}

export async function renderAnalysisPage(container) {
  container.innerHTML = `<div class="page animate-fadeIn portfolio-page">${renderLoadingBlock()}</div>`;
  const snapshot = await loadDemoSnapshot();
  let analysis = snapshot.analysis;
  let liveNotice = renderDemoNotice(snapshot);
  let perWiki = [];
  if (snapshot.live?.campaignAnalysis?.overview) {
    const campaignAnalysis = snapshot.live.campaignAnalysis;
    analysis = {
      categoryCounts: campaignAnalysis.category_counts || [],
      topTerms: snapshot.analysis.topTerms || [],
      network: campaignAnalysis.network || { nodes: [], edges: [] },
      quality: (campaignAnalysis.per_wiki || []).flatMap(item => item.quality || []),
    };
    perWiki = campaignAnalysis.per_wiki || [];
    liveNotice = `<div class="demo-notice mb-md"><strong>${escapeHtml(t('portfolio.analysis.liveCampaign'))}</strong><span>${escapeHtml(t('portfolio.analysis.showingCampaign', { id: snapshot.run.id }))}</span></div>`;
  }
  try {
    const jobs = await listUniversalJobs(20);
    const job = !snapshot.live?.campaignAnalysis?.overview && (jobs?.find(item => item.status === 'finished') || jobs?.[0]);
    if (job) {
      const response = await getUniversalJobWikiAnalysis(job.job_id);
      const live = response.analysis;
      analysis = {
        categoryCounts: live.category_counts || [],
        topTerms: live.top_terms || [],
        network: live.network || { nodes: [], edges: [] },
        quality: live.quality || [],
      };
      perWiki = [];
      liveNotice = `<div class="demo-notice mb-md"><strong>${escapeHtml(t('portfolio.analysis.liveWikiDb'))}</strong><span>${escapeHtml(t('portfolio.analysis.showingJob', { id: job.job_id }))}</span></div>`;
    }
  } catch {
    if (!snapshot.live?.campaignAnalysis?.overview) {
      analysis = snapshot.analysis;
    }
  }
  const topCategory = analysis.categoryCounts?.[0] || { label: 'n/a', value: 0 };
  const topTerm = analysis.topTerms?.[0] || { term: 'n/a', count: 0 };
  let selectedNode = analysis.network.nodes?.[0]?.id || null;

  function renderNetworkSection() {
    const node = (analysis.network.nodes || []).find(item => item.id === selectedNode);
    const el = container.querySelector('#analysis-network');
    if (!el) return;
    el.innerHTML = `
      <div class="network-summary">
        <span>${escapeHtml((analysis.network.nodes || []).length)} nodes</span>
        <span>${escapeHtml((analysis.network.edges || []).length)} sampled edges</span>
        ${node ? `<span>Selected: ${escapeHtml(node.id)} · degree ${escapeHtml(node.degree || 0)}</span>` : ''}
      </div>
      ${networkGraph(analysis.network, selectedNode)}
      <div class="network-layout">
        <div class="network-list">
          ${(analysis.network.nodes || []).slice(0, NETWORK_LIMIT).map(item => `
            <button class="network-node ${selectedNode === item.id ? 'network-node--active' : ''}" data-network-node="${escapeHtml(item.id)}">
              <strong>${escapeHtml(item.id)}</strong>
              <span>${escapeHtml(item.group || 'page')}</span>
              <em>degree ${escapeHtml(item.degree || 0)}</em>
            </button>
          `).join('')}
        </div>
        <div>
          <div class="text-xs text-muted mb-sm">${escapeHtml(t('portfolio.analysis.connectedEdges'))}</div>
          ${edgeList(analysis.network, selectedNode)}
        </div>
      </div>
    `;
    el.querySelectorAll('[data-network-node]').forEach(button => {
      button.addEventListener('click', () => {
        selectedNode = button.getAttribute('data-network-node');
        renderNetworkSection();
      });
    });
  }

  container.innerHTML = `
        <div class="page animate-fadeIn portfolio-page">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${escapeHtml(t('portfolio.analysis.title'))}</h1>
                    <p class="page__subtitle">${escapeHtml(t('portfolio.analysis.subtitle'))}</p>
                </div>
            </div>

            ${liveNotice}

            ${renderMetricCards([
    { label: t('portfolio.analysis.topCategory'), value: topCategory.label, help: `${topCategory.value} records` },
    { label: t('portfolio.analysis.topTerm'), value: topTerm.term, help: `${topTerm.count} occurrences` },
    { label: t('portfolio.analysis.networkNodes'), value: analysis.network.nodes.length, help: `${analysis.network.edges.length} sampled edges` },
    { label: t('portfolio.analysis.qualityWarnings'), value: analysis.quality.filter(item => item.status !== 'passed').length, help: 'Non-blocking review items' },
  ])}

            <div class="grid grid-cols-2 gap-lg mt-lg portfolio-grid">
                <section class="card">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.analysis.perWiki'))}</h3>
                    </div>
                    <div class="card__body">
                        ${wikiComparison(perWiki)}
                    </div>
                </section>

                <section class="card">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.analysis.categoryAnalysis'))}</h3>
                    </div>
                    <div class="card__body">
                        ${barList(analysis.categoryCounts)}
                    </div>
                </section>

                <section class="card">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.analysis.textAnalysis'))}</h3>
                    </div>
                    <div class="card__body">
                        ${barList(analysis.topTerms, 'term', 'count')}
                    </div>
                </section>

                <section class="card chart-card--wide" data-tour="analysis-network">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.analysis.relationshipNetwork'))}</h3>
                    </div>
                    <div class="card__body" id="analysis-network"></div>
                </section>

                <section class="card" data-tour="analysis-quality">
                    <div class="card__header">
                        <h3 class="card__title">${escapeHtml(t('portfolio.analysis.dataQuality'))}</h3>
                    </div>
                    <div class="card__body">
                        <div class="quality-list">
                            ${analysis.quality.map(item => `
                                <div class="quality-row">
                                    <div>
                                        <strong>${escapeHtml(item.check)}</strong>
                                        <div class="text-xs text-muted">${escapeHtml(item.affected)} affected records</div>
                                    </div>
                                    ${statusBadge(item.status)}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </section>
            </div>
        </div>
    `;
  renderNetworkSection();
}

export default { render: renderAnalysisPage };
