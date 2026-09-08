"""
Pytest configuration and shared fixtures for Cloud Files Backend tests
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import HttpUrl
import httpx


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_download_request():
    """Fixture for a sample DownloadRequest"""
    from app.models import DownloadRequest
    return DownloadRequest(
        url="https://example.com/files/document.pdf",
        access_token="test_access_token_12345"
    )


@pytest.fixture
def sample_access_token():
    """Fixture for a sample Google OAuth access token"""
    return "ya29.test_token_example_12345"


@pytest.fixture
def mock_httpx_response():
    """Fixture for a mocked httpx.Response"""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {
        "content-type": "application/pdf",
        "content-length": "1024000"
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_google_drive_service():
    """Fixture for a mocked Google Drive API service"""
    service = MagicMock()

    # Mock files().list().execute()
    files_list_mock = MagicMock()
    files_list_mock.execute.return_value = {
        "files": [{"id": "folder123", "name": "Drive-Drop"}]
    }
    service.files.return_value.list.return_value = files_list_mock

    # Mock files().create().execute()
    files_create_mock = MagicMock()
    files_create_mock.execute.return_value = {"id": "file123"}
    service.files.return_value.create.return_value = files_create_mock

    return service


@pytest.fixture
def mock_httpx_async_client():
    """Fixture for a mocked httpx.AsyncClient"""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_credentials():
    """Fixture for mocked Google OAuth credentials"""
    credentials = MagicMock()
    credentials.token = "test_access_token"
    return credentials


@pytest.fixture
def sample_file_data():
    """Fixture for sample file data"""
    return b"This is sample file content for testing purposes"


@pytest.fixture
def sample_large_file_data():
    """Fixture for large file data (over file limit)"""
    # Create data larger than FILE_LIMIT (1GB)
    size = (100 * 1024 * 1024) * 11  # 1.1 GB
    return b"x" * size


@pytest.fixture
def mock_queue():
    """Fixture for a mocked asyncio.Queue"""
    queue = MagicMock(spec=asyncio.Queue)
    queue.put = AsyncMock()
    queue.get = AsyncMock()
    queue.task_done = MagicMock()
    return queue


@pytest.fixture
def mock_drive_response():
    """Fixture for a mocked Google Drive upload response"""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 201
    response.json.return_value = {
        "id": "file123",
        "name": "uploaded_document.pdf",
        "webViewLink": "https://drive.google.com/file/d/file123/view"
    }
    response.raise_for_status = MagicMock()
    return response
