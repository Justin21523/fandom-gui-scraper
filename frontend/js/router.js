/**
 * Router - 前端路由器
 * 基於 Hash 的單頁應用路由
 */

/**
 * 路由器類別
 */
export class Router {
    constructor(options = {}) {
        this.routes = new Map();
        this.beforeHooks = [];
        this.afterHooks = [];
        this.errorHandler = options.errorHandler || this._defaultErrorHandler;
        this.notFoundHandler = options.notFound || null;
        this.currentRoute = null;
        this.params = {};
        this.query = {};

        // 綁定事件
        this._onHashChange = this._onHashChange.bind(this);
        window.addEventListener('hashchange', this._onHashChange);
    }

    /**
     * 註冊路由
     * @param {string} path - 路由路徑（支援參數如 /users/:id）
     * @param {Function} handler - 路由處理函數
     * @param {Object} meta - 路由元資料
     */
    register(path, handler, meta = {}) {
        // 將路徑轉換為正則表達式
        const paramNames = [];
        const pattern = path.replace(/:([^/]+)/g, (_, name) => {
            paramNames.push(name);
            return '([^/]+)';
        });

        this.routes.set(path, {
            pattern: new RegExp(`^${pattern}$`),
            paramNames,
            handler,
            meta
        });

        return this;
    }

    /**
     * 批次註冊路由
     * @param {Object} routes - 路由配置物件
     */
    registerAll(routes) {
        Object.entries(routes).forEach(([path, config]) => {
            if (typeof config === 'function') {
                this.register(path, config);
            } else {
                this.register(path, config.handler, config.meta);
            }
        });

        return this;
    }

    /**
     * 新增導航前鉤子
     * @param {Function} hook - (to, from, next) => void
     */
    beforeEach(hook) {
        this.beforeHooks.push(hook);
        return this;
    }

    /**
     * 新增導航後鉤子
     * @param {Function} hook - (to, from) => void
     */
    afterEach(hook) {
        this.afterHooks.push(hook);
        return this;
    }

    /**
     * 導航到指定路徑
     * @param {string} path - 目標路徑
     * @param {Object} options - 導航選項
     */
    navigate(path, options = {}) {
        const { replace = false, query = {} } = options;

        // 建立查詢字串
        const queryString = Object.entries(query)
            .filter(([_, v]) => v !== undefined && v !== null)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&');

        const fullPath = queryString ? `${path}?${queryString}` : path;

        if (replace) {
            window.location.replace(`#${fullPath}`);
        } else {
            window.location.hash = fullPath;
        }
    }

    /**
     * 返回上一頁
     */
    back() {
        window.history.back();
    }

    /**
     * 前進一頁
     */
    forward() {
        window.history.forward();
    }

    /**
     * 取得當前路徑
     * @returns {string}
     */
    getCurrentPath() {
        const hash = window.location.hash.slice(1) || '/';
        return hash.split('?')[0];
    }

    /**
     * 取得當前查詢參數
     * @returns {Object}
     */
    getQuery() {
        const hash = window.location.hash.slice(1) || '/';
        const queryString = hash.split('?')[1] || '';
        const query = {};

        new URLSearchParams(queryString).forEach((value, key) => {
            query[key] = value;
        });

        return query;
    }

    /**
     * 啟動路由器
     */
    start() {
        // 如果沒有 hash，設定為首頁
        if (!window.location.hash) {
            window.location.hash = '#/';
        }

        this._onHashChange();
        return this;
    }

    /**
     * 停止路由器
     */
    stop() {
        window.removeEventListener('hashchange', this._onHashChange);
    }

    /**
     * 處理 hash 變化
     * @private
     */
    async _onHashChange() {
        const path = this.getCurrentPath();
        const query = this.getQuery();

        // 尋找匹配的路由
        let matchedRoute = null;
        let params = {};

        for (const [routePath, route] of this.routes) {
            const match = path.match(route.pattern);
            if (match) {
                matchedRoute = { path: routePath, ...route };
                // 提取參數
                route.paramNames.forEach((name, index) => {
                    params[name] = decodeURIComponent(match[index + 1]);
                });
                break;
            }
        }

        // 404 處理
        if (!matchedRoute) {
            if (this.notFoundHandler) {
                await this.notFoundHandler(path);
            }
            return;
        }

        // 建立路由物件
        const to = {
            path,
            params,
            query,
            meta: matchedRoute.meta
        };

        const from = this.currentRoute;

        // 執行 beforeEach 鉤子
        try {
            for (const hook of this.beforeHooks) {
                const result = await this._runHook(hook, to, from);
                if (result === false) {
                    return; // 取消導航
                }
                if (typeof result === 'string') {
                    this.navigate(result, { replace: true });
                    return;
                }
            }
        } catch (error) {
            this.errorHandler(error, to, from);
            return;
        }

        // 更新當前路由
        this.currentRoute = to;
        this.params = params;
        this.query = query;

        // 執行路由處理函數
        try {
            await matchedRoute.handler(to);
        } catch (error) {
            this.errorHandler(error, to, from);
        }

        // 執行 afterEach 鉤子
        for (const hook of this.afterHooks) {
            try {
                await hook(to, from);
            } catch (error) {
                console.error('afterEach hook error:', error);
            }
        }
    }

    /**
     * 執行鉤子
     * @private
     */
    _runHook(hook, to, from) {
        return new Promise((resolve, reject) => {
            const next = (result) => {
                if (result instanceof Error) {
                    reject(result);
                } else {
                    resolve(result);
                }
            };

            try {
                const result = hook(to, from, next);
                // 如果 hook 沒有呼叫 next，檢查是否返回 Promise
                if (result instanceof Promise) {
                    result.then(resolve).catch(reject);
                } else if (result !== undefined) {
                    resolve(result);
                }
                // 如果 hook 有三個參數（使用 next），則等待 next 被呼叫
                else if (hook.length < 3) {
                    resolve();
                }
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * 預設錯誤處理
     * @private
     */
    _defaultErrorHandler(error, to, from) {
        console.error('Router error:', error);
        console.error('Route:', to);
    }
}

/**
 * 建立路由連結
 * @param {string} path - 路徑
 * @param {string} text - 連結文字
 * @param {Object} options - 選項
 * @returns {HTMLAnchorElement}
 */
export function createLink(path, text, options = {}) {
    const { className = '', activeClass = 'active', exact = false } = options;

    const link = document.createElement('a');
    link.href = `#${path}`;
    link.textContent = text;
    link.className = className;

    // 更新 active 狀態
    const updateActive = () => {
        const currentPath = window.location.hash.slice(1).split('?')[0] || '/';
        const isActive = exact
            ? currentPath === path
            : currentPath.startsWith(path);

        link.classList.toggle(activeClass, isActive);
    };

    updateActive();
    window.addEventListener('hashchange', updateActive);

    return link;
}

// 建立預設路由器實例
export const router = new Router();

export default router;
