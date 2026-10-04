"""Server-Side Request Forgery (SSRF) guard and safe HTTP transport."""

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import httpcore
import httpx

from mcp_forge.errors import SSRFBlockedError
from mcp_forge.version import __version__

FORGE_USER_AGENT = f"MCP-Forge/{__version__}"

# Disallowed network ranges for outbound requests
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),  # Current network
    ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback IPv4
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),  # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),  # Loopback IPv6
    ipaddress.ip_network("::/128"),  # Unspecified
    ipaddress.ip_network("fc00::/7"),  # Unique local (RFC 4193)
    ipaddress.ip_network("fe80::/10"),  # Link-local IPv6
    ipaddress.ip_network("ff00::/8"),  # Multicast IPv6
    ipaddress.ip_network("2001:db8::/32"),  # Documentation IPv6
]


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address falls within any blocked network range."""
    # Convert IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    for net in BLOCKED_NETWORKS:
        if ip in net:
            return True
    return False


def _try_parse_numeric_ip(host: str) -> ipaddress.IPv4Address | None:
    """Detect integer, hex, or octal representations of IPv4 addresses."""
    # Plain integer string (e.g. 2130706433 -> 127.0.0.1)
    if host.isdigit():
        try:
            return ipaddress.IPv4Address(int(host))
        except ValueError:
            pass

    # Hex representation (e.g. 0x7f000001)
    if host.lower().startswith("0x"):
        try:
            return ipaddress.IPv4Address(int(host, 16))
        except ValueError:
            pass

    # Octal representation (e.g. 0177.0.0.1)
    parts = host.split(".")
    if len(parts) == 4 and any(p.startswith("0") and len(p) > 1 for p in parts):
        try:
            octal_int = 0
            for part in parts:
                val = int(part, 8) if part.startswith("0") and len(part) > 1 else int(part)
                octal_int = (octal_int << 8) | val
            return ipaddress.IPv4Address(octal_int)
        except ValueError:
            pass

    return None


def validate_url_ssrf(url: str, allow_private: bool = False) -> str:
    """Validate a URL against SSRF vulnerabilities. Returns normalized URL string."""
    if not url or not isinstance(url, str):
        raise SSRFBlockedError("URL must be a non-empty string.")

    parsed = urlparse(url.strip())

    # Scheme check: only http and https permitted
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFBlockedError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
        )

    # Reject URLs containing embedded credentials (user:pass@host)
    if parsed.username or parsed.password:
        raise SSRFBlockedError("URLs with embedded authentication credentials are prohibited.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError("Invalid URL: missing host component.")

    if allow_private:
        return url

    # 1. Check numeric representations (decimal, hex, octal)
    numeric_ip = _try_parse_numeric_ip(hostname)
    if numeric_ip:
        if is_ip_blocked(numeric_ip):
            raise SSRFBlockedError(
                f"Access to blocked network address '{numeric_ip}' ({hostname}) is forbidden."
            )

    # 2. Check literal IP address
    try:
        ip = ipaddress.ip_address(hostname.strip("[]"))
        if is_ip_blocked(ip):
            raise SSRFBlockedError(f"Access to blocked IP address '{ip}' is forbidden.")
        return url
    except ValueError:
        pass

    # 3. Resolve DNS hostname and inspect all resolved IPs
    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFBlockedError(f"DNS resolution failed for host '{hostname}'.") from e

    if not resolved_ips:
        raise SSRFBlockedError(f"No IP addresses resolved for host '{hostname}'.")

    for item in resolved_ips:
        sockaddr = item[4]
        ip_str = sockaddr[0]
        ip_obj = ipaddress.ip_address(ip_str)
        if is_ip_blocked(ip_obj):
            raise SSRFBlockedError(f"Host '{hostname}' resolved to blocked IP '{ip_str}'.")

    return url


class SSRFProtectedNetworkBackend(httpcore.AnyIOBackend):
    """Network backend enforcing SSRF validation and connecting directly to the validated IP.

    Guarantees that the IP checked during DNS resolution is the exact IP connected to at the
    TCP socket level, eliminating TOCTOU / DNS rebinding attacks while preserving TLS SNI and
    hostname verification.
    """

    def __init__(self, allow_private: bool = False) -> None:
        super().__init__()
        self.allow_private = allow_private

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Any = None,
    ) -> httpcore.AsyncNetworkStream:
        if not self.allow_private:
            # 1. Numeric representations
            numeric_ip = _try_parse_numeric_ip(host)
            if numeric_ip and is_ip_blocked(numeric_ip):
                raise SSRFBlockedError(
                    f"Access to blocked network address '{numeric_ip}' ({host}) is forbidden."
                )

            # 2. Literal IP address
            try:
                literal_ip = ipaddress.ip_address(host.strip("[]"))
                if is_ip_blocked(literal_ip):
                    raise SSRFBlockedError(
                        f"Access to blocked IP address '{literal_ip}' is forbidden."
                    )
                return await super().connect_tcp(
                    host,
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except ValueError:
                pass

            # 3. Resolve DNS hostname and check all IP addresses
            try:
                resolved_ips = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            except socket.gaierror as e:
                raise SSRFBlockedError(f"DNS resolution failed for host '{host}'.") from e

            if not resolved_ips:
                raise SSRFBlockedError(f"No IP addresses resolved for host '{host}'.")

            chosen_ip: str | None = None
            for item in resolved_ips:
                ip_str = str(item[4][0])
                ip_obj = ipaddress.ip_address(ip_str)
                if is_ip_blocked(ip_obj):
                    raise SSRFBlockedError(f"Host '{host}' resolved to blocked IP '{ip_str}'.")
                if chosen_ip is None:
                    chosen_ip = ip_str

            target_connect_host = chosen_ip if chosen_ip else host
            return await super().connect_tcp(
                target_connect_host,
                port,
                timeout=timeout,
                local_address=local_address,
                socket_options=socket_options,
            )

        return await super().connect_tcp(
            host,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


async def safe_fetch_url(
    url: str,
    max_redirects: int = 3,
    allow_private: bool = False,
    timeout_s: float = 10.0,
    max_bytes: int = 10 * 1024 * 1024,
) -> tuple[bytes, str]:
    """Fetch URL with SSRF checks on initial URL, on all redirect hops, and at TCP socket level.

    Streams response chunks to enforce max_bytes before full buffering in memory.

    Returns:
        (content_bytes, content_type_header)
    """
    current_url = validate_url_ssrf(url, allow_private=allow_private)
    redirect_count = 0

    headers = {"User-Agent": FORGE_USER_AGENT}

    pool = httpcore.AsyncConnectionPool(
        network_backend=SSRFProtectedNetworkBackend(allow_private=allow_private)
    )
    transport = httpx.AsyncHTTPTransport()
    transport._pool = pool

    async with httpx.AsyncClient(
        transport=transport, timeout=timeout_s, follow_redirects=False
    ) as client:
        while True:
            async with client.stream("GET", current_url, headers=headers) as response:
                # Handle redirects manually to re-verify SSRF on each hop
                if response.is_redirect:
                    redirect_count += 1
                    if redirect_count > max_redirects:
                        raise SSRFBlockedError(f"Maximum redirects ({max_redirects}) exceeded.")

                    location = response.headers.get("Location")
                    if not location:
                        raise SSRFBlockedError("Redirect response missing Location header.")

                    # Resolve relative redirect URLs against current URL
                    next_url = str(response.url.join(location))
                    current_url = validate_url_ssrf(next_url, allow_private=allow_private)

                    # Strip credentials on cross-origin redirect
                    orig_parsed = urlparse(str(response.url))
                    next_parsed = urlparse(next_url)
                    if orig_parsed.netloc.lower() != next_parsed.netloc.lower():
                        headers = {
                            k: v
                            for k, v in headers.items()
                            if k.lower() not in ("authorization", "cookie")
                        }
                    continue

                # Check response status
                if response.status_code >= 400:
                    raise SSRFBlockedError(f"Remote server returned HTTP {response.status_code}.")

                # Safely inspect content length header before streaming
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        cl_bytes = int(content_length.strip())
                        if cl_bytes > max_bytes:
                            raise SSRFBlockedError(
                                f"Remote content size ({cl_bytes} bytes) exceeds limit ({max_bytes} bytes)."
                            )
                    except (ValueError, TypeError):
                        pass

                # Stream response content with strict chunk-by-chunk byte limit enforcement
                body_chunks: list[bytes] = []
                total_bytes = 0
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise SSRFBlockedError(
                            f"Remote response exceeded size limit of {max_bytes} bytes."
                        )
                    body_chunks.append(chunk)

                body = b"".join(body_chunks)
                content_type = response.headers.get("content-type", "")
                return body, content_type
