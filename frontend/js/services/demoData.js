import {
  getUniversalStatus,
  listUniversalJobs,
  getUniversalJobManifest,
  listUniversalJobFiles,
  previewUniversalJobFile,
  getUniversalJobOutputStats,
  getUniversalJobLogs,
  listCampaigns,
  getCampaignEvents,
  getCampaignAnalysis,
} from '../api/scraper.js';

export const DEMO_MODE = {
  DEMO: 'demo',
  LIVE: 'live',
};

const SAMPLE_RUN = {
  mode: DEMO_MODE.DEMO,
  demoNotice: 'Demo dataset based on a small public Fandom workflow sample. Long page text and images are summarized to avoid redistribution.',
  run: {
    id: 'demo-onepiece-action-api-001',
    status: 'completed',
    wikiName: 'One Piece Wiki',
    input: 'https://onepiece.fandom.com/wiki/Main_Page',
    normalizedBaseUrl: 'https://onepiece.fandom.com',
    apiEndpoint: 'https://onepiece.fandom.com/api.php',
    userAgent: 'FandomGuiScraperPortfolio/1.0 (+portfolio demo; contact: example@example.com)',
    startedAt: '2026-06-24T09:10:00Z',
    finishedAt: '2026-06-24T09:18:42Z',
    checkpoint: {
      enabled: true,
      lastCursor: 'gapcontinue=Monkey_D._Luffy&continue=gapcontinue||',
      pagesSeen: 128,
      duplicateSkipped: 16,
      resumable: true,
    },
    counts: {
      pages: 128,
      categories: 12,
      links: 342,
      templates: 48,
      images: 74,
      revisions: 128,
      infoboxes: 32,
      qualityWarnings: 9,
      errors: 2,
    },
  },
  pipelineSteps: [
    {
      key: 'normalize',
      title: 'Normalize wiki target',
      method: 'URL parser',
      request: 'input=https://onepiece.fandom.com/wiki/Main_Page',
      result: 'Base URL and api.php endpoint detected.',
      status: 'passed',
      durationMs: 42,
    },
    {
      key: 'robots',
      title: 'Check robots.txt',
      method: 'GET',
      request: 'https://onepiece.fandom.com/robots.txt',
      result: 'Allowed for API and selected public wiki paths.',
      status: 'passed',
      durationMs: 180,
    },
    {
      key: 'siteinfo',
      title: 'Discover MediaWiki capabilities',
      method: 'Action API',
      request: '/api.php?action=query&meta=siteinfo&siprop=general|namespaces&format=json',
      result: 'MediaWiki API available; HTML scraping remains fallback only.',
      status: 'passed',
      durationMs: 260,
    },
    {
      key: 'pages',
      title: 'Fetch pages and revisions metadata',
      method: 'Action API',
      request: '/api.php?action=query&generator=allpages&prop=info|revisions|categories&rvprop=ids|timestamp|user|size',
      result: '128 pages fetched with continuation checkpoint.',
      status: 'passed',
      durationMs: 2800,
    },
    {
      key: 'relations',
      title: 'Collect links, templates, and images',
      method: 'Action API',
      request: '/api.php?action=query&pageids=...&prop=links|templates|images',
      result: '342 links, 48 templates, 74 image references.',
      status: 'passed',
      durationMs: 2100,
    },
    {
      key: 'fallback',
      title: 'Parse infobox-like page details',
      method: 'HTML fallback',
      request: 'GET selected public page HTML only when API fields are incomplete',
      result: '32 infobox-like records extracted; no blocked page bypass attempted.',
      status: 'warning',
      durationMs: 1840,
    },
    {
      key: 'export',
      title: 'Persist and export',
      method: 'SQLite + file exporters',
      request: 'pages/categories/links/templates/images/revisions/infoboxes',
      result: 'SQLite, JSONL, CSV, and Parquet export artifacts prepared.',
      status: 'passed',
      durationMs: 940,
    },
  ],
  collections: {
    pages: [
      { pageid: 101, title: 'Monkey D. Luffy', namespace: 0, touched: '2026-06-23T18:12:00Z', size: 64218, quality: 94 },
      { pageid: 102, title: 'Roronoa Zoro', namespace: 0, touched: '2026-06-22T16:09:00Z', size: 51203, quality: 91 },
      { pageid: 103, title: 'Nami', namespace: 0, touched: '2026-06-22T13:45:00Z', size: 43812, quality: 88 },
      { pageid: 104, title: 'Category:Characters', namespace: 14, touched: '2026-06-20T08:31:00Z', size: 4021, quality: 82 },
    ],
    categories: [
      { title: 'Characters', pages: 428, crawled: 80 },
      { title: 'Episodes', pages: 1120, crawled: 28 },
      { title: 'Story Arcs', pages: 44, crawled: 12 },
      { title: 'Devil Fruits', pages: 214, crawled: 8 },
    ],
    links: [
      { source: 'Monkey D. Luffy', target: 'Straw Hat Pirates', type: 'internal' },
      { source: 'Monkey D. Luffy', target: 'Gomu Gomu no Mi', type: 'internal' },
      { source: 'Roronoa Zoro', target: 'Wano Country Arc', type: 'internal' },
      { source: 'Nami', target: 'Arlong Park Arc', type: 'internal' },
    ],
    templates: [
      { page: 'Monkey D. Luffy', template: 'Infobox Character', params: 28 },
      { page: 'Roronoa Zoro', template: 'Infobox Character', params: 24 },
      { page: 'Nami', template: 'Infobox Character', params: 22 },
    ],
    images: [
      { page: 'Monkey D. Luffy', file: 'Monkey D. Luffy Portrait.png', kind: 'metadata-only', width: 270, height: 380 },
      { page: 'Roronoa Zoro', file: 'Roronoa Zoro Portrait.png', kind: 'metadata-only', width: 270, height: 380 },
      { page: 'Nami', file: 'Nami Portrait.png', kind: 'metadata-only', width: 270, height: 380 },
    ],
    revisions: [
      { page: 'Monkey D. Luffy', revid: 901001, user: 'FandomContributor', timestamp: '2026-06-23T18:12:00Z', size: 64218 },
      { page: 'Roronoa Zoro', revid: 900884, user: 'FandomContributor', timestamp: '2026-06-22T16:09:00Z', size: 51203 },
      { page: 'Nami', revid: 900742, user: 'FandomContributor', timestamp: '2026-06-22T13:45:00Z', size: 43812 },
    ],
    infoboxes: [
      { page: 'Monkey D. Luffy', fields: { affiliation: 'Straw Hat Pirates', occupation: 'Pirate', origin: 'East Blue' } },
      { page: 'Roronoa Zoro', fields: { affiliation: 'Straw Hat Pirates', occupation: 'Swordsman', origin: 'East Blue' } },
      { page: 'Nami', fields: { affiliation: 'Straw Hat Pirates', occupation: 'Navigator', origin: 'East Blue' } },
    ],
    textSnippets: [
      { page: 'Monkey D. Luffy', snippet: 'Short summary retained for demo display; full article text is not redistributed.' },
      { page: 'Roronoa Zoro', snippet: 'Text analysis uses token counts and metadata summaries rather than full copied article bodies.' },
      { page: 'Nami', snippet: 'Snippet-only preview keeps the portfolio demo focused on pipeline behavior.' },
    ],
  },
  analysis: {
    categoryCounts: [
      { label: 'Characters', value: 80 },
      { label: 'Episodes', value: 28 },
      { label: 'Story Arcs', value: 12 },
      { label: 'Images', value: 74 },
    ],
    topTerms: [
      { term: 'pirate', count: 86 },
      { term: 'crew', count: 64 },
      { term: 'arc', count: 42 },
      { term: 'devil fruit', count: 31 },
      { term: 'bounty', count: 29 },
    ],
    network: {
      nodes: [
        { id: 'Monkey D. Luffy', group: 'character', degree: 18 },
        { id: 'Straw Hat Pirates', group: 'organization', degree: 24 },
        { id: 'Roronoa Zoro', group: 'character', degree: 15 },
        { id: 'Nami', group: 'character', degree: 14 },
        { id: 'Wano Country Arc', group: 'arc', degree: 11 },
      ],
      edges: [
        { source: 'Monkey D. Luffy', target: 'Straw Hat Pirates', weight: 5 },
        { source: 'Roronoa Zoro', target: 'Straw Hat Pirates', weight: 4 },
        { source: 'Nami', target: 'Straw Hat Pirates', weight: 4 },
        { source: 'Roronoa Zoro', target: 'Wano Country Arc', weight: 2 },
      ],
    },
    quality: [
      { check: 'Required title/source/pageid fields', status: 'passed', affected: 0 },
      { check: 'Missing infobox-like fields', status: 'warning', affected: 6 },
      { check: 'Duplicate page URLs', status: 'passed', affected: 0 },
      { check: 'Image metadata without downloadable file', status: 'warning', affected: 3 },
    ],
  },
  exports: [
    { format: 'SQLite', file: 'wiki_sample.sqlite', status: 'ready', rows: 764, size: '1.8 MB' },
    { format: 'JSONL', file: 'pages.jsonl.gz', status: 'ready', rows: 128, size: '246 KB' },
    { format: 'CSV', file: 'pages.csv', status: 'ready', rows: 128, size: '92 KB' },
    { format: 'Parquet', file: 'pages.parquet', status: 'planned', rows: 128, size: '64 KB' },
  ],
  complianceEvents: [
    { time: '09:10:00', level: 'info', event: 'Descriptive User-Agent configured', action: 'continue' },
    { time: '09:10:01', level: 'info', event: 'robots.txt checked for selected paths', action: 'continue' },
    { time: '09:10:04', level: 'info', event: 'Rate limit set to 30 requests/minute', action: 'continue' },
    { time: '09:12:18', level: 'warning', event: 'Transient 429 received from one API request', action: 'exponential backoff then retry' },
    { time: '09:16:22', level: 'warning', event: 'HTML page showed access restriction marker', action: 'record and skip; no bypass attempted' },
    { time: '09:18:42', level: 'info', event: 'Checkpoint and export manifest written', action: 'complete' },
  ],
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeJobStatus(job) {
  if (!job) return null;
  return {
    id: job.job_id,
    status: job.status,
    input: job.config?.input_source || '',
    startedAt: job.started_at,
    finishedAt: job.finished_at,
    counts: {
      pages: job.progress?.overall_completed || 0,
      errors: job.error ? 1 : 0,
    },
  };
}

async function tryLoadLiveSnapshot() {
  const jobs = await listUniversalJobs(5);
  const campaignList = await listCampaigns(5).catch(() => ({ items: [] }));
  const campaign = campaignList.items?.[0] || null;
  if (!Array.isArray(jobs) || jobs.length === 0) {
    if (campaign) {
      const live = clone(SAMPLE_RUN);
      const events = await getCampaignEvents(campaign.campaign_id, 100).catch(() => ({ events: [] }));
      const analysis = await getCampaignAnalysis(campaign.campaign_id).catch(() => ({ analysis: campaign.analysis || {} }));
      live.mode = DEMO_MODE.LIVE;
      live.demoNotice = 'Live multi-wiki campaign loaded from the local API.';
      live.run.id = campaign.campaign_id;
      live.run.status = campaign.status;
      live.run.input = `${campaign.targets?.length || 0} public Fandom wikis`;
      live.run.wikiName = 'Multi-wiki Campaign';
      live.run.normalizedBaseUrl = 'multiple Fandom domains';
      live.run.apiEndpoint = 'MediaWiki Action API per wiki';
      live.run.startedAt = campaign.started_at;
      live.run.finishedAt = campaign.finished_at;
      live.run.counts = { ...live.run.counts, ...(campaign.summary || analysis.analysis?.overview || {}) };
      live.live = { campaign, campaignEvents: events.events || [], campaignAnalysis: analysis.analysis || campaign.analysis || {} };
      return live;
    }
    throw new Error('No live jobs available');
  }

  const job = jobs[0];
  const [status, manifest, files, stats, logs] = await Promise.all([
    getUniversalStatus().catch(() => null),
    getUniversalJobManifest(job.job_id).catch(() => null),
    listUniversalJobFiles(job.job_id, 500).catch(() => ({ items: [] })),
    getUniversalJobOutputStats(job.job_id).catch(() => null),
    getUniversalJobLogs(job.job_id, 50).catch(() => []),
  ]);

  const live = clone(SAMPLE_RUN);
  live.mode = DEMO_MODE.LIVE;
  live.demoNotice = 'Live snapshot loaded from the local API. Missing sections still use demo placeholders.';
  live.run.id = job.job_id;
  live.run.status = status?.status || job.status;
  live.run.input = job.config?.input_source || live.run.input;
  live.run.wikiName = manifest?.manifest?.anime_name || live.run.wikiName;
  live.run.normalizedBaseUrl = manifest?.manifest?.wiki_url || live.run.normalizedBaseUrl;
  live.run.apiEndpoint = live.run.normalizedBaseUrl ? `${live.run.normalizedBaseUrl.replace(/\/$/, '')}/api.php` : live.run.apiEndpoint;
  live.run.startedAt = job.started_at || live.run.startedAt;
  live.run.finishedAt = job.finished_at || live.run.finishedAt;
  live.run.counts.pages = status?.progress?.overall_completed || live.run.counts.pages;
  live.live = {
    currentJob: normalizeJobStatus(job),
    campaign,
    files: files.items || [],
    outputStats: stats?.stats || null,
    logs,
  };
  if (campaign) {
    const events = await getCampaignEvents(campaign.campaign_id, 100).catch(() => ({ events: [] }));
    const analysis = await getCampaignAnalysis(campaign.campaign_id).catch(() => ({ analysis: campaign.analysis || {} }));
    live.demoNotice = 'Live snapshot loaded from the latest multi-wiki campaign and local job API.';
    live.run.id = campaign.campaign_id;
    live.run.status = campaign.status;
    live.run.input = `${campaign.targets?.length || 0} public Fandom wikis`;
    live.run.wikiName = 'Multi-wiki Campaign';
    live.run.counts = { ...live.run.counts, ...(campaign.summary || analysis.analysis?.overview || {}) };
    live.live.campaignEvents = events.events || [];
    live.live.campaignAnalysis = analysis.analysis || campaign.analysis || {};
  }

  return live;
}

export async function loadDemoSnapshot({ preferLive = true } = {}) {
  if (!preferLive) return clone(SAMPLE_RUN);

  try {
    return await tryLoadLiveSnapshot();
  } catch {
    return clone(SAMPLE_RUN);
  }
}

export async function loadPreviewRows(jobId, path, limit = 25) {
  if (!jobId || !path) return [];
  const preview = await previewUniversalJobFile(jobId, path, limit);
  if (preview.type === 'json') return [preview.data];
  return preview.items || [];
}

export function getSampleRun() {
  return clone(SAMPLE_RUN);
}
