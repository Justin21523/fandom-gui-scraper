/**
 * Demo Guide - 作品集導覽小幫手
 */

import { onLocaleChange, t } from '../i18n/i18n.js';

const STORAGE_KEY = 'demoGuide.state';
const WAIT_TIMEOUT_MS = 7000;

export const TOUR_STEPS = [
    {
        id: 'campaigns-overview',
        route: '/campaigns',
        target: '[data-tour="campaigns-overview"]',
        titleKey: 'tour.steps.campaigns.title',
        bodyKey: 'tour.steps.campaigns.body',
        placement: 'bottom',
    },
    {
        id: 'campaign-preset',
        route: '/campaigns',
        target: '[data-tour="campaign-preset"]',
        titleKey: 'tour.steps.preset.title',
        bodyKey: 'tour.steps.preset.body',
        placement: 'bottom',
        beforeStep: 'selectOfflinePreset',
    },
    {
        id: 'campaign-events',
        route: '/campaigns',
        target: '[data-tour="campaign-events"]',
        titleKey: 'tour.steps.events.title',
        bodyKey: 'tour.steps.events.body',
        placement: 'top',
    },
    {
        id: 'scraper-source',
        route: '/scraper',
        target: '[data-tour="scraper-source"]',
        titleKey: 'tour.steps.scraperSource.title',
        bodyKey: 'tour.steps.scraperSource.body',
        placement: 'right',
    },
    {
        id: 'scraper-compliance',
        route: '/scraper',
        target: '[data-tour="scraper-compliance"]',
        titleKey: 'tour.steps.scraperCompliance.title',
        bodyKey: 'tour.steps.scraperCompliance.body',
        placement: 'right',
    },
    {
        id: 'scraper-progress',
        route: '/scraper',
        target: '[data-tour="scraper-progress"]',
        titleKey: 'tour.steps.scraperProgress.title',
        bodyKey: 'tour.steps.scraperProgress.body',
        placement: 'left',
    },
    {
        id: 'process-timeline',
        route: '/process',
        target: '[data-tour="process-timeline"]',
        titleKey: 'tour.steps.process.title',
        bodyKey: 'tour.steps.process.body',
        placement: 'top',
    },
    {
        id: 'browse-runs',
        route: '/browse',
        target: '[data-tour="browse-runs"]',
        titleKey: 'tour.steps.browseRuns.title',
        bodyKey: 'tour.steps.browseRuns.body',
        placement: 'right',
    },
    {
        id: 'browse-datasets',
        route: '/browse',
        target: '[data-tour="browse-datasets"]',
        titleKey: 'tour.steps.browseDatasets.title',
        bodyKey: 'tour.steps.browseDatasets.body',
        placement: 'top',
    },
    {
        id: 'analysis-network',
        route: '/analysis',
        target: '[data-tour="analysis-network"]',
        titleKey: 'tour.steps.analysisNetwork.title',
        bodyKey: 'tour.steps.analysisNetwork.body',
        placement: 'top',
    },
    {
        id: 'analysis-quality',
        route: '/analysis',
        target: '[data-tour="analysis-quality"]',
        titleKey: 'tour.steps.analysisQuality.title',
        bodyKey: 'tour.steps.analysisQuality.body',
        placement: 'top',
    },
    {
        id: 'export-center',
        route: '/export',
        target: '[data-tour="export-center"]',
        titleKey: 'tour.steps.export.title',
        bodyKey: 'tour.steps.export.body',
        placement: 'top',
    },
    {
        id: 'compliance-log',
        route: '/compliance',
        target: '[data-tour="compliance-log"]',
        titleKey: 'tour.steps.compliance.title',
        bodyKey: 'tour.steps.compliance.body',
        placement: 'top',
    },
];

let state = {
    open: false,
    active: false,
    stepIndex: 0,
    targetMissing: false,
};

let routerRef = null;
let containerEl = null;
let highlightEl = null;
let overlayEl = null;
let targetEl = null;
let unsubscribeLocale = null;

function readState() {
    try {
        return { ...state, ...(JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')) };
    } catch {
        return { ...state };
    }
}

function persistState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
        open: state.open,
        active: state.active,
        stepIndex: state.stepIndex,
    }));
}

function clampStep(index) {
    return Math.max(0, Math.min(TOUR_STEPS.length - 1, index));
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForTarget(selector, timeoutMs = globalThis.__DEMO_GUIDE_WAIT_TIMEOUT_MS || WAIT_TIMEOUT_MS) {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
        const el = document.querySelector(selector);
        if (el) return el;
        await sleep(120);
    }
    return null;
}

function currentPath() {
    return routerRef?.getCurrentPath?.() || (window.location.hash.slice(1).split('?')[0] || '/');
}

function routeTo(path) {
    if (currentPath() === path) return;
    routerRef?.navigate?.(path);
}

function applyBeforeStep(step) {
    if (step.beforeStep === 'selectOfflinePreset') {
        const preset = document.querySelector('#campaign-preset-select');
        if (preset && preset.value !== 'offline-portfolio-smoke') {
            preset.value = 'offline-portfolio-smoke';
            preset.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}

function clearHighlight() {
    targetEl?.classList.remove('tour-target--active');
    targetEl = null;
    highlightEl?.remove();
    overlayEl?.remove();
    highlightEl = null;
    overlayEl = null;
}

function createHighlight(target) {
    clearHighlight();
    overlayEl = document.createElement('div');
    overlayEl.className = 'demo-guide__overlay';
    overlayEl.setAttribute('aria-hidden', 'true');
    highlightEl = document.createElement('div');
    highlightEl.className = 'demo-guide__spotlight';
    highlightEl.setAttribute('aria-hidden', 'true');
    document.body.append(overlayEl, highlightEl);
    targetEl = target;
    targetEl.classList.add('tour-target--active');
    updateHighlightPosition();
}

function updateHighlightPosition() {
    if (!highlightEl || !targetEl) return;
    const rect = targetEl.getBoundingClientRect();
    const pad = 8;
    highlightEl.style.left = `${Math.max(8, rect.left - pad)}px`;
    highlightEl.style.top = `${Math.max(8, rect.top - pad)}px`;
    highlightEl.style.width = `${Math.min(window.innerWidth - 16, rect.width + pad * 2)}px`;
    highlightEl.style.height = `${Math.min(window.innerHeight - 16, rect.height + pad * 2)}px`;
}

function panelPositionClass(step) {
    return `demo-guide--${step.placement || 'bottom'}`;
}

function render() {
    if (!containerEl) return;
    const step = TOUR_STEPS[state.stepIndex];
    const progress = Math.round(((state.stepIndex + 1) / TOUR_STEPS.length) * 100);
    containerEl.innerHTML = `
        <button class="demo-guide__launcher" type="button" data-tour="guide-open" aria-label="${t('tour.open')}">
            <span class="demo-guide__launcher-icon">?</span>
            <span>${t('tour.launcher')}</span>
        </button>
        <section class="demo-guide__panel ${state.open ? 'demo-guide__panel--open' : ''} ${panelPositionClass(step)}"
                 role="dialog"
                 aria-live="polite"
                 aria-label="${t('tour.title')}">
            <div class="demo-guide__header">
                <div>
                    <span class="demo-guide__eyebrow">${t('tour.eyebrow', { current: state.stepIndex + 1, total: TOUR_STEPS.length })}</span>
                    <h2>${t(step.titleKey)}</h2>
                </div>
                <button class="btn btn--icon demo-guide__close" type="button" aria-label="${t('common.close')}">×</button>
            </div>
            <div class="demo-guide__progress" aria-hidden="true">
                <span style="width:${progress}%"></span>
            </div>
            <p>${t(step.bodyKey)}</p>
            ${state.targetMissing ? `<div class="demo-guide__warning">${t('tour.targetMissing')}</div>` : ''}
            <div class="demo-guide__actions">
                <button class="btn btn--ghost btn--sm" type="button" data-guide-prev ${state.stepIndex === 0 ? 'disabled' : ''}>${t('common.previous')}</button>
                <button class="btn btn--ghost btn--sm" type="button" data-guide-skip>${t('tour.skip')}</button>
                <button class="btn btn--primary btn--sm" type="button" data-guide-next>
                    ${state.stepIndex === TOUR_STEPS.length - 1 ? t('tour.finish') : t('common.next')}
                </button>
            </div>
            <button class="demo-guide__restart" type="button" data-guide-restart>${t('tour.restart')}</button>
        </section>
    `;
    bindPanelEvents();
}

function bindPanelEvents() {
    containerEl.querySelector('.demo-guide__launcher')?.addEventListener('click', () => startGuide());
    containerEl.querySelector('.demo-guide__close')?.addEventListener('click', () => closeGuide());
    containerEl.querySelector('[data-guide-skip]')?.addEventListener('click', () => closeGuide());
    containerEl.querySelector('[data-guide-restart]')?.addEventListener('click', () => startGuide(0));
    containerEl.querySelector('[data-guide-prev]')?.addEventListener('click', () => goToStep(state.stepIndex - 1));
    containerEl.querySelector('[data-guide-next]')?.addEventListener('click', () => {
        if (state.stepIndex >= TOUR_STEPS.length - 1) {
            closeGuide();
        } else {
            goToStep(state.stepIndex + 1);
        }
    });
}

async function activateCurrentStep() {
    const step = TOUR_STEPS[state.stepIndex];
    state.targetMissing = false;
    routeTo(step.route);
    await sleep(180);
    applyBeforeStep(step);
    const target = await waitForTarget(step.target);
    if (!target) {
        state.targetMissing = true;
        clearHighlight();
        render();
        return;
    }
    target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    await sleep(260);
    createHighlight(target);
    updateHighlightPosition();
    render();
}

export async function goToStep(index) {
    state.stepIndex = clampStep(index);
    state.open = true;
    state.active = true;
    persistState();
    render();
    await activateCurrentStep();
}

export function startGuide(index = state.stepIndex) {
    state.open = true;
    state.active = true;
    state.stepIndex = clampStep(index);
    persistState();
    render();
    return activateCurrentStep();
}

export function closeGuide() {
    state.open = false;
    state.active = false;
    state.targetMissing = false;
    persistState();
    clearHighlight();
    render();
}

export function initDemoGuide({ router } = {}) {
    routerRef = router;
    state = readState();
    state.stepIndex = clampStep(state.stepIndex);
    containerEl = document.getElementById('demo-guide-root');
    if (!containerEl) {
        containerEl = document.createElement('div');
        containerEl.id = 'demo-guide-root';
        containerEl.className = 'demo-guide';
        document.body.appendChild(containerEl);
    }
    render();
    unsubscribeLocale?.();
    unsubscribeLocale = onLocaleChange(() => {
        render();
        if (state.open && targetEl) updateHighlightPosition();
    });
    window.addEventListener('resize', updateHighlightPosition);
    window.addEventListener('scroll', updateHighlightPosition, true);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && state.open) closeGuide();
    });
    if (state.open && state.active) {
        activateCurrentStep();
    }
    return {
        start: startGuide,
        close: closeGuide,
        goToStep,
    };
}

export default { initDemoGuide, startGuide, closeGuide, goToStep, TOUR_STEPS };
