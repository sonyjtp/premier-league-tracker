# Testing Guide

## Overview

This project includes comprehensive unit tests, integration tests, and code quality checks with automated pre-commit and pre-push hooks.

**Coverage Requirements:**
- Minimum: **85%** overall code coverage
- Target: **90%+**

## Backend Testing

### Running Backend Tests

```bash
cd backend
pytest
```

### With Coverage Report

```bash
cd backend
pytest --cov=app --cov-report=html --cov-fail-under=85
```

Coverage report will be generated in `backend/htmlcov/index.html`

### Test Organization

```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_schemas.py          # Schema validation tests
├── test_crud.py             # Database CRUD operations
└── test_cache.py            # Cache operations
```

### Test Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| `app/schemas.py` | 95% | ✅ |
| `app/crud.py` | 92% | ✅ |
| `app/services/cache.py` | 88% | ✅ |
| `app/models.py` | 85% | ✅ |

## Frontend Testing

### Running Frontend Tests

```bash
cd frontend
npm run test
```

### With Coverage Report

```bash
cd frontend
npm run test:coverage
```

Coverage report will be generated in `frontend/coverage/`

### Test Organization

```
frontend/src/
├── components/
│   └── __tests__/
│       ├── Navbar.test.tsx
│       ├── LeaguesTab.test.tsx
│       └── PlayerPage.test.tsx
└── contexts/
    └── __tests__/
        └── SettingsContext.test.tsx
```

## Code Quality Checks

### Manual Linting

```bash
# Backend
cd backend
flake8 app --max-line-length=100 --extend-ignore=E203
black --check app
isort --check-only app

# Frontend
cd frontend
npm run lint
```

### Auto-formatting

```bash
# Backend
cd backend
black app
isort app

# Frontend
cd frontend
npx eslint --fix .
```

## Pre-Commit Hooks

Hooks automatically run on `git commit` and check:

✅ **Code Formatting**
- Black (Python code style)
- isort (Python import sorting)

✅ **Linting**
- flake8 (Python style violations)
- ESLint (TypeScript/React issues)

✅ **Testing**
- Unit tests with 85% coverage minimum
- Trailing whitespace, merge conflicts

### Setup Hooks

```bash
./setup-hooks.sh
```

This will:
1. Install pre-commit framework
2. Install all hooks
3. Register pre-commit and pre-push hooks

### Skip Hooks (When Needed)

```bash
git commit --no-verify
git push --no-verify  # Not recommended!
```

### Run Hooks Manually

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run pytest-check --all-files
```

## Pre-Push Checks

Before pushing to remote, the following checks run automatically:

✅ **Backend**
- Full test suite with 85% coverage requirement
- flake8 linting

✅ **Frontend**
- Full test suite with coverage report

**Important:** Push will be blocked if any check fails!

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/test.yml`):
- Runs on every pull request
- Checks code style, tests, coverage
- Required status check before merging

## Coverage Reports

### Viewing Reports

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm run test:coverage
open coverage/index.html
```

### Coverage Badges

- Backend: ![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
- Frontend: ![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)

## Writing Tests

### Backend Test Template

```python
import pytest
from app import crud, models

class TestMyFeature:
    def test_happy_path(self, db):
        # Setup
        obj = models.MyModel(field="value")
        db.add(obj)
        db.commit()

        # Execute
        result = crud.get_my_model(db, obj.id)

        # Assert
        assert result.field == "value"

    def test_error_case(self, db):
        # Should handle missing data gracefully
        result = crud.get_my_model(db, 999)
        assert result is None
```

### Frontend Test Template

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<MyComponent onClick={handleClick} />)
    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalled()
  })
})
```

## Troubleshooting

### Tests Failing After Environment Changes

```bash
# Backend
cd backend
pip install -r requirements.txt
pytest tests/ --co  # List all tests

# Frontend
cd frontend
npm ci
npm run test
```

### Coverage Below 85%

1. Identify uncovered files:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

2. Write tests for missing coverage

3. Run coverage again to verify

### Pre-commit Hooks Not Running

```bash
# Reinstall hooks
pre-commit install
pre-commit install --hook-type pre-push

# Verify hooks installed
cat .git/hooks/pre-commit
```

## Best Practices

✅ **DO:**
- Write tests as you code
- Aim for 85%+ coverage
- Test edge cases and errors
- Use descriptive test names
- Keep tests focused and small
- Mock external dependencies

❌ **DON'T:**
- Skip writing tests
- Test implementation details
- Have slow tests (>1s)
- Commit without running tests
- Push failing tests

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Coverage.py](https://coverage.readthedocs.io/)
