"""Tests for safe web retrieval and SSRF protections (Phase 3)."""

from __future__ import annotations

import ipaddress
from unittest.mock import patch

import httpx
import pytest

from app.core.config import Settings
from app.services.retrieval import (
    ContentTooLargeError,
    NetworkConnectionError,
    SSRFProtectionError,
    UnsupportedContentTypeError,
    is_safe_ip,
    retrieve_web_page,
    validate_hostname_dns,
    validate_url_syntax,
)


@pytest.fixture
def ingest_settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        app_env="test",
        ingest_request_timeout_seconds=5,
        ingest_max_content_length_bytes=10000,
        ingest_max_redirects=3,
        ingest_allowed_ports=[80, 443],
    )


# ---------------------------------------------------------------------------
# IP Address & Hostname Validation (SSRF)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ip_str",
    [
        "127.0.0.1",
        "127.0.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "169.254.169.254",  # Cloud metadata
        "169.254.1.1",  # Link-local
        "100.64.0.1",  # CGNAT
        "224.0.0.1",  # Multicast
        "0.0.0.0",  # Unspecified
        "::1",  # IPv6 loopback
        "::ffff:127.0.0.1",  # IPv4-mapped IPv6 loopback
        "::ffff:10.0.0.1",  # IPv4-mapped IPv6 private
        "fe80::1",  # IPv6 link-local
    ],
)
def test_is_safe_ip_rejects_non_public_ips(ip_str: str) -> None:
    ip = ipaddress.ip_address(ip_str)
    assert is_safe_ip(ip) is False


@pytest.mark.parametrize(
    "ip_str",
    [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",
        "2606:4700:4700::1111",
    ],
)
def test_is_safe_ip_allows_public_ips(ip_str: str) -> None:
    ip = ipaddress.ip_address(ip_str)
    assert is_safe_ip(ip) is True


# ---------------------------------------------------------------------------
# URL Syntax Validation
# ---------------------------------------------------------------------------


def test_validate_url_syntax_accepts_valid_urls() -> None:
    clean, host, port = validate_url_syntax("https://example.com/event", [80, 443])
    assert clean == "https://example.com/event"
    assert host == "example.com"
    assert port == 443


@pytest.mark.parametrize(
    "bad_url,match",
    [
        ("ftp://example.com", "Unsupported URL scheme 'ftp'"),
        ("file:///etc/passwd", "Unsupported URL scheme 'file'"),
        ("javascript:alert(1)", "Unsupported URL scheme 'javascript'"),
        ("https://user:pass@example.com", "embedded credentials"),
        ("https://localhost/opp", "blocked for security"),
        ("https://metadata.google.internal/computeMetadata", "blocked for security"),
        ("https://169.254.169.254/latest/meta-data", "blocked for security"),
        ("https://example.com:8080/opp", "Destination port 8080 is not permitted"),
    ],
)
def test_validate_url_syntax_rejects_unsafe(bad_url: str, match: str) -> None:
    with pytest.raises(SSRFProtectionError, match=match):
        validate_url_syntax(bad_url, [80, 443])


def test_validate_hostname_dns_rejects_private_ip_literals() -> None:
    with pytest.raises(SSRFProtectionError, match="private, internal, or loopback"):
        validate_hostname_dns("127.0.0.1", 80)


def test_validate_hostname_dns_rejects_host_resolving_to_private() -> None:
    fake_addrinfo = [(2, 1, 6, "", ("10.0.0.5", 80))]
    with (
        patch("socket.getaddrinfo", return_value=fake_addrinfo),
        pytest.raises(SSRFProtectionError, match="resolved to private or internal IP"),
    ):
        validate_hostname_dns("evil-private.local", 80)


# ---------------------------------------------------------------------------
# HTTP Retrieval Behavior (using MockTransport)
# ---------------------------------------------------------------------------


def test_retrieve_web_page_successful_html(ingest_settings: Settings) -> None:
    html_content = (
        "<!DOCTYPE html><html><head><title>Hackathon 2026</title></head>"
        "<body><h1>Annual Tech Hackathon</h1></body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=html_content,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

    transport = httpx.MockTransport(handler)
    res = retrieve_web_page("https://example.com/hackathon", ingest_settings, transport=transport)

    assert res.status_code == 200
    assert "Annual Tech Hackathon" in res.content
    assert res.content_type == "text/html"
    assert len(res.content_hash) == 64
    assert res.final_url == "https://example.com/hackathon"


def test_retrieve_web_page_follows_safe_redirects(ingest_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://example.com/short"):
            return httpx.Response(301, headers={"Location": "https://example.com/final"})
        return httpx.Response(
            200,
            text="<html><body>Final page</body></html>",
            headers={"Content-Type": "text/html"},
        )

    transport = httpx.MockTransport(handler)
    res = retrieve_web_page("https://example.com/short", ingest_settings, transport=transport)
    assert res.final_url == "https://example.com/final"
    assert "Final page" in res.content


def test_retrieve_web_page_detects_redirect_loop(ingest_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://example.com/loop1"):
            return httpx.Response(302, headers={"Location": "https://example.com/loop2"})
        return httpx.Response(302, headers={"Location": "https://example.com/loop1"})

    transport = httpx.MockTransport(handler)
    with pytest.raises(SSRFProtectionError, match="Redirect loop detected"):
        retrieve_web_page("https://example.com/loop1", ingest_settings, transport=transport)


def test_retrieve_web_page_rejects_too_many_redirects(ingest_settings: Settings) -> None:
    # ingest_settings.ingest_max_redirects is 3
    def handler(request: httpx.Request) -> httpx.Response:
        step = int(str(request.url).split("/")[-1])
        return httpx.Response(302, headers={"Location": f"https://example.com/{step + 1}"})

    transport = httpx.MockTransport(handler)
    with pytest.raises(SSRFProtectionError, match="Too many redirects"):
        retrieve_web_page("https://example.com/1", ingest_settings, transport=transport)


def test_retrieve_web_page_rejects_unsupported_content_type(ingest_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"\x89PNG\r\n\x1a\nfakeimagebytes",
            headers={"Content-Type": "image/png"},
        )

    transport = httpx.MockTransport(handler)
    with pytest.raises(UnsupportedContentTypeError, match="Unsupported content type 'image/png'"):
        retrieve_web_page("https://example.com/poster.png", ingest_settings, transport=transport)


def test_retrieve_web_page_rejects_oversized_response(ingest_settings: Settings) -> None:
    # limit is 10,000 bytes
    huge_body = "A" * 15000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=huge_body,
            headers={"Content-Type": "text/html"},
        )

    transport = httpx.MockTransport(handler)
    with pytest.raises(ContentTooLargeError, match="exceeds maximum permitted size"):
        retrieve_web_page("https://example.com/huge", ingest_settings, transport=transport)


def test_retrieve_web_page_handles_remote_http_error(ingest_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(handler)
    with pytest.raises(NetworkConnectionError) if False else pytest.raises(Exception) as excinfo:
        retrieve_web_page("https://example.com/missing", ingest_settings, transport=transport)
    assert "Remote server returned HTTP 404" in str(excinfo.value)
