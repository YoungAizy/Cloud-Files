"""
Unit tests for app/main.py
Tests the FastAPI endpoints and request handling
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, download_file
from app.models import DownloadRequest


@pytest.fixture
def client():
    """Fixture for FastAPI TestClient"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for /health endpoint"""

    @pytest.mark.unit
    def test_health_endpoint_returns_ok(self, client):
        """Test that /health endpoint returns ok status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.unit
    def test_health_endpoint_content_type(self, client):
        """Test that /health endpoint returns JSON"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestDownloadEndpoint:
    """Test suite for /downloads endpoint"""

    @pytest.mark.unit
    def test_downloads_endpoint_accepts_valid_request(self, client):
        """Test /downloads endpoint accepts valid request"""
        response = client.post("/downloads", json={
            "url": "https://example.com/files/document.pdf",
            "access_token": "test_access_token_12345"
        })
        assert response.status_code == 200

    @pytest.mark.unit
    def test_downloads_endpoint_returns_success_message(self, client):
        """Test /downloads endpoint returns success response"""
        response = client.post("/downloads", json={
            "url": "https://example.com/files/document.pdf",
            "access_token": "test_access_token_12345"
        })
        data = response.json()
        assert data["success"] is True
        assert "email" in data["message"].lower()

    @pytest.mark.unit
    def test_downloads_endpoint_rejects_invalid_url(self, client):
        """Test /downloads endpoint rejects invalid URL"""
        response = client.post(
            "/downloads",
            json={
                "url": "not_a_valid_url",
                "access_token": "token123"
            }
        )
        assert response.status_code == 422

    @pytest.mark.unit
    def test_downloads_endpoint_rejects_missing_url(self, client):
        """Test /downloads endpoint rejects missing URL"""
        response = client.post(
            "/downloads",
            json={"access_token": "token123"}
        )
        assert response.status_code == 422

    @pytest.mark.unit
    def test_downloads_endpoint_rejects_missing_token(self, client):
        """Test /downloads endpoint rejects missing access token"""
        response = client.post(
            "/downloads",
            json={"url": "https://example.com/file.pdf"}
        )
        assert response.status_code == 422

    @pytest.mark.unit
    def test_downloads_endpoint_with_https_url(self, client):
        """Test /downloads endpoint with https URL"""
        response = client.post(
            "/downloads",
            json={
                "url": "https://secure.example.com/download/file.pdf",
                "access_token": "secure_token"
            }
        )
        assert response.status_code == 200

    @pytest.mark.unit
    def test_downloads_endpoint_content_type(self, client):
        """Test /downloads endpoint returns JSON"""
        response = client.post("/downloads", json={
            "url": "https://example.com/files/document.pdf",
            "access_token": "test_access_token_12345"
        })
        assert response.headers["content-type"] == "application/json"


class TestDownloadFileFunction:
    """Test suite for download_file async function"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_download_file_with_valid_response(self):
        """Test download_file with valid HTTP response"""
        # Mock the request
        request = DownloadRequest(
            url="https://example.com/files/document.pdf",
            access_token="test_token"
        )

        # Mock httpx response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-length": "1024000"
        }
        mock_response.aiter_bytes = AsyncMock()

        # Mock stream context manager
        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        with patch("app.main.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch("app.main.upload_g_drive", new_callable=AsyncMock) as mock_upload:
                mock_upload.return_value = {
                    "uploaded_name": "document.pdf",
                    "webViewLink": "https://drive.google.com/file/d/123/view"
                }

                with patch("app.main.send_completion_email") as mock_email:
                    await download_file(request)

                    # Verify email was sent with success status
                    mock_email.assert_called_once()
                    call_args = mock_email.call_args[0]
                    assert call_args[0] == "test_token"
                    assert call_args[1] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_download_file_handles_value_error(self):
        """Test download_file handles ValueError gracefully"""
        request = DownloadRequest(
            url="https://example.com/files/oversized.bin",
            access_token="test_token"
        )

        # Mock a stream that immediately fails
        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(side_effect=ValueError("File too large"))
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        with patch("app.main.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch("app.main.send_completion_email") as mock_email:
                await download_file(request)

                # Verify error email was sent
                mock_email.assert_called_once()
                call_args = mock_email.call_args[0]
                assert call_args[1] is False  # is_successful = False
                assert "File too large" in call_args[2]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_download_file_handles_generic_exception(self):
        """Test download_file handles generic exceptions"""
        request = DownloadRequest(
            url="https://example.com/files/document.pdf",
            access_token="test_token"
        )

        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        with patch("app.main.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch("app.main.send_completion_email") as mock_email:
                await download_file(request)

                # Verify error email was sent
                mock_email.assert_called_once()
                call_args = mock_email.call_args[0]
                assert call_args[1] is False  # is_successful = False
                assert "Network error" in call_args[2]
