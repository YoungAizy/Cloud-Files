"""
Unit and integration tests for app/ssrf.py
Tests SSRF (Server-Side Request Forgery) protection and URL validation
"""
import pytest
import socket
import ipaddress
from unittest.mock import AsyncMock, MagicMock, patch
from app.security.ssrf import (
    is_unsafe,
    validate_url,
    resolve_hostname,
    ALLOWED_SCHEMES
)


class TestIsPrivateOrReserved:
    """Test suite for is_unsafe function"""

    @pytest.mark.unit
    def test_private_ip_10_range(self):
        """Test detection of private IP in 10.0.0.0/8 range"""
        assert is_private_or_reserved("10.0.0.1") is True
        assert is_private_or_reserved("10.255.255.255") is True

    @pytest.mark.unit
    def test_private_ip_172_range(self):
        """Test detection of private IP in 172.16.0.0/12 range"""
        assert is_private_or_reserved("172.16.0.1") is True
        assert is_private_or_reserved("172.31.255.255") is True

    @pytest.mark.unit
    def test_private_ip_192_range(self):
        """Test detection of private IP in 192.168.0.0/16 range"""
        assert is_private_or_reserved("192.168.0.1") is True
        assert is_private_or_reserved("192.168.255.255") is True

    @pytest.mark.unit
    def test_loopback_ip_v4(self):
        """Test detection of IPv4 loopback addresses"""
        assert is_private_or_reserved("127.0.0.1") is True
        assert is_private_or_reserved("127.255.255.255") is True

    @pytest.mark.unit
    def test_link_local_ip(self):
        """Test detection of link-local addresses (169.254.x.x)"""
        assert is_private_or_reserved("169.254.0.1") is True
        assert is_private_or_reserved("169.254.169.254") is True

    @pytest.mark.unit
    def test_multicast_ip(self):
        """Test detection of multicast addresses (224.0.0.0/4)"""
        assert is_private_or_reserved("224.0.0.1") is True
        assert is_private_or_reserved("239.255.255.255") is True

    @pytest.mark.unit
    def test_reserved_ip(self):
        """Test detection of reserved addresses"""
        # 0.0.0.0/8 reserved
        assert is_private_or_reserved("0.0.0.0") is True
        # 240.0.0.0/4 reserved
        assert is_private_or_reserved("240.0.0.1") is True
        assert is_private_or_reserved("255.255.255.255") is True

    @pytest.mark.unit
    def test_unspecified_ip(self):
        """Test detection of unspecified address"""
        assert is_private_or_reserved("0.0.0.0") is True

    @pytest.mark.unit
    def test_public_ip_allowed(self):
        """Test that public IPs are not flagged as private/reserved"""
        assert is_private_or_reserved("8.8.8.8") is False
        assert is_private_or_reserved("1.1.1.1") is False
        assert is_private_or_reserved("208.67.222.222") is False

    @pytest.mark.unit
    def test_ipv6_private_loopback(self):
        """Test detection of IPv6 loopback"""
        assert is_private_or_reserved("::1") is True

    @pytest.mark.unit
    def test_ipv6_private_link_local(self):
        """Test detection of IPv6 link-local addresses"""
        assert is_private_or_reserved("fe80::1") is True

    @pytest.mark.unit
    def test_ipv6_private_range(self):
        """Test detection of IPv6 private addresses"""
        assert is_private_or_reserved("fc00::1") is True
        assert is_private_or_reserved("fd00::1") is True

    @pytest.mark.unit
    def test_ipv6_unspecified(self):
        """Test detection of IPv6 unspecified address"""
        assert is_private_or_reserved("::") is True

    @pytest.mark.unit
    def test_ipv6_public_allowed(self):
        """Test that IPv6 public addresses are allowed"""
        assert is_private_or_reserved("2001:4860:4860::8888") is False


class TestResolveHostname:
    """Test suite for resolve_hostname async function"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_valid_hostname(self):
        """Test resolving a valid hostname"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80))
            ]

            result = await resolve_hostname("example.com")

            assert "8.8.8.8" in result
            mock_getaddrinfo.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_hostname_multiple_ips(self):
        """Test hostname resolving to multiple IP addresses"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.4.4', 80))
            ]

            result = await resolve_hostname("dns.google.com")

            assert len(result) == 2
            assert "8.8.8.8" in result
            assert "8.8.4.4" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_hostname_ipv6(self):
        """Test resolving hostname that returns IPv6 addresses"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:4860:4860::8888', 80, 0, 0))
            ]

            result = await resolve_hostname("ipv6.example.com")

            assert "2001:4860:4860::8888" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_hostname_mixed_ipv4_ipv6(self):
        """Test hostname resolving to both IPv4 and IPv6"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80)),
                (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:4860:4860::8888', 80, 0, 0))
            ]

            result = await resolve_hostname("example.com")

            assert len(result) == 2
            assert "8.8.8.8" in result
            assert "2001:4860:4860::8888" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_hostname_duplicates(self):
        """Test that duplicate IPs are deduplicated"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            # Same IP returned multiple times
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))
            ]

            result = await resolve_hostname("example.com")

            # Should deduplicate
            assert len(result) == 1
            assert "8.8.8.8" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_hostname_gaierror(self):
        """Test handling of DNS resolution error"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.side_effect = socket.gaierror("Name or service not known")

            with pytest.raises(socket.gaierror):
                await resolve_hostname("nonexistent.invalid.domain")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_resolve_localhost(self):
        """Test resolving localhost"""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))
            ]

            result = await resolve_hostname("localhost")

            assert "127.0.0.1" in result


class TestValidateUrl:
    """Test suite for validate_url async function"""

    # Scheme validation tests
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://example.com/path")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("http://example.com/path")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_scheme_ftp(self):
        """Test that FTP URLs are rejected"""
        with pytest.raises(ValueError, match="Only HTTP and HTTPS URLs are allowed"):
            await validate_url("ftp://example.com/file")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_scheme_file(self):
        """Test that file:// URLs are rejected"""
        with pytest.raises(ValueError, match="Only HTTP and HTTPS URLs are allowed"):
            await validate_url("file:///etc/passwd")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_scheme_data(self):
        """Test that data: URLs are rejected"""
        with pytest.raises(ValueError, match="Only HTTP and HTTPS URLs are allowed"):
            await validate_url("data:text/html,<script>alert('xss')</script>")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_scheme_case_insensitive(self):
        """Test that scheme validation is case-insensitive"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise - schemes should be normalized to lowercase
            await validate_url("HTTPS://example.com")
            await validate_url("HTTP://example.com")
            await validate_url("HtTpS://example.com")

    # Hostname validation tests
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_missing_hostname(self):
        """Test that URL without hostname is rejected"""
        with pytest.raises(ValueError, match="URL must contain a hostname"):
            await validate_url("http://")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_path_only(self):
        """Test that path-only URLs are rejected"""
        with pytest.raises(ValueError, match="URL must contain a hostname"):
            await validate_url("http:///path/to/file")

    # Direct IP address tests
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_public_ip_address_allowed(self):
        """Test that public IP addresses are allowed"""
        # Should not raise
        await validate_url("https://8.8.8.8/")
        await validate_url("http://1.1.1.1/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_localhost_ip_rejected(self):
        """Test that localhost IP is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://127.0.0.1/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_private_10_range_rejected(self):
        """Test that 10.x.x.x IP is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://10.0.0.1/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_private_172_range_rejected(self):
        """Test that 172.16-31.x.x IP is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://172.16.0.1/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_private_192_range_rejected(self):
        """Test that 192.168.x.x IP is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://192.168.1.1/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_reserved_ip_rejected(self):
        """Test that reserved IPs are rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://0.0.0.0/")
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://255.255.255.255/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_ipv6_loopback_rejected(self):
        """Test that IPv6 loopback is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://[::1]/")

    # Hostname resolution tests
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_dns_failure(self):
        """Test handling of DNS resolution failure"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.side_effect = ValueError("Unable to resolve hostname")

            with pytest.raises(ValueError, match="Unable to resolve hostname"):
                await validate_url("http://nonexistent.invalid.domain.example/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_resolves_to_public_ip(self):
        """Test that hostname resolving to public IP is allowed"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("http://example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_resolves_to_localhost(self):
        """Test that hostname resolving to localhost IP is rejected"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"127.0.0.1"}

            with pytest.raises(ValueError, match="resolves to a private or reserved IP"):
                await validate_url("http://localhost.example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_resolves_to_private_ip(self):
        """Test that hostname resolving to private IP is rejected"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"192.168.1.1"}

            with pytest.raises(ValueError, match="resolves to a private or reserved IP"):
                await validate_url("http://internal.example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_multiple_ips_one_private(self):
        """Test that hostname with any private IP is rejected"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            # Public and private IPs
            mock_resolve.return_value = {"8.8.8.8", "192.168.1.1"}

            with pytest.raises(ValueError, match="resolves to a private or reserved IP"):
                await validate_url("http://mixed.example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_multiple_ips_all_public(self):
        """Test that hostname with all public IPs is allowed"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8", "8.8.4.4", "1.1.1.1"}

            # Should not raise
            await validate_url("http://cdn.example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_hostname_empty_resolution(self):
        """Test handling of hostname that resolves to no IPs"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = set()

            with pytest.raises(ValueError, match="did not resolve to an IP address"):
                await validate_url("http://empty.example.com/")

    # Complex URL tests
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_port(self):
        """Test URL with port number"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://example.com:8443/path")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_credentials(self):
        """Test URL with username and password"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://user:pass@example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_query_string(self):
        """Test URL with query parameters"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://example.com/path?param=value&other=test")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_fragment(self):
        """Test URL with fragment identifier"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://example.com/path#section")

    # Edge cases
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_ipv6_address(self):
        """Test URL with IPv6 address"""
        # Public IPv6
        await validate_url("https://[2001:4860:4860::8888]/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_private_ipv6_address(self):
        """Test URL with private IPv6 address is rejected"""
        with pytest.raises(ValueError, match="private or reserved IP"):
            await validate_url("http://[fc00::1]/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_subdomain(self):
        """Test URL with multiple subdomains"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://api.v1.example.com/")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_url_with_hyphenated_domain(self):
        """Test URL with hyphens in domain"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"8.8.8.8"}

            # Should not raise
            await validate_url("https://my-domain.example.com/")


class TestSSRFIntegration:
    """Integration tests for SSRF protection"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_common_attack_localhost_variations(self):
        """Test various localhost attack patterns"""
        attack_urls = [
            "http://localhost/",
            "http://127.0.0.1/",
            "http://[::1]/",
            "http://0.0.0.0/",
        ]

        for url in attack_urls:
            with pytest.raises(ValueError):
                await validate_url(url)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_common_attack_internal_ips(self):
        """Test various internal IP attack patterns"""
        attack_urls = [
            "http://10.0.0.1/",
            "http://172.16.0.1/",
            "http://192.168.1.1/",
            "http://169.254.169.254/",  # AWS metadata
        ]

        for url in attack_urls:
            with pytest.raises(ValueError):
                await validate_url(url)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_legitimate_public_urls(self):
        """Test that legitimate public URLs are allowed"""
        with patch("app.ssrf.resolve_hostname") as mock_resolve:
            mock_resolve.return_value = {"1.1.1.1"}

            legitimate_urls = [
                "https://example.com/",
                "http://www.example.com/path",
                "https://api.example.com:443/v1/resource",
                "http://cdn.example.com/static/image.png",
            ]

            for url in legitimate_urls:
                # Should not raise
                await validate_url(url)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_messages_are_informative(self):
        """Test that error messages provide useful information"""
        # Private IP should mention IP address
        with pytest.raises(ValueError) as exc_info:
            await validate_url("http://192.168.1.1/")
        assert "192.168.1.1" not in str(exc_info.value)  # Don't leak IP in message
        assert "private or reserved IP" in str(exc_info.value)

        # Invalid scheme should mention scheme
        with pytest.raises(ValueError) as exc_info:
            await validate_url("ftp://example.com/")
        assert "HTTP and HTTPS" in str(exc_info.value)

        # Missing hostname
        with pytest.raises(ValueError) as exc_info:
            await validate_url("http://")
        assert "hostname" in str(exc_info.value)
