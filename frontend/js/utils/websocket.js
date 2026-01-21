/**
 * WebSocket Manager - WebSocket 連接管理
 * 提供自動重連、訊息處理、訂閱機制
 */

import { createEventEmitter } from './helpers.js';

/**
 * WebSocket 管理器類別
 */
export class WebSocketManager {
    constructor(options = {}) {
        const wsUrl = (() => {
            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            return `${proto}//${window.location.host}/api/v1/ws/updates`;
        })();
        this.options = {
            url: options.url || wsUrl,
            reconnectInterval: options.reconnectInterval || 3000,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            heartbeatInterval: options.heartbeatInterval || 30000,
            ...options
        };

        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.reconnectTimer = null;
        this.messageQueue = [];

        this.events = createEventEmitter();
        this.subscriptions = new Map();
    }

    /**
     * 連接 WebSocket
     * @returns {Promise<void>}
     */
    connect() {
        return new Promise((resolve, reject) => {
            if (this.ws && this.isConnected) {
                resolve();
                return;
            }

            try {
                this.ws = new WebSocket(this.options.url);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;

                    // 發送佇列中的訊息
                    this._flushMessageQueue();

                    // 重新訂閱
                    this._resubscribe();

                    // 啟動心跳
                    this._startHeartbeat();

                    this.events.emit('connected');
                    resolve();
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket disconnected:', event.code, event.reason);
                    this.isConnected = false;
                    this._stopHeartbeat();

                    this.events.emit('disconnected', event);

                    // 嘗試重連
                    if (!event.wasClean) {
                        this._scheduleReconnect();
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.events.emit('error', error);
                    reject(error);
                };

                this.ws.onmessage = (event) => {
                    this._handleMessage(event);
                };

            } catch (error) {
                console.error('WebSocket connection failed:', error);
                reject(error);
            }
        });
    }

    /**
     * 斷開連接
     */
    disconnect() {
        this._stopHeartbeat();
        clearTimeout(this.reconnectTimer);

        if (this.ws) {
            this.ws.close(1000, 'User initiated disconnect');
            this.ws = null;
        }

        this.isConnected = false;
        this.subscriptions.clear();
    }

    /**
     * 發送訊息
     * @param {string} type - 訊息類型
     * @param {Object} data - 訊息資料
     */
    send(type, data = {}) {
        const message = JSON.stringify({ type, data });

        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            // 加入佇列，等待連接後發送
            this.messageQueue.push(message);
        }
    }

    /**
     * 訂閱頻道
     * @param {string} channel - 頻道名稱
     * @param {Function} callback - 回調函數
     * @returns {Function} 取消訂閱函數
     */
    subscribe(channel, callback) {
        if (!this.subscriptions.has(channel)) {
            this.subscriptions.set(channel, new Set());

            // 發送訂閱請求
            this.send('subscribe', { channel });
        }

        this.subscriptions.get(channel).add(callback);

        return () => this.unsubscribe(channel, callback);
    }

    /**
     * 取消訂閱
     * @param {string} channel - 頻道名稱
     * @param {Function} callback - 回調函數
     */
    unsubscribe(channel, callback) {
        const callbacks = this.subscriptions.get(channel);
        if (callbacks) {
            callbacks.delete(callback);

            if (callbacks.size === 0) {
                this.subscriptions.delete(channel);
                this.send('unsubscribe', { channel });
            }
        }
    }

    /**
     * 監聽事件
     * @param {string} event - 事件名稱
     * @param {Function} callback - 回調函數
     * @returns {Function} 取消監聽函數
     */
    on(event, callback) {
        return this.events.on(event, callback);
    }

    /**
     * 處理訊息
     * @private
     */
    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            const { type, channel, data } = message;

            // 發送給全域監聽器
            this.events.emit('message', message);
            this.events.emit(type, data);

            // 發送給頻道訂閱者
            if (channel && this.subscriptions.has(channel)) {
                this.subscriptions.get(channel).forEach(callback => {
                    try {
                        callback(data, message);
                    } catch (error) {
                        console.error(`Subscription callback error [${channel}]:`, error);
                    }
                });
            }

            // 處理特殊訊息類型
            switch (type) {
                case 'pong':
                    // 心跳回應，不需要特別處理
                    break;

                case 'error':
                    console.error('WebSocket server error:', data);
                    this.events.emit('serverError', data);
                    break;

                case 'scraper_progress':
                    this.events.emit('scraperProgress', data);
                    break;

                case 'scraper_complete':
                    this.events.emit('scraperComplete', data);
                    break;

                case 'scraper_error':
                    this.events.emit('scraperError', data);
                    break;

                case 'log':
                    this.events.emit('log', data);
                    break;
            }

        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    /**
     * 發送佇列中的訊息
     * @private
     */
    _flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(message);
            } else {
                // 連接未就緒，放回佇列
                this.messageQueue.unshift(message);
                break;
            }
        }
    }

    /**
     * 重新訂閱所有頻道
     * @private
     */
    _resubscribe() {
        for (const channel of this.subscriptions.keys()) {
            this.send('subscribe', { channel });
        }
    }

    /**
     * 排程重連
     * @private
     */
    _scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            this.events.emit('maxReconnectAttemptsReached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.options.reconnectInterval * Math.min(this.reconnectAttempts, 5);

        console.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            console.log('Attempting to reconnect...');
            this.connect().catch(() => {
                // 重連失敗，會觸發 onclose 再次排程
            });
        }, delay);
    }

    /**
     * 啟動心跳
     * @private
     */
    _startHeartbeat() {
        this._stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.send('ping');
            }
        }, this.options.heartbeatInterval);
    }

    /**
     * 停止心跳
     * @private
     */
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
}

// 建立預設實例
export const wsManager = new WebSocketManager();

export default wsManager;
