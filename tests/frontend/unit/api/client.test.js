/**
 * Unit tests for APIClient core class.
 *
 * Tests the HTTP client in frontend/js/api/client.js
 */

import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';

// Mock authStore before importing client
const mockGetToken = jest.fn();
const mockLogout = jest.fn();
const mockUpdateToken = jest.fn();

jest.unstable_mockModule('@/stores/authStore.js', () => ({
  getToken: mockGetToken,
  logout: mockLogout,
  updateToken: mockUpdateToken,
}));

// Now import the module under test
const { APIClient, APIError } = await import('@/api/client.js');

describe('APIClient', () => {
  let client;
  let fetchMock;

  beforeEach(() => {
    // Create fresh client instance
    client = new APIClient();

    // Setup fetch mock
    fetchMock = jest.fn();
    global.fetch = fetchMock;

    // Reset auth mocks
    mockGetToken.mockReturnValue(null);
    mockLogout.mockClear();
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  // ============================================================================
  // Construction and Configuration
  // ============================================================================

  describe('Constructor', () => {
    test('should initialize with default config', () => {
      const client = new APIClient();

      expect(client.config.baseURL).toBe('/api/v1');
      expect(client.config.timeout).toBe(30000);
      expect(client.config.headers['Content-Type']).toBe('application/json');
    });

    test('should merge custom config with defaults', () => {
      const customConfig = {
        baseURL: '/custom/api',
        timeout: 60000,
      };
      const client = new APIClient(customConfig);

      expect(client.config.baseURL).toBe('/custom/api');
      expect(client.config.timeout).toBe(60000);
      // Default headers should still be present
      expect(client.config.headers['Content-Type']).toBe('application/json');
    });

    test('should initialize interceptor arrays', () => {
      const client = new APIClient();

      expect(client._requestInterceptors).toEqual([]);
      expect(client._responseInterceptors).toEqual([]);
    });
  });

  // ============================================================================
  // Interceptors
  // ============================================================================

  describe('Interceptors', () => {
    test('should add request interceptor', () => {
      const interceptor = jest.fn((config) => config);

      client.addRequestInterceptor(interceptor);

      expect(client._requestInterceptors).toHaveLength(1);
      expect(client._requestInterceptors[0]).toBe(interceptor);
    });

    test('should add response interceptor', () => {
      const interceptor = jest.fn((response) => response);

      client.addResponseInterceptor(interceptor);

      expect(client._responseInterceptors).toHaveLength(1);
      expect(client._responseInterceptors[0]).toBe(interceptor);
    });

    test('should execute request interceptors in order', async () => {
      const order = [];
      const interceptor1 = jest.fn(async (config) => {
        order.push(1);
        return config;
      });
      const interceptor2 = jest.fn(async (config) => {
        order.push(2);
        return config;
      });

      client.addRequestInterceptor(interceptor1);
      client.addRequestInterceptor(interceptor2);

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await client.get('/test');

      expect(order).toEqual([1, 2]);
    });

    test('should execute response interceptors in order', async () => {
      const order = [];
      const interceptor1 = jest.fn(async (response) => {
        order.push(1);
        return response;
      });
      const interceptor2 = jest.fn(async (response) => {
        order.push(2);
        return response;
      });

      client.addResponseInterceptor(interceptor1);
      client.addResponseInterceptor(interceptor2);

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await client.get('/test');

      expect(order).toEqual([1, 2]);
    });
  });

  // ============================================================================
  // URL Building
  // ============================================================================

  describe('_buildURL', () => {
    test('should build URL with base URL', () => {
      const url = client._buildURL('/users');

      expect(url).toContain('/users');
      expect(url).toMatch(/^http/); // Should be absolute URL
    });

    test('should append query parameters', () => {
      const url = client._buildURL('/users', { id: 123, name: 'test' });

      expect(url).toContain('id=123');
      expect(url).toContain('name=test');
    });

    test('should skip null and undefined parameters', () => {
      const url = client._buildURL('/users', {
        id: 123,
        name: null,
        email: undefined,
        status: '',
      });

      expect(url).toContain('id=123');
      expect(url).not.toContain('name');
      expect(url).not.toContain('email');
      expect(url).not.toContain('status');
    });

    test('should handle array parameters', () => {
      const url = client._buildURL('/users', { tags: ['tag1', 'tag2', 'tag3'] });

      expect(url).toContain('tags=tag1');
      expect(url).toContain('tags=tag2');
      expect(url).toContain('tags=tag3');
    });
  });

  // ============================================================================
  // Request Methods
  // ============================================================================

  describe('GET Request', () => {
    test('should make GET request successfully', async () => {
      const mockData = { id: 1, name: 'Test' };
      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await client.get('/users/1');

      expect(fetchMock).toHaveBeenCalled();
      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[0]).toContain('/users/1');
      expect(callArgs[1].method).toBe('GET');
      expect(result).toEqual(mockData);
    });

    test('should include query parameters in GET request', async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await client.get('/users', { page: 1, limit: 10 });

      const url = fetchMock.mock.calls[0][0];
      expect(url).toContain('page=1');
      expect(url).toContain('limit=10');
    });
  });

  describe('POST Request', () => {
    test('should make POST request with JSON body', async () => {
      const postData = { name: 'New User', email: 'test@example.com' };
      const mockResponse = { id: 1, ...postData };

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await client.post('/users', postData);

      expect(fetchMock).toHaveBeenCalled();
      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].method).toBe('POST');
      expect(callArgs[1].body).toBe(JSON.stringify(postData));
      expect(callArgs[1].headers['Content-Type']).toBe('application/json');
      expect(result).toEqual(mockResponse);
    });

    test('should handle FormData POST', async () => {
      const formData = new FormData();
      formData.append('file', 'test-file');

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      });

      await client.post('/upload', formData);

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].body).toBe(formData);
      expect(callArgs[1].headers['Content-Type']).toBeUndefined(); // FormData sets it automatically
    });
  });

  describe('PUT Request', () => {
    test('should make PUT request with JSON body', async () => {
      const updateData = { name: 'Updated Name' };
      const mockResponse = { id: 1, ...updateData };

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await client.put('/users/1', updateData);

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].method).toBe('PUT');
      expect(callArgs[1].body).toBe(JSON.stringify(updateData));
      expect(result).toEqual(mockResponse);
    });
  });

  describe('PATCH Request', () => {
    test('should make PATCH request with JSON body', async () => {
      const patchData = { status: 'active' };
      const mockResponse = { id: 1, status: 'active' };

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse,
      });

      const result = await client.patch('/users/1', patchData);

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].method).toBe('PATCH');
      expect(callArgs[1].body).toBe(JSON.stringify(patchData));
      expect(result).toEqual(mockResponse);
    });
  });

  describe('DELETE Request', () => {
    test('should make DELETE request', async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      });

      const result = await client.delete('/users/1');

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].method).toBe('DELETE');
      expect(result).toEqual({ success: true });
    });
  });

  // ============================================================================
  // Authentication
  // ============================================================================

  describe('Authentication', () => {
    test('should include Authorization header when token exists', async () => {
      mockGetToken.mockReturnValue('test-token-123');

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await client.get('/users');

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].headers['Authorization']).toBe('Bearer test-token-123');
    });

    test('should not include Authorization header when no token', async () => {
      mockGetToken.mockReturnValue(null);

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      });

      await client.get('/users');

      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].headers['Authorization']).toBeUndefined();
    });

    test('should logout and redirect on 401 error', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Unauthorized' }),
      });

      await expect(client.get('/users')).rejects.toThrow(APIError);

      expect(mockLogout).toHaveBeenCalled();
      expect(window.location.hash).toBe('#/login');
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('Error Handling', () => {
    test('should throw APIError on HTTP error', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'User not found' }),
      });

      await expect(client.get('/users/999')).rejects.toThrow(APIError);
      await expect(client.get('/users/999')).rejects.toThrow('User not found');
    });

    test('should handle timeout', async () => {
      // Mock AbortController
      const abortController = {
        signal: {},
        abort: jest.fn(),
      };
      global.AbortController = jest.fn(() => abortController);

      fetchMock.mockImplementation(() =>
        new Promise((resolve, reject) => {
          setTimeout(() => {
            const error = new Error('Aborted');
            error.name = 'AbortError';
            reject(error);
          }, 100);
        })
      );

      jest.useFakeTimers();

      const promise = client.get('/slow-endpoint');

      jest.advanceTimersByTime(30000); // Advance past timeout

      await expect(promise).rejects.toThrow(APIError);
      await expect(promise).rejects.toThrow('請求超時');

      jest.useRealTimers();
    });

    test('should handle non-JSON responses', async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => 'Plain text response',
      });

      const result = await client.get('/text-endpoint');

      expect(result).toBe('Plain text response');
    });

    test('should handle malformed JSON', async () => {
      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      const result = await client.get('/bad-json');

      expect(result).toBeNull();
    });
  });

  // ============================================================================
  // File Upload/Download
  // ============================================================================

  describe('File Upload', () => {
    test('should upload file with correct format', async () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });
      const extraData = { description: 'Test file' };

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, fileId: '123' }),
      });

      const result = await client.upload('/files', file, 'document', extraData);

      expect(fetchMock).toHaveBeenCalled();
      const callArgs = fetchMock.mock.calls[0];
      expect(callArgs[1].method).toBe('POST');
      expect(callArgs[1].body).toBeInstanceOf(FormData);
      expect(result.success).toBe(true);
      expect(result.fileId).toBe('123');
    });
  });

  describe('File Download', () => {
    test('should download file and create download link', async () => {
      const mockBlob = new Blob(['file content'], { type: 'text/plain' });
      const mockHeaders = new Headers({
        'content-disposition': 'attachment; filename="test.txt"',
      });

      fetchMock.mockResolvedValue({
        ok: true,
        headers: mockHeaders,
        blob: async () => mockBlob,
      });

      // Mock URL methods
      const mockCreateObjectURL = jest.fn().mockReturnValue('blob:test-url');
      const mockRevokeObjectURL = jest.fn();
      global.URL.createObjectURL = mockCreateObjectURL;
      global.URL.revokeObjectURL = mockRevokeObjectURL;

      // Mock DOM methods
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      };
      const mockCreateElement = jest.spyOn(document, 'createElement').mockReturnValue(mockLink);
      const mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
      const mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});

      const result = await client.download('/files/123');

      expect(result.success).toBe(true);
      expect(result.filename).toBe('test.txt');
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test-url');

      // Cleanup
      mockCreateElement.mockRestore();
      mockAppendChild.mockRestore();
      mockRemoveChild.mockRestore();
    });

    test('should use custom filename if provided', async () => {
      const mockBlob = new Blob(['file content']);

      fetchMock.mockResolvedValue({
        ok: true,
        headers: new Headers(),
        blob: async () => mockBlob,
      });

      // Mock URL methods
      global.URL.createObjectURL = jest.fn().mockReturnValue('blob:test-url');
      global.URL.revokeObjectURL = jest.fn();

      const mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});

      await client.download('/files/123', {}, 'custom.txt');

      expect(mockLink.download).toBe('custom.txt');
    });
  });
});

// ============================================================================
// APIError Class
// ============================================================================

describe('APIError', () => {
  test('should create error with message and status', () => {
    const error = new APIError('Not found', 404);

    expect(error.message).toBe('Not found');
    expect(error.status).toBe(404);
    expect(error.name).toBe('APIError');
    expect(error.data).toBeNull();
  });

  test('should create error with data', () => {
    const errorData = { field: 'email', message: 'Invalid email' };
    const error = new APIError('Validation failed', 400, errorData);

    expect(error.status).toBe(400);
    expect(error.data).toEqual(errorData);
  });

  test('should be instance of Error', () => {
    const error = new APIError('Test error', 500);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(APIError);
  });
});
