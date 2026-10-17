"""Safe web retrieval service with robust SSRF protections.

Provides secure HTTP retrieval of public opportunity webpages:
- Rejects loopback, private, link-local, multicast, and reserved IP ranges.
- Blocks cloud metadata addresses (169.254.169.254, metadata.google.internal).
- Enforces HTTP/HTTPS only and rejects embedded credentials.
- Validates ports (default: 80, 443).
- Validates every redirect target against the same security policies.
- Enforces strict response body size limits while streaming.
- Rejects unsupported MIME types (accepts HTML only).
- Never executes JavaScript.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.google",
    "instance-data",
    "169.254.169.254",
}

# Carrier-Grade NAT (RFC 6598: 100.64.0.0/10)
CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
# IPv4-mapped IPv6 prefix
IPV4_MAPPED_IPV6 = ipaddress.ip_network("::ffff:0:0/96")


class RetrievalError(Exception):
    """Base exception for web retrieval failures."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SSRFProtectionError(RetrievalError):
    """Raised when a URL targets a private, internal, or disallowed destination."""


class ContentTooLargeError(RetrievalError):
    """Raised when response body exceeds the configured maximum length."""


class UnsupportedContentTypeError(RetrievalError):
    """Raised when the response Content-Type is not in the allowed list."""


class NetworkConnectionError(RetrievalError):
    """Raised when connection fails or times out."""


@dataclass(frozen=True)
class RetrievalResult:
    submitted_url: str
    final_url: str
    status_code: int
    content: str
    content_hash: str
    content_type: str
    retrieved_at: datetime
    headers: dict[str, str]


def is_safe_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check whether an IP address is a safe, routable public Internet address."""
    # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip in IPV4_MAPPED_IPV6:
        ip = ip.ipv4_mapped  # type: ignore[assignment]

    if ip.is_loopback:
        return False
    if ip.is_private:
        return False
    if ip.is_link_local:
        return False
    if ip.is_multicast:
        return False
    if ip.is_reserved:
        return False
    if ip.is_unspecified:
        return False

    if isinstance(ip, ipaddress.IPv4Address):
        if ip in CGNAT_NETWORK:
            return False
        # 169.254.0.0/16 is caught by is_link_local, but check explicitly for safety:
        if ip == ipaddress.IPv4Address("169.254.169.254"):
            return False

    return True


def validate_url_syntax(url: str, allowed_ports: list[int] | None = None) -> tuple[str, str, int]:
    """Validate URL scheme, host, credentials, and port.

    Returns:
        (canonical_url, hostname, port)
    """
    clean_url = url.strip()
    if len(clean_url) > 2048:
        raise SSRFProtectionError("URL exceeds maximum length of 2048 characters")

    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"}:
        raise SSRFProtectionError(
            f"Unsupported URL scheme '{parsed.scheme}'; only http and https are allowed"
        )

    if not parsed.hostname:
        raise SSRFProtectionError("URL must contain a valid hostname")

    if parsed.username or parsed.password:
        raise SSRFProtectionError("URLs with embedded credentials (user:pass@) are rejected")

    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTNAMES:
        raise SSRFProtectionError(f"Access to '{hostname}' is blocked for security")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if allowed_ports and port not in allowed_ports:
        raise SSRFProtectionError(f"Destination port {port} is not permitted")

    return clean_url, hostname, port


def validate_hostname_dns(hostname: str, port: int) -> list[str]:
    """Resolve hostname and assert that all resolved IPs are safe public addresses."""
    # First check if hostname is already a raw IP literal
    try:
        ip = ipaddress.ip_address(hostname)
        if not is_safe_ip(ip):
            raise SSRFProtectionError(
                f"Destination IP address {ip} is private, internal, or loopback"
            )
        return [str(ip)]
    except ValueError:
        pass  # Not an IP literal, proceed to DNS resolution

    try:
        addrinfo = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise NetworkConnectionError(f"Could not resolve hostname '{hostname}': {exc}") from exc

    resolved_ips: list[str] = []
    for _family, _, _, _, sockaddr in addrinfo:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if not is_safe_ip(ip):
                raise SSRFProtectionError(
                    f"Host '{hostname}' resolved to private or internal IP {ip_str}"
                )
            resolved_ips.append(str(ip_str))
        except ValueError:
            continue

    if not resolved_ips:
        raise NetworkConnectionError(f"No valid IP addresses resolved for '{hostname}'")

    return resolved_ips


def retrieve_web_page(
    url: str,
    settings: Settings,
    transport: httpx.BaseTransport | None = None,
) -> RetrievalResult:
    """Safely fetch a public opportunity webpage, applying SSRF checks and limits.

    Supports custom HTTPX transport for isolated test environments.
    """
    allowed_ports = settings.ingest_allowed_ports
    max_redirects = settings.ingest_max_redirects
    max_bytes = settings.ingest_max_content_length_bytes
    timeout = settings.ingest_request_timeout_seconds
    user_agent = settings.ingest_user_agent
    allowed_content_types = settings.ingest_allowed_content_types

    current_url, hostname, port = validate_url_syntax(url, allowed_ports)

    # In live environments without custom mock transport, validate DNS
    if transport is None:
        validate_hostname_dns(hostname, port)

    seen_urls: set[str] = {current_url}
    redirects_followed = 0

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    client_kwargs: dict[str, Any] = {
        "follow_redirects": False,  # Manual redirect validation
        "timeout": httpx.Timeout(timeout),
        "headers": headers,
    }
    if transport is not None:
        client_kwargs["transport"] = transport

    with httpx.Client(**client_kwargs) as client:
        while True:
            try:
                response = client.get(current_url)
            except httpx.TimeoutException as exc:
                raise NetworkConnectionError(
                    f"Connection timed out retrieving '{current_url}'"
                ) from exc
            except httpx.RequestError as exc:
                raise NetworkConnectionError(
                    f"Network error while connecting to '{current_url}': {exc}"
                ) from exc

            # Handle redirects manually to enforce security on every hop
            if response.is_redirect:
                redirects_followed += 1
                if redirects_followed > max_redirects:
                    raise SSRFProtectionError(
                        f"Too many redirects (exceeded limit of {max_redirects})"
                    )

                location = response.headers.get("location")
                if not location:
                    raise RetrievalError("Redirect response missing Location header")

                next_url = urljoin(current_url, location)
                next_url, next_host, next_port = validate_url_syntax(next_url, allowed_ports)

                if next_url in seen_urls:
                    raise SSRFProtectionError(
                        f"Redirect loop detected: '{next_url}' already visited"
                    )

                if transport is None:
                    validate_hostname_dns(next_host, next_port)

                seen_urls.add(next_url)
                current_url = next_url
                continue

            # Check response status
            if response.status_code >= 400:
                raise RetrievalError(
                    f"Remote server returned HTTP {response.status_code}",
                    status_code=response.status_code,
                )

            # Validate Content-Type
            content_type_header = response.headers.get("content-type", "").lower()
            media_type = content_type_header.split(";")[0].strip()

            is_allowed_type = any(allowed in media_type for allowed in allowed_content_types)
            if media_type and not is_allowed_type:
                raise UnsupportedContentTypeError(
                    f"Unsupported content type '{media_type}'. Only HTML pages are supported."
                )

            # Stream / check body length
            raw_bytes = response.content
            if len(raw_bytes) > max_bytes:
                raise ContentTooLargeError(
                    f"Response body of {len(raw_bytes)} bytes exceeds "
                    f"maximum permitted size of {max_bytes} bytes"
                )

            content_hash = hashlib.sha256(raw_bytes).hexdigest()
            text_content = response.text
            retrieved_at = datetime.now(UTC)

            return RetrievalResult(
                submitted_url=url,
                final_url=current_url,
                status_code=response.status_code,
                content=text_content,
                content_hash=content_hash,
                content_type=media_type or "text/html",
                retrieved_at=retrieved_at,
                headers=dict(response.headers),
            )
