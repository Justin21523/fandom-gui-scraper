/**
 * Charts Page - 圖表分析頁面
 */

import { t } from '../i18n/i18n.js';
import { getCharacterStats, getCharacters, getAnimeList } from '../api/characters.js';
import toast from '../components/toast.js';

// Chart.js 實例
let chartInstances = {};

/**
 * 渲染圖表分析頁面
 * @param {HTMLElement} container - 容器元素
 */
export async function renderChartsPage(container) {
    container.innerHTML = `
        <div class="page animate-fadeIn">
            <div class="page__header">
                <div>
                    <h1 class="page__title">${t('charts.title')}</h1>
                    <p class="page__subtitle">視覺化分析角色資料</p>
                </div>
                <div class="page__actions">
                    <button class="btn btn--outline" id="export-charts-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        ${t('charts.exportChart')}
                    </button>
                    <button class="btn btn--primary" id="refresh-charts-btn">
                        <svg viewBox="0 0 20 20" fill="currentColor" class="btn__icon">
                            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                        </svg>
                        ${t('common.refresh')}
                    </button>
                </div>
            </div>

            <!-- 統計摘要 -->
            <div class="stats-grid mb-xl" id="stats-summary">
                <div class="stat-card">
                    <div class="stat-card__icon stat-card__icon--primary">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                        </svg>
                    </div>
                    <div class="stat-card__content">
                        <div class="stat-card__label">總角色數</div>
                        <div class="stat-card__value" id="total-characters">-</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card__icon stat-card__icon--success">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                        </svg>
                    </div>
                    <div class="stat-card__content">
                        <div class="stat-card__label">動畫數量</div>
                        <div class="stat-card__value" id="total-anime">-</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card__icon stat-card__icon--warning">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="stat-card__content">
                        <div class="stat-card__label">平均品質分數</div>
                        <div class="stat-card__value" id="avg-quality">-</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card__icon stat-card__icon--error">
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="stat-card__content">
                        <div class="stat-card__label">總圖片數</div>
                        <div class="stat-card__value" id="total-images">-</div>
                    </div>
                </div>
            </div>

            <!-- 圖表區域 -->
            <div class="charts-grid">
                <!-- 角色分佈圖 -->
                <div class="card chart-card">
                    <div class="card__header">
                        <h3 class="card__title">${t('charts.charactersByAnime')}</h3>
                        <div class="chart-controls">
                            <select class="select select--sm" id="anime-chart-type">
                                <option value="doughnut">圓餅圖</option>
                                <option value="bar">長條圖</option>
                                <option value="polarArea">極座標圖</option>
                            </select>
                        </div>
                    </div>
                    <div class="card__body">
                        <div class="chart-container">
                            <canvas id="anime-distribution-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 品質分數分佈 -->
                <div class="card chart-card">
                    <div class="card__header">
                        <h3 class="card__title">${t('charts.qualityDistribution')}</h3>
                    </div>
                    <div class="card__body">
                        <div class="chart-container">
                            <canvas id="quality-distribution-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 爬取時間線 -->
                <div class="card chart-card chart-card--wide">
                    <div class="card__header">
                        <h3 class="card__title">${t('charts.scrapingTimeline')}</h3>
                        <div class="chart-controls">
                            <select class="select select--sm" id="timeline-range">
                                <option value="7">最近 7 天</option>
                                <option value="30" selected>最近 30 天</option>
                                <option value="90">最近 90 天</option>
                            </select>
                        </div>
                    </div>
                    <div class="card__body">
                        <div class="chart-container chart-container--wide">
                            <canvas id="scraping-timeline-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 標籤雲 -->
                <div class="card chart-card">
                    <div class="card__header">
                        <h3 class="card__title">${t('charts.tagCloud')}</h3>
                    </div>
                    <div class="card__body">
                        <div class="tag-cloud" id="tag-cloud">
                            <div class="loading-container">
                                <div class="loading-spinner"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 載入 Chart.js
    await loadChartJS();

    // 綁定事件
    bindChartsEvents(container);

    // 載入資料並渲染圖表
    await loadChartsData(container);
}

/**
 * 載入 Chart.js
 */
async function loadChartJS() {
    if (window.Chart) return;

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = '/frontend/libs/chart.min.js';
        script.onload = resolve;
        script.onerror = () => {
            // 嘗試從 CDN 載入
            const cdnScript = document.createElement('script');
            cdnScript.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
            cdnScript.onload = resolve;
            cdnScript.onerror = reject;
            document.head.appendChild(cdnScript);
        };
        document.head.appendChild(script);
    });
}

/**
 * 綁定圖表頁面事件
 * @param {HTMLElement} container - 容器元素
 */
function bindChartsEvents(container) {
    // 重新整理
    container.querySelector('#refresh-charts-btn')?.addEventListener('click', () => {
        loadChartsData(container);
    });

    // 匯出圖表
    container.querySelector('#export-charts-btn')?.addEventListener('click', () => {
        exportCharts();
    });

    // 動畫分佈圖表類型切換
    container.querySelector('#anime-chart-type')?.addEventListener('change', (e) => {
        updateAnimeChart(e.target.value);
    });

    // 時間線範圍切換
    container.querySelector('#timeline-range')?.addEventListener('change', (e) => {
        updateTimelineChart(parseInt(e.target.value));
    });
}

/**
 * 載入圖表資料
 * @param {HTMLElement} container - 容器元素
 */
async function loadChartsData(container) {
    try {
        // 並行載入資料
        const [stats, characters, animeList] = await Promise.all([
            getCharacterStats().catch(() => null),
            getCharacters({ pageSize: 1000 }).catch(() => ({ items: [] })),
            getAnimeList().catch(() => [])
        ]);

        // 更新統計摘要
        updateStatsSummary(container, stats, characters.items, animeList);

        // 渲染圖表
        renderAnimeDistributionChart(characters.items, animeList);
        renderQualityDistributionChart(characters.items);
        renderScrapingTimelineChart(characters.items);
        renderTagCloud(container, characters.items);

    } catch (error) {
        console.error('Failed to load charts data:', error);
        toast.error('載入圖表資料失敗');
    }
}

/**
 * 更新統計摘要
 */
function updateStatsSummary(container, stats, characters, animeList) {
    const totalCharacters = stats?.total_characters || characters.length;
    const totalAnime = stats?.total_anime || animeList.length;

    // 計算平均品質分數
    const qualityScores = characters
        .filter(c => c.quality_score !== undefined && c.quality_score !== null)
        .map(c => c.quality_score);
    const avgQuality = qualityScores.length > 0
        ? Math.round(qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length)
        : 0;

    // 計算總圖片數
    const totalImages = characters.reduce((sum, c) => {
        const imageCount = c.images?.length || (c.image ? 1 : 0);
        return sum + imageCount;
    }, 0);

    container.querySelector('#total-characters').textContent = totalCharacters.toLocaleString();
    container.querySelector('#total-anime').textContent = totalAnime.toLocaleString();
    container.querySelector('#avg-quality').textContent = avgQuality;
    container.querySelector('#total-images').textContent = totalImages.toLocaleString();
}

/**
 * 渲染動畫分佈圖
 */
function renderAnimeDistributionChart(characters, animeList, type = 'doughnut') {
    const ctx = document.getElementById('anime-distribution-chart');
    if (!ctx) return;

    // 統計每個動畫的角色數
    const animeCounts = {};
    characters.forEach(char => {
        const anime = char.anime || '未分類';
        animeCounts[anime] = (animeCounts[anime] || 0) + 1;
    });

    // 排序並取前 10 個
    const sortedAnime = Object.entries(animeCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const labels = sortedAnime.map(([name]) => name);
    const data = sortedAnime.map(([, count]) => count);

    // 顏色
    const colors = [
        '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#ec4899', '#f97316', '#14b8a6', '#6366f1'
    ];

    // 銷毀舊圖表
    if (chartInstances.animeDistribution) {
        chartInstances.animeDistribution.destroy();
    }

    chartInstances.animeDistribution = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: getComputedStyle(document.documentElement)
                    .getPropertyValue('--bg-primary').trim() || '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: type === 'bar' ? 'top' : 'right',
                    labels: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-primary').trim() || '#111827',
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });

    // 儲存資料供類型切換使用
    chartInstances.animeDistribution._chartData = { characters, animeList };
}

/**
 * 更新動畫圖表類型
 */
function updateAnimeChart(type) {
    if (chartInstances.animeDistribution?._chartData) {
        const { characters, animeList } = chartInstances.animeDistribution._chartData;
        renderAnimeDistributionChart(characters, animeList, type);
    }
}

/**
 * 渲染品質分數分佈圖
 */
function renderQualityDistributionChart(characters) {
    const ctx = document.getElementById('quality-distribution-chart');
    if (!ctx) return;

    // 分組統計品質分數
    const ranges = [
        { label: '0-20 (很差)', min: 0, max: 20, color: '#ef4444' },
        { label: '21-40 (較差)', min: 21, max: 40, color: '#f97316' },
        { label: '41-60 (普通)', min: 41, max: 60, color: '#f59e0b' },
        { label: '61-80 (良好)', min: 61, max: 80, color: '#22c55e' },
        { label: '81-100 (優秀)', min: 81, max: 100, color: '#3b82f6' }
    ];

    const counts = ranges.map(range => {
        return characters.filter(c => {
            const score = c.quality_score || 0;
            return score >= range.min && score <= range.max;
        }).length;
    });

    // 銷毀舊圖表
    if (chartInstances.qualityDistribution) {
        chartInstances.qualityDistribution.destroy();
    }

    chartInstances.qualityDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ranges.map(r => r.label),
            datasets: [{
                label: '角色數量',
                data: counts,
                backgroundColor: ranges.map(r => r.color),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    grid: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--border-color').trim() || '#e5e7eb'
                    }
                },
                x: {
                    ticks: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * 渲染爬取時間線圖
 */
function renderScrapingTimelineChart(characters, days = 30) {
    const ctx = document.getElementById('scraping-timeline-chart');
    if (!ctx) return;

    // 生成日期範圍
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const dates = [];
    const currentDate = new Date(startDate);
    while (currentDate <= endDate) {
        dates.push(new Date(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }

    // 統計每天新增的角色數
    const dailyCounts = dates.map(date => {
        const dateStr = date.toISOString().split('T')[0];
        return characters.filter(c => {
            const createdAt = c.created_at || c.updated_at;
            if (!createdAt) return false;
            const charDate = new Date(createdAt).toISOString().split('T')[0];
            return charDate === dateStr;
        }).length;
    });

    // 計算累計數量
    let cumulative = 0;
    const cumulativeCounts = dailyCounts.map(count => {
        cumulative += count;
        return cumulative;
    });

    // 銷毀舊圖表
    if (chartInstances.scrapingTimeline) {
        chartInstances.scrapingTimeline.destroy();
    }

    chartInstances.scrapingTimeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.map(d => d.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' })),
            datasets: [
                {
                    label: '每日新增',
                    data: dailyCounts,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: '累計數量',
                    data: cumulativeCounts,
                    borderColor: '#22c55e',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-primary').trim() || '#111827',
                        usePointStyle: true
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '每日新增',
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    ticks: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    grid: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--border-color').trim() || '#e5e7eb'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '累計數量',
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    ticks: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--text-secondary').trim() || '#4b5563',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // 儲存資料供時間範圍切換使用
    chartInstances.scrapingTimeline._chartData = { characters };
}

/**
 * 更新時間線圖表範圍
 */
function updateTimelineChart(days) {
    if (chartInstances.scrapingTimeline?._chartData) {
        const { characters } = chartInstances.scrapingTimeline._chartData;
        renderScrapingTimelineChart(characters, days);
    }
}

/**
 * 渲染標籤雲
 */
function renderTagCloud(container, characters) {
    const tagCloudEl = container.querySelector('#tag-cloud');
    if (!tagCloudEl) return;

    // 統計標籤
    const tagCounts = {};
    characters.forEach(char => {
        const tags = char.tags || [];
        tags.forEach(tag => {
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        });
    });

    // 排序並取前 30 個
    const sortedTags = Object.entries(tagCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 30);

    if (sortedTags.length === 0) {
        tagCloudEl.innerHTML = `
            <div class="empty-state">
                <p class="text-muted">尚無標籤資料</p>
            </div>
        `;
        return;
    }

    // 計算字體大小範圍
    const maxCount = Math.max(...sortedTags.map(([, count]) => count));
    const minCount = Math.min(...sortedTags.map(([, count]) => count));

    const minSize = 12;
    const maxSize = 32;

    tagCloudEl.innerHTML = sortedTags.map(([tag, count]) => {
        const size = minCount === maxCount
            ? (minSize + maxSize) / 2
            : minSize + ((count - minCount) / (maxCount - minCount)) * (maxSize - minSize);

        const opacity = 0.5 + (count / maxCount) * 0.5;

        return `
            <span class="tag-cloud__item"
                  style="font-size: ${size}px; opacity: ${opacity};"
                  title="${count} 個角色">
                ${tag}
            </span>
        `;
    }).join('');
}

/**
 * 匯出圖表
 */
function exportCharts() {
    // 建立一個臨時 canvas 來合併所有圖表
    const chartsToExport = ['anime-distribution-chart', 'quality-distribution-chart', 'scraping-timeline-chart'];

    chartsToExport.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            const link = document.createElement('a');
            link.download = `${id}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
        }
    });

    toast.success('圖表已匯出');
}

export default { render: renderChartsPage };
