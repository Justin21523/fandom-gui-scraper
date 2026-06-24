/**
 * Unit tests for Scraper API client.
 *
 * Tests the API functions in frontend/js/api/scraper.js
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Mock the API client before importing scraper
const mockGet = jest.fn();
const mockPost = jest.fn();
const mockDelete = jest.fn();
const mockBuildURL = jest.fn((path, params = {}) => {
  const query = new URLSearchParams(params).toString();
  return `http://localhost/api/v1${path}${query ? `?${query}` : ''}`;
});

jest.unstable_mockModule('@/api/client.js', () => ({
  default: {
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
    _buildURL: mockBuildURL,
  },
}));

// Now import the module under test
const {
  // Universal Scraper
  searchAnime,
  startUniversalScraper,
  getUniversalStatus,
  stopUniversalScraper,
  pauseUniversalScraper,
  resumeUniversalScraper,
  getUniversalLogs,
  getUniversalJobWikiSummary,
  getUniversalJobWikiTables,
  browseUniversalJobWikiTable,
  getUniversalJobWikiPage,
  getUniversalJobWikiAnalysis,
  buildUniversalJobWikiExportUrl,
  listCampaigns,
  listCampaignPresets,
  getCampaign,
  getCampaignEvents,
  getCampaignAnalysis,
  runCampaign,
  // Legacy Scraper
  getPresets,
  startScraper,
  stopScraper,
  pauseScraper,
  resumeScraper,
  getScraperStatus,
  getScraperHistory,
  getScraperLogs,
  validateUrl,
  testSelectors,
  getScraperStats,
  saveConfig,
  getConfig,
  getConfigs,
  deleteConfig,
} = await import('@/api/scraper.js');

describe('Scraper API Client - Universal Scraper', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('searchAnime', () => {
    test('should search for anime with default top_n', async () => {
      const mockResults = [
        {
          url: 'https://onepiece.fandom.com/wiki/Main_Page',
          domain: 'onepiece',
          title: 'One Piece Wiki',
          relevance_score: 95.5,
        },
      ];
      mockPost.mockResolvedValue(mockResults);

      const result = await searchAnime('One Piece');

      expect(mockPost).toHaveBeenCalledWith('/scraper/search-anime', {
        anime_name: 'One Piece',
        top_n: 5,
      });
      expect(result).toEqual(mockResults);
    });

    test('should search for anime with custom top_n', async () => {
      const mockResults = [];
      mockPost.mockResolvedValue(mockResults);

      await searchAnime('Naruto', 10);

      expect(mockPost).toHaveBeenCalledWith('/scraper/search-anime', {
        anime_name: 'Naruto',
        top_n: 10,
      });
    });

    test('should handle search errors', async () => {
      mockPost.mockRejectedValue(new Error('API Error'));

      await expect(searchAnime('Invalid')).rejects.toThrow('API Error');
    });
  });

  describe('startUniversalScraper', () => {
    test('should start scraper with full config', async () => {
      const config = {
        input_source: 'One Piece',
        input_type: 'name',
        crawl_characters: true,
        crawl_episodes: true,
        max_chars: 100,
        max_episodes: 50,
      };
      const mockResponse = { message: 'Scraper started', status: 'running' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await startUniversalScraper(config);

      expect(mockPost).toHaveBeenCalledWith('/scraper/start-universal', config);
      expect(result).toEqual(mockResponse);
    });

    test('should handle start errors', async () => {
      mockPost.mockRejectedValue(new Error('Already running'));

      await expect(startUniversalScraper({})).rejects.toThrow('Already running');
    });
  });

  describe('getUniversalStatus', () => {
    test('should get scraper status', async () => {
      const mockStatus = {
        status: 'running',
        anime_name: 'One Piece',
        progress: {
          overall_completed: 50,
          overall_total: 100,
        },
      };
      mockGet.mockResolvedValue(mockStatus);

      const result = await getUniversalStatus();

      expect(mockGet).toHaveBeenCalledWith('/scraper/universal-status');
      expect(result).toEqual(mockStatus);
    });

    test('should handle status fetch errors', async () => {
      mockGet.mockRejectedValue(new Error('Network error'));

      await expect(getUniversalStatus()).rejects.toThrow('Network error');
    });
  });

  describe('stopUniversalScraper', () => {
    test('should stop the scraper', async () => {
      const mockResponse = { message: 'Scraper stopped', status: 'stopped' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await stopUniversalScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/stop-universal');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('pauseUniversalScraper', () => {
    test('should pause the scraper', async () => {
      const mockResponse = { message: 'Scraper paused', status: 'paused' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await pauseUniversalScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/pause-universal');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('resumeUniversalScraper', () => {
    test('should resume the scraper', async () => {
      const mockResponse = { message: 'Scraper resumed', status: 'running' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await resumeUniversalScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/resume-universal');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getUniversalLogs', () => {
    test('should get logs with default options', async () => {
      const mockLogs = [
        { timestamp: '2023-05-15T10:00:00', level: 'INFO', message: 'Test log' },
      ];
      mockGet.mockResolvedValue(mockLogs);

      const result = await getUniversalLogs();

      expect(mockGet).toHaveBeenCalledWith('/scraper/universal-logs', {
        limit: 100,
        level: 'all',
      });
      expect(result).toEqual(mockLogs);
    });

    test('should get logs with custom options', async () => {
      const mockLogs = [];
      mockGet.mockResolvedValue(mockLogs);

      await getUniversalLogs({ limit: 50, level: 'ERROR' });

      expect(mockGet).toHaveBeenCalledWith('/scraper/universal-logs', {
        limit: 50,
        level: 'ERROR',
      });
    });
  });

  describe('wiki.db APIs', () => {
    test('should fetch wiki db summary', async () => {
      mockGet.mockResolvedValue({ summary: { counts: { pages: 1 } } });

      await getUniversalJobWikiSummary('job-1');

      expect(mockGet).toHaveBeenCalledWith('/scraper/jobs/job-1/wiki-db/summary');
    });

    test('should browse wiki db table with options', async () => {
      mockGet.mockResolvedValue({ items: [] });

      await browseUniversalJobWikiTable('job-1', 'pages', { limit: 25, offset: 50, q: 'Luffy' });

      expect(mockGet).toHaveBeenCalledWith('/scraper/jobs/job-1/wiki-db/table/pages', {
        limit: 25,
        offset: 50,
        q: 'Luffy',
      });
    });

    test('should fetch wiki db tables, page detail, analysis, and export URL', async () => {
      mockGet.mockResolvedValue({});

      await getUniversalJobWikiTables('job-1');
      await getUniversalJobWikiPage('job-1', 7);
      await getUniversalJobWikiAnalysis('job-1');
      const url = buildUniversalJobWikiExportUrl('job-1', 'pages', 'csv');

      expect(mockGet).toHaveBeenCalledWith('/scraper/jobs/job-1/wiki-db/tables');
      expect(mockGet).toHaveBeenCalledWith('/scraper/jobs/job-1/wiki-db/pages/7');
      expect(mockGet).toHaveBeenCalledWith('/scraper/jobs/job-1/wiki-db/analysis');
      expect(url).toContain('/scraper/jobs/job-1/wiki-db/export?dataset=pages&format=csv');
    });
  });

  describe('campaign APIs', () => {
    test('should call campaign endpoints', async () => {
      mockGet.mockResolvedValue({});
      mockPost.mockResolvedValue({ status: 'queued' });

      await listCampaigns(5);
      await listCampaignPresets();
      await getCampaign('portfolio-smoke');
      await getCampaignEvents('portfolio-smoke', 50);
      await getCampaignAnalysis('portfolio-smoke');
      await runCampaign({ campaign_id: 'portfolio-smoke' });

      expect(mockGet).toHaveBeenCalledWith('/scraper/campaigns', { limit: 5 });
      expect(mockGet).toHaveBeenCalledWith('/scraper/campaigns/presets');
      expect(mockGet).toHaveBeenCalledWith('/scraper/campaigns/portfolio-smoke');
      expect(mockGet).toHaveBeenCalledWith('/scraper/campaigns/portfolio-smoke/events', { limit: 50 });
      expect(mockGet).toHaveBeenCalledWith('/scraper/campaigns/portfolio-smoke/analysis');
      expect(mockPost).toHaveBeenCalledWith('/scraper/campaigns/run', { campaign_id: 'portfolio-smoke' });
    });
  });
});

// ============================================================================
// Legacy Scraper API Tests
// ============================================================================

describe('Scraper API Client - Legacy Scraper', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getPresets', () => {
    test('should fetch anime presets', async () => {
      const mockPresets = [
        { name: 'One Piece', base_url: 'https://onepiece.fandom.com' },
        { name: 'Naruto', base_url: 'https://naruto.fandom.com' },
      ];
      mockGet.mockResolvedValue(mockPresets);

      const result = await getPresets();

      expect(mockGet).toHaveBeenCalledWith('/scraper/presets');
      expect(result).toEqual(mockPresets);
    });

    test('should handle empty presets', async () => {
      mockGet.mockResolvedValue([]);

      const result = await getPresets();

      expect(result).toEqual([]);
    });
  });

  describe('startScraper', () => {
    test('should start legacy scraper with config', async () => {
      const config = {
        base_url: 'https://onepiece.fandom.com',
        character_list_url: '/wiki/Category:Characters',
        delay: 1.0,
      };
      const mockResponse = { message: 'Started', status: 'running' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await startScraper(config);

      expect(mockPost).toHaveBeenCalledWith('/scraper/start', config);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('stopScraper', () => {
    test('should stop legacy scraper', async () => {
      const mockResponse = { message: 'Stopped', status: 'stopped' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await stopScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/stop');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('pauseScraper', () => {
    test('should pause legacy scraper', async () => {
      const mockResponse = { message: 'Paused', status: 'paused' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await pauseScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/pause');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('resumeScraper', () => {
    test('should resume legacy scraper', async () => {
      const mockResponse = { message: 'Resumed', status: 'running' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await resumeScraper();

      expect(mockPost).toHaveBeenCalledWith('/scraper/resume');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getScraperStatus', () => {
    test('should get legacy scraper status', async () => {
      const mockStatus = {
        status: 'running',
        progress: { completed: 50, total: 100 },
      };
      mockGet.mockResolvedValue(mockStatus);

      const result = await getScraperStatus();

      expect(mockGet).toHaveBeenCalledWith('/scraper/status');
      expect(result).toEqual(mockStatus);
    });
  });

  describe('getScraperHistory', () => {
    test('should get scraper history with default options', async () => {
      const mockHistory = [
        { anime: 'One Piece', completed: 100, timestamp: '2023-01-01' },
      ];
      mockGet.mockResolvedValue(mockHistory);

      const result = await getScraperHistory();

      expect(mockGet).toHaveBeenCalledWith('/scraper/history', {});
      expect(result).toEqual(mockHistory);
    });

    test('should get scraper history with options', async () => {
      const options = { limit: 10, offset: 0 };
      mockGet.mockResolvedValue([]);

      await getScraperHistory(options);

      expect(mockGet).toHaveBeenCalledWith('/scraper/history', options);
    });
  });

  describe('getScraperLogs', () => {
    test('should get logs with default options', async () => {
      const mockLogs = [
        { level: 'INFO', message: 'Test log', timestamp: '2023-01-01T10:00:00' },
      ];
      mockGet.mockResolvedValue(mockLogs);

      const result = await getScraperLogs();

      expect(mockGet).toHaveBeenCalledWith('/scraper/logs', {
        limit: 100,
        level: 'all',
        since: null,
      });
      expect(result).toEqual(mockLogs);
    });

    test('should get logs with custom options', async () => {
      const options = { limit: 50, level: 'ERROR', since: '2023-01-01' };
      mockGet.mockResolvedValue([]);

      await getScraperLogs(options);

      expect(mockGet).toHaveBeenCalledWith('/scraper/logs', options);
    });
  });

  describe('validateUrl', () => {
    test('should validate a URL', async () => {
      const url = 'https://onepiece.fandom.com/wiki/Characters';
      const mockResponse = { valid: true, message: 'URL is valid' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await validateUrl(url);

      expect(mockPost).toHaveBeenCalledWith('/scraper/validate-url', { url });
      expect(result).toEqual(mockResponse);
    });

    test('should handle invalid URL', async () => {
      const mockResponse = { valid: false, message: 'Invalid URL' };
      mockPost.mockResolvedValue(mockResponse);

      const result = await validateUrl('invalid-url');

      expect(result.valid).toBe(false);
    });
  });

  describe('testSelectors', () => {
    test('should test selectors on a URL', async () => {
      const url = 'https://onepiece.fandom.com/wiki/Luffy';
      const selectors = { name: 'h1.title', description: 'p.description' };
      const mockResponse = {
        name: 'Monkey D. Luffy',
        description: 'Protagonist of One Piece',
      };
      mockPost.mockResolvedValue(mockResponse);

      const result = await testSelectors(url, selectors);

      expect(mockPost).toHaveBeenCalledWith('/scraper/test-selectors', {
        url,
        selectors,
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getScraperStats', () => {
    test('should get scraper statistics', async () => {
      const mockStats = {
        total_scraped: 1000,
        successful: 950,
        failed: 50,
        status: 'idle',
      };
      mockGet.mockResolvedValue(mockStats);

      const result = await getScraperStats();

      expect(mockGet).toHaveBeenCalledWith('/scraper/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('Configuration Management', () => {
    describe('saveConfig', () => {
      test('should save a configuration', async () => {
        const name = 'my-config';
        const config = { base_url: 'https://test.fandom.com', delay: 1.5 };
        const mockResponse = { message: 'Config saved', name };
        mockPost.mockResolvedValue(mockResponse);

        const result = await saveConfig(name, config);

        expect(mockPost).toHaveBeenCalledWith(
          `/scraper/configs?name=${encodeURIComponent(name)}`,
          config
        );
        expect(result).toEqual(mockResponse);
      });

      test('should encode config name with special characters', async () => {
        const name = 'my config #1';
        const config = {};
        mockPost.mockResolvedValue({});

        await saveConfig(name, config);

        expect(mockPost).toHaveBeenCalledWith(
          `/scraper/configs?name=${encodeURIComponent(name)}`,
          config
        );
      });
    });

    describe('getConfig', () => {
      test('should get a specific configuration', async () => {
        const name = 'my-config';
        const mockConfig = {
          name,
          config: { base_url: 'https://test.fandom.com' },
        };
        mockGet.mockResolvedValue(mockConfig);

        const result = await getConfig(name);

        expect(mockGet).toHaveBeenCalledWith(
          `/scraper/configs/${encodeURIComponent(name)}`
        );
        expect(result).toEqual(mockConfig);
      });
    });

    describe('getConfigs', () => {
      test('should get all configurations', async () => {
        const mockConfigs = [
          { name: 'config1', config: {} },
          { name: 'config2', config: {} },
        ];
        mockGet.mockResolvedValue(mockConfigs);

        const result = await getConfigs();

        expect(mockGet).toHaveBeenCalledWith('/scraper/configs');
        expect(result).toEqual(mockConfigs);
      });

      test('should handle empty configurations', async () => {
        mockGet.mockResolvedValue([]);

        const result = await getConfigs();

        expect(result).toEqual([]);
      });
    });

    describe('deleteConfig', () => {
      test('should delete a configuration', async () => {
        const name = 'my-config';
        const mockResponse = { message: 'Config deleted' };
        mockDelete.mockResolvedValue(mockResponse);

        const result = await deleteConfig(name);

        expect(mockDelete).toHaveBeenCalledWith(
          `/scraper/configs/${encodeURIComponent(name)}`
        );
        expect(result).toEqual(mockResponse);
      });
    });
  });
});
