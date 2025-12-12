/**
 * API Client - HTTP 請求封裝
 * 封裝 fetch，自動處理認證 Token、錯誤和重試
 */

import { getToken, logout, updateToken } from '../stores/authStore.js';

// API 基礎設定
const DEFAULT_CONFIG = {
    baseURL: '/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
};

/**
 * API 錯誤類別
 */
export class APIError extends Error {
    constructor(message, status, data = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

/**
 * API Client 類別
 */
export class APIClient {
    constructor(config = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
        this._requestInterceptors = [];
        this._responseInterceptors = [];
    }

    /**
     * 新增請求攔截器
     * @param {Function} interceptor - (config) => config
     */
    addRequestInterceptor(interceptor) {
        this._requestInterceptors.push(interceptor);
    }

    /**
     * 新增回應攔截器
     * @param {Function} interceptor - (response) => response
     */
    addResponseInterceptor(interceptor) {
        this._responseInterceptors.push(interceptor);
    }

    /**
     * 建立完整 URL
     * @private
     */
    _buildURL(path, params = {}) {
        const url = new URL(path, window.location.origin + this.config.baseURL + '/');

        // 處理查詢參數
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                if (Array.isArray(value)) {
                    value.forEach(v => url.searchParams.append(key, v));
                } else {
                    url.searchParams.append(key, value);
                }
            }
        });

        return url.toString();
    }

    /**
     * 執行請求
     * @private
     */
    async _request(method, path, options = {}) {
        const { params, data, headers: customHeaders, ...rest } = options;

        // 建立請求配置
        let config = {
            method,
            headers: { ...this.config.headers, ...customHeaders },
            ...rest
        };

        // 加入認證 Token
        const token = getToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        // 加入請求體
        if (data) {
            if (data instanceof FormData) {
                delete config.headers['Content-Type'];
                config.body = data;
            } else {
                config.body = JSON.stringify(data);
            }
        }

        // 執行請求攔截器
        for (const interceptor of this._requestInterceptors) {
            config = await interceptor(config);
        }

        // 建立 URL
        const url = this._buildURL(path, params);

        // 執行請求（帶超時）
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        try {
            let response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // 執行回應攔截器
            for (const interceptor of this._responseInterceptors) {
                response = await interceptor(response);
            }

            // 處理回應
            return await this._handleResponse(response);

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new APIError('請求超時', 408);
            }

            throw error;
        }
    }

    /**
     * 處理回應
     * @private
     */
    async _handleResponse(response) {
        // 嘗試解析 JSON
        let data;
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            try {
                data = await response.json();
            } catch {
                data = null;
            }
        } else {
            data = await response.text();
        }

        // 處理錯誤狀態
        if (!response.ok) {
            // 401 未授權 - 自動登出
            if (response.status === 401) {
                logout();
                window.location.hash = '#/login';
            }

            const message = data?.detail || data?.message || response.statusText;
            throw new APIError(message, response.status, data);
        }

        return data;
    }

    /**
     * GET 請求
     */
    async get(path, params = {}, options = {}) {
        return this._request('GET', path, { params, ...options });
    }

    /**
     * POST 請求
     */
    async post(path, data = {}, options = {}) {
        return this._request('POST', path, { data, ...options });
    }

    /**
     * PUT 請求
     */
    async put(path, data = {}, options = {}) {
        return this._request('PUT', path, { data, ...options });
    }

    /**
     * PATCH 請求
     */
    async patch(path, data = {}, options = {}) {
        return this._request('PATCH', path, { data, ...options });
    }

    /**
     * DELETE 請求
     */
    async delete(path, options = {}) {
        return this._request('DELETE', path, options);
    }

    /**
     * 上傳檔案
     */
    async upload(path, file, fieldName = 'file', extraData = {}) {
        const formData = new FormData();
        formData.append(fieldName, file);

        Object.entries(extraData).forEach(([key, value]) => {
            formData.append(key, value);
        });

        return this._request('POST', path, { data: formData });
    }

    /**
     * 下載檔案
     */
    async download(path, params = {}, filename = null) {
        const token = getToken();
        const url = this._buildURL(path, params);

        const response = await fetch(url, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (!response.ok) {
            throw new APIError('下載失敗', response.status);
        }

        const blob = await response.blob();

        // 從 Content-Disposition 取得檔名
        if (!filename) {
            const disposition = response.headers.get('content-disposition');
            if (disposition) {
                const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }
        }

        // 建立下載連結
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename || 'download';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);

        return { success: true, filename };
    }
}

// 預設 API Client 實例
export const api = new APIClient();

export default api;
