/**
 * Formatters - 格式化函數
 */

/**
 * 格式化日期
 * @param {Date|string|number} date - 日期
 * @param {Object} options - 格式選項
 * @returns {string}
 */
export function formatDate(date, options = {}) {
    const {
        locale = 'zh-TW',
        format = 'default',
        includeTime = false
    } = options;

    const d = date instanceof Date ? date : new Date(date);

    if (isNaN(d.getTime())) {
        return '-';
    }

    const formatOptions = {
        default: {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        },
        long: {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        },
        short: {
            month: 'short',
            day: 'numeric'
        },
        relative: null // 特殊處理
    };

    if (format === 'relative') {
        return formatRelativeTime(d);
    }

    let opts = formatOptions[format] || formatOptions.default;

    if (includeTime) {
        opts = {
            ...opts,
            hour: '2-digit',
            minute: '2-digit'
        };
    }

    return d.toLocaleDateString(locale, opts);
}

/**
 * 格式化相對時間
 * @param {Date|string|number} date - 日期
 * @returns {string}
 */
export function formatRelativeTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    if (seconds < 60) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (hours < 24) return `${hours} 小時前`;
    if (days < 7) return `${days} 天前`;
    if (weeks < 4) return `${weeks} 週前`;
    if (months < 12) return `${months} 個月前`;
    return `${years} 年前`;
}

/**
 * 格式化數字
 * @param {number} num - 數字
 * @param {Object} options - 格式選項
 * @returns {string}
 */
export function formatNumber(num, options = {}) {
    const {
        locale = 'zh-TW',
        decimals = 0,
        compact = false,
        currency = null,
        prefix = '',
        suffix = ''
    } = options;

    if (num === null || num === undefined || isNaN(num)) {
        return '-';
    }

    let formatted;

    if (currency) {
        formatted = new Intl.NumberFormat(locale, {
            style: 'currency',
            currency,
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    } else if (compact) {
        formatted = formatCompactNumber(num);
    } else {
        formatted = new Intl.NumberFormat(locale, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    return `${prefix}${formatted}${suffix}`;
}

/**
 * 格式化緊湊數字（如 1K, 1M）
 * @param {number} num - 數字
 * @returns {string}
 */
export function formatCompactNumber(num) {
    if (num === null || num === undefined) return '-';

    const absNum = Math.abs(num);
    const sign = num < 0 ? '-' : '';

    if (absNum >= 1e9) {
        return `${sign}${(absNum / 1e9).toFixed(1)}B`;
    }
    if (absNum >= 1e6) {
        return `${sign}${(absNum / 1e6).toFixed(1)}M`;
    }
    if (absNum >= 1e3) {
        return `${sign}${(absNum / 1e3).toFixed(1)}K`;
    }

    return `${sign}${absNum}`;
}

/**
 * 格式化百分比
 * @param {number} value - 值（0-1 或 0-100）
 * @param {Object} options - 格式選項
 * @returns {string}
 */
export function formatPercent(value, options = {}) {
    const {
        decimals = 1,
        isDecimal = true // true: 0.5 -> 50%, false: 50 -> 50%
    } = options;

    if (value === null || value === undefined || isNaN(value)) {
        return '-';
    }

    const percent = isDecimal ? value * 100 : value;
    return `${percent.toFixed(decimals)}%`;
}

/**
 * 格式化檔案大小
 * @param {number} bytes - 位元組數
 * @param {Object} options - 格式選項
 * @returns {string}
 */
export function formatFileSize(bytes, options = {}) {
    const {
        decimals = 2,
        binary = false // true: KiB, false: KB
    } = options;

    if (bytes === null || bytes === undefined || isNaN(bytes)) {
        return '-';
    }

    if (bytes === 0) return '0 B';

    const k = binary ? 1024 : 1000;
    const units = binary
        ? ['B', 'KiB', 'MiB', 'GiB', 'TiB']
        : ['B', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = bytes / Math.pow(k, i);

    return `${size.toFixed(decimals)} ${units[i]}`;
}

/**
 * 格式化時間長度
 * @param {number} seconds - 秒數
 * @param {Object} options - 格式選項
 * @returns {string}
 */
export function formatDuration(seconds, options = {}) {
    const { format = 'auto' } = options;

    if (seconds === null || seconds === undefined || isNaN(seconds)) {
        return '-';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (format === 'clock') {
        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }

    // auto format
    const parts = [];
    if (hours > 0) parts.push(`${hours} 小時`);
    if (minutes > 0) parts.push(`${minutes} 分鐘`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs} 秒`);

    return parts.join(' ');
}

/**
 * 截斷文字
 * @param {string} text - 文字
 * @param {number} maxLength - 最大長度
 * @param {string} suffix - 截斷後綴
 * @returns {string}
 */
export function truncate(text, maxLength = 50, suffix = '...') {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * 首字母大寫
 * @param {string} text - 文字
 * @returns {string}
 */
export function capitalize(text) {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/**
 * 轉換為標題格式
 * @param {string} text - 文字
 * @returns {string}
 */
export function toTitleCase(text) {
    if (!text) return '';
    return text
        .toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * 轉換為 slug 格式
 * @param {string} text - 文字
 * @returns {string}
 */
export function toSlug(text) {
    if (!text) return '';
    return text
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^\w\-]+/g, '')
        .replace(/\-\-+/g, '-')
        .replace(/^-+/, '')
        .replace(/-+$/, '');
}

/**
 * 高亮搜尋文字
 * @param {string} text - 原始文字
 * @param {string} query - 搜尋關鍵字
 * @param {string} className - 高亮 CSS 類別
 * @returns {string} HTML 字串
 */
export function highlightText(text, query, className = 'highlight') {
    if (!text || !query) return text;

    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, `<mark class="${className}">$1</mark>`);
}

/**
 * 跳脫正則表達式特殊字元
 * @param {string} string - 字串
 * @returns {string}
 */
export function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * 跳脫 HTML
 * @param {string} text - 文字
 * @returns {string}
 */
export function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 格式化品質分數
 * @param {number} score - 分數（0-100）
 * @returns {Object} { text, className }
 */
export function formatQualityScore(score) {
    if (score === null || score === undefined) {
        return { text: '-', className: '' };
    }

    if (score >= 80) {
        return { text: `${score}`, className: 'text-success' };
    }
    if (score >= 60) {
        return { text: `${score}`, className: 'text-warning' };
    }
    return { text: `${score}`, className: 'text-error' };
}

export default {
    formatDate,
    formatRelativeTime,
    formatNumber,
    formatCompactNumber,
    formatPercent,
    formatFileSize,
    formatDuration,
    truncate,
    capitalize,
    toTitleCase,
    toSlug,
    highlightText,
    escapeRegExp,
    escapeHtml,
    formatQualityScore
};
