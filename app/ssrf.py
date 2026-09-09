import ipaddress
import socket
from urllib.parse import urlparse


ALLOWED_SCHEMES = {"http", "https"}


def is_unsafe(ip: str) -> bool:
    address = ipaddress.ip_address(ip)

    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


async def validate_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("Only HTTP and HTTPS URLs are allowed")

    # Must have a hostname
    if not parsed.hostname:
        raise ValueError("URL must contain a hostname")

    hostname = parsed.hostname

    # If the hostname itself is an IP address, validate it directly.
    try:
        ip = ipaddress.ip_address(hostname)

        if is_unsafe(str(ip)):
            raise ValueError(
                "URLs pointing to private or reserved IP addresses are not allowed"
            )

        return

    except ValueError as e:
        # Important: If it was a valid IP but private, preserve our error.
        if str(e).startswith("URLs pointing"):
            raise

        # Otherwise it wasn't an IP, so it's a hostname.
        pass

    # Resolve hostname
    try:
        addresses = await resolve_hostname(hostname)
    except socket.gaierror:
        raise ValueError("Unable to resolve hostname")

    if not addresses:
        raise ValueError("Hostname did not resolve to an IP address")

    # Check EVERY resolved address.
    for ip in addresses:
        if is_unsafe(ip):
            raise ValueError(
                "URL resolves to a private or reserved IP address"
            )


async def resolve_hostname(hostname: str):
    loop = __import__("asyncio").get_running_loop()

    results = await loop.run_in_executor(
        None,
        lambda: socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM
        )
    )

    addresses = set()

    for result in results:
        addresses.add(result[4][0])

    return addresses