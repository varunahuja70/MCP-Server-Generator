"""Runtime HTTP client with timeouts, safe retries, backoff, and SSRF protection."""

import asyncio
import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import RuntimeConfig
from .logging import log
from .response import shape_error_response, shape_exception_error, shape_success_response

# Blocked private networks (matching Forge SSRF guard)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_private_target(url: str) -> bool:
    """Check if URL targets loopback, private, or metadata networks."""
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return True

    # Numeric or direct IP check
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        return any(ip in net for net in BLOCKED_NETWORKS)
    except ValueError:
        pass

    # Check common local hostnames
    if host.lower() in ("localhost", "127.0.0.1", "::1"):
        return True

    # DNS resolve
    try:
        addrinfo = socket.getaddrinfo(host, None)
        for _, _, _, _, sockaddr in addrinfo:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
            if any(ip in net for net in BLOCKED_NETWORKS):
                return True
    except Exception:  # noqa: S110
        pass

    return False


def _parse_retry_after(response: httpx.Response, default_wait: float) -> float:
    """Parse Retry-After header as seconds, if present."""
    header = response.headers.get("retry-after")
    if header and header.isdigit():
        return float(header)
    return default_wait


class ApiClient:
    """Async HTTP client for dispatching MCP tool requests."""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                follow_redirects=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def execute_request(
        self,
        method: str,
        url: str,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        json_body: Any = None,
        form_body: Any = None,
        tool_name: str | None = None,
    ) -> str:
        """Execute request with retries, backoff, SSRF checks, and response shaping."""
        # SSRF Check
        if not self.config.allow_private_targets and is_private_target(url):
            msg = (
                f"Blocked access to private network address '{url}'. "
                "Set ALLOW_PRIVATE_TARGETS=true in environment to permit local targets."
            )
            log("ERROR", msg, tool=tool_name)
            return msg

        client = await self.get_client()
        m = method.upper()
        is_safe_method = m in ("GET", "HEAD")

        max_attempts = 1 + (
            self.config.max_retries if (is_safe_method and self.config.retry_safe_requests) else 0
        )
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                log("INFO", f"Calling {m} {url} (attempt {attempt}/{max_attempts})", tool=tool_name)
                start_time = time.perf_counter()

                current_url = url
                current_method = m
                redirect_hops = 0
                max_hops = 5

                while True:
                    response = await client.request(
                        method=current_method,
                        url=current_url,
                        params=query_params if redirect_hops == 0 else None,
                        headers=headers,
                        cookies=cookies,
                        json=json_body if redirect_hops == 0 else None,
                        data=form_body if redirect_hops == 0 else None,
                    )

                    if response.is_redirect and redirect_hops < max_hops:
                        redirect_hops += 1
                        location = response.headers.get("location")
                        if not location:
                            break
                        next_url = str(response.url.join(location))
                        if not self.config.allow_private_targets and is_private_target(next_url):
                            msg = f"Blocked access to private network redirect target '{next_url}'."
                            log("ERROR", msg, tool=tool_name)
                            return msg
                        current_url = next_url
                        if response.status_code in (301, 302, 303) and current_method not in (
                            "GET",
                            "HEAD",
                        ):
                            current_method = "GET"
                        continue
                    break

                duration = time.perf_counter() - start_time

                # Check if retryable status code (429 or 503)
                if response.status_code in (429, 503) and attempt < max_attempts:
                    wait_time = _parse_retry_after(
                        response, default_wait=0.5 * (2 ** (attempt - 1))
                    )
                    log(
                        "WARN",
                        f"Received {response.status_code}, retrying in {wait_time}s",
                        tool=tool_name,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                if response.is_success:
                    log(
                        "INFO",
                        f"Request succeeded ({response.status_code}) in {duration:.2f}s",
                        tool=tool_name,
                    )
                    return shape_success_response(
                        response, max_chars=self.config.max_response_chars
                    )
                else:
                    log("WARN", f"Request failed with HTTP {response.status_code}", tool=tool_name)
                    return shape_error_response(response)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                if attempt < max_attempts:
                    wait_time = 0.5 * (2 ** (attempt - 1))
                    log("WARN", f"Network error: {exc}, retrying in {wait_time}s", tool=tool_name)
                    await asyncio.sleep(wait_time)
                else:
                    break
            except Exception as exc:
                last_error = exc
                break

        # If all attempts exhausted
        if last_error:
            log("ERROR", f"Request failed with exception: {last_error}", tool=tool_name)
            return shape_exception_error(last_error)

        return "Unknown error during request execution."
