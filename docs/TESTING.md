# Testing Documentation

Complete testing guide for the Fandom GUI Scraper project.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Coverage Requirements](#coverage-requirements)
- [Best Practices](#best-practices)

---

## Overview

This project has comprehensive test coverage across multiple layers:

- **Backend Unit Tests**: Python modules and utilities
- **Backend Integration Tests**: API endpoints and database operations
- **Frontend Unit Tests**: JavaScript components and utilities
- **Frontend Integration Tests**: Page-level functionality
- **E2E Tests**: Complete user workflows (planned)

### Test Statistics

| Layer | Tests | Coverage | Status |
|-------|-------|----------|--------|
| Backend Unit | 216+ | 85-95% | ✅ Complete |
| Backend Integration | 31+ | 60-70% | ✅ Complete |
| Frontend Unit | TBD | 60%+ target | 🔄 In Progress |
| Frontend Integration | TBD | 60%+ target | ⏳ Planned |
| E2E | TBD | Key flows | ⏳ Planned |

---

## Test Structure

```
tests/
├── unit/                          # Python unit tests
│   ├── test_utils/               # Utility tests
│   │   └── test_brave_search.py  # Brave Search API (32 tests)
│   ├── test_models/              # Data model tests
│   │   ├── test_episode_model.py # Episode models (43 tests)
│   │   └── test_gallery_model.py # Gallery models (57 tests)
│   └── test_scraper/             # Scraper tests
│       ├── test_universal_spider.py        # Spider tests (39 tests)
│       └── test_file_export_pipeline.py    # Pipeline tests (45 tests)
│
├── integration/                   # Python integration tests
│   └── test_universal_api.py     # API endpoint tests (31 tests)
│
├── frontend/                      # Frontend tests
│   ├── unit/                     # JavaScript unit tests
│   │   ├── api/                  # API client tests
│   │   ├── components/           # Component tests
│   │   ├── utils/                # Utility tests
│   │   └── stores/               # State management tests
│   ├── integration/              # Page integration tests
│   ├── e2e/                      # End-to-end tests
│   ├── setup.js                  # Jest setup
│   └── README.md                 # Frontend testing guide
│
├── conftest.py                   # Pytest fixtures (247 lines)
└── pytest.ini                    # Pytest configuration
```

---

## Running Tests

### Prerequisites

```bash
# Python dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Frontend dependencies
npm install

# Pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Backend Tests

```bash
# All Python tests
pytest

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Specific test file
pytest tests/unit/test_utils/test_brave_search.py -v

# With coverage
pytest --cov=. --cov-report=html

# Fast tests only (exclude slow tests)
pytest -m "not slow"

# Verbose output with full tracebacks
pytest -vv --tb=long

# Stop on first failure
pytest -x
```

### Frontend Tests

```bash
# All frontend tests
npm test

# Watch mode (for development)
npm run test:watch

# With coverage
npm run test:coverage

# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# Specific test file
npm test -- scraper.test.js

# Update snapshots
npm test -- -u
```

### Pre-commit Hooks

```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run pytest-quick --all-files

# Skip hooks for a commit (not recommended)
git commit --no-verify
```

---

## Writing Tests

### Backend (Python) Tests

#### Test File Structure

```python
"""
Module docstring describing what is being tested.
"""

import pytest
from unittest.mock import Mock, patch

# Fixtures
@pytest.fixture
def sample_data():
    return {"key": "value"}

# Test classes
class TestClassName:
    """Test class docstring."""

    def test_feature_name(self, sample_data):
        """Test specific behavior."""
        # Arrange
        expected = "value"

        # Act
        result = function_under_test(sample_data)

        # Assert
        assert result == expected
```

#### Common Patterns

```python
# Mocking external APIs
@patch('module.external_api.call')
def test_with_mock(mock_call):
    mock_call.return_value = {"data": "test"}
    result = my_function()
    assert result["data"] == "test"

# Testing async functions
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# Testing exceptions
def test_raises_exception():
    with pytest.raises(ValueError) as exc_info:
        function_that_raises()
    assert "error message" in str(exc_info.value)

# Parametrized tests
@pytest.mark.parametrize("input,expected", [
    ("test", True),
    ("", False),
    (None, False),
])
def test_multiple_cases(input, expected):
    assert validate(input) == expected
```

### Frontend (JavaScript) Tests

#### Test File Structure

```javascript
import { describe, test, expect, beforeEach } from '@jest/globals';

describe('Component Name', () => {
  let component;

  beforeEach(() => {
    // Setup
    component = createComponent();
  });

  describe('method name', () => {
    test('should do something', () => {
      // Arrange
      const input = 'test';

      // Act
      const result = component.method(input);

      // Assert
      expect(result).toBe('expected');
    });
  });
});
```

#### Common Patterns

```javascript
// Mocking modules
const mockGet = jest.fn();
jest.unstable_mockModule('@/api/client.js', () => ({
  default: { get: mockGet }
}));

// Testing DOM
import { screen } from '@testing-library/dom';

test('renders element', () => {
  document.body.innerHTML = '<div>Hello</div>';
  expect(screen.getByText('Hello')).toBeInTheDocument();
});

// Testing async operations
test('async operation', async () => {
  const promise = asyncFunction();
  await expect(promise).resolves.toBe('value');
});

// Testing errors
test('throws error', () => {
  expect(() => functionThatThrows()).toThrow('Error message');
});
```

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Manual trigger via Actions tab

#### Workflow Jobs

1. **python-unit-tests**: Python unit tests with coverage
2. **python-integration-tests**: API integration tests
3. **frontend-unit-tests**: JavaScript unit tests
4. **code-quality**: Linting and formatting checks
5. **security-scan**: Vulnerability scanning
6. **dependency-check**: Dependency audit
7. **build-test**: Build verification
8. **test-summary**: Results aggregation

#### Viewing Results

```bash
# Locally view coverage
# Python
open htmlcov/index.html

# JavaScript
open coverage/frontend/index.html

# CI/CD: Check Actions tab on GitHub
# Coverage reports uploaded to Codecov
```

---

## Coverage Requirements

### Global Thresholds

| Metric | Target | Current |
|--------|--------|---------|
| Lines | 60%+ | 85%+ |
| Branches | 60%+ | 80%+ |
| Functions | 60%+ | 85%+ |
| Statements | 60%+ | 85%+ |

### Module-Specific Requirements

| Module | Lines | Functions |
|--------|-------|-----------|
| API Endpoints | 80%+ | 80%+ |
| Core Models | 90%+ | 90%+ |
| Utilities | 85%+ | 85%+ |
| Scrapers | 80%+ | 80%+ |

### Exemptions

The following are exempt from coverage requirements:
- Test files themselves
- Configuration files
- Migration scripts
- Main entry points (tested via E2E)

---

## Best Practices

### General

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: When possible
3. **Descriptive Test Names**: `test_should_X_when_Y`
4. **Independent Tests**: No dependencies between tests
5. **Fast Tests**: Mock slow operations (API calls, DB queries)
6. **Clean Up**: Use fixtures and teardown methods

### Python-Specific

1. **Use Fixtures**: For reusable test data
2. **Mock External Dependencies**: APIs, file system, database
3. **Test Edge Cases**: Empty input, None, boundaries
4. **Use Parametrize**: For multiple similar test cases
5. **Type Hints**: In test code too (helps with IDE)

### JavaScript-Specific

1. **Mock Modules Early**: Before importing code under test
2. **Clean Up DOM**: After each test
3. **Test User Interactions**: Not implementation details
4. **Async/Await**: For async operations
5. **Snapshot Testing**: For UI components (use sparingly)

### Code Coverage

1. **Don't Game Coverage**: Write meaningful tests
2. **Cover Happy Paths**: First priority
3. **Cover Error Paths**: Second priority
4. **Cover Edge Cases**: Third priority
5. **Ignore Trivial Code**: Getters, setters, simple properties

### Continuous Improvement

1. **Review Failed Tests**: In CI/CD
2. **Update Tests**: When changing functionality
3. **Refactor Tests**: Keep them maintainable
4. **Monitor Trends**: Coverage should not decrease
5. **Add Tests**: For bug fixes (regression tests)

---

## Troubleshooting

### Common Issues

#### Python Tests

```bash
# ImportError: Module not found
export PYTHONPATH=$PWD
pytest

# Fixture not found
# Check conftest.py and import order

# Async tests hanging
# Add timeout: @pytest.mark.timeout(5)

# Mock not working
# Ensure patch path matches import path
```

#### JavaScript Tests

```bash
# Module not found
# Check jest.config.js moduleNameMapper

# Timeout errors
# Increase testTimeout in jest.config.js

# Mock not applied
# Ensure jest.unstable_mockModule before import

# DOM not available
# Check testEnvironment: 'jsdom' in config
```

### Getting Help

1. Check test output for detailed error messages
2. Review test documentation in `tests/frontend/README.md`
3. Check CI/CD logs in GitHub Actions
4. Run tests with `-vv` or `--verbose` for more details

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Testing Library](https://testing-library.com/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Pre-commit](https://pre-commit.com/)

---

## Quick Reference

```bash
# Backend
pytest -v                          # Run all Python tests
pytest --cov                       # With coverage
pytest -m "not slow"               # Fast tests only
pytest -x                          # Stop on first failure

# Frontend
npm test                           # Run all JS tests
npm run test:watch                 # Watch mode
npm run test:coverage              # With coverage

# Quality
pre-commit run --all-files         # Run all hooks
black .                            # Format Python
npm run lint                       # Lint JavaScript

# CI/CD
git push                           # Triggers CI
# Check GitHub Actions tab for results
```
