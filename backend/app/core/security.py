"""Authentication and security primitives.

Implements PBKDF2-HMAC-SHA256 password hashing and HMAC-SHA256 signed bearer
tokens using Python standard library cryptographic modules. Zero external C-extensions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison."""
    if not plain_password or not hashed_password:
        return False
    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != PBKDF2_ALGORITHM:
        return False
    try:
        iterations = int(parts[1])
        salt = parts[2]
        expected_hash = parts[3]
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(dk.hex(), expected_hash)
    except (ValueError, TypeError):
        return False


def _b64encode_str(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode_str(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding and padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str)


def create_access_token(
    subject: str,
    secret_key: str,
    expires_in_seconds: int = 86400,
    claims: dict[str, Any] | None = None,
) -> str:
    """Generate a signed HMAC-SHA256 bearer token with expiration and arbitrary claims."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    if claims:
        payload.update(claims)

    header_bytes = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64encode_str(header_bytes)
    payload_b64 = _b64encode_str(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret_key.encode(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64encode_str(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and verify an HMAC-SHA256 bearer token.

    Raises ValueError if signature is invalid or token has expired.
    """
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(secret_key.encode(), signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64decode_str(signature_b64)
    except Exception as exc:
        raise ValueError("Malformed token signature encoding") from exc

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    try:
        payload_bytes = _b64decode_str(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Malformed token payload") from exc

    if not isinstance(payload, dict):
        raise ValueError("Token payload must be a JSON object")

    exp = payload.get("exp")
    if exp is not None:
        now = int(time.time())
        if now > exp:
            raise ValueError("Token has expired")

    return payload
