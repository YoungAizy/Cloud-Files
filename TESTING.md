# Cloud Files Backend - Test Suite Documentation

## Overview

This project includes a comprehensive test suite with **57 unit and integration tests** using pytest. The tests cover all major modules and functionality with proper mocking of external services (Google Drive API, httpx client, email notifications).

## Test Results Summary

✅ **57 tests passed**
- Unit tests: 50+
- Integration tests: 6+
- All async operations properly tested

## Project Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_models.py             # Pydantic model validation tests
├── test_main.py              # FastAPI endpoint tests
├── test_drive_upload.py       # Google Drive upload functionality tests
├── test_email_sender.py       # Email notification tests
└── test_httpx_stream.py       # HTTP streaming tests

pytest.ini                       # Pytest configuration
requirements-test.txt           # Testing dependencies
```

## Installation

### 1. Install Testing Dependencies

```bash
pip install -r requirements-test.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage measurement
- `pytest-mock` - Mocking utilities
- All application dependencies

### 2. Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Tests with Verbose Output

```bash
pytest tests/ -v
```

### Run Tests with Coverage Report

```bash
pytest tests/ --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/test_models.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_models.py::TestDownloadRequest -v
```

### Run Specific Test Method

```bash
pytest tests/test_models.py::TestDownloadRequest::test_valid_download_request -v
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run only async tests
pytest tests/ -m async
```

## Test Coverage

### test_models.py (10 tests)
Tests the Pydantic data models:
- ✅ Valid DownloadRequest creation
- ✅ URL validation (http/https, complex paths)
- ✅ Required field validation
- ✅ URL component extraction (host, path)
- ✅ Edge cases (empty tokens, invalid URLs)

### test_main.py (15 tests)
Tests FastAPI endpoints and request handling:
- ✅ Health endpoint (`GET /health`)
- ✅ Downloads endpoint (`POST /downloads`)
  - Request validation
  - Success responses
  - Error handling
  - Content-type verification
- ✅ Async download_file function
  - Successful file downloads
  - Error handling (ValueError, generic exceptions)
  - Email notification on completion/failure

### test_drive_upload.py (14 tests)
Tests Google Drive API integration:
- ✅ `get_g_service()` - Service initialization
- ✅ `create_upload_session()` - Session creation with proper headers
- ✅ `upload_chunk()` - Chunk upload with Content-Range headers
- ✅ `get_or_create_folder()` - Folder management
- ✅ `upload_g_drive()` - Full upload flow with size validation

### test_email_sender.py (7 tests)
Tests email notification functionality:
- ✅ Email retrieval from access token
- ✅ Success notifications
- ✅ Failure notifications
- ✅ Various payload formats (dict, string)
- ✅ Integration workflow tests

### test_httpx_stream.py (11 tests)
Tests HTTP streaming and chunking:
- ✅ Stream iterator initialization
- ✅ File streaming in chunks
- ✅ Chunk size enforcement
- ✅ File size limit enforcement (1GB)
- ✅ Empty stream handling
- ✅ Error handling
- ✅ Queue integration

## Key Testing Features

### Mocking Strategy
- External services are properly mocked (Google Drive API, httpx client)
- No real API calls are made during tests
- Fixtures provide consistent test data

### Async Support
- All async operations use `@pytest.mark.asyncio`
- AsyncMock properly used for async functions
- Event loop management handled via fixtures

### Test Organization
- Tests organized by functionality (one test file per module)
- Clear test class grouping for related tests
- Descriptive test names indicating what is being tested

### Markers for Test Classification
```python
@pytest.mark.unit       # Quick unit tests
@pytest.mark.integration # Integration tests (may be slower)
@pytest.mark.asyncio    # Async tests
```

## Fixtures (conftest.py)

Common fixtures available to all tests:

```python
sample_download_request      # Valid DownloadRequest object
sample_access_token         # Mock Google OAuth token
sample_file_data            # Sample file content (bytes)
sample_large_file_data      # Large file exceeding 1GB limit
mock_httpx_response         # Mocked httpx.Response
mock_google_drive_service   # Mocked Google Drive service
mock_httpx_async_client     # Mocked AsyncClient
mock_queue                  # Mocked asyncio.Queue
mock_drive_response         # Mocked successful upload response
```

Use fixtures in test functions:

```python
def test_something(mock_google_drive_service, sample_access_token):
    # Use fixtures here
    pass
```

## Coverage Goals

Current coverage includes:
- ✅ Model validation and edge cases
- ✅ API endpoint functionality
- ✅ Google Drive integration (mocked)
- ✅ Streaming and chunk handling
- ✅ Error handling and exceptions
- ✅ Async operations
- ✅ Email notifications (stubbed)

## Running Tests in CI/CD

Add to your CI/CD pipeline:

```bash
# Install dependencies
pip install -r requirements-test.txt

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Exit with failure if coverage below threshold
pytest tests/ --cov=app --cov-fail-under=70
```

## Debugging Tests

### Run with Print Statements
```bash
pytest tests/test_models.py -v -s
```

The `-s` flag captures stdout/print statements.

### Run with Detailed Traceback
```bash
pytest tests/ --tb=long
```

### Run Single Test with Full Output
```bash
pytest tests/test_models.py::TestDownloadRequest::test_valid_download_request -vv
```

## Common Issues & Solutions

### Issue: "Event loop is closed" warnings
**Solution:** These are expected for async tests with mocked services. They don't affect test results. They occur because mocked async tasks are cleaned up by the test framework.

### Issue: Tests taking too long
**Solution:** Run specific tests or use markers:
```bash
pytest tests/ -m unit  # Skip integration tests
```

### Issue: Import errors when running tests
**Solution:** Ensure you're in the backend directory:
```bash
cd "C:\Users\Administrator\Desktop\PROJECTS\Cloud Files\Backend"
pytest tests/
```

## Dependencies

See `requirements-test.txt` for full list. Key packages:

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | 7.4.3 | Test framework |
| pytest-asyncio | 0.21.1 | Async test support |
| pytest-cov | 4.1.0 | Coverage reporting |
| pytest-mock | 3.12.0 | Enhanced mocking |
| fastapi | 0.109.0 | Web framework |
| httpx | 0.25.2 | HTTP client |

## Adding New Tests

1. Create test file: `tests/test_module_name.py`
2. Import pytest and required modules
3. Create test class: `class TestFeatureName:`
4. Write test methods: `def test_specific_behavior(self):`
5. Use fixtures from `conftest.py` as needed
6. Run: `pytest tests/test_module_name.py -v`

Example:

```python
import pytest
from app.module import function_to_test

class TestMyFeature:
    @pytest.mark.unit
    def test_basic_functionality(self):
        result = function_to_test()
        assert result is True
```

## Continuous Integration

To integrate with GitHub Actions, create `.github/workflows/tests.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements-test.txt
      - run: pytest tests/ -v
```

## Summary

This comprehensive test suite ensures:
- ✅ Code quality and reliability
- ✅ Regression prevention
- ✅ Clear documentation through tests
- ✅ Safe refactoring
- ✅ External service integration validation (via mocks)

Total: **57 passing tests** covering all major functionality!
