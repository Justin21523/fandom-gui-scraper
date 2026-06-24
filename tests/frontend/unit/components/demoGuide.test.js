import { describe, test, expect, beforeEach, jest } from '@jest/globals';

const mockRouter = {
  currentPath: '/campaigns',
  getCurrentPath: jest.fn(() => mockRouter.currentPath),
  navigate: jest.fn((path) => {
    mockRouter.currentPath = path;
    window.location.hash = `#${path}`;
  }),
};

const translations = {
  'common.close': 'Close',
  'common.next': 'Next',
  'common.previous': 'Previous',
  'tour.title': 'Portfolio Demo Guide',
  'tour.launcher': 'Guide',
  'tour.open': 'Open guide',
  'tour.eyebrow': 'Step {{current}} / {{total}}',
  'tour.skip': 'Skip',
  'tour.finish': 'Finish',
  'tour.restart': 'Restart guide',
  'tour.targetMissing': 'Target missing',
};

function translate(key, params = {}) {
  const value = translations[key] || key.split('.').slice(-1)[0];
  return String(value).replace(/\{\{(\w+)\}\}/g, (_, name) => params[name] ?? `{{${name}}}`);
}

jest.unstable_mockModule('@/i18n/i18n.js', () => ({
  onLocaleChange: jest.fn(() => jest.fn()),
  t: translate,
}));

const { initDemoGuide, goToStep, closeGuide } = await import('@/components/demoGuide.js');

function setupStorage() {
  const store = new Map();
  const mockStorage = {
    getItem: jest.fn(key => store.get(key) || null),
    setItem: jest.fn((key, value) => store.set(key, value)),
    removeItem: jest.fn(key => store.delete(key)),
    clear: jest.fn(() => store.clear()),
  };
  Object.defineProperty(window, 'localStorage', {
    value: mockStorage,
    configurable: true,
  });
}

function addTarget(name) {
  const el = document.createElement('section');
  el.setAttribute('data-tour', name);
  el.style.height = '80px';
  el.scrollIntoView = jest.fn();
  document.body.appendChild(el);
  return el;
}

describe('demo guide assistant', () => {
  beforeEach(() => {
    setupStorage();
    mockRouter.currentPath = '/campaigns';
    mockRouter.getCurrentPath.mockClear();
    mockRouter.navigate.mockClear();
    window.location.hash = '#/campaigns';
    document.body.innerHTML = '<div id="demo-guide-root" class="demo-guide"></div>';
    globalThis.__DEMO_GUIDE_WAIT_TIMEOUT_MS = 120;
  });

  test('opens the floating guide and highlights the first target', async () => {
    addTarget('campaigns-overview');
    initDemoGuide({ router: mockRouter });

    document.querySelector('[data-tour="guide-open"]').click();
    await new Promise(resolve => setTimeout(resolve, 700));

    expect(document.querySelector('.demo-guide__panel--open')).toBeTruthy();
    expect(document.querySelector('[data-tour="campaigns-overview"]').classList.contains('tour-target--active')).toBe(true);
    expect(document.body.textContent).toContain('Step 1');
  });

  test('next step can navigate to another route', async () => {
    addTarget('scraper-source');
    initDemoGuide({ router: mockRouter });

    await goToStep(3);
    await new Promise(resolve => setTimeout(resolve, 700));

    expect(mockRouter.navigate).toHaveBeenCalledWith('/scraper');
    expect(document.querySelector('[data-tour="scraper-source"]').classList.contains('tour-target--active')).toBe(true);
  });

  test('shows a fallback warning when a target is missing', async () => {
    initDemoGuide({ router: mockRouter });

    await goToStep(12);
    await new Promise(resolve => setTimeout(resolve, 500));

    expect(document.querySelector('.demo-guide__warning')?.textContent).toContain('Target missing');
    closeGuide();
    expect(document.querySelector('.demo-guide__panel--open')).toBeFalsy();
  });
});
