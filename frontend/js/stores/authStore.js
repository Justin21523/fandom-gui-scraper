/**
 * AuthStore - 認證狀態管理
 */

import { createPersistentStore } from './store.js';

const initialState = {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null,
    tokenExpiry: null
};

export const authStore = createPersistentStore('auth', initialState);

/**
 * 登入
 * @param {Object} credentials - 認證資訊
 */
export function login(credentials) {
    const { access_token, refresh_token, user, expires_in } = credentials;

    authStore.setState({
        isAuthenticated: true,
        user: user || null,
        token: access_token,
        refreshToken: refresh_token || null,
        tokenExpiry: expires_in ? Date.now() + expires_in * 1000 : null
    });
}

/**
 * 登出
 */
export function logout() {
    authStore.reset(initialState);
    localStorage.removeItem('auth');
}

/**
 * 檢查 Token 是否過期
 * @returns {boolean}
 */
export function isTokenExpired() {
    const { tokenExpiry } = authStore.getState();
    if (!tokenExpiry) return false;
    return Date.now() >= tokenExpiry;
}

/**
 * 取得存取 Token
 * @returns {string|null}
 */
export function getToken() {
    const state = authStore.getState();
    if (!state.isAuthenticated || isTokenExpired()) {
        return null;
    }
    return state.token;
}

/**
 * 更新 Token
 * @param {string} newToken - 新的存取 Token
 * @param {number} expiresIn - 過期時間（秒）
 */
export function updateToken(newToken, expiresIn) {
    authStore.setState({
        token: newToken,
        tokenExpiry: expiresIn ? Date.now() + expiresIn * 1000 : null
    });
}

export default authStore;
