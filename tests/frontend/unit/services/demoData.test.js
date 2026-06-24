import { describe, test, expect, beforeEach, jest } from '@jest/globals';

const mockGetUniversalStatus = jest.fn();
const mockListUniversalJobs = jest.fn();
const mockGetUniversalJobManifest = jest.fn();
const mockListUniversalJobFiles = jest.fn();
const mockPreviewUniversalJobFile = jest.fn();
const mockGetUniversalJobOutputStats = jest.fn();
const mockGetUniversalJobLogs = jest.fn();
const mockListCampaigns = jest.fn();
const mockGetCampaignEvents = jest.fn();
const mockGetCampaignAnalysis = jest.fn();

jest.unstable_mockModule('@/api/scraper.js', () => ({
  getUniversalStatus: mockGetUniversalStatus,
  listUniversalJobs: mockListUniversalJobs,
  getUniversalJobManifest: mockGetUniversalJobManifest,
  listUniversalJobFiles: mockListUniversalJobFiles,
  previewUniversalJobFile: mockPreviewUniversalJobFile,
  getUniversalJobOutputStats: mockGetUniversalJobOutputStats,
  getUniversalJobLogs: mockGetUniversalJobLogs,
  listCampaigns: mockListCampaigns,
  getCampaignEvents: mockGetCampaignEvents,
  getCampaignAnalysis: mockGetCampaignAnalysis,
}));

const {
  DEMO_MODE,
  getSampleRun,
  loadDemoSnapshot,
  loadPreviewRows,
} = await import('@/services/demoData.js');

describe('demoData service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockListCampaigns.mockResolvedValue({ items: [] });
    mockGetCampaignEvents.mockResolvedValue({ events: [] });
    mockGetCampaignAnalysis.mockResolvedValue({ analysis: {} });
  });

  test('returns a stable demo snapshot when live API is disabled', async () => {
    const snapshot = await loadDemoSnapshot({ preferLive: false });

    expect(snapshot.mode).toBe(DEMO_MODE.DEMO);
    expect(snapshot.run.apiEndpoint).toContain('/api.php');
    expect(snapshot.pipelineSteps.some(step => step.method === 'Action API')).toBe(true);
    expect(snapshot.collections.pages.length).toBeGreaterThan(0);
    expect(snapshot.complianceEvents.length).toBeGreaterThan(0);
  });

  test('falls back to demo data when live jobs are unavailable', async () => {
    mockListUniversalJobs.mockRejectedValue(new Error('Redis disabled'));

    const snapshot = await loadDemoSnapshot();

    expect(snapshot.mode).toBe(DEMO_MODE.DEMO);
    expect(snapshot.run.id).toBe('demo-onepiece-action-api-001');
  });

  test('maps a live campaign when jobs are unavailable', async () => {
    mockListUniversalJobs.mockResolvedValue([]);
    mockListCampaigns.mockResolvedValue({
      items: [
        {
          campaign_id: 'portfolio-smoke',
          status: 'finished',
          targets: ['https://onepiece.fandom.com'],
          summary: { pages: 50, links: 100, errors: 0 },
          analysis: { overview: { pages: 50 } },
        },
      ],
    });
    mockGetCampaignEvents.mockResolvedValue({ events: [{ stage: 'campaign_finish', status: 'finished' }] });
    mockGetCampaignAnalysis.mockResolvedValue({ analysis: { overview: { pages: 50 } } });

    const snapshot = await loadDemoSnapshot();

    expect(snapshot.mode).toBe(DEMO_MODE.LIVE);
    expect(snapshot.run.id).toBe('portfolio-smoke');
    expect(snapshot.run.counts.pages).toBe(50);
    expect(snapshot.live.campaignEvents).toHaveLength(1);
  });

  test('maps a live job into the portfolio snapshot shape', async () => {
    mockListUniversalJobs.mockResolvedValue([
      {
        job_id: 'job-live-1',
        status: 'running',
        started_at: '2026-06-24T10:00:00Z',
        config: { input_source: 'https://example.fandom.com' },
      },
    ]);
    mockGetUniversalStatus.mockResolvedValue({
      status: 'running',
      progress: { overall_completed: 12 },
    });
    mockGetUniversalJobManifest.mockResolvedValue({
      manifest: {
        anime_name: 'Example Wiki',
        wiki_url: 'https://example.fandom.com',
      },
    });
    mockListUniversalJobFiles.mockResolvedValue({ items: [{ type: 'file', path: 'data/pages.jsonl.gz' }] });
    mockGetUniversalJobOutputStats.mockResolvedValue({ stats: { total_files: 1, total_bytes: 100 } });
    mockGetUniversalJobLogs.mockResolvedValue(['started']);

    const snapshot = await loadDemoSnapshot();

    expect(snapshot.mode).toBe(DEMO_MODE.LIVE);
    expect(snapshot.run.id).toBe('job-live-1');
    expect(snapshot.run.apiEndpoint).toBe('https://example.fandom.com/api.php');
    expect(snapshot.live.files).toHaveLength(1);
  });

  test('loadPreviewRows returns jsonl items or wraps json preview data', async () => {
    mockPreviewUniversalJobFile.mockResolvedValueOnce({ type: 'jsonl', items: [{ title: 'Page' }] });
    await expect(loadPreviewRows('job-1', 'data/pages.jsonl.gz')).resolves.toEqual([{ title: 'Page' }]);

    mockPreviewUniversalJobFile.mockResolvedValueOnce({ type: 'json', data: { manifest: true } });
    await expect(loadPreviewRows('job-1', 'manifest.json')).resolves.toEqual([{ manifest: true }]);
  });

  test('getSampleRun returns a defensive copy', () => {
    const first = getSampleRun();
    first.run.id = 'mutated';

    expect(getSampleRun().run.id).toBe('demo-onepiece-action-api-001');
  });
});
