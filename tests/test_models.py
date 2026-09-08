"""
Unit tests for app/models.py
Tests the Pydantic models and their validation
"""
import pytest
from pydantic import ValidationError
from app.models import DownloadRequest


class TestDownloadRequest:
    """Test suite for DownloadRequest model"""

    @pytest.mark.unit
    def test_valid_download_request(self):
        """Test creating a valid DownloadRequest"""
        request = DownloadRequest(
            url="https://example.com/files/document.pdf",
            access_token="test_access_token_12345"
        )
        # Verify URL is a string representation
        assert str(request.url) == "https://example.com/files/document.pdf"
        assert request.access_token == "test_access_token_12345"

    @pytest.mark.unit
    def test_download_request_with_http_url(self):
        """Test DownloadRequest accepts http:// URLs"""
        request = DownloadRequest(
            url="http://example.com/file.zip",
            access_token="token123"
        )
        assert str(request.url) == "http://example.com/file.zip"

    @pytest.mark.unit
    def test_download_request_with_https_url(self):
        """Test DownloadRequest accepts https:// URLs"""
        request = DownloadRequest(
            url="https://example.com/file.zip",
            access_token="token123"
        )
        assert str(request.url) == "https://example.com/file.zip"

    @pytest.mark.unit
    def test_download_request_url_with_path(self):
        """Test DownloadRequest URL with complex path"""
        request = DownloadRequest(
            url="https://example.com/path/to/file with spaces.pdf",
            access_token="token123"
        )
        assert "file%20with%20spaces.pdf" in str(request.url)

    @pytest.mark.unit
    def test_download_request_invalid_url(self):
        """Test DownloadRequest rejects invalid URLs"""
        with pytest.raises(ValidationError):
            DownloadRequest(
                url="not_a_valid_url",
                access_token="token123"
            )

    @pytest.mark.unit
    def test_download_request_missing_url(self):
        """Test DownloadRequest requires url field"""
        with pytest.raises(ValidationError):
            DownloadRequest(access_token="token123")

    @pytest.mark.unit
    def test_download_request_missing_access_token(self):
        """Test DownloadRequest requires access_token field"""
        with pytest.raises(ValidationError):
            DownloadRequest(url="https://example.com/file.pdf")

    @pytest.mark.unit
    def test_download_request_empty_access_token(self):
        """Test DownloadRequest with empty access token"""
        request = DownloadRequest(
            url="https://example.com/file.pdf",
            access_token=""
        )
        assert request.access_token == ""

    @pytest.mark.unit
    def test_download_request_url_path_extraction(self):
        """Test extracting path from URL"""
        request = DownloadRequest(
            url="https://example.com/files/document.pdf",
            access_token="test_access_token_12345"
        )
        path = request.url.path
        assert path == "/files/document.pdf"

    @pytest.mark.unit
    def test_download_request_url_host_extraction(self):
        """Test extracting host from URL"""
        request = DownloadRequest(
            url="https://files.example.com/download/document.pdf",
            access_token="token123"
        )
        assert request.url.host == "files.example.com"
