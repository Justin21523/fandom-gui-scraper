import { describe, test, expect, beforeEach, jest } from '@jest/globals';

const mockListCampaigns = jest.fn();
const mockListCampaignPresets = jest.fn();
const mockGetCampaignEvents = jest.fn();
const mockRunCampaign = jest.fn();
const mockListUniversalJobs = jest.fn();
const mockGetUniversalJobManifest = jest.fn();
const mockListUniversalJobFiles = jest.fn();
const mockGetUniversalJobWikiSummary = jest.fn();
const mockBrowseUniversalJobWikiTable = jest.fn();
const mockGetUniversalJobWikiPage = jest.fn();
const mockGetUniversalJobWikiAnalysis = jest.fn();
const mockGetCampaignAnalysis = jest.fn();

const translations = {
  'common.actions': 'Actions',
  'common.clear': 'Clear',
  'common.close': 'Close',
  'common.error': 'Error',
  'common.loading': 'Loading...',
  'common.next': 'Next',
  'common.noData': 'No data',
  'common.previous': 'Previous',
  'common.queued': 'Queued',
  'common.refresh': 'Refresh',
  'common.retry': 'Retry',
  'common.search': 'Search',
  'status.finished': 'Finished',
  'status.passed': 'Passed',
  'status.warning': 'Warning',
  'portfolio.actions.browse': 'Browse',
  'portfolio.actions.loadSample': 'Load Sample Demo',
  'portfolio.actions.openErrors': 'Open errors dataset',
  'portfolio.actions.refreshStatus': 'Refresh Status',
  'portfolio.actions.runLive': 'Run Live Campaign',
  'portfolio.actions.runPreset': 'Run Selected Preset',
  'portfolio.analysis.categoryAnalysis': 'Category analysis',
  'portfolio.analysis.connectedEdges': 'Connected edges',
  'portfolio.analysis.dataQuality': 'Data quality',
  'portfolio.analysis.liveCampaign': 'Live campaign analysis',
  'portfolio.analysis.liveWikiDb': 'Live wiki.db analysis',
  'portfolio.analysis.networkNodes': 'Network nodes',
  'portfolio.analysis.noData': 'No data available.',
  'portfolio.analysis.noEdges': 'No visible edges for this selection.',
  'portfolio.analysis.noNetwork': 'No sampled links available.',
  'portfolio.analysis.noPerWiki': 'No per-wiki analysis available.',
  'portfolio.analysis.perWiki': 'Per-wiki Comparison',
  'portfolio.analysis.qualityWarnings': 'Quality warnings',
  'portfolio.analysis.relationshipNetwork': 'Relationship Network',
  'portfolio.analysis.showingCampaign': 'Showing aggregate analysis from campaign {{id}}.',
  'portfolio.analysis.showingJob': 'Showing SQLite analysis from job {{id}}.',
  'portfolio.analysis.subtitle': 'Category, text, relationship network, and data quality views for a wiki crawl.',
  'portfolio.analysis.textAnalysis': 'Text analysis',
  'portfolio.analysis.title': 'Analysis',
  'portfolio.analysis.topCategory': 'Top category',
  'portfolio.analysis.topTerm': 'Top term',
  'portfolio.browse.dataset': '{{dataset}} dataset',
  'portfolio.browse.datasetBrowser': 'Dataset browser',
  'portfolio.browse.demoNotice': 'Live jobs were not available, so this browser is showing a small public Fandom workflow sample.',
  'portfolio.browse.demoRun': 'Demo sample dataset',
  'portfolio.browse.fileHelp': 'Select a file to preview the first records.',
  'portfolio.browse.files': 'Files',
  'portfolio.browse.length': 'Length',
  'portfolio.browse.loadFailed': 'Failed to load data',
  'portfolio.browse.manifest': 'manifest.json',
  'portfolio.browse.matchingRows': '{{count}} matching rows',
  'portfolio.browse.namespace': 'Namespace',
  'portfolio.browse.noRelationRows': 'No rows',
  'portfolio.browse.noRows': 'No rows match the current filter.',
  'portfolio.browse.pageId': 'Page ID',
  'portfolio.browse.preview': 'Preview',
  'portfolio.browse.runs': 'Runs',
  'portfolio.browse.searchDataset': 'Search {{dataset}}',
  'portfolio.browse.selectRun': 'Select a run',
  'portfolio.browse.selectedPageDetail': 'Selected page detail',
  'portfolio.browse.subtitle': 'Browse pages, categories, links, templates, images, revisions, infobox-like data, errors, and checkpoints.',
  'portfolio.browse.title': 'Browse',
  'portfolio.browse.touched': 'Touched',
  'portfolio.browse.wikiDb': 'SQLite wiki.db',
  'portfolio.browse.wikiDbUnavailable': 'wiki.db unavailable',
  'portfolio.campaigns.errorDrilldown': 'Error Drill-down',
  'portfolio.campaigns.errorRecords': '{{count}} crawl error records',
  'portfolio.campaigns.eventsCount': '{{count}} events',
  'portfolio.campaigns.executionEvents': 'Execution events',
  'portfolio.campaigns.defaultSummary': '{{pages}} pages · {{delay}}s delay · {{html}} HTML fallback pages',
  'portfolio.campaigns.defaults': 'Defaults',
  'portfolio.campaigns.mode': 'Mode',
  'portfolio.campaigns.noCampaign': 'No campaign found. Load the sample demo or run a live campaign.',
  'portfolio.campaigns.noErrors': 'No recorded crawl errors or warning events in this campaign.',
  'portfolio.campaigns.offlineTarget': 'Bundled offline sample',
  'portfolio.campaigns.preset': 'Demo preset',
  'portfolio.campaigns.queued': 'Campaign queued. The page will refresh while it runs.',
  'portfolio.campaigns.sampleLoaded': 'Sample demo loaded from local data.',
  'portfolio.campaigns.searchWikis': 'Search wikis',
  'portfolio.campaigns.selector': 'Campaign',
  'portfolio.campaigns.status': 'Status',
  'portfolio.campaigns.subtitle': 'Run and inspect multi-wiki Fandom campaigns across public MediaWiki sites.',
  'portfolio.campaigns.title': 'Campaigns',
  'portfolio.campaigns.unavailable': 'Campaign data is unavailable.',
  'portfolio.campaigns.warningEvents': 'Warning and stop events',
  'portfolio.campaigns.wikiTable': 'Wiki outputs',
  'portfolio.datasets.categories': 'Categories',
  'portfolio.datasets.errors': 'Errors',
  'portfolio.datasets.images': 'Images',
  'portfolio.datasets.infoboxes': 'Infoboxes',
  'portfolio.datasets.links': 'Links',
  'portfolio.datasets.pages': 'Pages',
  'portfolio.datasets.revisions': 'Revisions',
  'portfolio.datasets.templates': 'Templates',
  'portfolio.loadingPreparing': 'Preparing live data, charts, and workflow state...',
  'portfolio.metrics.errors': 'Errors',
  'portfolio.metrics.errorsHelp': 'Recorded crawl issues',
  'portfolio.metrics.links': 'Links',
  'portfolio.metrics.linksHelp': 'Network edge inputs',
  'portfolio.metrics.pages': 'Pages',
  'portfolio.metrics.pagesHelp': 'SQLite page records',
  'portfolio.metrics.wikis': 'Wikis',
  'portfolio.metrics.wikisHelp': 'Public Fandom sites',
  'portfolio.notice.demo': 'Demo sample dataset',
  'portfolio.notice.live': 'Live API snapshot',
};

function translate(key, params = {}) {
  const value = translations[key] || key;
  return String(value).replace(/\{\{(\w+)\}\}/g, (_, name) => params[name] ?? `{{${name}}}`);
}

jest.unstable_mockModule('@/api/scraper.js', () => ({
  listCampaigns: mockListCampaigns,
  listCampaignPresets: mockListCampaignPresets,
  getCampaignEvents: mockGetCampaignEvents,
  runCampaign: mockRunCampaign,
  listUniversalJobs: mockListUniversalJobs,
  getUniversalJobManifest: mockGetUniversalJobManifest,
  listUniversalJobFiles: mockListUniversalJobFiles,
  previewUniversalJobFile: jest.fn(),
  getUniversalJobWikiSummary: mockGetUniversalJobWikiSummary,
  browseUniversalJobWikiTable: mockBrowseUniversalJobWikiTable,
  getUniversalJobWikiPage: mockGetUniversalJobWikiPage,
  getUniversalJobWikiAnalysis: mockGetUniversalJobWikiAnalysis,
  getUniversalStatus: jest.fn(),
  getUniversalJobOutputStats: jest.fn(),
  getUniversalJobLogs: jest.fn(),
  getCampaignAnalysis: mockGetCampaignAnalysis,
}));

jest.unstable_mockModule('@/i18n/i18n.js', () => ({
  getAvailableLocales: jest.fn(() => [{ code: 'en', name: 'English' }]),
  getLocale: jest.fn(() => 'en'),
  initI18n: jest.fn(),
  setLocale: jest.fn(),
  t: translate,
}));

jest.unstable_mockModule('@/components/toast.js', () => ({
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

const { renderCampaignsPage } = await import('@/pages/campaigns.js');
const { renderBrowsePage } = await import('@/pages/browse.js');
const { renderAnalysisPage } = await import('@/pages/analysis.js');

function container() {
  const el = document.createElement('main');
  document.body.appendChild(el);
  return el;
}

const campaign = {
  campaign_id: 'portfolio-smoke',
  status: 'finished',
  targets: ['https://onepiece.fandom.com'],
  summary: { pages: 50, categories: 10, links: 200, templates: 5, images: 12, revisions: 50, infoboxes: 3, errors: 1 },
  jobs: [
    {
      job_id: 'portfolio-smoke-onepiece',
      wiki_url: 'https://onepiece.fandom.com',
      status: 'finished',
      counts: { pages: 50, categories: 10, links: 200, infoboxes: 3, errors: 1 },
    },
  ],
};

describe('web-first product polish pages', () => {
  beforeEach(() => {
    window.location.hash = '';
    mockListCampaigns.mockResolvedValue({ items: [campaign] });
    mockListCampaignPresets.mockResolvedValue({
      items: [
        {
          id: 'offline-portfolio-smoke',
          label: 'Offline Demo',
          mode: 'sample',
          campaign_id: 'portfolio-smoke',
          targets: [],
          defaults: { page_limit: 50, batch_size: 25, rate_delay: 1, parse_html_limit: 10, force: false },
        },
        {
          id: 'live-quick-two-wikis',
          label: 'Live Quick',
          mode: 'live',
          campaign_id: 'portfolio-live-quick',
          targets: ['https://onepiece.fandom.com', 'https://stardewvalley.fandom.com'],
          defaults: { page_limit: 30, batch_size: 15, rate_delay: 1.25, parse_html_limit: 6, force: false },
        },
      ],
    });
    mockGetCampaignEvents.mockResolvedValue({
      events: [{ time: '10:00', stage: 'robots', status: 'warning', message: 'slowed down' }],
    });
    mockListUniversalJobs.mockResolvedValue([
      { job_id: 'portfolio-smoke-onepiece', status: 'finished', created_at: '2026-06-24T10:00:00Z', config: { input_source: 'https://onepiece.fandom.com' } },
    ]);
    mockGetUniversalJobManifest.mockResolvedValue({ manifest: { wiki_url: 'https://onepiece.fandom.com', wiki_db: { path: 'wiki.db' } } });
    mockListUniversalJobFiles.mockResolvedValue({ items: [{ type: 'file', path: 'wiki.db' }] });
    mockGetUniversalJobWikiSummary.mockResolvedValue({
      summary: { counts: { pages: 2, categories: 1, links: 3, templates: 1, images: 1, revisions: 2, infoboxes: 1, errors: 1, checkpoints: 1 } },
    });
    mockBrowseUniversalJobWikiTable.mockResolvedValue({
      dataset: 'errors',
      columns: ['id', 'error_type', 'message'],
      limit: 25,
      offset: 0,
      total: 1,
      items: [{ id: 1, error_type: 'warning', message: 'rate limited' }],
    });
    mockGetUniversalJobWikiPage.mockResolvedValue({
      page: { id: 1, pageid: 101, title: 'Monkey D. Luffy', ns: 0, length: 1000 },
      categories: [{ category_title: 'Characters' }],
      links: [{ target_title: 'Straw Hat Pirates' }],
      templates: [],
      images: [],
      revisions: [],
      infoboxes: [],
    });
    mockGetCampaignAnalysis.mockResolvedValue({ analysis: {} });
  });

  test('Campaigns shows dataset counts and error drill-down', async () => {
    const el = container();
    await renderCampaignsPage(el);

    expect(el.textContent).toContain('Campaigns');
    expect(el.textContent).toContain('Demo preset');
    expect(el.textContent).toContain('Error Drill-down');
    expect(el.textContent).toContain('Open errors dataset');
    expect(el.textContent).toContain('Links');
    expect(el.textContent).toContain('200');
  });

  test('Campaigns runs the selected live preset payload', async () => {
    const el = container();
    await renderCampaignsPage(el);

    el.querySelector('#campaign-preset-select').value = 'live-quick-two-wikis';
    el.querySelector('#campaign-preset-select').dispatchEvent(new Event('change'));
    await Promise.resolve();
    await Promise.resolve();

    await el.querySelector('#campaign-run').click();

    expect(mockRunCampaign).toHaveBeenCalledWith({
      campaign_id: 'portfolio-live-quick',
      targets: ['https://onepiece.fandom.com', 'https://stardewvalley.fandom.com'],
      page_limit: 30,
      batch_size: 15,
      rate_delay: 1.25,
      parse_html_limit: 6,
      force: false,
    });
  });

  test('Browse honors URL dataset state and renders searchable wiki.db table', async () => {
    window.location.hash = '#/browse?job=portfolio-smoke-onepiece&dataset=errors&q=rate&limit=25';
    const el = container();
    await renderBrowsePage(el);

    expect(mockBrowseUniversalJobWikiTable).toHaveBeenCalledWith('portfolio-smoke-onepiece', 'errors', {
      limit: 25,
      offset: 0,
      q: 'rate',
    });
    expect(el.textContent).toContain('errors dataset');
    expect(el.textContent).toContain('rate limited');
    expect(el.querySelector('.dataset-tab--active')?.textContent).toContain('errors');
  });

  test('Analysis renders campaign comparison and selectable network section', async () => {
    mockListCampaigns.mockResolvedValue({
      items: [{
        ...campaign,
        analysis: {
          overview: { pages: 50, links: 200, errors: 1 },
          category_counts: [{ label: 'Characters', value: 10 }],
          network: {
            nodes: [{ id: 'Monkey D. Luffy', degree: 4 }, { id: 'Straw Hat Pirates', degree: 3 }],
            edges: [{ source: 'Monkey D. Luffy', target: 'Straw Hat Pirates' }],
          },
          per_wiki: [{ job_id: 'portfolio-smoke-onepiece', wiki: 'https://onepiece.fandom.com', counts: { pages: 50, links: 200 }, quality: [{ status: 'warning' }] }],
        },
      }],
    });
    mockGetCampaignAnalysis.mockResolvedValue({
      analysis: {
        overview: { pages: 50, links: 200, errors: 1 },
        category_counts: [{ label: 'Characters', value: 10 }],
        network: {
          nodes: [{ id: 'Monkey D. Luffy', degree: 4 }, { id: 'Straw Hat Pirates', degree: 3 }],
          edges: [{ source: 'Monkey D. Luffy', target: 'Straw Hat Pirates' }],
        },
        per_wiki: [{ job_id: 'portfolio-smoke-onepiece', wiki: 'https://onepiece.fandom.com', counts: { pages: 50, links: 200 }, quality: [{ status: 'warning' }] }],
      },
    });

    const el = container();
    await renderAnalysisPage(el);

    expect(el.textContent).toContain('Per-wiki Comparison');
    expect(el.textContent).toContain('Relationship Network');
    expect(el.textContent).toContain('Connected edges');
    expect(el.textContent).toContain('Monkey D. Luffy');
  });
});
