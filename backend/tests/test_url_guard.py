"""SSRF guard used on the LTI Dynamic Registration fetches."""
from __future__ import annotations

import pytest

from app.core.url_guard import UnsafeUrlError, require_safe_url


def test_requires_https():
    with pytest.raises(UnsafeUrlError):
        require_safe_url("http://canvas.instructure.com/.well-known")


@pytest.mark.parametrize("url", [
    "https://127.0.0.1/x",                       # loopback
    "https://169.254.169.254/latest/meta-data/", # cloud metadata (link-local)
    "https://10.0.0.5/register",                 # private
    "https://[::1]/x",                           # IPv6 loopback
])
def test_blocks_internal_addresses(url):
    with pytest.raises(UnsafeUrlError):
        require_safe_url(url)


def test_allows_unresolvable_placeholder():
    # A non-resolving domain is allowed through (the real HTTP call just fails) so test/
    # placeholder hosts don't need network; the guard's job is blocking internal IPs.
    assert require_safe_url("https://canvas.invalid/.well-known").endswith("/.well-known")
