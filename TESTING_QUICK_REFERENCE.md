# Quick Test Commands Reference

## Essential Commands

### Run all tests
```bash
pytest tests/
```

### Run tests with verbose output
```bash
pytest tests/ -v
```

### Run tests with coverage
```bash
pytest tests/ --cov=app
```

### Run specific test file
```bash
pytest tests/test_models.py
```

### Run specific test class
```bash
pytest tests/test_models.py::TestDownloadRequest
```

### Run specific test method
```bash
pytest tests/test_models.py::TestDownloadRequest::test_valid_download_request
```

## Filter Tests

### Run only unit tests
```bash
pytest tests/ -m unit
```

### Run only integration tests  
```bash
pytest tests/ -m integration
```

### Run only async tests
```bash
pytest tests/ -m async
```

## Output & Debugging

### Show print statements
```bash
pytest tests/ -s
```

### Show detailed traceback
```bash
pytest tests/ --tb=long
```

### Run with minimal output
```bash
pytest tests/ -q
```

### Run specific test and show output
```bash
pytest tests/test_models.py::TestDownloadRequest::test_valid_download_request -vv -s
```

## Installation

### First time setup
```bash
pip install -r requirements-test.txt
```

## Test Statistics

- **Total Tests**: 57 ✅
- **Passing**: 57 ✅
- **Coverage**: Models, Endpoints, Google Drive, Streaming, Email
- **Async Tests**: Full support with pytest-asyncio

## Files

- `tests/conftest.py` - Shared fixtures
- `tests/test_models.py` - Data model tests
- `tests/test_main.py` - FastAPI endpoint tests  
- `tests/test_drive_upload.py` - Google Drive tests
- `tests/test_email_sender.py` - Email tests
- `tests/test_httpx_stream.py` - Streaming tests
- `pytest.ini` - Pytest configuration
- `requirements-test.txt` - Test dependencies
