# Frontend Testing Guide

This directory contains all frontend tests for the Fandom GUI Scraper project.

## 📁 Directory Structure

```
tests/frontend/
├── unit/                  # Unit tests for individual modules
│   ├── api/              # API client tests
│   ├── components/       # UI component tests
│   ├── utils/            # Utility function tests
│   └── stores/           # State management tests
├── integration/          # Integration tests
│   └── pages/           # Full page integration tests
├── e2e/                 # End-to-end tests (future)
├── setup.js             # Jest setup file
└── README.md            # This file
```

## 🚀 Getting Started

### Installation

Install dependencies:
```bash
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode (for development)
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests with verbose output
npm run test:verbose

# Run only unit tests
npm run test:unit

# Run only integration tests
npm run test:integration
```

### Running Specific Tests

```bash
# Run a specific test file
npm test -- scraper.test.js

# Run tests matching a pattern
npm test -- --testNamePattern="searchAnime"

# Run tests for a specific file
npm test -- tests/frontend/unit/api/scraper.test.js
```

## 🧪 Writing Tests

### Test File Structure

```javascript
import { describe, test, expect, beforeEach } from '@jest/globals';

describe('Module Name', () => {
  beforeEach(() => {
    // Setup code
  });

  describe('Function Name', () => {
    test('should do something', () => {
      // Test code
      expect(result).toBe(expected);
    });
  });
});
```

### Mocking Modules

For ES modules, use `jest.unstable_mockModule`:

```javascript
const mockGet = jest.fn();

jest.unstable_mockModule('@/api/client.js', () => ({
  default: {
    get: mockGet,
    post: jest.fn(),
  },
}));

// Import after mocking
const { searchAnime } = await import('@/api/scraper.js');
```

### DOM Testing

Use `@testing-library/dom` for DOM manipulation tests:

```javascript
import { screen, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom';

test('should render element', () => {
  document.body.innerHTML = '<div id="test">Hello</div>';

  const element = screen.getByText('Hello');
  expect(element).toBeInTheDocument();
});
```

## 📊 Coverage

Coverage reports are generated in `coverage/frontend/`:

- **Text**: Console output
- **HTML**: Open `coverage/frontend/index.html` in browser
- **LCOV**: For CI/CD integration

### Coverage Thresholds

- Global: 60% for all metrics
- API modules: 80% for all metrics

## 🔧 Configuration Files

- `package.json`: npm scripts and Jest config
- `jest.config.js`: Detailed Jest configuration
- `tests/frontend/setup.js`: Global test setup
- `.eslintrc.json`: ESLint rules

## 🐛 Debugging Tests

### Run with Node Debugger

```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

Then open `chrome://inspect` in Chrome.

### Common Issues

1. **Module not found**: Check path aliases in `jest.config.js`
2. **Timeout errors**: Increase timeout in test or `jest.config.js`
3. **Mock not working**: Ensure mocks are set up before imports

## 📝 Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names**: "should X when Y"
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Mock external dependencies**: API calls, timers, etc.
5. **Clean up after tests**: Use `afterEach()` for cleanup
6. **Test edge cases**: Empty data, errors, boundary values
7. **Keep tests fast**: Mock slow operations
8. **Use test data factories**: For consistent test data

## 📚 Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/docs/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## 🎯 Testing Checklist

For each module, ensure:

- [ ] Happy path tests
- [ ] Error handling tests
- [ ] Edge case tests
- [ ] Async operation tests
- [ ] Mock verification tests
- [ ] Coverage > 60% (80% for API modules)

## 🚦 CI/CD

Tests are automatically run on:
- Every commit (via pre-commit hooks)
- Every pull request (via GitHub Actions)
- Before deployment

See `.github/workflows/tests.yml` for CI configuration.
