/**
 * Auth API - 認證相關 API
 */

import api from './client.js';
import { login as storeLogin, logout as storeLogout } from '../stores/authStore.js';

/**
 * 使用者登入
 * @param {string} username - 使用者名稱
 * @param {string} password - 密碼
 * @returns {Promise<Object>} 認證結果
 */
export async function login(username, password) {
    // OAuth2 表單格式
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    // 使用原生 fetch 因為 OAuth2 需要 application/x-www-form-urlencoded
    const tokenResponse = await fetch('http://localhost:8000/api/v1/auth/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });

    if (!tokenResponse.ok) {
        const error = await tokenResponse.json().catch(() => ({}));
        const errorMessage = error.detail || '登入失敗';
        throw new Error(errorMessage);
    }

    const data = await tokenResponse.json();

    // 更新認證狀態
    storeLogin(data);

    return data;
}

/**
 * 使用者登出
 */
export async function logout() {
    try {
        await api.post('/auth/logout');
    } catch {
        // 忽略錯誤，繼續登出
    }

    storeLogout();
}

/**
 * 取得當前使用者資訊
 * @returns {Promise<Object>} 使用者資訊
 */
export async function getCurrentUser() {
    return api.get('/auth/me');
}

/**
 * 重新整理 Token
 * @param {string} refreshToken - 更新 Token
 * @returns {Promise<Object>} 新的認證資訊
 */
export async function refreshToken(refreshToken) {
    const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
        throw new Error('Token 更新失敗');
    }

    const data = await response.json();
    storeLogin(data);

    return data;
}

/**
 * 註冊新使用者
 * @param {Object} userData - 使用者資料
 * @returns {Promise<Object>} 新使用者資訊
 */
export async function register(userData) {
    return api.post('/auth/register', userData);
}

/**
 * 變更密碼
 * @param {string} oldPassword - 舊密碼
 * @param {string} newPassword - 新密碼
 * @returns {Promise<Object>}
 */
export async function changePassword(oldPassword, newPassword) {
    return api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
    });
}

export default {
    login,
    logout,
    getCurrentUser,
    refreshToken,
    register,
    changePassword
};
