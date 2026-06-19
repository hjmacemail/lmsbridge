"""Vendor-side tooling to issue self-hosted license keys.

The private key stays with the vendor (you) and is NEVER shipped to customers. Customers
receive only the signed token (LICENSE_KEY) and the public key (LICENSE_PUBLIC_KEY).

Generate a signing keypair (once):
    python -m app.scripts.mint_license keygen --out ./license_keys
        -> writes license_private.pem (keep secret) and license_public.pem (ship to customers)

Mint a license token for a customer:
    python -m app.scripts.mint_license issue \
        --private ./license_keys/license_private.pem \
        --customer "Demo University" --plan enterprise --seats 5000 --days 365
        -> prints the signed LICENSE_KEY token to stdout
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from jose import jwt

from app.services.license_service import LICENSE_ISSUER


def _keygen(out_dir: str) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    (out / "license_private.pem").write_bytes(priv)
    (out / "license_public.pem").write_bytes(pub)
    print(f"Wrote {out/'license_private.pem'} (KEEP SECRET) and {out/'license_public.pem'}")


def _issue(args: argparse.Namespace) -> None:
    private_pem = Path(args.private).read_text()
    now = int(time.time())
    claims = {
        "iss": LICENSE_ISSUER,
        "sub": args.customer,
        "plan": args.plan,
        "seats": args.seats,
        "iat": now,
        "exp": now + args.days * 86400,
    }
    if args.features:
        claims["features"] = [f.strip() for f in args.features.split(",") if f.strip()]
    token = jwt.encode(claims, private_pem, algorithm="RS256")
    print(token)


def main() -> None:
    p = argparse.ArgumentParser(description="LMS Bridge self-hosted license tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("keygen", help="Generate a signing keypair")
    g.add_argument("--out", default="./license_keys")

    i = sub.add_parser("issue", help="Issue a signed license token")
    i.add_argument("--private", required=True, help="Path to license_private.pem")
    i.add_argument("--customer", required=True, help="Customer / institution name")
    i.add_argument("--plan", default="enterprise")
    i.add_argument("--seats", type=int, default=1000)
    i.add_argument("--days", type=int, default=365)
    i.add_argument("--features", default="", help="Comma-separated feature flags")

    args = p.parse_args()
    if args.cmd == "keygen":
        _keygen(args.out)
    elif args.cmd == "issue":
        _issue(args)


if __name__ == "__main__":
    main()
