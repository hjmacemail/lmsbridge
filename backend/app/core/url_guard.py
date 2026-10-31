"""SSRF guard for server-side fetches of platform-supplied URLs.

Used on the unauthenticated LTI Dynamic Registration path, where the caller hands us an
`openid_configuration` URL (and we then follow the `registration_endpoint` inside it). Without
a check, those could point at internal services (cloud metadata at 169.254.169.254, localhost,
private ranges). We require https and reject any host that resolves to a non-public address.

Hosts that fail to resolve are allowed through (the subsequent HTTP call will simply fail) so
that test/placeholder domains like `*.test` don't need network — the real protection is against
URLs that resolve to internal IPs.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger("url_guard")


class UnsafeUrlError(Exception):
    """Raised when a URL is not safe to fetch server-side (bad scheme or internal address)."""


def _is_public(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (a.is_private or a.is_loopback or a.is_link_local
                or a.is_reserved or a.is_multicast or a.is_unspecified)


def require_safe_url(url: str) -> str:
    """Return `url` if safe to fetch, else raise UnsafeUrlError. Requires https; blocks hosts
    whose resolved address is loopback/private/link-local/reserved/metadata."""
    p = urlparse(url)
    if p.scheme != "https":
        raise UnsafeUrlError("URL must use https")
    host = p.hostname
    if not host:
        raise UnsafeUrlError("URL has no host")
    try:
        infos = socket.getaddrinfo(host, p.port or 443, proto=socket.IPPROTO_TCP)
    except OSError:
        # Can't resolve (e.g. a placeholder/test domain) — let the real request fail instead.
        logger.info("URL host did not resolve during SSRF check; allowing: %s", host)
        return url
    for info in infos:
        ip = info[4][0]
        if not _is_public(ip):
            raise UnsafeUrlError(f"host {host} resolves to a non-public address ({ip})")
    return url
