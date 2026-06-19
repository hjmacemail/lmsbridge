"""Fetch and cache a platform's JWK Set, and resolve the signing key by `kid`."""
from __future__ import annotations

import time

import httpx

_CACHE: dict[str, tuple[float, dict]] = {}
_TTL = 3600  # seconds


def get_jwks(key_set_url: str) -> dict:
    now = time.time()
    cached = _CACHE.get(key_set_url)
    if cached and now - cached[0] < _TTL:
        return cached[1]
    resp = httpx.get(key_set_url, timeout=10.0)
    resp.raise_for_status()
    jwks = resp.json()
    _CACHE[key_set_url] = (now, jwks)
    return jwks


def find_key(key_set_url: str, kid: str) -> dict:
    jwks = get_jwks(key_set_url)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    # kid not found — bust cache once (platform may have rotated keys).
    _CACHE.pop(key_set_url, None)
    for key in get_jwks(key_set_url).get("keys", []):
        if key.get("kid") == kid:
            return key
    raise ValueError(f"No JWKS key found for kid={kid}")


def prime_cache(key_set_url: str, jwks: dict) -> None:
    """Test/seed helper to inject a JWKS without a network call."""
    _CACHE[key_set_url] = (time.time(), jwks)
